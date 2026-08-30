from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any
import polars as pl

from build_score_spine import build_score_spine

STRUCTURAL_SPOT_COLUMNS = [
    "spot_id", "sector_name", "type_name", "state", "municipality",
    "settlement", "corridor", "region", "lat", "lon", "area_sqm", "modality",
    "created_at",
]


def _compatible_search_modes(spot_modality: str) -> tuple[str, ...]:
    if spot_modality == "both":
        return ("rent", "sale", "both")
    return (spot_modality, "both")


def build_candidate_spots(repo_root: Path) -> pl.DataFrame:
    root = repo_root / "data" / "candidate" / "parquet"
    spine = build_score_spine(repo_root)
    leads = pl.read_parquet(root / "leads.parquet").select(
        "lead_id", "search_sector", "search_modality",
        "preferred_state", "preferred_municipality", "preferred_corridor",
    )
    spots_df = pl.read_parquet(root / "spots.parquet").select(*STRUCTURAL_SPOT_COLUMNS)
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
                    index[
                        (
                            str(spot["sector_name"]),
                            search_mode,
                            level,
                            str(value),
                        )
                    ].append(spot)

    lead_lookup = {int(r["lead_id"]): r for r in leads.to_dicts()}
    spot_lookup = {int(r["spot_id"]): r for r in spots}
    rows: list[dict[str, Any]] = []

    for snap in spine.to_dicts():
        lead = lead_lookup[int(snap["lead_id"])]
        seen: set[int] = set()
        levels = []
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
                if sid in seen:
                    continue
                created = pl.Series([spot["created_at"]]).str.to_datetime(strict=True)[0]
                if created > snap["score_time"]:
                    continue
                seen.add(sid)
                rows.append(
                    {
                        "prediction_key": snap["prediction_key"],
                        "lead_id": snap["lead_id"],
                        "stage": snap["stage"],
                        "score_time": snap["score_time"],
                        "candidate_spot_id": sid,
                        "fallback_rank": rank,
                        "fallback_tier": level,
                        "candidate_source": "POLICY_UNIVERSE",
                        "is_observed_current_spot": (
                            snap["current_spot_id"] is not None
                            and sid == int(snap["current_spot_id"])
                        ),
                    }
                )

        if snap["current_spot_id"] is not None:
            sid = int(snap["current_spot_id"])
            if sid not in seen:
                spot = spot_lookup[sid]
                created = pl.Series([spot["created_at"]]).str.to_datetime(strict=True)[0]
                if created > snap["score_time"]:
                    raise AssertionError("Observed current Spot did not exist at score_time")
                rows.append(
                    {
                        "prediction_key": snap["prediction_key"],
                        "lead_id": snap["lead_id"],
                        "stage": snap["stage"],
                        "score_time": snap["score_time"],
                        "candidate_spot_id": sid,
                        "fallback_rank": 99,
                        "fallback_tier": "OBSERVED_OVERRIDE",
                        "candidate_source": "OBSERVED_CURRENT_OVERRIDE",
                        "is_observed_current_spot": True,
                    }
                )

    out = pl.DataFrame(rows)
    if out.is_duplicated().any():
        raise AssertionError("Candidate decision table contains duplicate rows")
    key_dupes = out.group_by("prediction_key", "candidate_spot_id").len().filter(
        pl.col("len") > 1
    )
    if key_dupes.height:
        raise AssertionError("prediction_key × candidate_spot_id is not unique")
    return out.sort(["prediction_key", "fallback_rank", "candidate_spot_id"])


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "AssessmentSol1" / "abt" / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    build_candidate_spots(repo_root).write_parquet(
        out_dir / "candidate_spots.parquet"
    )


if __name__ == "__main__":
    main()
