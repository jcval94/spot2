from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from target_contract import TARGET_NAME, label_scoring_snapshots


class TargetContractBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.anchor = pd.Timestamp("2026-01-01 00:00:00")
        self.observation_end = pd.Timestamp("2026-03-15 00:00:00")

    def _snapshot(self, lead_id: str, anchor: pd.Timestamp | None = None) -> pd.DataFrame:
        return pd.DataFrame([{
            "lead_id": lead_id,
            "score_time": self.anchor if anchor is None else anchor,
        }])

    def _event(
        self,
        lead_id: str,
        inquiry_at: pd.Timestamp,
        response_hours: float | None,
        response: str = "scheduled_visit",
    ) -> pd.DataFrame:
        return pd.DataFrame([{
            "lead_id": lead_id,
            "inquiry_at": inquiry_at,
            "broker_response_hours": np.nan if response_hours is None else response_hours,
            "broker_response": response,
        }])

    def _label(self, snapshots: pd.DataFrame, inquiries: pd.DataFrame) -> pd.Series:
        out = label_scoring_snapshots(
            snapshots,
            inquiries,
            observation_end=self.observation_end,
        )
        return out.iloc[0]

    def test_known_event_strictly_after_anchor_is_positive(self) -> None:
        row = self._label(
            self._snapshot("inside"),
            self._event("inside", self.anchor + pd.Timedelta(days=1), 24),
        )
        self.assertEqual(row["target_status"], "POSITIVE")
        self.assertEqual(row[TARGET_NAME], 1.0)

    def test_event_exactly_at_horizon_end_is_positive(self) -> None:
        row = self._label(
            self._snapshot("at_end"),
            self._event("at_end", self.anchor + pd.Timedelta(days=29), 24),
        )
        self.assertEqual(row["target_status"], "POSITIVE")
        self.assertEqual(row[TARGET_NAME], 1.0)

    def test_event_after_horizon_is_negative(self) -> None:
        row = self._label(
            self._snapshot("after_end"),
            self._event("after_end", self.anchor + pd.Timedelta(days=30), 24),
        )
        self.assertEqual(row["target_status"], "NEGATIVE")
        self.assertEqual(row[TARGET_NAME], 0.0)

    def test_event_exactly_at_anchor_is_prior_and_ineligible(self) -> None:
        row = self._label(
            self._snapshot("at_anchor"),
            self._event("at_anchor", self.anchor - pd.Timedelta(hours=1), 1),
        )
        self.assertEqual(row["target_status"], "INELIGIBLE_PRIOR_SCHEDULED_VISIT")
        self.assertTrue(pd.isna(row[TARGET_NAME]))

    def test_known_prior_visit_makes_snapshot_ineligible(self) -> None:
        row = self._label(
            self._snapshot("prior"),
            self._event("prior", self.anchor - pd.Timedelta(days=2), 12),
        )
        self.assertEqual(row["target_status"], "INELIGIBLE_PRIOR_SCHEDULED_VISIT")
        self.assertTrue(pd.isna(row[TARGET_NAME]))

    def test_unknown_event_time_that_can_touch_window_is_ambiguous(self) -> None:
        row = self._label(
            self._snapshot("unknown_touch"),
            self._event("unknown_touch", self.anchor + pd.Timedelta(days=10), None),
        )
        self.assertEqual(row["target_status"], "AMBIGUOUS_UNKNOWN_EVENT_TIME")
        self.assertTrue(pd.isna(row[TARGET_NAME]))

    def test_unknown_event_starting_after_window_is_negative(self) -> None:
        row = self._label(
            self._snapshot("unknown_after"),
            self._event("unknown_after", self.anchor + pd.Timedelta(days=31), None),
        )
        self.assertEqual(row["target_status"], "NEGATIVE")
        self.assertEqual(row[TARGET_NAME], 0.0)

    def test_immature_snapshot_is_right_censored(self) -> None:
        anchor = self.observation_end - pd.Timedelta(days=20)
        row = self._label(
            self._snapshot("censored", anchor),
            self._event("other", self.anchor + pd.Timedelta(days=5), 2),
        )
        self.assertEqual(row["target_status"], "RIGHT_CENSORED")
        self.assertTrue(pd.isna(row[TARGET_NAME]))


if __name__ == "__main__":
    unittest.main()
