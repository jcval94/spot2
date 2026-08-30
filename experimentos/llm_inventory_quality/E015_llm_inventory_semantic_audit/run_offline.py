from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from src.io_utils import load_inventory, write_csv, write_json
from src.make_holdout_v2 import run as make_holdout_v2
from src.make_labeling_sample import run as make_labeling_sample
from src.profile_copy import run as profile_copy
from src.rules import PATTERNS, audit_row
from src.rules_v2 import audit_row_v2
from src.semantic_discovery import semantic_observations


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DISCOVERY_SAMPLE = HERE / "labeling" / "labeling_sample.csv"
HOLDOUT_V2 = HERE / "labeling" / "labeling_holdout_v2.csv"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    profile_summary = profile_copy(RESULTS)
    inventory = load_inventory()

    # Rules v1: frozen pre-semantic-discovery baseline.
    issues_v1 = [issue for row in inventory for issue in audit_row(row)]
    flagged_v1 = {issue["spot_id"] for issue in issues_v1}
    issue_counts = Counter(issue["claim_type"] for issue in issues_v1)
    by_sector: dict[str, dict[str, int | float]] = {}
    issues_by_spot: dict[str, list[dict]] = {}
    for issue in issues_v1:
        issues_by_spot.setdefault(issue["spot_id"], []).append(issue)

    for row in inventory:
        sector = row["sector_name"]
        bucket = by_sector.setdefault(sector, {"n_spots": 0, "flagged_spots": 0})
        bucket["n_spots"] += 1
        if row["spot_id"] in flagged_v1:
            bucket["flagged_spots"] += 1

    sector_rows = []
    for sector, values in sorted(by_sector.items()):
        sector_rows.append({
            "sector_name": sector,
            "n_spots": values["n_spots"],
            "flagged_spots": values["flagged_spots"],
            "flag_rate": values["flagged_spots"] / values["n_spots"],
        })

    write_csv(
        RESULTS / "rule_flags_by_sector.csv",
        sector_rows,
        ["sector_name", "n_spots", "flagged_spots", "flag_rate"],
    )
    write_csv(
        RESULTS / "rule_candidate_issues.csv",
        issues_v1,
        [
            "spot_id", "sector_name", "type_name", "rule_id", "claim_type",
            "evidence_text", "structured_field", "structured_value",
            "classification", "severity", "reason",
        ],
    )

    multi_issue = Counter(len(v) for v in issues_by_spot.values())
    rule_summary = {
        "ruleset": "v1_frozen_pre_semantic_discovery",
        "n_spots": len(inventory),
        "n_rule_candidate_issues": len(issues_v1),
        "n_unique_flagged_spots": len(flagged_v1),
        "share_unique_flagged_spots": len(flagged_v1) / len(inventory),
        "candidate_issues_by_claim_type": dict(sorted(issue_counts.items())),
        "flagged_spots_by_issue_count": {
            str(k): v for k, v in sorted(multi_issue.items())
        },
        "rule_phrase_families": {k: list(v) for k, v in PATTERNS.items()},
        "interpretation": (
            "Rule flags are candidate semantic conflicts requiring review; "
            "they are not gold labels."
        ),
    }
    write_json(RESULTS / "rules_summary.json", rule_summary)

    # Semantic discovery observations: informational and actionable are separated.
    observations = [
        observation
        for row in inventory
        for observation in semantic_observations(row)
    ]
    write_csv(
        RESULTS / "semantic_discovery_observations.csv",
        observations,
        [
            "spot_id", "pattern_id", "classification", "actionable", "severity",
            "evidence_text", "structured_context", "reason",
        ],
    )

    pattern_counts = Counter(x["pattern_id"] for x in observations)
    class_counts = Counter(x["classification"] for x in observations)
    actionable_observations = [x for x in observations if x["actionable"]]
    actionable_semantic_spots = {x["spot_id"] for x in actionable_observations}

    # Rules v2: post-discovery challenger, never relabeled as the original baseline.
    issues_v2 = [issue for row in inventory for issue in audit_row_v2(row)]
    flagged_v2 = {issue["spot_id"] for issue in issues_v2}
    v2_incremental = flagged_v2 - flagged_v1

    semantic_summary = {
        "n_observations": len(observations),
        "observations_by_pattern": dict(sorted(pattern_counts.items())),
        "observations_by_classification": dict(sorted(class_counts.items())),
        "n_actionable_semantic_observations": len(actionable_observations),
        "n_unique_actionable_semantic_spots": len(actionable_semantic_spots),
        "rules_v1_unique_flagged_spots": len(flagged_v1),
        "rules_v2_unique_flagged_spots": len(flagged_v2),
        "rules_v2_incremental_unique_spots": len(v2_incremental),
        "rules_v2_incremental_share_inventory": len(v2_incremental) / len(inventory),
        "rules_v2_note": (
            "Rules v2 includes S001 Land x building/interior copy. It is a "
            "post-discovery challenger and must not be evaluated as if pre-registered."
        ),
    }
    write_json(RESULTS / "semantic_discovery_summary.json", semantic_summary)

    discovery_n = make_labeling_sample(DISCOVERY_SAMPLE)
    holdout_n = make_holdout_v2(HOLDOUT_V2)

    combined = {
        "experiment_id": "E015_llm_inventory_semantic_audit",
        "phase": "offline_semantic_discovery_v2",
        "copy_profile": profile_summary,
        "rules_v1": rule_summary,
        "semantic_discovery": semantic_summary,
        "discovery_sample_n": discovery_n,
        "clean_holdout_v2_n": holdout_n,
        "llm_executed": False,
        "conclusion": "INCOMPLETE_LLM_PENDING",
    }
    write_json(RESULTS / "offline_summary.json", combined)
    print(json.dumps(combined, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
