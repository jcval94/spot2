from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
SRC = HERE / "src"
sys.path.insert(0, str(SRC))

from run_set import actual_cost, reserve_cost  # noqa: E402
from client import load_prompt_schema  # noqa: E402


class TestBudgetContract(unittest.TestCase):
    def test_actual_cost_matches_gpt5mini_prices(self):
        record = {"input_tokens": 1_000_000, "output_tokens": 1_000_000}
        self.assertAlmostEqual(actual_cost(record), 2.25)

    def test_single_call_reservation_is_below_one_cent_for_small_payload(self):
        prompt, schema = load_prompt_schema()
        payload = {
            "spot_id": "1",
            "title": "x",
            "description": "y",
            "attributes": {}
        }
        self.assertLess(reserve_cost(payload, prompt, schema), 0.01)


if __name__ == "__main__":
    unittest.main()
