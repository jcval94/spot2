from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models" / "lead_quality"


def test_p7_promotion_rule_was_frozen_before_results() -> None:
    rule = json.loads((MODEL / "MODEL_PROMOTION_RULE.json").read_text())
    assert rule["frozen_before_model_results"] is True


def test_single_frozen_champion_is_base_rate_without_features() -> None:
    cfg = json.loads((MODEL / "FROZEN_MODEL_CONFIG.json").read_text())
    assert cfg["status"] == "FROZEN"
    assert cfg["model_family"] == "BASE_RATE"
    assert cfg["feature_set"]["variant"] == "BASE_RATE_NO_FEATURES"
    assert cfg["feature_set"]["features"] == []
    assert cfg["calibrator"]["method"] == "PLATT"


def test_holdout_incident_is_explicit_and_not_used_for_selection() -> None:
    cfg = json.loads((MODEL / "FROZEN_MODEL_CONFIG.json").read_text())
    assert cfg["holdout_integrity"]["pristine"] is False
    assert (
        cfg["holdout_integrity"]["status"]
        == "CONSUMED_BY_METHOD_INCIDENT_BEFORE_FREEZE"
    )
    assert cfg["selection_populations"]["procedural_holdout"]["used_for_selection"] is False


def test_prediction_populations_are_physically_separate() -> None:
    pred = MODEL / "predictions"
    dev = pd.read_csv(pred / "champion_development_oof.csv")
    cal = pd.read_csv(pred / "calibration_predictions.csv")
    hold = pd.read_csv(pred / "procedural_holdout_predictions.csv")

    assert set(dev["population"]) == {"DEVELOPMENT_OOF"}
    assert set(cal["population"]) == {"CALIBRATION"}
    assert set(hold["population"]) == {"DIAGNOSTIC_ONLY_NON_PRISTINE"}
    assert set(dev["lead_id"]).isdisjoint(set(cal["lead_id"]))
    assert set(dev["lead_id"]).isdisjoint(set(hold["lead_id"]))
    assert set(cal["lead_id"]).isdisjoint(set(hold["lead_id"]))


def test_development_fold_metrics_cover_frozen_model_variants() -> None:
    df = pd.read_csv(MODEL / "metrics" / "development_fold_metrics.csv")
    expected = {
        "BASE_RATE",
        "BUSINESS_RULE",
        "LOGISTIC_A",
        "LOGISTIC_B",
        "LOGISTIC_C",
        "LOGISTIC_D_WITH_ASKED_VISIT",
        "LOGISTIC_D_WITHOUT_ASKED_VISIT",
        "LOGISTIC_E",
        "CATBOOST_A",
    }
    assert expected <= set(df["model_variant"])
    for model in expected:
        assert set(df.loc[df["model_variant"].eq(model), "fold"]) == {
            "F1",
            "F2",
            "F3",
            "F4",
        }


def test_base_rate_terminal_gate_evidence_is_persisted() -> None:
    boot = pd.read_csv(MODEL / "metrics" / "bootstrap_comparisons.csv")
    comp = boot.loc[boot["comparison"].eq("BASE_to_LOGISTIC_A")]
    ap = comp.loc[comp["metric"].eq("average_precision")].iloc[0]
    brier = comp.loc[comp["metric"].eq("brier")].iloc[0]
    assert ap["ci95_low"] < 0 < ap["ci95_high"]
    assert brier["ci95_low"] > 0


def test_constant_champion_does_not_claim_ranking() -> None:
    artifact = json.loads(
        (MODEL / "artifacts" / "base_rate_champion.json").read_text()
    )
    assert artifact["ranking_capability"] is False
