"""Non-scientific clean-room guardrails for PROMPT 0."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath


class InformationStatus(str, Enum):
    KNOWN = "KNOWN"
    CONDITIONAL = "CONDITIONAL"
    AUDIT_ONLY = "AUDIT_ONLY"
    BLOCKED_FUTURE = "BLOCKED_FUTURE"
    BLOCKED_TEMPORAL_SEMANTICS = "BLOCKED_TEMPORAL_SEMANTICS"


@dataclass(frozen=True)
class StageContract:
    stage: str
    score_time_definition: str


STAGES = (
    StageContract("T0", "leads.created_at"),
    StageContract("T1", "first inquiries.inquiry_at for lead_id"),
    StageContract(
        "T2",
        "current second-or-later inquiries.inquiry_at while no visit is already known",
    ),
)


def is_allowed_assessment_write(path: str) -> bool:
    """Return True only for paths allowed by PROMPT 0.

    .github is intentionally excluded here because PROMPT 0 did not need a
    workflow change. Future phases may add a separate explicit exception.
    """
    p = PurePosixPath(path)
    parts = p.parts
    return bool(parts) and parts[0] == "AssessmentSol1"
