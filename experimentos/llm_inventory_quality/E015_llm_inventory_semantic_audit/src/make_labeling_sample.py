from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io_utils import load_inventory, write_csv
from .rules import audit_row


SEED = 15015
PER_SECTOR_PER_STATUS = 25


def deterministic_score(spot_id: str) -> int:
    return (int(spot_id) * 1103515245 + SEED) % 2147483647


def build_sample() -> list[dict[str, Any]]:
    rows = load_inventory()
    enriched: list[dict[str, Any]] = []
    for row in rows:
        issues = audit_row(row)
        attrs = row["attributes"]
        enriched.append({
            **row,
            "rule_positive": bool(issues),
            "rule_issue_types": sorted({x["claim_type"] for x in issues}),
            "natural_light": attrs.get("natural_light"),
            "security_type": attrs.get("security_type"),
            "parking_spaces": attrs.get("parking_spaces"),
            "building_status": attrs.get("building_status"),
            "amenities": attrs.get("amenities"),
        })

    sample: list[dict[str, Any]] = []
    sectors = sorted({row["sector_name"] for row in enriched})
    for sector in sectors:
        sector_rows = [row for row in enriched if row["sector_name"] == sector]
        for status in (True, False):
            candidates = [row for row in sector_rows if row["rule_positive"] is status]
            candidates.sort(key=lambda row: (deterministic_score(row["spot_id"]), int(row["spot_id"])))
            selected = candidates[:PER_SECTOR_PER_STATUS]
            if len(selected) < PER_SECTOR_PER_STATUS:
                raise ValueError(f"Insufficient rows for sector={sector} rule_positive={status}")
            sample.extend(selected)

    sample.sort(key=lambda row: int(row["spot_id"]))
    return sample


def run(output_path: Path) -> int:
    rows = build_sample()
    serializable: list[dict[str, Any]] = []
    for row in rows:
        serializable.append({
            "spot_id": row["spot_id"],
            "sector_name": row["sector_name"],
            "type_name": row["type_name"],
            "title": row["title"],
            "description": row["description"],
            "natural_light": row["natural_light"],
            "security_type": row["security_type"],
            "parking_spaces": row["parking_spaces"],
            "building_status": row["building_status"],
            "amenities": json.dumps(row["amenities"], ensure_ascii=False),
            "rule_positive": int(row["rule_positive"]),
            "rule_issue_types": json.dumps(row["rule_issue_types"], ensure_ascii=False),
            "human_actionable_issue": "",
            "human_claim_labels_json": "",
            "human_notes": "",
            "reviewer": "",
            "reviewed_at": "",
        })

    fields = list(serializable[0].keys())
    write_csv(output_path, serializable, fields)
    return len(serializable)
