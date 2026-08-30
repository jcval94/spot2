from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from src.io_utils import load_inventory, write_csv, write_json
from src.make_labeling_sample import run as make_labeling_sample
from src.profile_copy import run as profile_copy
from src.rules import PATTERNS, audit_row


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
LABELING = HERE / "labeling" / "labeling_sample.csv"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    profile_summary = profile_copy(RESULTS)

    inventory = load_inventory()
    issues = [issue for row in inventory for issue in audit_row(row)]
    flagged_spots = {issue["spot_id"] for issue in issues}

    issue_counts = Counter(issue["claim_type"] for issue in issues)
    by_sector: dict[str, dict[str, int | float]] = {}
    issues_by_spot: dict[str, list[dict]] = {}
    for issue in issues:
        issues_by_spot.setdefault(issue["spot_id"], []).append(issue)

    for row in inventory:
        sector = row["sector_name"]
        bucket = by_sector.setdefault(sector, {"n_spots": 0, "flagged_spots": 0})
        bucket["n_spots"] += 1
        if row["spot_id"] in flagged_spots:
            bucket["flagged_spots"] += 1

    sector_rows = []
    for sector, values in sorted(by_sector.items()):
        rate = values["flagged_spots"] / values["n_spots"]
        sector_rows.append({
            "sector_name": sector,
            "n_spots": values["n_spots"],
            "flagged_spots": values["flagged_spots"],
            "flag_rate": rate,
        })
    write_csv(RESULTS / "rule_flags_by_sector.csv", sector_rows, ["sector_name", "n_spots", "flagged_spots", "flag_rate"])

    write_csv(
        RESULTS / "rule_candidate_issues.csv",
        issues,
        ["spot_id", "sector_name", "type_name", "rule_id", "claim_type", "evidence_text", "structured_field", "structured_value", "classification", "severity", "reason"],
    )

    multi_issue = Counter(len(v) for v in issues_by_spot.values())
    rule_summary = {
        "n_spots": len(inventory),
        "n_rule_candidate_issues": len(issues),
        "n_unique_flagged_spots": len(flagged_spots),
        "share_unique_flagged_spots": len(flagged_spots) / len(inventory),
        "candidate_issues_by_claim_type": dict(sorted(issue_counts.items())),
        "flagged_spots_by_issue_count": {str(k): v for k, v in sorted(multi_issue.items())},
        "rule_phrase_families": {k: list(v) for k, v in PATTERNS.items()},
        "interpretation": "Rule flags are candidate semantic conflicts requiring review; they are not gold labels."
    }
    write_json(RESULTS / "rules_summary.json", rule_summary)

    sample_n = make_labeling_sample(LABELING)
    combined = {
        "experiment_id": "E015_llm_inventory_semantic_audit",
        "phase": "offline_baseline",
        "copy_profile": profile_summary,
        "rules": rule_summary,
        "human_labeling_sample_n": sample_n,
        "llm_executed": False,
        "conclusion": "INCOMPLETE_LLM_PENDING"
    }
    write_json(RESULTS / "offline_summary.json", combined)
    print(json.dumps(combined, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
