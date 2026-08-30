from __future__ import annotations

import importlib.util
from pathlib import Path
from datetime import datetime, timezone
import polars as pl
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ABT_DIR = REPO_ROOT / "AssessmentSol1" / "abt"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ABT_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate = _load("validate_abts")


def test_prediction_key_unique_synthetic() -> None:
    validate.assert_prediction_key_unique(pl.DataFrame({"prediction_key": ["a", "b"]}))
    with pytest.raises(AssertionError):
        validate.assert_prediction_key_unique(pl.DataFrame({"prediction_key": ["a", "a"]}))


def test_no_future_snapshot() -> None:
    ok = pl.DataFrame({
        "score_time": [datetime(2026, 1, 2, tzinfo=timezone.utc)],
        "snapshot_time": [datetime(2026, 1, 1, tzinfo=timezone.utc)],
    })
    validate.assert_no_future_snapshot(ok)
    bad = pl.DataFrame({
        "score_time": [datetime(2026, 1, 1, tzinfo=timezone.utc)],
        "snapshot_time": [datetime(2026, 1, 2, tzinfo=timezone.utc)],
    })
    with pytest.raises(AssertionError):
        validate.assert_no_future_snapshot(bad)


def test_no_future_inquiry() -> None:
    bad = pl.DataFrame({
        "score_time": [datetime(2026, 1, 1, tzinfo=timezone.utc)],
        "hist_max_inquiry_time": [datetime(2026, 1, 1, tzinfo=timezone.utc)],
    })
    with pytest.raises(AssertionError):
        validate.assert_no_future_inquiry(bad)


def test_forbidden_feature_guard() -> None:
    with pytest.raises(AssertionError):
        validate.assert_no_forbidden_model_feature(
            pl.DataFrame({"lead_id": [1], "broker_response": ["accepted"]})
        )


def test_target_status_contract() -> None:
    good = pl.DataFrame({
        "target_status": ["POSITIVE", "NEGATIVE", "CENSORED"],
        "target_value": [1, 0, None],
    })
    validate.assert_target_statuses(good)


def test_candidate_join_grain() -> None:
    good = pl.DataFrame({
        "prediction_key": ["a", "a"],
        "candidate_spot_id": [1, 2],
    })
    validate.assert_candidate_grain(good)
    bad = pl.DataFrame({
        "prediction_key": ["a", "a"],
        "candidate_spot_id": [1, 1],
    })
    with pytest.raises(AssertionError):
        validate.assert_candidate_grain(bad)


def test_split_integrity_fails_entity_leakage() -> None:
    validate.assert_split_integrity(
        pl.DataFrame({"lead_id": [1, 2], "partition": ["train", "eval"]})
    )
    with pytest.raises(AssertionError):
        validate.assert_split_integrity(
            pl.DataFrame({
                "lead_id": [1, 1],
                "partition": ["train", "eval"],
            })
        )


def test_stage_observability() -> None:
    good = pl.DataFrame({
        "stage": ["T0", "T1", "T2"],
        "current_inquiry_id": [None, 10, 11],
        "inquiry_number": [0, 1, 2],
    })
    validate.assert_stage_observability(good)


def test_lineage_complete_for_minimal_artifact() -> None:
    validate.assert_lineage_complete(
        {"prediction_key", "lead_id", "stage", "score_time"},
        ABT_DIR / "COLUMN_LINEAGE.csv",
    )


def test_committed_abt_evidence_passes() -> None:
    result = validate.validate_committed_evidence(REPO_ROOT)
    assert result["status"] == "PASS"
    assert result["score_spine_rows"] == 27576
    assert result["audit_rows"] == 27576
    assert result["model_ready_rows"] == 19298
    assert result["candidate_full_rows"] == 1114990
    assert result["inventory_full_rows"] == 1114990
    assert result["future_inquiry_count"] == 0
    assert result["future_snapshot_count"] == 0
    assert result["forbidden_model_feature_count"] == 0


def test_no_split_assignment_is_embedded_in_committed_abts() -> None:
    audit_dir = ABT_DIR / "artifacts" / "lead_quality_audit_all_snapshots"
    model_dir = ABT_DIR / "artifacts" / "lead_quality_model_ready"
    audit_header = pl.read_csv(sorted(audit_dir.glob("part-*.csv"))[0], n_rows=1).columns
    model_header = pl.read_csv(sorted(model_dir.glob("part-*.csv"))[0], n_rows=1).columns
    assert not {"partition", "fold", "split"}.intersection(audit_header)
    assert not {"partition", "fold", "split"}.intersection(model_header)
