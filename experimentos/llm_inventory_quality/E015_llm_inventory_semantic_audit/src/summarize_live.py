from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any


PRICE_PER_M_INPUT = {"gpt-5-nano": 0.05}
PRICE_PER_M_OUTPUT = {"gpt-5-nano": 0.40}


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
    for issue in record.get("audit", {}).get("issues", []):
        if (
            issue.get("actionable") is True
            and issue.get("classification")
            in {"contradiction", "semantic_cross_field_mismatch"}
        ):
            return True
    return False


def summarize(labels: dict[str, dict[str, str]], preds: dict[str, dict[str, Any]], model: str) -> dict[str, Any]:
    classes = Counter()
    actionable_count = 0
    errors = 0
    input_tokens = output_tokens = 0
    latencies = []

    for rec in preds.values():
        if rec.get("status") != "ok":
            errors += 1
            continue
        input_tokens += int(rec.get("input_tokens") or 0)
        output_tokens += int(rec.get("output_tokens") or 0)
        if rec.get("latency_ms") is not None:
            latencies.append(float(rec["latency_ms"]))
        if actionable(rec):
            actionable_count += 1
        for issue in rec.get("audit", {}).get("issues", []):
            classes[str(issue.get("classification"))] += 1

    price_in = PRICE_PER_M_INPUT.get(model)
    price_out = PRICE_PER_M_OUTPUT.get(model)
    estimated_cost = None
    if price_in is not None and price_out is not None:
        estimated_cost = input_tokens / 1_000_000 * price_in + output_tokens / 1_000_000 * price_out

    result = {
        "model": model,
        "n_expected": len(labels),
        "n_predictions": len(preds),
        "n_errors": errors,
        "n_actionable_predictions": actionable_count,
        "classification_counts": dict(sorted(classes.items())),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd_standard": estimated_cost,
        "latency_median_ms": median(latencies) if latencies else None,
    }

    if labels and "rules_v1_positive" in next(iter(labels.values())):
        ids = set(labels) & set(preds)
        llm_ids = {sid for sid in ids if actionable(preds[sid])}
        v1 = {sid for sid in ids if labels[sid].get("rules_v1_positive") == "1"}
        v2 = {sid for sid in ids if labels[sid].get("rules_v2_positive") == "1"}
        result.update({
            "llm_actionable_overlap_rules_v1": len(llm_ids & v1),
            "llm_actionable_incremental_vs_rules_v1": len(llm_ids - v1),
            "llm_actionable_overlap_rules_v2": len(llm_ids & v2),
            "llm_actionable_incremental_vs_rules_v2": len(llm_ids - v2),
        })

    if labels and "s001_discovery_pattern_present" in next(iter(labels.values())):
        ids = set(labels) & set(preds)
        truth = {sid: labels[sid]["s001_discovery_pattern_present"] == "1" for sid in ids}
        pred = {sid: actionable(preds[sid]) for sid in ids}
        tp = sum(truth[sid] and pred[sid] for sid in ids)
        tn = sum((not truth[sid]) and (not pred[sid]) for sid in ids)
        fp = sum((not truth[sid]) and pred[sid] for sid in ids)
        fn = sum(truth[sid] and (not pred[sid]) for sid in ids)
        result["s001_challenge"] = {
            "tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "sensitivity": tp / (tp + fn) if tp + fn else None,
            "specificity": tn / (tn + fp) if tn + fp else None,
            "precision_vs_discovery_pattern": tp / (tp + fp) if tp + fp else None,
        }

    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--labels", type=Path, required=True)
    p.add_argument("--predictions", type=Path, required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    summary = summarize(read_csv(args.labels), read_jsonl(args.predictions), args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
