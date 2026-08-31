from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_pre_p8_gate_passed() -> None:
    gate = json.loads((ROOT / "audit" / "PRE_P8_GATE_STATUS.json").read_text())
    assert gate["status"] == "PASS"


def test_t1_remains_frozen_and_unchanged() -> None:
    cfg = json.loads(
        (ROOT / "models" / "lead_quality" / "FROZEN_MODEL_CONFIG.json").read_text()
    )
    assert cfg["status"] == "FROZEN"
    assert cfg["model_family"] == "BASE_RATE"
    assert cfg["calibrator"]["method"] == "RAW"


def test_p8_decisions_are_bounded() -> None:
    p8 = json.loads((ROOT / "models" / "P8_EXECUTION_MANIFEST.json").read_text())
    assert p8["status"] == "COMPLETE"
    assert p8["t1_modified"] is False
    assert p8["t0"]["decision"] == "NEUTRAL_EVIDENCE_BACKED"
    assert p8["t0"]["promotion"] is False
    assert p8["t2"]["decision"] == "FUTURE_EXTENSION"
    assert p8["t2"]["promotion"] is False


def test_t0_and_t1_are_different_estimands() -> None:
    contract = json.loads((ROOT / "target" / "target_contract.json").read_text())
    assert (
        contract["secondary_targets"]["T0"]["id"]
        != contract["primary_target"]["id"]
    )
    assert contract["secondary_targets"]["T0"]["same_estimand_as_primary"] is False


def test_t0_exposure_drift_is_audit_only_evidence() -> None:
    df = pd.read_csv(ROOT / "models" / "t0" / "metrics" / "exposure_drift.csv")
    assert df.loc[df["cohort"].eq("2025H1"), "mean_inquiries_30d"].iloc[0] < 2
    assert df.loc[df["cohort"].eq("2026APR"), "mean_inquiries_30d"].iloc[0] > 3.9
    assert df.loc[df["cohort"].eq("2025H1"), "target_rate"].iloc[0] < 0.35
    assert df.loc[df["cohort"].eq("2026APR"), "target_rate"].iloc[0] > 0.50


def test_t2_trajectory_fails_frozen_promotion_requirements() -> None:
    protocol = json.loads((ROOT / "models" / "P8_PROTOCOL.json").read_text())
    p8 = json.loads((ROOT / "models" / "P8_EXECUTION_MANIFEST.json").read_text())
    rule = protocol["t2"]["promotion_rule"]
    assert p8["t2"]["delta_ap"] < rule["min_macro_delta_average_precision"]
    assert p8["t2"]["positive_ap_folds"] < rule["min_folds_with_positive_delta_ap"]


def test_t2_temporal_invariants_hold() -> None:
    p8 = json.loads((ROOT / "models" / "P8_EXECUTION_MANIFEST.json").read_text())
    assert p8["t2"]["strict_history_violations"] == 0
    assert p8["t2"]["response_history_predictors"] == 0


def test_no_stage_claims_learned_ranking_deployment() -> None:
    p8 = json.loads((ROOT / "models" / "P8_EXECUTION_MANIFEST.json").read_text())
    policy = p8["final_stage_policy"]
    assert policy["t0_deploy_predictive_ranking"] is False
    assert policy["t1_deploy_learned_ranking"] is False
    assert policy["t2_deploy_predictive_ranking"] is False
