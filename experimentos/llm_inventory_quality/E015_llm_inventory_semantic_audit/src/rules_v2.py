from __future__ import annotations

from typing import Any

from .rules import audit_row
from .semantic_discovery import semantic_observations


def audit_row_v2(row: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Post-discovery ruleset.

    v1 is intentionally preserved in rules.py because S001 was discovered after
    reviewing the original 200-row discovery sample. v2 adds only the semantic
    pattern considered actionable enough to promote to a deterministic rule.
    """
    issues = list(audit_row(row))
    for observation in semantic_observations(row):
        if not observation["actionable"]:
            continue
        issues.append({
            "spot_id": row["spot_id"],
            "sector_name": row.get("sector_name"),
            "type_name": row.get("type_name"),
            "rule_id": observation["pattern_id"],
            "claim_type": "cross_field_semantics",
            "evidence_text": observation["evidence_text"],
            "structured_field": "sector_name",
            "structured_value": row.get("sector_name"),
            "classification": observation["classification"],
            "severity": observation["severity"],
            "reason": observation["reason"],
        })
    return issues
