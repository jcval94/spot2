from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INVENTORY_DIR = ROOT / "AssessmentSol1" / "inventory"
ABT_DIR = ROOT / "AssessmentSol1" / "abt"
if str(INVENTORY_DIR) not in sys.path:
    sys.path.insert(0, str(INVENTORY_DIR))
if str(ABT_DIR) not in sys.path:
    sys.path.insert(0, str(ABT_DIR))

from build_inventory import build_inventory  # noqa: E402
from rank_fallbacks import rank_fallbacks  # noqa: E402
from _common import load_inquiries, load_leads, load_spots, read_raw, SPOT_ATTRIBUTE_FIELDS  # noqa: E402

OUTPUT_COLUMNS = [
    "lead_id", "score_time", "lead_quality_probability", "lead_quality_score_0_100",
    "inventory_actionability_gate", "inventory_serviceability", "inventory_confidence",
    "opportunity_score_0_100", "priority_band", "exact_spot_serviceable",
    "fallback_status", "fallback_spot_ids", "fallback_relaxation_tier", "reason_codes",
    "model_version", "inventory_version", "score_version", "data_fingerprint",
]

ACTIONABLE_RECOMMENDATION_STATUS = {"KNOWN_AVAILABLE", "VERIFY_AVAILABILITY"}


def load_score_config() -> dict[str, Any]:
    return json.loads((HERE / "frozen_score_config.json").read_text(encoding="utf-8"))


def load_recovered_config() -> dict[str, Any]:
    path = ROOT / "AssessmentSol1" / "models" / "lead_quality_recovery" / "frozen_recovered_model_config.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _assign_priority_bands(scored: pl.DataFrame, cfg: dict[str, Any]) -> pl.DataFrame:
    """Exact percentile bands; score ties are resolved only by the frozen lead_id tie-break."""
    n = scored.height
    n5 = math.ceil(n * 0.05)
    n10 = math.ceil(n * 0.10)
    n20 = math.ceil(n * 0.20)
    ranked = scored.sort(["opportunity_score_0_100", "lead_id"], descending=[True, False]).with_row_index("_rank", offset=1)
    return ranked.with_columns(
        pl.when(pl.col("_rank") <= n5).then(pl.lit("PRIORITY"))
        .when(pl.col("_rank") <= n10).then(pl.lit("HIGH"))
        .when(pl.col("_rank") <= n20).then(pl.lit("MEDIUM"))
        .otherwise(pl.lit("LOW")).alias("priority_band")
    ).drop("_rank")


def _recovered_probability_frame(repo_root: Path) -> pl.DataFrame:
    cfg = load_recovered_config()
    iq = (
        load_inquiries(repo_root)
        .filter(pl.col("inquiry_number") == 1)
        .select("lead_id", "inquiry_id", "spot_id", pl.col("_inquiry_time").alias("score_time"), "requested_area_sqm")
    )
    leads = load_leads(repo_root).select("lead_id", "preferred_state", "preferred_municipality", "preferred_corridor")
    spots = load_spots(repo_root).select(
        "spot_id", "spot_created_at", "area_sqm", "state", "municipality", "corridor"
    )
    attrs = read_raw(repo_root, "spot_attributes").select("spot_id", *SPOT_ATTRIBUTE_FIELDS)

    x = (
        iq.join(leads, on="lead_id", how="left", validate="m:1")
        .join(spots, on="spot_id", how="left", validate="m:1")
        .join(attrs, on="spot_id", how="left", validate="m:1")
    )
    if x.filter(pl.col("spot_created_at") > pl.col("score_time")).height:
        raise AssertionError("Recovered Lead Quality selected Spot is from the future")

    valid_area = (
        pl.col("requested_area_sqm").is_not_null()
        & (pl.col("requested_area_sqm") > 0)
        & pl.col("area_sqm").is_not_null()
    )
    area = (
        pl.when(valid_area)
        .then(
            (1.0 - ((pl.col("area_sqm") - pl.col("requested_area_sqm")).abs()
                    / pl.col("requested_area_sqm")).clip(0.0, 1.0))
        )
        .otherwise(None)
        .alias("selected_spot_area_closeness")
    )
    geo = (
        pl.when(pl.col("preferred_corridor").is_not_null() & (pl.col("corridor") == pl.col("preferred_corridor"))).then(1.0)
        .when(pl.col("preferred_municipality").is_not_null() & (pl.col("municipality") == pl.col("preferred_municipality"))).then(0.8)
        .when(pl.col("preferred_state").is_not_null() & (pl.col("state") == pl.col("preferred_state"))).then(0.5)
        .otherwise(0.0)
        .alias("selected_spot_geographic_fit")
    )
    completeness = (
        pl.mean_horizontal([pl.col(c).is_not_null().cast(pl.Float64) for c in SPOT_ATTRIBUTE_FIELDS])
        .alias("selected_spot_attribute_completeness")
    )
    x = x.with_columns(area, geo, completeness)

    ff = cfg["full_development_fit"]
    logit = pl.lit(float(ff["intercept"]))
    for spec in ff["preprocessing"]:
        name = spec["name"]
        z = ((pl.col(name).fill_null(float(spec["median"])) - float(spec["mean"])) / float(spec["std"]))
        logit = logit + float(ff["coefficients"][name]) * z
    x = x.with_columns(logit.alias("_logit")).with_columns(
        (1.0 / (1.0 + (-pl.col("_logit")).exp())).alias("lead_quality_probability")
    )
    return x.select("lead_id", "score_time", "lead_quality_probability")


def _fallback_aggregate(recs: pl.DataFrame) -> pl.DataFrame:
    if recs.is_empty():
        return pl.DataFrame(schema={
            "score_id": pl.String, "fallback_spot_ids": pl.List(pl.Int64),
            "fallback_relaxation_tier": pl.String,
        })
    return (
        recs.sort(["score_id", "rank"])
        .group_by("score_id", maintain_order=True)
        .agg(
            pl.col("spot_id").alias("fallback_spot_ids"),
            pl.col("relaxation_tier").first().alias("fallback_relaxation_tier"),
        )
    )


def build_scored_population(repo_root: Path, cfg: dict[str, Any] | None = None) -> pl.DataFrame:
    cfg = cfg or load_score_config()
    if cfg["status"] != "POST_RECOVERY_FROZEN_BEFORE_ANY_NEW_HOLDOUT_USE":
        raise AssertionError("Opportunity V2 config is not the frozen authority")

    lq = _recovered_probability_frame(repo_root)
    candidates = build_inventory(repo_root)
    recs, summary = rank_fallbacks(candidates)
    summary = summary.rename({"serviceability_score": "inventory_serviceability"})
    fb = _fallback_aggregate(recs)

    scored = (
        lq.with_columns(pl.format("L{}:T1", "lead_id").alias("_unused"))
        .join(summary.drop("score_id"), on=["lead_id", "score_time"], how="left", validate="1:1")
    )
    # Recover score_id only for fallback aggregation.
    score_id = candidates.select("score_id", "lead_id", "score_time").unique()
    scored = scored.join(score_id, on=["lead_id", "score_time"], how="left", validate="1:1")
    scored = scored.join(fb, on="score_id", how="left", validate="1:1")

    scored = scored.with_columns(
        pl.col("inventory_serviceability").fill_null(0.0),
        pl.col("inventory_confidence").fill_null(0.0),
        pl.col("exact_spot_serviceable").fill_null(False),
        pl.col("recommendation_status").fill_null("NO_RESULT"),
        pl.col("no_result_reason").fill_null("NO_INVENTORY"),
        pl.col("fallback_spot_ids").fill_null(pl.lit([], dtype=pl.List(pl.Int64))),
        pl.col("fallback_relaxation_tier").fill_null("NONE"),
    ).with_columns(
        pl.col("recommendation_status").is_in(list(ACTIONABLE_RECOMMENDATION_STATUS)).cast(pl.Int8).alias("inventory_actionability_gate"),
        (100.0 * pl.col("lead_quality_probability")).alias("lead_quality_score_0_100"),
    ).with_columns(
        (100.0 * pl.col("lead_quality_probability") * pl.col("inventory_actionability_gate")).alias("opportunity_score_0_100")
    )
    scored = _assign_priority_bands(scored, cfg)

    scored = scored.with_columns(
        pl.when(pl.col("recommendation_status") == "KNOWN_AVAILABLE")
        .then(pl.when(pl.col("no_result_reason") == "TIER3_ONLY_EXPERIMENTAL")
              .then(pl.lit("TIER3_ONLY_EXPERIMENTAL")).otherwise(pl.lit("KNOWN_AVAILABLE")))
        .when(pl.col("recommendation_status") == "VERIFY_AVAILABILITY").then(pl.lit("VERIFY_AVAILABILITY"))
        .otherwise(pl.col("no_result_reason")).alias("fallback_status"),
        pl.concat_list([
            pl.when(pl.col("exact_spot_serviceable")).then(pl.lit("EXACT_SERVICEABLE")).otherwise(pl.lit("NO_EXACT_SERVICEABLE")),
            pl.when(pl.col("inventory_actionability_gate") == 1).then(pl.lit("INVENTORY_ACTIONABLE")).otherwise(pl.lit("NO_RESULT")),
            pl.lit("BUDGET_UNVERIFIED_PRICE_NOT_PIT"),
        ]).alias("reason_codes"),
        pl.lit(cfg["lead_quality"]["version"]).alias("model_version"),
        pl.lit(cfg["inventory"]["version"]).alias("inventory_version"),
        pl.lit(cfg["score_version"]).alias("score_version"),
        pl.lit(cfg["data_fingerprints"]["raw_source_manifest_git_blob_sha1"]).alias("data_fingerprint"),
    )

    if scored["lead_id"].n_unique() != scored.height:
        raise AssertionError("V2 score must be one row per T1 lead")
    expected = 100.0 * scored["lead_quality_probability"] * scored["inventory_actionability_gate"]
    if (expected - scored["opportunity_score_0_100"]).abs().max() > 1e-12:
        raise AssertionError("Opportunity V2 formula mismatch")
    return scored.select(*OUTPUT_COLUMNS).sort(["score_time", "lead_id"])


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = HERE / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    scored = build_scored_population(repo_root)
    scored.write_csv(out / "scored_population.csv")
    scored.write_parquet(out / "scored_population.parquet")
    n = math.ceil(scored.height * load_score_config()["capacity_policy"]["selected_capacity_pct"] / 100)
    scored.sort(["opportunity_score_0_100", "lead_id"], descending=[True, False]).head(n).write_csv(out / "priority_leads.csv")
    print(json.dumps({"rows": scored.height, "priority_rows": n, "score_version": load_score_config()["score_version"]}, indent=2))


if __name__ == "__main__":
    main()
