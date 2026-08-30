from __future__ import annotations

from pathlib import Path
import polars as pl

from _common import (
    CURRENT_INQUIRY_FEATURES,
    FORBIDDEN_RAW_FEATURES,
    HISTORY_FEATURES,
    LEAD_AUDIT_ONLY,
    LEAD_QUALITY_FEATURES,
    MATURITY_DAYS,
    activity_horizon,
    add_binary_target,
    assert_columns_absent,
    ensure_output_dir,
    load_inquiries,
    load_leads,
    load_spots,
    model_ready_filter,
    target_status_expr,
)

TARGET_CONTRACT_ID = "T2_CURRENT_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1"


def _strict_history(iq: pl.DataFrame, current: pl.DataFrame) -> pl.DataFrame:
    refs = current.select("score_id", "lead_id", "score_time")
    hist = (
        refs.join(
            iq.select(
                "lead_id",
                "_inquiry_time",
                "spot_id",
                "asked_visit",
                "message_length",
                "urgency_days",
            ),
            on="lead_id",
            how="left",
        )
        .filter(pl.col("_inquiry_time") < pl.col("score_time"))
        .group_by("score_id")
        .agg(
            pl.len().alias("hist_prior_inquiry_count"),
            pl.col("spot_id").n_unique().alias("hist_prior_unique_spots"),
            pl.col("asked_visit")
            .cast(pl.Int64)
            .sum()
            .alias("hist_prior_asked_visit_count"),
            pl.col("asked_visit")
            .cast(pl.Float64)
            .mean()
            .alias("hist_prior_asked_visit_rate"),
            pl.col("message_length").mean().alias("hist_prior_message_length_mean"),
            pl.col("urgency_days")
            .count()
            .alias("hist_prior_urgency_known_count"),
            pl.col("urgency_days").mean().alias("hist_prior_urgency_days_mean"),
            pl.col("_inquiry_time").max().alias("hist_max_inquiry_time"),
        )
    )
    return (
        refs.select("score_id")
        .join(hist, on="score_id", how="left")
        .with_columns(
            pl.col("hist_prior_inquiry_count").fill_null(0).cast(pl.Int64),
            pl.col("hist_prior_unique_spots").fill_null(0).cast(pl.Int64),
            pl.col("hist_prior_asked_visit_count").fill_null(0).cast(pl.Int64),
            pl.col("hist_prior_urgency_known_count").fill_null(0).cast(pl.Int64),
        )
    )


def _stage_eligibility(iq: pl.DataFrame, current: pl.DataFrame) -> pl.DataFrame:
    refs = current.select("score_id", "lead_id", "score_time")
    prior_visits = (
        refs.join(
            iq.select(
                "lead_id",
                "_inquiry_time",
                "broker_response",
                "broker_response_hours",
            ),
            on="lead_id",
            how="left",
        )
        .filter(
            (pl.col("_inquiry_time") < pl.col("score_time"))
            & (pl.col("broker_response") == "scheduled_visit")
        )
        .with_columns(
            pl.when(pl.col("broker_response_hours").is_not_null())
            .then(
                pl.col("_inquiry_time")
                + pl.duration(
                    milliseconds=(pl.col("broker_response_hours") * 3_600_000).cast(pl.Int64)
                )
            )
            .otherwise(None)
            .alias("_response_event_time")
        )
        .with_columns(
            (
                pl.col("_response_event_time").is_not_null()
                & (pl.col("_response_event_time") <= pl.col("score_time"))
            ).alias("_known_prior_visit"),
            pl.col("_response_event_time").is_null().alias("_untimed_prior_visit"),
        )
        .group_by("score_id")
        .agg(
            pl.col("_known_prior_visit").any().alias("_known_prior_visit"),
            pl.col("_untimed_prior_visit").any().alias("_untimed_prior_visit"),
        )
    )
    return (
        refs.select("score_id")
        .join(prior_visits, on="score_id", how="left")
        .with_columns(
            pl.col("_known_prior_visit").fill_null(False),
            pl.col("_untimed_prior_visit").fill_null(False),
        )
        .with_columns(
            pl.when(pl.col("_known_prior_visit"))
            .then(pl.lit("INELIGIBLE_PRIOR_SCHEDULED_VISIT_KNOWN"))
            .when(pl.col("_untimed_prior_visit"))
            .then(pl.lit("AMBIGUOUS_PRIOR_SCHEDULED_VISIT_TIME"))
            .otherwise(pl.lit("ELIGIBLE"))
            .alias("stage_eligibility")
        )
        .select("score_id", "stage_eligibility")
    )


def build_t2(
    repo_root: Path,
    *,
    max_score_time_exclusive=None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Build second-and-later inquiry challenger ABT.

    Current inquiry request fields are allowed. Historical features use only
    inquiry events with inquiry_at strictly earlier than the current score_time.
    No broker-response history is used as a predictive feature. Timed prior
    scheduled-visit responses may only determine cohort/stage eligibility; an
    untimed prior scheduled visit makes the snapshot ambiguous.
    """
    leads = load_leads(repo_root)
    iq = load_inquiries(repo_root)
    spots = load_spots(repo_root).select(
        pl.col("spot_id").cast(pl.Int64).alias("matching_current_spot_id"),
        "spot_created_at",
    )
    horizon = activity_horizon(iq)

    current = (
        iq.filter(pl.col("inquiry_number") >= 2)
        .select(
            "lead_id",
            pl.col("inquiry_id").cast(pl.Int64).alias("inquiry_id"),
            "inquiry_number",
            pl.col("_inquiry_time").alias("score_time"),
            pl.col("spot_id").cast(pl.Int64).alias("matching_current_spot_id"),
            pl.col("broker_response").alias("_label_response"),
            *CURRENT_INQUIRY_FEATURES,
        )
        .with_columns(
            pl.format(
                "L{}:T2:I{}", pl.col("lead_id"), pl.col("inquiry_id")
            ).alias("score_id")
        )
    )
    if max_score_time_exclusive is not None:
        current = current.filter(
            pl.col("score_time") < pl.lit(max_score_time_exclusive)
        )

    history = _strict_history(iq, current)
    stage_gate = _stage_eligibility(iq, current)

    audit = (
        current.join(
            leads.select("lead_id", *LEAD_QUALITY_FEATURES, *LEAD_AUDIT_ONLY),
            on="lead_id",
            how="left",
        )
        .join(history, on="score_id", how="left")
        .join(stage_gate, on="score_id", how="left")
        .join(spots, on="matching_current_spot_id", how="left")
        .with_columns(
            pl.lit("T2").alias("stage"),
            pl.lit(TARGET_CONTRACT_ID).alias("target_contract_id"),
            (pl.col("score_time") + pl.duration(days=MATURITY_DAYS)).alias(
                "target_mature_at"
            ),
            pl.when(pl.col("stage_eligibility").str.starts_with("INELIGIBLE"))
            .then(pl.lit("INELIGIBLE"))
            .when(pl.col("stage_eligibility").str.starts_with("AMBIGUOUS"))
            .then(pl.lit("AMBIGUOUS"))
            .otherwise(target_status_expr("_label_response", "score_time", horizon))
            .alias("target_status"),
            (
                pl.col("spot_created_at").is_not_null()
                & (pl.col("spot_created_at") <= pl.col("score_time"))
            ).alias("audit_current_spot_existed_at_score_time"),
            pl.lit(False).alias("audit_response_history_feature_used"),
        )
        .pipe(add_binary_target)
        .select(
            "score_id",
            "lead_id",
            "stage",
            "inquiry_id",
            "inquiry_number",
            "score_time",
            "target_contract_id",
            "target_mature_at",
            "target_status",
            "target_value",
            "stage_eligibility",
            *LEAD_QUALITY_FEATURES,
            *CURRENT_INQUIRY_FEATURES,
            *HISTORY_FEATURES,
            "hist_max_inquiry_time",
            "matching_current_spot_id",
            pl.col("spot_created_at").alias("audit_current_spot_created_at"),
            "audit_current_spot_existed_at_score_time",
            "audit_response_history_feature_used",
            *LEAD_AUDIT_ONLY,
        )
        .sort(["lead_id", "score_time", "inquiry_id"])
    )

    if audit.height != current.height or audit["inquiry_id"].n_unique() != current.height:
        raise AssertionError("T2 grain must be exactly one row per second-or-later inquiry")
    if audit.filter(
        pl.col("hist_max_inquiry_time").is_not_null()
        & (pl.col("hist_max_inquiry_time") >= pl.col("score_time"))
    ).height:
        raise AssertionError("T2 history contains same-time or future inquiry events")
    if audit["audit_response_history_feature_used"].any():
        raise AssertionError("T2 response history must remain disabled as a feature")

    model = model_ready_filter(audit).filter(
        pl.col("stage_eligibility") == "ELIGIBLE"
    ).select(
        "score_id",
        "lead_id",
        "stage",
        "inquiry_id",
        "inquiry_number",
        "score_time",
        "target_contract_id",
        "target_mature_at",
        "target_status",
        "target_value",
        *LEAD_QUALITY_FEATURES,
        *CURRENT_INQUIRY_FEATURES,
        *HISTORY_FEATURES,
    )
    assert_columns_absent(model, FORBIDDEN_RAW_FEATURES, "abt_t2_model_ready")
    if "matching_current_spot_id" in model.columns:
        raise AssertionError("Selected Spot leaked into T2 LeadQuality view")
    return audit, model


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = ensure_output_dir(repo_root)
    audit, model = build_t2(repo_root)
    audit.write_parquet(out / "abt_t2_audit_all_rows.parquet")
    model.write_parquet(out / "abt_t2_model_ready.parquet")


if __name__ == "__main__":
    main()
