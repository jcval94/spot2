from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parents[1]
DEFAULT_LABELS = HERE / "labeling" / "labeling_holdout_v2.csv"
DEFAULT_LLM = HERE / "results" / "llm_predictions.jsonl"
DEFAULT_OUTPUT = HERE / "results" / "evaluation.json"

ACTIONABLE_LLM_CLASSES = {"contradiction", "semantic_cross_field_mismatch"}


def _binary_metrics(y_true: list[int], y_pred: list[int]) -> dict[str, float | int]:
    tp = sum(1 for y, p in zip(y_true, y_pred) if y == 1 and p == 1)
    tn = sum(1 for y, p in zip(y_true, y_pred) if y == 0 and p == 0)
    fp = sum(1 for y, p in zip(y_true, y_pred) if y == 0 and p == 1)
    fn = sum(1 for y, p in zip(y_true, y_pred) if y == 1 and p == 0)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fpr,
    }


def load_labels(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return {row["spot_id"]: row for row in csv.DictReader(fh)}


def load_llm(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        rows[str(obj["spot_id"])] = obj
    return rows


def _row_bool(row: dict[str, str], preferred: str, fallback: str | None = None) -> int:
    value = row.get(preferred, "")
    if value.strip() in {"0", "1"}:
        return int(value)
    if fallback:
        value = row.get(fallback, "")
        if value.strip() in {"0", "1"}:
            return int(value)
    return 0


def llm_positive(record: dict[str, Any] | None) -> int:
    if not record or record.get("status") != "ok":
        return 0

    issues = record.get("audit", {}).get("issues", [])
    for issue in issues:
        if issue.get("classification") not in ACTIONABLE_LLM_CLASSES:
            continue
        if issue.get("actionable") is True:
            return 1
    return 0


def llm_informational_counts(records: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records.values():
        if record.get("status") != "ok":
            continue
        for issue in record.get("audit", {}).get("issues", []):
            classification = str(issue.get("classification", "unknown"))
            if issue.get("actionable") is True:
                continue
            counts[classification] = counts.get(classification, 0) + 1
    return dict(sorted(counts.items()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--llm", type=Path, default=DEFAULT_LLM)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    labels = load_labels(args.labels)
    llm = load_llm(args.llm)
    eligible = [
        row
        for row in labels.values()
        if row.get("human_actionable_issue", "").strip() in {"0", "1"}
    ]

    result: dict[str, Any] = {
        "n_rows": len(labels),
        "n_human_labeled": len(eligible),
        "n_llm_predictions": len(llm),
        "ready_for_final_evaluation": bool(eligible and llm),
        "actionable_llm_classes": sorted(ACTIONABLE_LLM_CLASSES),
        "non_actionable_llm_findings": llm_informational_counts(llm),
    }

    if eligible:
        y = [int(row["human_actionable_issue"]) for row in eligible]
        rules_v1 = [
            _row_bool(row, "rules_v1_positive", fallback="rule_positive")
            for row in eligible
        ]
        rules_v2 = [
            _row_bool(row, "rules_v2_positive", fallback="rules_v1_positive")
            for row in eligible
        ]
        result["rules_v1"] = _binary_metrics(y, rules_v1)
        result["rules_v2_post_discovery"] = _binary_metrics(y, rules_v2)

        if llm:
            llm_pred = [llm_positive(llm.get(row["spot_id"])) for row in eligible]
            v1_union = [int(r or l) for r, l in zip(rules_v1, llm_pred)]
            v2_union = [int(r or l) for r, l in zip(rules_v2, llm_pred)]

            result["llm_only"] = _binary_metrics(y, llm_pred)
            result["rules_v1_plus_llm"] = _binary_metrics(y, v1_union)
            result["rules_v2_plus_llm"] = _binary_metrics(y, v2_union)
            result["incremental_recall_vs_rules_v1"] = (
                result["rules_v1_plus_llm"]["recall"] - result["rules_v1"]["recall"]
            )
            result["incremental_recall_vs_rules_v2"] = (
                result["rules_v2_plus_llm"]["recall"]
                - result["rules_v2_post_discovery"]["recall"]
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
