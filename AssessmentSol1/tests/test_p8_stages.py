from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_pre_p8_gate_is_closed_without_resetting_holdout() -> None:
    gate = json.loads((ROOT / "audit" / "PRE_P8_GATE_STATUS.json").read_text())
    assert gate["status"] == "PASS"
    assert gate["p4_validation"]["status"] == "PASS"
    assert gate["frozen_foundations"]["t1_champion"] == "BASE_RATE + RAW"


def test_p8_protocol_was_frozen_before_results() -> None:
    protocol = json.loads((ROOT / "models" / "P8_PROTOCOL.json").read_text())
    assert protocol["frozen_before_results"] is True
    assert protocol["t1_immutable"] is True
    assert protocol["procedural_holdout_selection_allowed"] is False
    assert protocol["t2"]["models"] == ["T2_BASELINE", "T2_TRAJECTORY"]


def test_t0_is_intake_only_and_neutral() -> None:
    result = json.loads((ROOT / "models" / "t0" / "RESULT.json").read_text())
    assert result["decision"] == "NEUTRAL_EVIDENCE_BACKED"
    assert result["forbidden_predictors_used"] is False
    assert result["future_exposure_used_as_predictor"] is False
    assert "different quantities" in result["statement"]


def test_t2_trajectory_not_promoted_and_history_is_strict() -> None:
    result = json.loads((ROOT / "models" / "t2" / "RESULT.json").read_text())
    assert result["decision"] == "FUTURE_EXTENSION"
    assert result["promotion_passed"] is False
    assert result["strict_history_violations"] == 0
    assert result["response_history_predictor_used"] is False
    assert result["future_snapshot_test"] == "PASS_NOT_IN_INFORMATION_SET"


def test_t2_boundary_crossing_is_actively_blocked() -> None:
    df = pd.read_csv(ROOT / "models" / "t2" / "boundary_audit.csv")
    assert (df["train_validation_lead_overlap"] == 0).all()
    assert (df["train_lead_late_rows_excluded"] > 0).all()
    assert (df["validation_lead_rows_after_window_excluded"] > 0).all()
    assert (
        pd.to_datetime(df["max_train_score_time"], utc=True)
        < pd.to_datetime(df["min_validation_score_time"], utc=True)
    ).all()


def test_t2_increment_is_below_frozen_complexity_gate() -> None:
    result = json.loads((ROOT / "models" / "t2" / "RESULT.json").read_text())
    assert result["deltas"]["average_precision"] < result["promotion_rule"]["min_macro_delta_ap"]


def test_p4_equivalence_audit_has_no_selected_future_rows() -> None:
    qa = json.loads((ROOT / "abt" / "artifacts" / "p4_qa_summary.json").read_text())
    assert qa["status"] == "PASS"
    assert qa["historical_abts_used_as_inputs"] is False
    assert qa["invariants"]["selected_future_spot_count"] == 0
    assert qa["invariants"]["future_snapshot_count"] == 0
    assert qa["invariants"]["split_unique_leads"] == 5000
