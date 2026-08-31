from __future__ import annotations

import argparse
import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import Any

import polars as pl

from build_inventory import HERE as INVENTORY_DIR, build_inventory, load_config

AVAILABLE_STATES = {"AVAILABLE_NOW", "AVAILABLE_WITHIN_URGENCY"}
AVAILABILITY_PRIORITY = {
    "AVAILABLE_NOW": 0,
    "AVAILABLE_WITHIN_URGENCY": 1,
    "UNKNOWN": 2,
    "UNAVAILABLE": 3,
}


def _neg(value: Any, missing: float = -1.0) -> float:
    return -(missing if value is None else float(value))


def lexicographic_key(row: dict[str, Any]) -> tuple[Any, ...]:
    """Tier first, then deterministic within-tier quality."""
    return (
        int(row["relaxation_tier_index"]),
        AVAILABILITY_PRIORITY[str(row["availability_state"])],
        0 if bool(row["is_viable"]) else 1,
        _neg(row.get("area_fit_relative")),
        _neg(row.get("budget_fit")),
        _neg(row.get("inventory_confidence")),
        int(row["candidate_spot_id"]),
    )


def continuous_matching_score(row: dict[str, Any], config: dict[str, Any]) -> float:
    weights = config["ranking"]["continuous_weights"]
    values = {
        "area": row.get("area_fit_relative"),
        "budget": row.get("budget_fit"),
        "geography": row.get("location_fit"),
        "sector": row.get("sector_fit"),
        "availability": row.get("availability_fit"),
    }
    used = [(float(values[k]), float(weights[k])) for k in weights if values.get(k) is not None]
    denom = sum(weight for _, weight in used)
    if denom <= 0:
        return 0.0
    return sum(value * weight for value, weight in used) / denom


def _reason_codes(row: dict[str, Any]) -> list[str]:
    tier = str(row["relaxation_tier"])
    codes = [
        {
            "TIER_0": "EXACT_PREFERRED_MARKET",
            "TIER_1": "MUNICIPALITY_RELAXATION",
            "TIER_2": "STATE_RELAXATION",
            "TIER_3_EXPERIMENTAL": "EXPERIMENTAL_SECTOR_RELAXATION",
        }[tier]
    ]
    state = str(row["availability_state"])
    codes.append("VERIFY_AVAILABILITY" if state == "UNKNOWN" else state)
    area_fit = row.get("area_fit_relative")
    if area_fit is None:
        codes.append("AREA_UNKNOWN")
    elif float(area_fit) >= 0.5:
        codes.append("AREA_WITHIN_50PCT_RELATIVE_GAP")
    else:
        codes.append("AREA_WEAK_FIT")
    codes.append(str(row.get("budget_status") or "BUDGET_UNKNOWN"))
    bucket = str(row.get("freshness_bucket") or "UNKNOWN")
    codes.append(f"FRESHNESS_{bucket}")
    return codes


def rank_score_rows(rows: list[dict[str, Any]], config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    top_k = int(config["fallback"]["max_recommendations"])
    viable = [r for r in rows if bool(r.get("is_viable"))]
    known_available = [r for r in viable if r.get("availability_state") in AVAILABLE_STATES]
    unknown = [r for r in viable if r.get("availability_state") == "UNKNOWN"]

    known_available.sort(key=lexicographic_key)
    unknown.sort(key=lexicographic_key)

    if known_available:
        selected = known_available[:top_k]
        recommendation_status = "KNOWN_AVAILABLE"
    elif unknown:
        selected = unknown[:top_k]
        recommendation_status = "VERIFY_AVAILABILITY"
    else:
        selected = []
        recommendation_status = "NO_RESULT"

    recommendations: list[dict[str, Any]] = []
    for rank, row in enumerate(selected, start=1):
        recommendations.append(
            {
                "score_id": row["score_id"],
                "lead_id": row["lead_id"],
                "score_time": row["score_time"],
                "spot_id": row["candidate_spot_id"],
                "rank": rank,
                "relaxation_tier": row["relaxation_tier"],
                "modality_match": row["modality_match"],
                "sector_match": row["sector_match"],
                "area_gap": row.get("area_gap_relative"),
                "area_gap_sqm": row.get("area_gap_sqm"),
                "budget_gap": row.get("budget_gap"),
                "geographic_match": row["geographic_match"],
                "availability_state": row["availability_state"],
                "snapshot_age": row.get("snapshot_age_days"),
                "inventory_confidence": row.get("inventory_confidence"),
                "recommendation_status": recommendation_status,
                "reason_codes": _reason_codes(row),
            }
        )

    exact = any(
        bool(r.get("is_viable"))
        and int(r["relaxation_tier_index"]) == 0
        and r.get("availability_state") in AVAILABLE_STATES
        for r in rows
    )
    same_sector_fallback = any(
        bool(r.get("is_viable"))
        and int(r["relaxation_tier_index"]) in {1, 2}
        and r.get("availability_state") in AVAILABLE_STATES
        for r in rows
    )
    tier3_available = any(
        bool(r.get("is_viable"))
        and int(r["relaxation_tier_index"]) == 3
        and r.get("availability_state") in AVAILABLE_STATES
        for r in rows
    )

    viable_count = len(viable)
    available_viable_count = sum(r.get("availability_state") in AVAILABLE_STATES for r in viable)
    unknown_count = sum(r.get("availability_state") == "UNKNOWN" for r in viable)
    serviceability_score = max(
        (float(r.get("candidate_serviceability_score") or 0.0) for r in viable),
        default=0.0,
    )
    inventory_confidence = float(selected[0].get("inventory_confidence") or 0.0) if selected else 0.0

    if not rows:
        no_result_reason = "NO_INVENTORY"
    elif not viable:
        if rows and all(r.get("budget_status") not in {"UNKNOWN_PRICE_NOT_PIT", "MISSING_BUDGET"} for r in rows):
            no_result_reason = "BUDGET_OR_AREA_IMPOSSIBLE"
        else:
            no_result_reason = "NO_AREA_COMPATIBLE_INVENTORY"
    elif known_available:
        if all(int(r["relaxation_tier_index"]) == 3 for r in known_available):
            no_result_reason = "TIER3_ONLY_EXPERIMENTAL"
        else:
            no_result_reason = "OK"
    elif unknown:
        no_result_reason = "AVAILABILITY_UNKNOWN_VERIFY"
    else:
        no_result_reason = "ALL_UNAVAILABLE"

    summary = {
        "score_id": rows[0]["score_id"] if rows else None,
        "lead_id": rows[0]["lead_id"] if rows else None,
        "score_time": rows[0]["score_time"] if rows else None,
        "exact_spot_serviceable": exact,
        "viable_spot_count": viable_count,
        "available_viable_count": available_viable_count,
        "unknown_availability_count": unknown_count,
        "serviceability_score": serviceability_score,
        "inventory_confidence": inventory_confidence,
        "fallback_available": same_sector_fallback,
        "tier3_experimental_available": tier3_available,
        "recommendation_status": recommendation_status,
        "no_result_reason": no_result_reason,
        "budget_verified": False,
        "serviceability_completeness": "PARTIAL_PIT_NO_VERSIONED_PRICE",
    }
    return recommendations, summary


def rank_fallbacks(candidates: pl.DataFrame, config: dict[str, Any] | None = None) -> tuple[pl.DataFrame, pl.DataFrame]:
    config = config or load_config()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates.to_dicts():
        row["continuous_matching_score"] = continuous_matching_score(row, config)
        grouped[str(row["score_id"])].append(row)

    recommendations: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for score_id in sorted(grouped):
        recs, summary = rank_score_rows(grouped[score_id], config)
        recommendations.extend(recs)
        summaries.append(summary)

    rec_df = pl.DataFrame(recommendations) if recommendations else pl.DataFrame(
        schema={"score_id": pl.String, "spot_id": pl.Int64, "rank": pl.Int64}
    )
    summary_df = pl.DataFrame(summaries) if summaries else pl.DataFrame(
        schema={"score_id": pl.String, "serviceability_score": pl.Float64}
    )

    if rec_df.height:
        if rec_df.filter(pl.col("rank") > int(config["fallback"]["max_recommendations"])).height:
            raise AssertionError("More than five fallback recommendations emitted")
        if rec_df.group_by("score_id", "rank").len().filter(pl.col("len") > 1).height:
            raise AssertionError("Recommendation rank must be unique within score_id")
    return rec_df.sort(["score_id", "rank"]), summary_df.sort("score_id")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank deterministic Inventory fallbacks")
    parser.add_argument("--input", type=Path, default=None, help="Optional candidate Parquet; otherwise rebuild from raw")
    parser.add_argument("--development-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    cutoff = datetime(2026, 5, 1) if args.development_only else None
    candidates = pl.read_parquet(args.input) if args.input else build_inventory(
        repo_root, max_score_time_exclusive=cutoff
    )
    recs, summary = rank_fallbacks(candidates)
    out = INVENTORY_DIR / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    recs.write_parquet(out / "fallback_recommendations.parquet")
    summary.write_parquet(out / "score_serviceability.parquet")
    print(json.dumps({"recommendations": recs.height, "scores": summary.height}, indent=2))


if __name__ == "__main__":
    main()
