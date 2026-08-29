from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from experimentos._sistema.harness.experiment_harness import (
    HarnessError,
    build_record,
    compare_with_parent,
    validate_spec,
    write_record,
)


def base_spec() -> dict:
    return {
        "experiment_id": "E001_baseline",
        "parent_experiment": None,
        "question": "Does the baseline satisfy the experiment contract?",
        "hypothesis": "A point-in-time-safe baseline can be evaluated.",
        "primary_change": "baseline",
        "secondary_changes": [],
        "scoring_time": {
            "stage": "T0",
            "timestamp_definition": "leads.created_at",
        },
        "target": {
            "event": "scheduled_visit",
            "horizon_days": 30,
            "anchor": "scoring_time",
            "censoring": "right",
        },
        "population": {
            "eligibility": "Eligible leads",
            "exclusions": ["Right-censored leads"],
            "period": {"start": None, "end": None},
        },
        "data_sources": ["data.csv"],
        "features": {
            "inherited": [],
            "added": ["user_type"],
            "removed": [],
        },
        "validation": {
            "strategy": "temporal",
            "time_column": "created_at",
            "split_description": "Chronological 80/20 split",
        },
        "metrics": [
            "roc_auc",
            "average_precision",
            "brier",
            "log_loss",
            "lift_top_10pct",
            "recall_top_20pct",
        ],
        "segments": ["search_sector", "search_modality", "user_type"],
        "leakage": {
            "check_status": "PASS",
            "items": [
                {
                    "element": "user_type",
                    "source": "leads.user_type",
                    "scoring_time": "leads.created_at",
                    "information_available_at": "leads.created_at",
                    "status": "ALLOW",
                    "evidence": "Available on the lead row at creation.",
                }
            ],
        },
    }


def base_results(experiment_id: str = "E001_baseline") -> dict:
    return {
        "experiment_id": experiment_id,
        "metrics": {
            "roc_auc": 0.51,
            "average_precision": 0.40,
            "brier": 0.20,
            "log_loss": 0.69,
            "lift_top_10pct": 1.10,
            "recall_top_20pct": 0.23,
        },
        "segment_metrics": {},
        "conclusion": "INCONCLUSIVE",
        "caveats": ["Synthetic test fixture."],
        "next_experiment": "Add one safe feature.",
    }


class ExperimentHarnessTests(unittest.TestCase):
    def test_valid_baseline_spec_passes(self) -> None:
        validate_spec(base_spec())

    def test_blocked_leakage_fails(self) -> None:
        spec = base_spec()
        spec["leakage"]["items"][0]["status"] = "BLOCK"
        with self.assertRaises(HarnessError):
            validate_spec(spec)

    def test_added_feature_requires_leakage_review(self) -> None:
        spec = base_spec()
        spec["features"]["added"].append("company_size")
        with self.assertRaises(HarnessError):
            validate_spec(spec)

    def test_changed_target_is_non_equivalent(self) -> None:
        parent = base_spec()
        child = json.loads(json.dumps(parent))
        child["experiment_id"] = "E002_target_change"
        child["parent_experiment"] = "E001_baseline"
        child["features"] = {
            "inherited": ["user_type"],
            "added": [],
            "removed": [],
        }
        child["leakage"]["items"] = []
        child["target"]["horizon_days"] = 60
        child["primary_change"] = "change target horizon"

        validate_spec(child)
        comparison = compare_with_parent(child, parent)
        self.assertEqual(comparison["status"], "NON_EQUIVALENT")
        self.assertIn("target differs from parent", comparison["reasons"])

    def test_finalized_record_is_immutable(self) -> None:
        spec = base_spec()
        results = base_results()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data.csv").write_text("x\n1\n", encoding="utf-8")
            record = build_record(spec, results, repo_root=root)
            destination = write_record(record, root / "out")
            self.assertTrue((destination / "record.json").exists())
            self.assertTrue((destination / "summary.md").exists())
            with self.assertRaises(HarnessError):
                write_record(record, root / "out")


if __name__ == "__main__":
    unittest.main()
