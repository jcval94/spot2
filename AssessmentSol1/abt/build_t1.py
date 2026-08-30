from __future__ import annotations

from pathlib import Path
import polars as pl

from _common import (
    CURRENT_INQUIRY_FEATURES,
    FORBIDDEN_RAW_FEATURES,
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

TARGET_CONTRACT_ID = "T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1"


def build_t1(repo_root: Path) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Build the principal one-row-per-lead T1 ABT.

    The scoring instant is the deterministically selected first inquiry after
    its request payload is persisted and before its broker response is known.
    Selected Spot context is retained only in audit/matching columns and is
    excluded from the LeadQuality model-ready view.
    """
    leads = load_leads(repo_root)
    iq = load_inquiries(repo_root)
    spots = load_spots(repo_root).select(
        pl.col("spot_id").cast(pl.Int64).alias("matching_current_spot_id"),
        "spot_created_at",
    )
    horizon = activity_horizon(iq)

    first = (
        iq.filter(pl.col("inquiry_number") == 1)
        .select(
            "lead_id",
            pl.col("inquiry_id").cast(pl.Int64).alias("first_inquiry_id"),
            pl.col("_inquiry_time").alias("score_time"),
            pl.col("spot_id").cast(pl.Int64).alias("matching_current_spot_id"),
            pl.col("broker_response").alias("_label_response"),
            *CURRENT_INQUIRY_FEATURES,
        )
    )

    audit = (
        first.join(
            leads.select("lead_id", *LEAD_QUALITY_FEATURES, *LEAD_AUDIT_ONLY),
            on="lead_id",
            how="left",
        )
        .join(spots, on="matching_current_spot_id", how="left")
        .with_columns(
            pl.format(
                "L{}:T1:I{}", pl.col("lead_id"), pl.col("first_inquiry_id")
            ).alias("score_id"),
            pl.lit("T1").alias("stage"),
            pl.lit(TARGET_CONTRACT_ID).alias("target_contract_id"),
            (pl.col("score_time") + pl.duration(days=MATURITY_DAYS)).alias(
                "target_mature_at"
            ),
            target_status_expr("_label_response", "score_time", horizon).alias(
                "target_status"
            ),
            (
                pl.col("spot_created_at").is_not_null()
                & (pl.col("spot_created_at") <= pl.col("score_time"))
            ).alias("audit_current_spot_existed_at_score_time"),
        )
        .pipe(add_binary_target)
        .select(
            "score_id",
            "lead_id",
            "stage",
            "first_inquiry_id",
            "score_time",
            "target_contract_id",
            "target_mature_at",
            "target_status",
            "target_value",
            *LEAD_QUALITY_FEATURES,
            *CURRENT_INQUIRY_FEATURES,
            "matching_current_spot_id",
            pl.col("spot_created_at").alias("audit_current_spot_created_at"),
            "audit_current_spot_existed_at_score_time",
            *LEAD_AUDIT_ONLY,
        )
        .sort("lead_id")
    )

    expected = first.height
    if audit.height != expected or audit["lead_id"].n_unique() != expected:
        raise AssertionError("T1 grain must be exactly one first-inquiry row per lead")
    if audit["first_inquiry_id"].n_unique() != expected:
        raise AssertionError("T1 first_inquiry_id must be unique")

    model = model_ready_filter(audit).select(
        "score_id",
        "lead_id",
        "stage",
        "first_inquiry_id",
        "score_time",
        "target_contract_id",
        "target_mature_at",
        "target_status",
        "target_value",
        *LEAD_QUALITY_FEATURES,
        *CURRENT_INQUIRY_FEATURES,
    )
    assert_columns_absent(model, FORBIDDEN_RAW_FEATURES, "abt_t1_model_ready")
    if "matching_current_spot_id" in model.columns:
        raise AssertionError("Selected Spot leaked into primary T1 LeadQuality view")
    return audit, model


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = ensure_output_dir(repo_root)
    audit, model = build_t1(repo_root)
    audit.write_parquet(out / "abt_t1_audit_all_rows.parquet")
    model.write_parquet(out / "abt_t1_model_ready.parquet")


if __name__ == "__main__":
    main()
