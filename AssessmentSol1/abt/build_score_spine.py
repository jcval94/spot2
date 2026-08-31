from __future__ import annotations

from pathlib import Path
import polars as pl

STAGES = ("T0", "T1", "T2")


def _dt(expr: str) -> pl.Expr:
    return pl.col(expr).str.to_datetime(strict=True)


def build_score_spine(repo_root: Path) -> pl.DataFrame:
    root = repo_root / "data" / "candidate" / "parquet"
    leads = pl.read_parquet(root / "leads.parquet")
    iq = (
        pl.read_parquet(root / "inquiries.parquet")
        .with_columns(_dt("inquiry_at").alias("_score_time"))
        .sort(["lead_id", "_score_time", "inquiry_id"])
        .with_columns(
            pl.int_range(1, pl.len() + 1).over("lead_id").alias("inquiry_number")
        )
    )

    t0 = leads.select(
        "lead_id",
        pl.lit("T0").alias("stage"),
        _dt("created_at").alias("score_time"),
        pl.lit(None, dtype=pl.Int64).alias("current_inquiry_id"),
        pl.lit(None, dtype=pl.Int64).alias("current_spot_id"),
        pl.lit(0).alias("inquiry_number"),
    )
    later = iq.select(
        "lead_id",
        pl.when(pl.col("inquiry_number") == 1)
        .then(pl.lit("T1"))
        .otherwise(pl.lit("T2"))
        .alias("stage"),
        pl.col("_score_time").alias("score_time"),
        pl.col("inquiry_id").cast(pl.Int64).alias("current_inquiry_id"),
        pl.col("spot_id").cast(pl.Int64).alias("current_spot_id"),
        "inquiry_number",
    )
    spine = pl.concat([t0, later], how="vertical").sort(
        ["lead_id", "score_time", "stage", "current_inquiry_id"]
    )
    return spine.with_columns(
        pl.when(pl.col("stage") == "T0")
        .then(pl.format("L{}:T0", pl.col("lead_id")))
        .when(pl.col("stage") == "T1")
        .then(
            pl.format(
                "L{}:T1:I{}",
                pl.col("lead_id"),
                pl.col("current_inquiry_id"),
            )
        )
        .otherwise(
            pl.format(
                "L{}:T2:I{}",
                pl.col("lead_id"),
                pl.col("current_inquiry_id"),
            )
        )
        .alias("prediction_key")
    ).select(
        "prediction_key",
        "lead_id",
        "stage",
        "score_time",
        "current_inquiry_id",
        "current_spot_id",
        "inquiry_number",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = repo_root / "AssessmentSol1" / "abt" / "artifacts"
    out.mkdir(parents=True, exist_ok=True)
    spine = build_score_spine(repo_root)
    spine.write_parquet(out / "score_spine.parquet")


if __name__ == "__main__":
    main()
