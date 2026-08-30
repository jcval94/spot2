from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, g in results.groupby("sample_stratum", dropna=False):
        rows.append(
            {
                "sample_stratum": name,
                "n": len(g),
                "llm_incremental_issue_rate": g["llm_incremental_issue"].mean(),
                "llm_new_rule_candidate_rate": g["llm_new_rule_candidate"].mean(),
                "llm_human_review_rate": g["llm_requires_human_review"].mean(),
                "llm_mean_confidence": g["llm_confidence"].mean(),
            }
        )
    total = {
        "sample_stratum": "TOTAL",
        "n": len(results),
        "llm_incremental_issue_rate": results["llm_incremental_issue"].mean(),
        "llm_new_rule_candidate_rate": results["llm_new_rule_candidate"].mean(),
        "llm_human_review_rate": results["llm_requires_human_review"].mean(),
        "llm_mean_confidence": results["llm_confidence"].mean(),
    }
    rows.append(total)
    return pd.DataFrame(rows)


def diagnostic_gates(results: pd.DataFrame) -> pd.DataFrame:
    clean = results[results["sample_stratum"].eq("clean_control")]
    known = results[results["sample_stratum"].eq("rules_positive")]
    residual = results[
        results["sample_stratum"].isin(
            ["land_semantic_residual", "ambiguity_challenge"]
        )
    ]

    checks = [
        {
            "gate": "clean_control_incremental_issue_rate",
            "value": clean["llm_incremental_issue"].mean(),
            "reference": "<=0.10 preferred",
            "status": (
                "PASS"
                if clean["llm_incremental_issue"].mean() <= 0.10
                else "REVIEW"
            ),
        },
        {
            "gate": "rules_positive_new_rule_rate",
            "value": known["llm_new_rule_candidate"].mean(),
            "reference": "<=0.10 preferred",
            "status": (
                "PASS"
                if known["llm_new_rule_candidate"].mean() <= 0.10
                else "REVIEW"
            ),
        },
        {
            "gate": "residual_incremental_issue_rate",
            "value": residual["llm_incremental_issue"].mean(),
            "reference": "descriptive; human precision required",
            "status": "REVIEW",
        },
        {
            "gate": "residual_new_rule_candidate_rate",
            "value": residual["llm_new_rule_candidate"].mean(),
            "reference": "descriptive; inspect repeated patterns",
            "status": "REVIEW",
        },
    ]
    return pd.DataFrame(checks)


def main():
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser()
    p.add_argument(
        "--results",
        type=Path,
        default=root / "results" / "pilot_llm_results_100.csv",
    )
    p.add_argument(
        "--summary",
        type=Path,
        default=root / "results" / "pilot_segment_summary.csv",
    )
    p.add_argument(
        "--gates",
        type=Path,
        default=root / "results" / "pilot_diagnostic_gates.csv",
    )
    args = p.parse_args()

    results = pd.read_csv(args.results)
    summary = summarize(results)
    gates = diagnostic_gates(results)
    summary.to_csv(args.summary, index=False)
    gates.to_csv(args.gates, index=False)
    print(summary.to_string(index=False))
    print("\nDiagnostic gates:")
    print(gates.to_string(index=False))


if __name__ == "__main__":
    main()
