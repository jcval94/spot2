from __future__ import annotations

import numpy as np

from spot2_codexway.evaluation import binary_metrics


def test_top_k_metrics_are_invariant_to_row_order_when_boundary_is_tied():
    y = np.array([1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0])
    score = np.array([0.8] * 4 + [0.2] * 8)
    permutation = np.array([3, 0, 2, 1, 11, 4, 10, 5, 9, 6, 8, 7])

    original = binary_metrics(y, score)
    shuffled = binary_metrics(y[permutation], score[permutation])

    for metric in ("precision_top_5pct", "recall_top_10pct", "lift_top_20pct"):
        assert original[metric] == shuffled[metric]


def test_top_k_boundary_uses_fractional_expected_capture():
    y = np.array([1, 0, 1, 0, 0, 0, 0, 0, 0, 0])
    score = np.array([0.8] * 4 + [0.2] * 6)

    metrics = binary_metrics(y, score)

    # Top 20% has two slots inside a four-row tie containing two positives.
    assert metrics["precision_top_20pct"] == 0.5
    assert metrics["recall_top_20pct"] == 0.5
    assert metrics["lift_top_20pct"] == 2.5
