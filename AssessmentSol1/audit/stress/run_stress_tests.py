from __future__ import annotations

"""Reproducible, intentionally unsafe leakage demonstrations.

This module is audit-only. It deliberately does NOT import product pipeline
modules. S001-S003 are reconstructed from raw CSV sources using only the Python
standard library, preserving the frozen DEVELOPMENT population and evaluation.
"""

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
DEVELOPMENT_END = datetime(2026, 5, 1, tzinfo=timezone.utc)
MATURITY_DAYS = 14
LQ = 0.20375457875457875


def dt(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def num(value: Any) -> float | None:
    return None if value in (None, "") else float(value)


def norm(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text.casefold() if text else None


def read_raw(name: str) -> list[dict[str, str]]:
    path = REPO_ROOT / "data" / "candidate" / "csv" / f"{name}.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def area_fit(candidate: float | None, requested: float | None) -> float | None:
    if candidate is None or requested is None or candidate <= 0 or requested <= 0:
        return None
    return max(0.0, 1.0 - abs(candidate - requested) / requested)


def tier_cap(tier: int) -> float:
    return {0: 1.0, 1: 0.85, 2: 0.70, 3: 0.45}[tier]


def search_modes(spot_mode: str | None) -> tuple[str, ...]:
    spot_mode = norm(spot_mode)
    if spot_mode == "both":
        return ("rent", "sale", "both")
    return (spot_mode, "both") if spot_mode in {"rent", "sale"} else ()


def availability_fit(snapshot: dict[str, Any] | None, urgency: float | None) -> float:
    if snapshot is None:
        return 0.4
    if snapshot["is_available"]:
        return 1.0
    days = snapshot["days_until_available"]
    if days is not None and urgency is not None and days <= urgency:
        return 0.8
    return 0.0


def snapshot_asof(
    snapshots: list[dict[str, Any]] | None,
    score_time: datetime,
    strategy: str,
) -> dict[str, Any] | None:
    if not snapshots:
        return None
    score_date = score_time.date()
    if strategy == "backward":
        eligible = [x for x in snapshots if x["date"] <= score_date]
        return eligible[-1] if eligible else None
    if strategy != "nearest":
        raise ValueError(strategy)
    # Deliberately unsafe: absolute distance; on a tie prefer the later date.
    return min(
        snapshots,
        key=lambda x: (
            abs((x["date"] - score_date).days),
            -x["date"].toordinal(),
            -x["snapshot_id"],
        ),
    )


def build_sources() -> tuple[
    dict[int, dict[str, Any]],
    dict[int, list[dict[str, Any]]],
    list[dict[str, Any]],
    dict[int, list[dict[str, Any]]],
    datetime,
]:
    leads = {}
    for r in read_raw("leads"):
        leads[int(r["lead_id"])] = {
            "lead_id": int(r["lead_id"]),
            "sector": norm(r["search_sector"]),
            "modality": norm(r["search_modality"]),
            "area": num(r["target_area_sqm"]),
            "state": r["preferred_state"],
            "municipality": r["preferred_municipality"],
            "corridor": r["preferred_corridor"],
            "lead_score_internal": num(r["lead_score_internal"]),
        }

    inquiries: dict[int, list[dict[str, Any]]] = defaultdict(list)
    horizon: datetime | None = None
    for r in read_raw("inquiries"):
        t = dt(r["inquiry_at"])
        horizon = t if horizon is None or t > horizon else horizon
        inquiries[int(r["lead_id"])].append({
            "inquiry_id": int(r["inquiry_id"]),
            "time": t,
            "area": num(r["requested_area_sqm"]),
            "urgency": num(r["urgency_days"]),
            "asked_visit": str(r["asked_visit"]).lower() == "true",
            "broker_response": r["broker_response"],
        })
    for rows in inquiries.values():
        rows.sort(key=lambda x: (x["time"], x["inquiry_id"]))

    spots = []
    for r in read_raw("spots"):
        spots.append({
            "spot_id": int(r["spot_id"]),
            "sector": norm(r["sector_name"]),
            "modality": norm(r["modality"]),
            "state": r["state"],
            "municipality": r["municipality"],
            "corridor": r["corridor"],
            "area": num(r["area_sqm"]),
            "created_at": dt(r["created_at"]),
        })

    availability: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for r in read_raw("availability_snapshot"):
        availability[int(r["spot_id"])].append({
            "snapshot_id": int(r["snapshot_id"]),
            "date": datetime.fromisoformat(r["snapshot_date"]).date(),
            "is_available": str(r["is_available"]).lower() == "true",
            "days_until_available": num(r["days_until_available"]),
        })
    for rows in availability.values():
        rows.sort(key=lambda x: (x["date"], x["snapshot_id"]))

    assert horizon is not None
    return leads, inquiries, spots, availability, horizon


def inventory_serviceability(
    lead: dict[str, Any],
    inquiry: dict[str, Any],
    spots: list[dict[str, Any]],
    availability: dict[int, list[dict[str, Any]]],
    *,
    snapshot_strategy: str,
) -> tuple[float, int, int]:
    requested_area = inquiry["area"] if inquiry["area"] is not None else lead["area"]
    candidates: list[tuple[int, dict[str, Any]]] = []
    seen: set[int] = set()

    levels = (
        (0, "corridor", lead["corridor"]),
        (1, "municipality", lead["municipality"]),
        (2, "state", lead["state"]),
    )

    def modality_ok(spot: dict[str, Any]) -> bool:
        return lead["modality"] in search_modes(spot["modality"])

    for tier, geo, value in levels:
        if not value:
            continue
        for spot in spots:
            if (
                spot["spot_id"] not in seen
                and spot["created_at"] <= inquiry["time"]
                and modality_ok(spot)
                and spot["sector"] == lead["sector"]
                and norm(spot[geo]) == norm(value)
            ):
                seen.add(spot["spot_id"])
                candidates.append((tier, spot))

    for _, geo, value in levels:
        if not value:
            continue
        for spot in spots:
            if (
                spot["spot_id"] not in seen
                and spot["created_at"] <= inquiry["time"]
                and modality_ok(spot)
                and spot["sector"] != lead["sector"]
                and norm(spot[geo]) == norm(value)
            ):
                seen.add(spot["spot_id"])
                candidates.append((3, spot))

    scores: list[float] = []
    future_snapshot_count = 0
    selected_snapshot_count = 0
    for tier, spot in candidates:
        af = area_fit(spot["area"], requested_area)
        viable = af is not None and af >= 0.5
        snap = snapshot_asof(
            availability.get(spot["spot_id"]),
            inquiry["time"],
            snapshot_strategy,
        )
        if snap is not None:
            selected_snapshot_count += 1
            if snap["date"] > inquiry["time"].date():
                future_snapshot_count += 1
        if viable:
            scores.append(
                ((af + availability_fit(snap, inquiry["urgency"])) / 2.0)
                * tier_cap(tier)
            )
    return (max(scores, default=0.0), future_snapshot_count, selected_snapshot_count)


def auc(rows: list[dict[str, Any]], key: str) -> float:
    groups: dict[float, list[int]] = defaultdict(lambda: [0, 0])
    positives = negatives = 0
    for r in rows:
        y = int(r["target"])
        groups[float(r[key])][y] += 1
        positives += y
        negatives += 1 - y
    negatives_below = 0
    concordant = 0.0
    for score in sorted(groups):
        n, p = groups[score]
        concordant += p * negatives_below + 0.5 * p * n
        negatives_below += n
    return concordant / (positives * negatives)


def average_precision(rows: list[dict[str, Any]], key: str) -> float:
    groups: dict[float, list[int]] = defaultdict(lambda: [0, 0])
    total_positive = 0
    for r in rows:
        y = int(r["target"])
        groups[float(r[key])][y] += 1
        total_positive += y
    tp = fp = 0
    previous_recall = 0.0
    result = 0.0
    for score in sorted(groups, reverse=True):
        n, p = groups[score]
        tp += p
        fp += n
        recall = tp / total_positive
        precision = tp / (tp + fp)
        result += (recall - previous_recall) * precision
        previous_recall = recall
    return result


def capacity(rows: list[dict[str, Any]], key: str, frac: float) -> dict[str, float | int]:
    ranked = sorted(rows, key=lambda r: (-float(r[key]), int(r["lead_id"])))
    n = math.ceil(len(ranked) * frac)
    top = ranked[:n]
    total_positive = sum(int(r["target"]) for r in ranked)
    captured = sum(int(r["target"]) for r in top)
    precision = captured / n
    recall = captured / total_positive
    base_rate = total_positive / len(ranked)
    return {
        "n": n,
        "positives": captured,
        "recall": recall,
        "precision": precision,
        "lift": precision / base_rate,
    }


def compute() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    leads, inquiries, spots, availability, horizon = build_sources()
    rows: list[dict[str, Any]] = []
    future_snaps = nearest_snaps = 0
    future_lead_count = future_asked_count = future_inquiry_total = 0

    for lead_id, history in inquiries.items():
        first = history[0]
        if first["time"] >= DEVELOPMENT_END:
            continue
        if (horizon - first["time"]).days < MATURITY_DAYS:
            continue

        lead = leads[lead_id]
        clean, _, _ = inventory_serviceability(
            lead, first, spots, availability, snapshot_strategy="backward"
        )
        nearest, fs, ns = inventory_serviceability(
            lead, first, spots, availability, snapshot_strategy="nearest"
        )
        future_snaps += fs
        nearest_snaps += ns

        future = [x for x in history[1:] if x["time"] > first["time"]]
        if future:
            future_lead_count += 1
        if any(x["asked_visit"] for x in future):
            future_asked_count += 1
        future_inquiry_total += len(future)

        # S002 rule is fixed before evaluation; no future outcome field is used.
        s002 = len(future) + 2 * int(any(x["asked_visit"] for x in future))
        target = int(first["broker_response"] == "scheduled_visit")
        rows.append({
            "lead_id": lead_id,
            "target": target,
            "clean": LQ * clean,
            "s001": float(lead["lead_score_internal"]),
            "s002": float(s002),
            "s003": LQ * nearest,
        })

    systems = (
        ("CLEAN_OPPORTUNITY", "CLEAN", "DEPLOYABLE_REFERENCE", "clean"),
        ("LEAD_SCORE_INTERNAL", "S001", "LEAKAGE_EXPECTED_UNKNOWN_PROVENANCE_NON_DEPLOYABLE", "s001"),
        ("FUTURE_INQUIRIES", "S002", "FUTURE_LEAKAGE_NON_DEPLOYABLE", "s002"),
        ("NEAREST_SNAPSHOT", "S003", "FUTURE_SNAPSHOT_LEAKAGE_NON_DEPLOYABLE", "s003"),
    )
    metrics = []
    for system, stress_id, status, key in systems:
        c5, c10, c20 = capacity(rows, key, 0.05), capacity(rows, key, 0.10), capacity(rows, key, 0.20)
        metrics.append({
            "system": system,
            "stress_id": stress_id,
            "status": status,
            "roc_auc": auc(rows, key),
            "average_precision": average_precision(rows, key),
            "top5_lift": c5["lift"],
            "top10_lift": c10["lift"],
            "top20_lift": c20["lift"],
            "top10_recall": c10["recall"],
            "top10_precision": c10["precision"],
        })

    diagnostics = {
        "development_rows": len(rows),
        "positives": sum(r["target"] for r in rows),
        "s002_leads_with_future_inquiry": future_lead_count,
        "s002_share_with_future_inquiry": future_lead_count / len(rows),
        "s002_leads_with_future_asked_visit": future_asked_count,
        "s002_share_with_future_asked_visit": future_asked_count / len(rows),
        "s002_mean_future_inquiries": future_inquiry_total / len(rows),
        "s003_nearest_future_snapshot_share": future_snaps / nearest_snaps,
        "selection_use": "FORBIDDEN",
    }
    return metrics, diagnostics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-unsafe-stress", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not args.allow_unsafe_stress:
        raise SystemExit("Refusing unsafe stress execution without --allow-unsafe-stress")

    for path in sorted(HERE.glob("S00*.json")):
        spec = json.loads(path.read_text(encoding="utf-8"))
        if not spec.get("unsafe") or spec.get("deployable") is not False:
            raise AssertionError(f"Stress spec lost unsafe/non-deployable flag: {path.name}")

    metrics, diagnostics = compute()
    if args.write:
        with (HERE / "stress_metrics.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(metrics[0]))
            writer.writeheader()
            writer.writerows(metrics)
        (HERE / "stress_diagnostics.json").write_text(
            json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps({"metrics": metrics, "diagnostics": diagnostics}, indent=2))


if __name__ == "__main__":
    main()
