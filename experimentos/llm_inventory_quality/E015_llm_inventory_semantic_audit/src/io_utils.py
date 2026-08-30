from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = ROOT / "data" / "candidate" / "csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_inventory() -> list[dict[str, Any]]:
    spots = read_csv(DATA_DIR / "spots.csv")
    attrs = read_csv(DATA_DIR / "spot_attributes.csv")
    by_spot = {row["spot_id"]: row for row in attrs}

    joined: list[dict[str, Any]] = []
    for spot in spots:
        attr = by_spot.get(spot["spot_id"])
        if attr is None:
            raise ValueError(f"Missing spot_attributes row for spot_id={spot['spot_id']}")
        row: dict[str, Any] = {**spot}
        row["attributes"] = {
            "natural_light": _as_bool(attr.get("natural_light")),
            "luminaires": _as_number(attr.get("luminaires")),
            "charging_ports": _as_number(attr.get("charging_ports")),
            "security_type": attr.get("security_type") or None,
            "floor_level": _as_number(attr.get("floor_level")),
            "elevators": _as_number(attr.get("elevators")),
            "vertical_height_m": _as_number(attr.get("vertical_height_m")),
            "parking_spaces": _as_number(attr.get("parking_spaces")),
            "building_status": attr.get("building_status") or None,
            "floor_material": attr.get("floor_material") or None,
            "amenities": _parse_json_list(attr.get("amenities")),
        }
        joined.append(row)
    return joined


def _parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(x) for x in parsed] if isinstance(parsed, list) else []


def _as_bool(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    lowered = value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def _as_number(value: str | None) -> int | float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return int(number) if number.is_integer() else number


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
