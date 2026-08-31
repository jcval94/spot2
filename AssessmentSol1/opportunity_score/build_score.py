from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INVENTORY_DIR = ROOT / "AssessmentSol1" / "inventory"
if str(INVENTORY_DIR) not in sys.path:
    sys.path.insert(0, str(INVENTORY_DIR))

from build_inventory import build_inventory, build_score_frame  # noqa: E402
from rank_fallbacks import rank_fallbacks  # noqa: E402


OUTPUT_COLUMNS = [
    "lead_id", "score_time", "lead_quality_probability", "lead_quality_score_0_100",
    "inventory_serviceability", "inventory_confidence", "opportunity_score_0_100",
    "priority_band", "exact_spot_serviceable", "fallback_status", "fallback_spot_ids",
    "fallback_relaxation_tier", "reason_codes", "model_version", "inventory_version",
    "data_fingerprint",
]


def load_score_config() -> dict[str, Any]:
    return json.loads((HERE / "frozen_score_config.json").read_text(encoding="utf-8"))


def _band_expr(cfg: dict[str, Any]) -> pl.Expr:
    bands = cfg["priority_bands"]
    return (
        pl.when(pl.col("opportunity_score_0_100") >= bands["PRIORITY"]["min_score_0_100"])
        .then(pl.lit("PRIORITY"))
        .when(pl.col("opportunity_score_0_100") >= bands["HIGH"]["min_score_0_100"])
        .then(pl.lit("HIGH"))
        .when(pl.col("opportunity_score_0_100") >= bands["MEDIUM"]["min_score_0_100"])
        .then(pl.lit("MEDIUM"))
        .otherwise(pl.lit("LOW"))
        .alias("priority_band")
    )


def _fallback_aggregate(recs: pl.DataFrame) -> pl.DataFrame:
    if recs.is_empty():
        return pl.DataFrame(
            schema={
                "score_id": pl.String,
                "fallback_spot_ids": pl.List(pl.Int64),
                "fallback_relaxation_tier": pl.String,
                "top_fallback_reason_codes": pl.List(pl.String),
            }
        )
    return (
        recs.sort(["score_id", "rank"])
        .group_by("score_id", maintain_order=True)
        .agg(
            pl.col("spot_id").alias("fallback_spot_ids"),
            pl.col("relaxation_tier").first().alias("fallback_relaxation_tier"),
            pl.col("reason_codes").first().alias("top_fallback_reason_codes"),
        )
    )


def build_scored_population(repo_root: Path, cfg: dict[str, Any] | None = None) -> pl.DataFrame:
    cfg = cfg or load_score_config()
    if cfg["status"] != "FROZEN_BEFORE_PROCEDURAL_HOLDOUT_EVALUATION":
        raise AssertionError("Opportunity score config is not the frozen authority")

    # Product spine is outcome-blind: one deterministic T1 score row per lead.
    spine = build_score_frame(repo_root).select("score_id", "lead_id", "score_time")
    candidates = build_inventory(repo_root)
    recs, summary = rank_fallbacks(candidates)

    summary = summary.rename({"serviceability_score": "inventory_serviceability"})
    fb = _fallback_aggregate(recs)
    scored = spine.join(summary, on=["score_id", "lead_id", "score_time"], how="left", validate="1:1")
    scored = scored.join(fb, on="score_id", how="left", validate="1:1")

    lq = float(cfg["lead_quality"]["probability"])
    fingerprint = (
        f'{cfg["data_fingerprints"]["raw_source_manifest_git_blob_sha1"]}:'
        f'{cfg["data_fingerprints"]["leads_csv_git_blob_sha1"]}:'
        f'{cfg["data_fingerprints"]["inquiries_csv_git_blob_sha1"]}:'
        f'{cfg["data_fingerprints"]["spots_csv_git_blob_sha1"]}:'
        f'{cfg["data_fingerprints"]["availability_snapshot_csv_git_blob_sha1"]}'
    )

    scored = scored.with_columns(
        pl.col("inventory_serviceability").fill_null(0.0),
        pl.col("inventory_confidence").fill_null(0.0),
        pl.col("exact_spot_serviceable").fill_null(False),
        pl.col("fallback_available").fill_null(False),
        pl.col("tier3_experimental_available").fill_null(False),
        pl.col("recommendation_status").fill_null("NO_RESULT"),
        pl.col("no_result_reason").fill_null("NO_INVENTORY"),
        pl.col("fallback_spot_ids").fill_null(pl.lit([], dtype=pl.List(pl.Int64))),
        pl.col("fallback_relaxation_tier").fill_null("NONE"),
        pl.col("top_fallback_reason_codes").fill_null(pl.lit([], dtype=pl.List(pl.String))),
    ).with_columns(
        pl.lit(lq).alias("lead_quality_probability"),
        pl.lit(100.0 * lq).alias("lead_quality_score_0_100"),
        (100.0 * pl.lit(lq) * pl.col("inventory_serviceability")).alias("opportunity_score_0_100"),
    ).with_columns(_band_expr(cfg))

    scored = scored.with_columns(
        pl.when(pl.col("recommendation_status") == "KNOWN_AVAILABLE")
        .then(pl.when(pl.col("no_result_reason") == "TIER3_ONLY_EXPERIMENTAL")
              .then(pl.lit("TIER3_ONLY_EXPERIMENTAL"))
              .otherwise(pl.lit("KNOWN_AVAILABLE")))
        .when(pl.col("recommendation_status") == "VERIFY_AVAILABILITY")
        .then(pl.lit("VERIFY_AVAILABILITY"))
        .otherwise(pl.col("no_result_reason"))
        .alias("fallback_status"),
        pl.concat_list([
            pl.when(pl.col("exact_spot_serviceable")).then(pl.lit("EXACT_SERVICEABLE")).otherwise(pl.lit("NO_EXACT_SERVICEABLE")),
            pl.when(pl.col("fallback_available")).then(pl.lit("SAME_SECTOR_FALLBACK_AVAILABLE")).otherwise(pl.lit("NO_SAME_SECTOR_FALLBACK")),
            pl.when(pl.col("tier3_experimental_available")).then(pl.lit("TIER3_EXPERIMENTAL_AVAILABLE")).otherwise(pl.lit("NO_TIER3_EXPERIMENTAL")),
            pl.lit("BUDGET_UNVERIFIED_PRICE_NOT_PIT"),
        ]).alias("reason_codes"),
        pl.lit(cfg["lead_quality"]["version"]).alias("model_version"),
        pl.lit(cfg["inventory"]["version"]).alias("inventory_version"),
        pl.lit(fingerprint).alias("data_fingerprint"),
    )

    if scored["lead_id"].n_unique() != scored.height:
        raise AssertionError("Product T1 score must be one row per lead")
    expected = 100.0 * scored["lead_quality_probability"] * scored["inventory_serviceability"]
    if (expected - scored["opportunity_score_0_100"]).abs().max() > 1e-12:
        raise AssertionError("Opportunity formula mismatch")
    if scored.filter(~pl.col("opportunity_score_0_100").is_between(0.0, 100.0)).height:
        raise AssertionError("Published score outside 0-100")

    return scored.select(*OUTPUT_COLUMNS).sort(["score_time", "lead_id"])


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = HERE / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    scored = build_scored_population(repo_root)
    scored.write_parquet(out / "scored_population.parquet")
    scored.write_csv(out / "scored_population.csv")
    scored.filter(pl.col("priority_band").is_in(["PRIORITY", "HIGH"])).sort(
        ["opportunity_score_0_100", "inventory_confidence", "lead_id"],
        descending=[True, True, False],
    ).write_csv(out / "priority_leads.csv")
    print(json.dumps({
        "rows": scored.height,
        "priority_or_high": scored.filter(pl.col("priority_band").is_in(["PRIORITY", "HIGH"])).height,
        "score_version": load_score_config()["score_version"],
    }, indent=2))


if __name__ == "__main__":
    main()
