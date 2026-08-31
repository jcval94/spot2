from __future__ import annotations

from pathlib import Path
import polars as pl

from _common import (
    LEAD_AUDIT_ONLY,
    LEAD_QUALITY_FEATURES,
    T0_HORIZON_DAYS,
    MATURITY_DAYS,
    FORBIDDEN_RAW_FEATURES,
    activity_horizon,
    add_binary_target,
    assert_columns_absent,
    ensure_output_dir,
    load_inquiries,
    load_leads,
    model_ready_filter,
)

TARGET_CONTRACT_ID = "T0_30D_INQUIRY_INITIATION_PROGRESS_V1"


def build_t0(repo_root: Path) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Build cold-start/sensitivity ABT at lead intake.

    Grain is exactly one row per lead. No inquiry payload, Spot context,
    Availability state, market context, or historical ABT is used as a feature.
    """
    leads = load_leads(repo_root)
    iq = load_inquiries(repo_root)
    horizon = activity_horizon(iq)

    base = leads.select(
        "lead_id",
        pl.format("L{}:T0", pl.col("lead_id")).alias("score_id"),
        pl.lit("T0").alias("stage"),
        pl.col("lead_created_at").alias("score_time"),
        *LEAD_QUALITY_FEATURES,
        *LEAD_AUDIT_ONLY,
    )

    # Label-only join. Inquiry/outcome fields are never selected into the ABT.
    events = (
        base.select("score_id", "lead_id", "score_time")
        .join(
            iq.select("lead_id", "_inquiry_time", "broker_response"),
            on="lead_id",
            how="left",
        )
        .filter(
            pl.col("_inquiry_time").is_not_null()
            & (pl.col("_inquiry_time") >= pl.col("score_time"))
            & (
                pl.col("_inquiry_time")
                <= pl.col("score_time") + pl.duration(days=T0_HORIZON_DAYS)
            )
        )
        .group_by("score_id")
        .agg(
            (pl.col("broker_response") == "scheduled_visit")
            .fill_null(False)
            .any()
            .alias("_t0_positive"),
            pl.col("broker_response").is_null().any().alias("_t0_ambiguous"),
        )
    )

    audit = (
        base.join(events, on="score_id", how="left")
        .with_columns(
            pl.col("_t0_positive").fill_null(False),
            pl.col("_t0_ambiguous").fill_null(False),
            (pl.col("score_time") + pl.duration(days=T0_HORIZON_DAYS + MATURITY_DAYS))
            .alias("target_mature_at"),
            pl.lit(TARGET_CONTRACT_ID).alias("target_contract_id"),
            pl.lit(T0_HORIZON_DAYS).cast(pl.Int16).alias("audit_label_horizon_days"),
        )
        .with_columns(
            pl.when(pl.col("target_mature_at") > pl.lit(horizon))
            .then(pl.lit("CENSORED"))
            .when(pl.col("_t0_positive"))
            .then(pl.lit("POSITIVE"))
            .when(pl.col("_t0_ambiguous"))
            .then(pl.lit("AMBIGUOUS"))
            .otherwise(pl.lit("NEGATIVE"))
            .alias("target_status")
        )
        .pipe(add_binary_target)
        .drop("_t0_positive", "_t0_ambiguous")
        .select(
            "score_id",
            "lead_id",
            "stage",
            "score_time",
            "target_contract_id",
            "target_mature_at",
            "target_status",
            "target_value",
            "audit_label_horizon_days",
            *LEAD_QUALITY_FEATURES,
            *LEAD_AUDIT_ONLY,
        )
        .sort("lead_id")
    )

    if audit.height != leads.height or audit["lead_id"].n_unique() != leads.height:
        raise AssertionError("T0 grain must be exactly one row per lead")

    model = model_ready_filter(audit).drop(
        "audit_label_horizon_days", *LEAD_AUDIT_ONLY
    )
    assert_columns_absent(model, FORBIDDEN_RAW_FEATURES, "abt_t0_model_ready")
    return audit, model


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = ensure_output_dir(repo_root)
    audit, model = build_t0(repo_root)
    audit.write_parquet(out / "abt_t0_audit_all_rows.parquet")
    model.write_parquet(out / "abt_t0_model_ready.parquet")


if __name__ == "__main__":
    main()
