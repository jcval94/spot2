from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any
import polars as pl

from _common import (
    FORBIDDEN_RAW_FEATURES,
    SPOT_ATTRIBUTE_FIELDS,
    SPOT_STRUCTURAL_FIELDS,
    UNVERSIONED_SPOT_FIELDS,
    assert_columns_absent,
    ensure_output_dir,
    load_leads,
    load_spots,
    parse_date,
    read_raw,
)
from build_t0 import build_t0
from build_t1 import build_t1
from build_t2 import build_t2


def _compatible_search_modes(spot_modality: str) -> tuple[str, ...]:
    if spot_modality == "both":
        return ("rent", "sale", "both")
    return (spot_modality, "both")


def _score_frame(repo_root: Path) -> pl.DataFrame:
    t0, _ = build_t0(repo_root)
    t1, _ = build_t1(repo_root)
    t2, _ = build_t2(repo_root)

    s0 = t0.select(
        "score_id", "lead_id", "stage", "score_time", "target_area_sqm",
        pl.lit(None, dtype=pl.Int64).alias("source_inquiry_id"),
        pl.lit(None, dtype=pl.Int64).alias("matching_current_spot_id"),
        pl.lit(None, dtype=pl.Float64).alias("requested_area_sqm"),
    )
    s1 = t1.select(
        "score_id", "lead_id", "stage", "score_time", "target_area_sqm",
        pl.col("first_inquiry_id").alias("source_inquiry_id"),
        "matching_current_spot_id",
        "requested_area_sqm",
    )
    s2 = t2.select(
        "score_id", "lead_id", "stage", "score_time", "target_area_sqm",
        pl.col("inquiry_id").alias("source_inquiry_id"),
        "matching_current_spot_id",
        "requested_area_sqm",
    )
    return pl.concat([s0, s1, s2], how="vertical").with_columns(
        pl.coalesce(["requested_area_sqm", "target_area_sqm"]).alias(
            "matching_area_reference_sqm"
        )
    )


def _candidate_rows(repo_root: Path, scores: pl.DataFrame) -> pl.DataFrame:
    leads = load_leads(repo_root).select(
        "lead_id",
        "search_sector",
        "search_modality",
        "preferred_state",
        "preferred_municipality",
        "preferred_corridor",
    )
    spots_df = load_spots(repo_root).select(
        "spot_id", "spot_created_at", *SPOT_STRUCTURAL_FIELDS
    )
    spots = spots_df.to_dicts()

    index: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for spot in spots:
        for search_mode in _compatible_search_modes(str(spot["modality"])):
            for level, value in (
                ("CORRIDOR", spot["corridor"]),
                ("MUNICIPALITY", spot["municipality"]),
                ("STATE", spot["state"]),
            ):
                if value is not None:
                    index[(str(spot["sector_name"]), search_mode, level, str(value))].append(spot)

    lead_lookup = {int(r["lead_id"]): r for r in leads.to_dicts()}
    spot_lookup = {int(r["spot_id"]): r for r in spots}
    rows: list[dict[str, Any]] = []

    for score in scores.to_dicts():
        lead = lead_lookup[int(score["lead_id"])]
        seen: set[int] = set()
        levels: list[tuple[str, Any]] = []
        if lead["preferred_corridor"] is not None:
            levels.append(("CORRIDOR", lead["preferred_corridor"]))
        if lead["preferred_municipality"] is not None:
            levels.append(("MUNICIPALITY", lead["preferred_municipality"]))
        if lead["preferred_state"] is not None:
            levels.append(("STATE", lead["preferred_state"]))

        for rank, (level, value) in enumerate(levels):
            key = (
                str(lead["search_sector"]),
                str(lead["search_modality"]),
                level,
                str(value),
            )
            for spot in index.get(key, []):
                sid = int(spot["spot_id"])
                if sid in seen or spot["spot_created_at"] > score["score_time"]:
                    continue
                seen.add(sid)
                rows.append(
                    _candidate_record(score, lead, spot, rank, level, "POLICY_UNIVERSE")
                )

        current_spot = score.get("matching_current_spot_id")
        if current_spot is not None:
            sid = int(current_spot)
            spot = spot_lookup.get(sid)
            # The observed Spot is not allowed to bypass the existence gate.
            if spot is not None and spot["spot_created_at"] <= score["score_time"] and sid not in seen:
                rows.append(
                    _candidate_record(
                        score,
                        lead,
                        spot,
                        99,
                        "OBSERVED_OVERRIDE",
                        "OBSERVED_CURRENT_OVERRIDE",
                    )
                )

    if not rows:
        raise AssertionError("Candidate policy produced zero rows")
    out = pl.DataFrame(rows)
    dupes = out.group_by("score_id", "candidate_spot_id").len().filter(pl.col("len") > 1)
    if dupes.height:
        raise AssertionError("inventory_candidates grain is not unique")
    if out.filter(pl.col("spot_created_at") > pl.col("score_time")).height:
        raise AssertionError("Future Spot entered inventory candidate universe")
    return out


def _candidate_record(
    score: dict[str, Any],
    lead: dict[str, Any],
    spot: dict[str, Any],
    rank: int,
    tier: str,
    source: str,
) -> dict[str, Any]:
    area_ref = score.get("matching_area_reference_sqm")
    area = spot.get("area_sqm")
    observed = (
        score.get("matching_current_spot_id") is not None
        and int(score["matching_current_spot_id"]) == int(spot["spot_id"])
    )
    modality_ok = str(lead["search_modality"]) in _compatible_search_modes(str(spot["modality"]))
    ratio = None
    gap = None
    if area_ref is not None and area is not None:
        gap = abs(float(area) - float(area_ref))
        if float(area_ref) != 0:
            ratio = float(area) / float(area_ref)

    return {
        "score_id": score["score_id"],
        "lead_id": score["lead_id"],
        "stage": score["stage"],
        "score_time": score["score_time"],
        "source_inquiry_id": score.get("source_inquiry_id"),
        "candidate_spot_id": int(spot["spot_id"]),
        "candidate_source": source,
        "matching_fallback_rank": rank,
        "matching_fallback_tier": tier,
        "matching_is_observed_current_spot": observed,
        "matching_sector_exact": str(spot["sector_name"]) == str(lead["search_sector"]),
        "matching_modality_compatible": modality_ok,
        "matching_candidate_type_name": spot.get("type_name"),
        "matching_candidate_state": spot.get("state"),
        "matching_candidate_municipality": spot.get("municipality"),
        "matching_candidate_settlement": spot.get("settlement"),
        "matching_candidate_corridor": spot.get("corridor"),
        "matching_candidate_region": spot.get("region"),
        "matching_candidate_lat": spot.get("lat"),
        "matching_candidate_lon": spot.get("lon"),
        "matching_candidate_area_sqm": area,
        "matching_candidate_modality": spot.get("modality"),
        "matching_area_reference_sqm": area_ref,
        "matching_area_gap_sqm": gap,
        "matching_area_ratio": ratio,
        "spot_created_at": spot["spot_created_at"],
    }


def _attach_attributes(repo_root: Path, candidates: pl.DataFrame) -> pl.DataFrame:
    attrs = read_raw(repo_root, "spot_attributes").select(
        pl.col("spot_id").cast(pl.Int64).alias("candidate_spot_id"),
        *[pl.col(c).alias(f"inventory_{c}") for c in SPOT_ATTRIBUTE_FIELDS],
    )
    return candidates.join(attrs, on="candidate_spot_id", how="left", validate="m:1")


def _attach_availability(repo_root: Path, candidates: pl.DataFrame) -> pl.DataFrame:
    av = parse_date(read_raw(repo_root, "availability_snapshot"), "snapshot_date")
    # Deterministic tie-break if more than one snapshot exists for a spot/date.
    av = (
        av.sort(["spot_id", "snapshot_date", "snapshot_id"])
        .unique(subset=["spot_id", "snapshot_date"], keep="last", maintain_order=True)
        .select(
            pl.col("spot_id").cast(pl.Int64).alias("candidate_spot_id"),
            "snapshot_id",
            pl.col("snapshot_date").alias("snapshot_date_asof"),
            "is_available",
            "days_until_available",
            # competing_inquiries_30d intentionally not selected.
        )
        .sort(["candidate_spot_id", "snapshot_date_asof"])
    )

    left = (
        candidates.with_columns(pl.col("score_time").dt.date().alias("_score_date"))
        .sort(["candidate_spot_id", "_score_date"])
    )
    joined = left.join_asof(
        av,
        left_on="_score_date",
        right_on="snapshot_date_asof",
        by="candidate_spot_id",
        strategy="backward",
    )
    if joined.filter(
        pl.col("snapshot_date_asof").is_not_null()
        & (pl.col("snapshot_date_asof") > pl.col("_score_date"))
    ).height:
        raise AssertionError("Future Availability snapshot selected")

    return (
        joined.with_columns(
            pl.col("snapshot_id").is_not_null().alias("availability_known"),
            (pl.col("_score_date") - pl.col("snapshot_date_asof"))
            .dt.total_days()
            .alias("snapshot_age_days"),
        )
        .with_columns(
            pl.when(pl.col("availability_known"))
            .then(pl.col("is_available"))
            .otherwise(None)
            .alias("is_available_asof"),
            pl.when(pl.col("availability_known"))
            .then(pl.col("days_until_available"))
            .otherwise(None)
            .alias("days_until_available_asof"),
            pl.when(~pl.col("availability_known"))
            .then(pl.lit("UNKNOWN"))
            .when(pl.col("snapshot_age_days") == 0)
            .then(pl.lit("SAME_DAY"))
            .when(pl.col("snapshot_age_days") <= 7)
            .then(pl.lit("1_7D"))
            .when(pl.col("snapshot_age_days") <= 30)
            .then(pl.lit("8_30D"))
            .when(pl.col("snapshot_age_days") <= 90)
            .then(pl.lit("31_90D"))
            .otherwise(pl.lit("GT_90D"))
            .alias("freshness_bucket"),
            pl.when(~pl.col("availability_known"))
            .then(pl.lit("UNKNOWN"))
            .when(pl.col("is_available"))
            .then(pl.lit("AVAILABLE"))
            .otherwise(pl.lit("UNAVAILABLE"))
            .alias("availability_state"),
        )
        .drop("_score_date", "is_available", "days_until_available")
    )


def build_inventory_candidates(repo_root: Path) -> tuple[pl.DataFrame, pl.DataFrame]:
    scores = _score_frame(repo_root)
    candidates = _candidate_rows(repo_root, scores)
    audit = _attach_availability(repo_root, _attach_attributes(repo_root, candidates))

    audit = audit.sort(["score_id", "matching_fallback_rank", "candidate_spot_id"])
    if audit.group_by("score_id", "candidate_spot_id").len().filter(pl.col("len") > 1).height:
        raise AssertionError("Availability/attribute joins caused row explosion")

    forbidden = FORBIDDEN_RAW_FEATURES | UNVERSIONED_SPOT_FIELDS
    assert_columns_absent(audit, forbidden, "inventory_candidates_audit_all_rows")

    model = audit.drop(
        "candidate_source",
        "spot_created_at",
        "snapshot_id",
        "snapshot_date_asof",
    )
    assert_columns_absent(model, forbidden, "inventory_candidates_model_ready")
    return audit, model


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = ensure_output_dir(repo_root)
    audit, model = build_inventory_candidates(repo_root)
    audit.write_parquet(out / "inventory_candidates_audit_all_rows.parquet")
    model.write_parquet(out / "inventory_candidates_model_ready.parquet")


if __name__ == "__main__":
    main()
