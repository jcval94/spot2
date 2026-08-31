from __future__ import annotations

from pathlib import Path
import polars as pl


def build_inventory_state(repo_root: Path) -> pl.DataFrame:
    root = repo_root / "data" / "candidate" / "parquet"
    artifacts = repo_root / "AssessmentSol1" / "abt" / "artifacts"
    candidates = pl.read_parquet(artifacts / "candidate_spots.parquet")
    av = (
        pl.read_parquet(root / "availability_snapshot.parquet")
        .with_columns(
            pl.col("snapshot_date").str.to_date(strict=True).cast(pl.Datetime).alias("_snapshot_time")
        )
        .sort(["spot_id", "_snapshot_time", "snapshot_id"])
    )

    left = candidates.select(
        "prediction_key", "candidate_spot_id", "score_time"
    ).sort(["candidate_spot_id", "score_time"])
    right = av.rename({"spot_id": "candidate_spot_id"}).sort(
        ["candidate_spot_id", "_snapshot_time"]
    )

    joined = left.join_asof(
        right,
        left_on="score_time",
        right_on="_snapshot_time",
        by="candidate_spot_id",
        strategy="backward",
    )
    if joined.filter(pl.col("_snapshot_time") > pl.col("score_time")).height:
        raise AssertionError("Future Availability snapshot selected")

    joined = joined.with_columns(
        pl.col("snapshot_id").is_not_null().alias("snapshot_found"),
        (
            (pl.col("score_time") - pl.col("_snapshot_time"))
            .dt.total_seconds()
            .truediv(86_400)
        ).alias("snapshot_age_days"),
    ).with_columns(
        (pl.col("snapshot_found") & (pl.col("snapshot_age_days") > 30)).alias("stale_gt_30d"),
        (pl.col("snapshot_found") & (pl.col("snapshot_age_days") > 60)).alias("stale_gt_60d"),
        (pl.col("snapshot_found") & (pl.col("snapshot_age_days") > 90)).alias("stale_gt_90d"),
    ).with_columns(
        (pl.col("snapshot_found") & ~pl.col("stale_gt_90d")).alias("availability_known"),
        pl.when(pl.col("snapshot_found") & ~pl.col("stale_gt_90d"))
        .then(pl.col("is_available"))
        .otherwise(None)
        .alias("is_available_asof"),
        pl.when(pl.col("snapshot_found") & ~pl.col("stale_gt_90d"))
        .then(pl.col("days_until_available"))
        .otherwise(None)
        .alias("days_until_available_asof"),
        pl.col("competing_inquiries_30d").alias("competing_inquiries_30d_asof"),
        pl.when(~pl.col("snapshot_found"))
        .then(pl.lit("NO_SNAPSHOT"))
        .when(pl.col("stale_gt_90d"))
        .then(pl.lit("STALE_GT_90D"))
        .otherwise(pl.lit("COVERED"))
        .alias("coverage_status"),
        pl.lit(False).alias("competing_inquiries_30d_model_allowed"),
    )

    return joined.select(
        pl.format(
            "{}:S{}",
            pl.col("prediction_key"),
            pl.col("candidate_spot_id"),
        ).alias("inventory_state_key"),
        "prediction_key",
        "candidate_spot_id",
        "score_time",
        "snapshot_id",
        pl.col("_snapshot_time").alias("snapshot_time"),
        "snapshot_found",
        "availability_known",
        "is_available_asof",
        "days_until_available_asof",
        "competing_inquiries_30d_asof",
        "snapshot_age_days",
        "stale_gt_30d",
        "stale_gt_60d",
        "stale_gt_90d",
        "coverage_status",
        "competing_inquiries_30d_model_allowed",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "AssessmentSol1" / "abt" / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    build_inventory_state(repo_root).write_parquet(
        out_dir / "inventory_serviceability_state.parquet"
    )


if __name__ == "__main__":
    main()
