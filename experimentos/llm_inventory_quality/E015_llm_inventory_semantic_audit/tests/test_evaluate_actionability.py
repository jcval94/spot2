from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from src.evaluate import llm_positive  # noqa: E402


def record(classification: str, actionable: bool):
    return {
        "status": "ok",
        "audit": {
            "issues": [
                {
                    "classification": classification,
                    "actionable": actionable,
                }
            ]
        },
    }


class TestEvaluateActionability(unittest.TestCase):
    def test_unsupported_claim_never_counts_positive(self):
        self.assertEqual(llm_positive(record("unsupported_claim", True)), 0)

    def test_not_verifiable_never_counts_positive(self):
        self.assertEqual(llm_positive(record("not_verifiable", True)), 0)

    def test_ambiguous_never_counts_positive(self):
        self.assertEqual(llm_positive(record("ambiguous", True)), 0)

    def test_actionable_contradiction_counts_positive(self):
        self.assertEqual(llm_positive(record("contradiction", True)), 1)

    def test_non_actionable_contradiction_does_not_count(self):
        self.assertEqual(llm_positive(record("contradiction", False)), 0)

    def test_actionable_cross_field_mismatch_counts_positive(self):
        self.assertEqual(
            llm_positive(record("semantic_cross_field_mismatch", True)),
            1,
        )


if __name__ == "__main__":
    unittest.main()
