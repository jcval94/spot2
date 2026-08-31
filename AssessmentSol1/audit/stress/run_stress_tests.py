from __future__ import annotations

"""Unsafe leakage demonstrations for audit only.

This module intentionally lives under audit/stress and must never be imported
from AssessmentSol1 product builders. It uses only the Python standard library
so the demonstrations remain runnable even when the ML environment is absent.
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
ROOT = HERE.parents[2]
DEVELOPMENT_END = datetime(2026, 5, 1, tzinfo=timezone.utc)
MATURITY_DAYS = 14
LQ = 0.20375457875457875


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def _num(x: Any) -> float | None:
    return None if x in (None, "") else float(x)


def _read(name: str) -> list[dict[str, str]]:
    path = ROOT / "data" / "candidate" / "csv" / f"{name}.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _auc(rows: list[dict[str, Any]], key: str) -> float:
    groups: dict[float, list[int]] = defaultdict(lambda: [0, 0])
    pos = neg = 0
    for r in rows:
        y = int(r["target"])
        groups[float(r[key])][y] += 1
        pos += y
        neg += 1 - y
    neg_below = 0
    concordant = 0.0
    for score in sorted(groups):
        n, p = groups[score][0], groups[score][1]
        concordant += p * neg_below + 0.5 * p * n
        neg_below += n
    return concordant / (pos * neg)


def _average_precision(rows: list[dict[str, Any]], key: str) -> float:
    groups: dict[float, list[int]] = defaultdict(lambda: [0, 0])
    positives = 0
    for r in rows:
        y = int(r["target"])
        groups[float(r[key])][y] += 1
        positives += y
    tp = fp = 0
    prev_recall = 0.0
    ap = 0.0
    for score in sorted(groups, reverse=True):
        n, p = groups[score][0], groups[score][1]
        tp += p
        fp += n
        recall = tp / positives
        precision = tp / (tp + fp)
        ap += (recall - prev_recall) * precision
        prev_recall = recall
    return ap


def _capacity(rows: list[dict[str, Any]], key: str, frac: float) -> dict[str, float | int]:
    ranked = sorted(rows, key=lambda r: (-float(r[key]), int(r["lead_id"])))
    n = math.ceil(len(ranked) * frac)
    top = ranked[:n]
    total_pos = sum(int(r["target"]) for r in ranked)
    captured = sum(int(r["target"]) for r in top)
    precision = captured / n
    recall = captured / total_pos
    base = total_pos / len(ranked)
    return {
        "n": n,
        "positives": captured,
        "recall": recall,
        "precision": precision,
        "lift": precision / base,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-unsafe-stress",
        action="store_true",
        help="Required acknowledgement: these specs are intentionally non-deployable.",
    )
    args = parser.parse_args()
    if not args.allow_unsafe_stress:
        raise SystemExit("Refusing unsafe stress execution without --allow-unsafe-stress")

    # The committed Prompt-11 metrics are the audited reference. This runner
    # exists to force an explicit unsafe acknowledgement and to validate specs.
    # Full raw reconstruction logic is intentionally kept separate from product
    # code; do not import AssessmentSol1 product builders from this directory.
    specs = []
    for path in sorted(HERE.glob("S00*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not payload.get("unsafe") or payload.get("deployable") is not False:
            raise AssertionError(f"Stress spec lost unsafe/non-deployable flag: {path.name}")
        specs.append(payload["id"])

    metrics = list(csv.DictReader((HERE / "stress_metrics.csv").open(encoding="utf-8")))
    print(json.dumps({
        "status": "UNSAFE_STRESS_ONLY",
        "specs": specs,
        "metrics_rows": len(metrics),
        "selection_use": "FORBIDDEN",
    }, indent=2))


if __name__ == "__main__":
    main()
