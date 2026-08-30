from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any


NANO = {
    "sensitivity": 0.76,
    "specificity": 0.28,
    "precision": 0.5135135135,
    "holdout_actionable": 194,
    "incremental_vs_rules_v2": 77,
    "cost_usd": 0.053522
}


def read_csv(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return {row["spot_id"]: row for row in csv.DictReader(fh)}


def read_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out[str(row["spot_id"])] = row
    return out


def actionable(record: dict[str, Any]) -> bool:
    if record.get("status") != "ok":
        return False
    return any(
        issue.get("actionable") is True
        and issue.get("classification")
        in {"contradiction", "semantic_cross_field_mismatch"}
        for issue in record.get("audit", {}).get("issues", [])
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--labels", type=Path, required=True)
    p.add_argument("--predictions", type=Path, required=True)
    p.add_argument("--budget-state", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    labels = read_csv(args.labels)
    preds = read_jsonl(args.predictions)
    ok = [r for r in preds.values() if r.get("status") == "ok"]
    classes = Counter()
    for rec in ok:
        for issue in rec.get("audit", {}).get("issues", []):
            classes[str(issue.get("classification"))] += 1

    actionable_ids = {sid for sid, rec in preds.items() if actionable(rec)}
    latencies = [
        float(r["latency_ms"]) for r in ok if r.get("latency_ms") is not None
    ]
    result: dict[str, Any] = {
        "model": "gpt-5-mini",
        "n_expected": len(labels),
        "n_predictions": len(preds),
        "n_errors": len(preds) - len(ok),
        "n_actionable_predictions": len(actionable_ids),
        "classification_counts": dict(sorted(classes.items())),
        "input_tokens": sum(int(r.get("input_tokens") or 0) for r in ok),
        "output_tokens": sum(int(r.get("output_tokens") or 0) for r in ok),
        "latency_median_ms": median(latencies) if latencies else None
    }

    first = next(iter(labels.values()))
    if "rules_v1_positive" in first:
        v1 = {sid for sid, row in labels.items() if row["rules_v1_positive"] == "1"}
        v2 = {sid for sid, row in labels.items() if row["rules_v2_positive"] == "1"}
        result.update({
            "overlap_rules_v1": len(actionable_ids & v1),
            "incremental_vs_rules_v1": len(actionable_ids - v1),
            "overlap_rules_v2": len(actionable_ids & v2),
            "incremental_vs_rules_v2": len(actionable_ids - v2),
            "nano_reference": {
                "holdout_actionable": NANO["holdout_actionable"],
                "incremental_vs_rules_v2": NANO["incremental_vs_rules_v2"]
            }
        })

    if "s001_discovery_pattern_present" in first:
        truth = {
            sid: row["s001_discovery_pattern_present"] == "1"
            for sid, row in labels.items()
        }
        ids = set(labels) & set(preds)
        tp = sum(truth[sid] and sid in actionable_ids for sid in ids)
        tn = sum((not truth[sid]) and sid not in actionable_ids for sid in ids)
        fp = sum((not truth[sid]) and sid in actionable_ids for sid in ids)
        fn = sum(truth[sid] and sid not in actionable_ids for sid in ids)
        sens = tp / (tp + fn) if tp + fn else None
        spec = tn / (tn + fp) if tn + fp else None
        precision = tp / (tp + fp) if tp + fp else None
        result["s001_challenge"] = {
            "tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "sensitivity": sens,
            "specificity": spec,
            "precision_vs_pattern": precision,
            "delta_sensitivity_vs_nano": sens - NANO["sensitivity"],
            "delta_specificity_vs_nano": spec - NANO["specificity"],
            "delta_precision_vs_nano": precision - NANO["precision"],
            "decision_supported": bool(
                sens is not None and spec is not None
                and sens >= 0.70 and spec >= 0.70
            )
        }

    budget = json.loads(args.budget_state.read_text(encoding="utf-8"))
    result["shared_budget_state"] = budget
    result["hard_budget_respected"] = (
        float(budget["reserved_max_cost_usd"])
        <= float(budget["hard_budget_usd"])
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
