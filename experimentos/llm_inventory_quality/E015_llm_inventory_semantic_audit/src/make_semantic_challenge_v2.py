from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io_utils import load_inventory, read_csv, write_csv
from .rules import audit_row
from .semantic_discovery import semantic_observations


SEED = 35015
N_PER_CLASS = 50
HERE = Path(__file__).resolve().parents[1]
DISCOVERY_SAMPLE = HERE / "labeling" / "labeling_sample.csv"
GENERAL_HOLDOUT = HERE / "labeling" / "labeling_holdout_v2.csv"


def deterministic_score(spot_id: str) -> int:
    return (int(spot_id) * 22695477 + 1 + SEED) % 4294967296


def excluded_ids() -> set[str]:
    ids = {row["spot_id"] for row in read_csv(DISCOVERY_SAMPLE)}
    if GENERAL_HOLDOUT.exists():
        ids.update(row["spot_id"] for row in read_csv(GENERAL_HOLDOUT))
    return ids


def is_s001(row: dict[str, Any]) -> bool:
    return any(
        item["pattern_id"] == "S001" and item["actionable"]
        for item in semantic_observations(row)
    )


def build_challenge() -> list[dict[str, Any]]:
    excluded = excluded_ids()
    rows = [
        row
        for row in load_inventory()
        if row["spot_id"] not in excluded
        and row["sector_name"] == "Land"
        and not audit_row(row)
    ]

    positive = [row for row in rows if is_s001(row)]
    control = [row for row in rows if not is_s001(row)]

    positive.sort(key=lambda row: (deterministic_score(row["spot_id"]), int(row["spot_id"])))
    control.sort(key=lambda row: (deterministic_score(row["spot_id"]), int(row["spot_id"])))

    if len(positive) < N_PER_CLASS or len(control) < N_PER_CLASS:
        raise ValueError(
            f"Insufficient disjoint Land candidates: positive={len(positive)} control={len(control)}"
        )
    selected = [(row, 1) for row in positive[:N_PER_CLASS]]
    selected += [(row, 0) for row in control[:N_PER_CLASS]]
    selected.sort(key=lambda pair: int(pair[0]["spot_id"]))

    output: list[dict[str, Any]] = []
    for row, discovery_pattern_present in selected:
        attrs = row["attributes"]
        output.append({
            "spot_id": row["spot_id"],
            "sector_name": row["sector_name"],
            "type_name": row["type_name"],
            "modality": row["modality"],
            "title": row["title"],
            "description": row["description"],
            "natural_light": attrs.get("natural_light"),
            "security_type": attrs.get("security_type"),
            "parking_spaces": attrs.get("parking_spaces"),
            "building_status": attrs.get("building_status"),
            "amenities": json.dumps(attrs.get("amenities", []), ensure_ascii=False),
            "s001_discovery_pattern_present": discovery_pattern_present,
            "human_actionable_issue": "",
            "human_claim_labels_json": "",
            "human_notes": "",
            "reviewer": "",
            "reviewed_at": "",
        })
    return output


def run(output_path: Path) -> int:
    rows = build_challenge()
    write_csv(output_path, rows, list(rows[0].keys()))
    return len(rows)
