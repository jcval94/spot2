"""Deterministic helpers for the future online experiment protocol."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable


def sticky_assignment(lead_id: object, salt: str, treatment_share: float = 0.5) -> str:
    if not 0 < treatment_share < 1:
        raise ValueError("treatment_share must be between zero and one")
    digest = hashlib.sha256(f"{salt}|{lead_id}".encode("utf-8")).digest()
    uniform = int.from_bytes(digest[:8], "big") / 2**64
    return "treatment" if uniform < treatment_share else "control"


def sample_ratio_mismatch_z(assignments: Iterable[str], expected_treatment_share: float = 0.5) -> float:
    values = list(assignments)
    if not values:
        return 0.0
    treatment = sum(value == "treatment" for value in values)
    expected = len(values) * expected_treatment_share
    standard_error = math.sqrt(len(values) * expected_treatment_share * (1 - expected_treatment_share))
    return (treatment - expected) / max(1e-12, standard_error)

