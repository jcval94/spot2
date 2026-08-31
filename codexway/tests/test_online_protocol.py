from __future__ import annotations

from spot2_codexway.online import sample_ratio_mismatch_z, sticky_assignment


def test_assignment_is_sticky_and_balanced():
    first = [sticky_assignment(i, "spot2-pilot-v1") for i in range(10000)]
    second = [sticky_assignment(i, "spot2-pilot-v1") for i in range(10000)]
    assert first == second
    assert abs(sample_ratio_mismatch_z(first)) < 3

