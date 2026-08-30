from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import polars as pl

from build_score_spine import build_score_spine

MATURITY_DAYS = 14
T0_HORIZON_DAYS = 30
FORBIDDEN_RAW = {
    "lead_score_internal",
    "broker_response",
    "broker_response_hours",
    "days_on_market",
    "total_views",
    "total_inquiries",
    "is_active",
}

LEAD_FEATURES = [
    "user_type", "company_size", "industry", "search_sector", "search_modality",
    "target_area_sqm", "min_budget_mxn_rent_monthly",
    "max_budget_mxn_rent_monthly", "min_budget_mxn_sale_total",
    "max_budget_mxn_sale_total", "preferred_state", "preferred_municipality",
    "preferred_corridor", "source",
]
CURRENT_IQ_FEATURES = [
    "channel", "message_length", "requested_area_sqm",
    "requested_budget_mxn_rent_monthly", "requested_budget_mxn_sale_total",
    "urgency_days", "asked_visit",
]
SPOT_ATTR_FEATURES = [
    "natural_light", "luminaires", "charging_ports", "security_type",
    "floor_level", "elevators", "vertical_height_m", "parking_spaces",
    "building_status", "floor_material", "amenities",
]


def _read(repo_root: Path):
    root = repo_root / "data" / "candidate" / "parquet"
    leads = pl.read_parquet(root / "leads.parquet")
    iq = pl.read_parquet(root / "inquiries.parquet").with_columns(
        pl.col("inquiry_at").str.to_datetime(strict=True).alias("_inquiry_time")
    )
    spots = pl.read_parquet(root / "spots.parquet").select(
        "spot_id",
        pl.col("created_at").str.to_datetime(strict=True).alias("_spot_created"),
    )
    attrs = pl.read_parquet(root / "spot_attributes.parquet")
    return leads, iq, spots, attrs


def _history(iq: pl.DataFrame, spine: pl.DataFrame) -> pl.DataFrame:
    # Range join expressed as an inequality join: only strict prior inquiries.
    hist = (
        spine.select("prediction_key", "lead_id", "score_time")
        .join(iq, on="lead_id", how="left")
        .filter(pl.col("_inquiry_time") < pl.col("score_time"))
        .group_by("prediction_key")
        .agg(
            pl.len().alias("hist_prior_inquiry_count"),
            pl.col("spot_id").n_unique().alias("hist_prior_unique_spots"),
            pl.col("asked_visit").cast(pl.Int64).sum().alias("hist_prior_asked_visit_count"),
            pl.col("asked_visit").cast(pl.Float64).mean().alias("hist_prior_asked_visit_rate"),
            pl.col("message_length").mean().alias("hist_prior_message_length_mean"),
            pl.col("urgency_days").count().alias("hist_prior_urgency_known_count"),
            pl.col("urgency_days").mean().alias("hist_prior_urgency_days_mean"),
            pl.col("_inquiry_time").max().alias("hist_max_inquiry_time"),
        )
    )
    return spine.select("prediction_key").join(hist, on="prediction_key", how="left").with_columns(
        pl.col("hist_prior_inquiry_count").fill_null(0),
        pl.col("hist_prior_unique_spots").fill_null(0),
        pl.col("hist_prior_asked_visit_count").fill_null(0),
        pl.col("hist_prior_urgency_known_count").fill_null(0),
    )


def _t2_stage_status(spine: pl.DataFrame, iq: pl.DataFrame) -> pl.DataFrame:
    t2 = spine.filter(pl.col("stage") == "T2").select(
        "prediction_key", "lead_id", "score_time"
    )
    prior = (
        t2.join(iq, on="lead_id", how="left")
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
            ).alias("_known_at_score"),
            pl.col("_response_event_time").is_null().alias("_untimed"),
        )
        .group_by("prediction_key")
        .agg(
            pl.col("_known_at_score").any().alias("_known_prior_visit"),
            pl.col("_untimed").any().alias("_untimed_prior_visit"),
        )
    )
    return t2.select("prediction_key").join(prior, on="prediction_key", how="left").with_columns(
        pl.col("_known_prior_visit").fill_null(False),
        pl.col("_untimed_prior_visit").fill_null(False),
        pl.when(pl.col("_known_prior_visit"))
        .then(pl.lit("INELIGIBLE_PRIOR_SCHEDULED_VISIT"))
        .when(pl.col("_untimed_prior_visit"))
        .then(pl.lit("AMBIGUOUS_PRIOR_SCHEDULED_TIME"))
        .otherwise(pl.lit("ELIGIBLE"))
        .alias("stage_eligibility"),
    ).select("prediction_key", "stage_eligibility")


def build_lead_quality(repo_root: Path) -> tuple[pl.DataFrame, pl.DataFrame]:
    leads, iq, spots, attrs = _read(repo_root)
    spine = build_score_spine(repo_root)
    activity_horizon = iq["_inquiry_time"].max()

    current = iq.select(
        pl.col("inquiry_id").cast(pl.Int64).alias("current_inquiry_id"),
        pl.col("spot_id").cast(pl.Int64).alias("_iq_spot_id"),
        pl.col("broker_response").alias("_label_response"),
        pl.col("broker_response_hours").alias("_label_response_hours"),
        *CURRENT_IQ_FEATURES,
    )
    base = (
        spine.join(leads.select("lead_id", *LEAD_FEATURES, "prior_searches", "prior_inquiries", "has_converted_before"), on="lead_id", how="left")
        .join(current, on="current_inquiry_id", how="left")
        .join(spots, left_on="current_spot_id", right_on="spot_id", how="left")
        .join(attrs, left_on="current_spot_id", right_on="spot_id", how="left", suffix="_attr")
    )
    history = _history(iq, spine)
    base = base.join(history, on="prediction_key", how="left")

    t2_status = _t2_stage_status(spine, iq)
    base = base.join(t2_status, on="prediction_key", how="left").with_columns(
        pl.when(pl.col("stage") == "T2")
        .then(pl.col("stage_eligibility"))
        .otherwise(pl.lit("ELIGIBLE"))
        .alias("stage_eligibility")
    )

    # T0 secondary target.
    t0_events = (
        spine.filter(pl.col("stage") == "T0")
        .select("prediction_key", "lead_id", "score_time")
        .join(iq.select("lead_id", "_inquiry_time", "broker_response"), on="lead_id", how="left")
        .filter(
            (pl.col("_inquiry_time") >= pl.col("score_time"))
            & (
                pl.col("_inquiry_time")
                <= pl.col("score_time") + pl.duration(days=T0_HORIZON_DAYS)
            )
        )
        .group_by("prediction_key")
        .agg(
            (pl.col("broker_response") == "scheduled_visit").any().alias("_t0_positive"),
            pl.col("broker_response").is_null().any().alias("_t0_missing_status"),
        )
    )
    base = base.join(t0_events, on="prediction_key", how="left").with_columns(
        pl.col("_t0_positive").fill_null(False),
        pl.col("_t0_missing_status").fill_null(False),
    )

    mature_t1_t2 = (
        pl.col("score_time") + pl.duration(days=MATURITY_DAYS)
        <= pl.lit(activity_horizon)
    )
    mature_t0 = (
        pl.col("score_time")
        + pl.duration(days=T0_HORIZON_DAYS + MATURITY_DAYS)
        <= pl.lit(activity_horizon)
    )

    base = base.with_columns(
        pl.when(pl.col("stage_eligibility").str.starts_with("INELIGIBLE"))
        .then(pl.lit("INELIGIBLE"))
        .when(pl.col("stage_eligibility").str.starts_with("AMBIGUOUS"))
        .then(pl.lit("AMBIGUOUS"))
        .when((pl.col("stage") == "T0") & ~mature_t0)
        .then(pl.lit("CENSORED"))
        .when((pl.col("stage") != "T0") & ~mature_t1_t2)
        .then(pl.lit("CENSORED"))
        .when((pl.col("stage") == "T0") & pl.col("_t0_positive"))
        .then(pl.lit("POSITIVE"))
        .when((pl.col("stage") == "T0") & pl.col("_t0_missing_status"))
        .then(pl.lit("AMBIGUOUS"))
        .when(pl.col("stage") == "T0")
        .then(pl.lit("NEGATIVE"))
        .when(pl.col("_label_response").is_null())
        .then(pl.lit("AMBIGUOUS"))
        .when(pl.col("_label_response") == "scheduled_visit")
        .then(pl.lit("POSITIVE"))
        .otherwise(pl.lit("NEGATIVE"))
        .alias("target_status")
    ).with_columns(
        pl.when(pl.col("target_status") == "POSITIVE").then(1)
        .when(pl.col("target_status") == "NEGATIVE").then(0)
        .otherwise(None)
        .cast(pl.Int8)
        .alias("target_value"),
        (pl.col("_spot_created").is_null() | (pl.col("_spot_created") <= pl.col("score_time")))
        .alias("current_spot_existed_at_score_time"),
    )

    audit_only = ["prior_searches", "prior_inquiries", "has_converted_before"]
    safe_cols = [
        "prediction_key", "lead_id", "stage", "score_time", "current_inquiry_id",
        "current_spot_id", "inquiry_number", "stage_eligibility", "target_status",
        "target_value", "current_spot_existed_at_score_time",
        *LEAD_FEATURES, *CURRENT_IQ_FEATURES,
        "hist_prior_inquiry_count", "hist_prior_unique_spots",
        "hist_prior_asked_visit_count", "hist_prior_asked_visit_rate",
        "hist_prior_message_length_mean", "hist_prior_urgency_known_count",
        "hist_prior_urgency_days_mean", "hist_max_inquiry_time",
        *SPOT_ATTR_FEATURES, *audit_only,
    ]
    audit = base.select([c for c in safe_cols if c in base.columns])

    model_ready = audit.filter(
        pl.col("target_status").is_in(["POSITIVE", "NEGATIVE"])
        & (pl.col("stage_eligibility") == "ELIGIBLE")
        & pl.col("current_spot_existed_at_score_time")
    ).drop(audit_only)

    if FORBIDDEN_RAW.intersection(model_ready.columns):
        raise AssertionError("Forbidden raw predictor reached model_ready")
    return audit, model_ready


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = repo_root / "AssessmentSol1" / "abt" / "artifacts"
    out.mkdir(parents=True, exist_ok=True)
    audit, model = build_lead_quality(repo_root)
    audit.write_parquet(out / "lead_quality_audit_all_snapshots.parquet")
    model.write_parquet(out / "lead_quality_model_ready.parquet")


if __name__ == "__main__":
    main()
