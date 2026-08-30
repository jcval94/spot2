from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io_utils import load_inventory, read_csv, write_csv
from .rules import audit_row
from .rules_v2 import audit_row_v2


SEED = 25015
PER_SECTOR_PER_V1_STATUS = 30
HERE = Path(__file__).resolve().parents[1]
DISCOVERY_SAMPLE = HERE / "labeling" / "labeling_sample.csv"


def deterministic_score(spot_id: str) -> int:
    return (int(spot_id) * 1664525 + 1013904223 + SEED) % 4294967296


def discovery_ids() -> set[str]:
    return {row["spot_id"] for row in read_csv(DISCOVERY_SAMPLE)}


def build_holdout() -> list[dict[str, Any]]:
    excluded = discovery_ids()
    rows = [row for row in load_inventory() if row["spot_id"] not in excluded]
    enriched: list[dict[str, Any]] = []

    for row in rows:
        v1 = audit_row(row)
        v2 = audit_row_v2(row)
        attrs = row["attributes"]
        enriched.append({
            **row,
            "rules_v1_positive": bool(v1),
            "rules_v2_positive": bool(v2),
            "rules_v1_issue_types": sorted({x["claim_type"] for x in v1}),
            "rules_v2_issue_types": sorted({x["claim_type"] for x in v2}),
            "natural_light": attrs.get("natural_light"),
            "security_type": attrs.get("security_type"),
            "parking_spaces": attrs.get("parking_spaces"),
            "building_status": attrs.get("building_status"),
            "amenities": attrs.get("amenities"),
        })

    sample: list[dict[str, Any]] = []
    for sector in sorted({row["sector_name"] for row in enriched}):
        sector_rows = [row for row in enriched if row["sector_name"] == sector]
        for status in (True, False):
            candidates = [
                row for row in sector_rows if row["rules_v1_positive"] is status
            ]
            candidates.sort(
                key=lambda row: (
                    deterministic_score(row["spot_id"]),
                    int(row["spot_id"]),
                )
            )
            selected = candidates[:PER_SECTOR_PER_V1_STATUS]
            if len(selected) < PER_SECTOR_PER_V1_STATUS:
                raise ValueError(
                    f"Insufficient holdout rows sector={sector} v1_positive={status}"
                )
            sample.extend(selected)

    sample.sort(key=lambda row: int(row["spot_id"]))
    return sample


def run(output_path: Path) -> int:
    rows = build_holdout()
    serializable: list[dict[str, Any]] = []
    for row in rows:
        serializable.append({
            "spot_id": row["spot_id"],
            "sector_name": row["sector_name"],
            "type_name": row["type_name"],
            "modality": row["modality"],
            "title": row["title"],
            "description": row["description"],
            "natural_light": row["natural_light"],
            "security_type": row["security_type"],
            "parking_spaces": row["parking_spaces"],
            "building_status": row["building_status"],
            "amenities": json.dumps(row["amenities"], ensure_ascii=False),
            "rules_v1_positive": int(row["rules_v1_positive"]),
            "rules_v2_positive": int(row["rules_v2_positive"]),
            "rules_v1_issue_types": json.dumps(
                row["rules_v1_issue_types"], ensure_ascii=False
            ),
            "rules_v2_issue_types": json.dumps(
                row["rules_v2_issue_types"], ensure_ascii=False
            ),
            "human_actionable_issue": "",
            "human_claim_labels_json": "",
            "human_notes": "",
            "reviewer": "",
            "reviewed_at": "",
        })

    fields = list(serializable[0].keys())
    write_csv(output_path, serializable, fields)
    return len(serializable)
