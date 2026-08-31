from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from harness.experiment_harness import finalize_record


def test_system_evaluation_clears_absolute_lift_gate_without_hiding_caveat(settings):
    path = settings.codexway_root / "outputs" / "metrics" / "system_evaluation.json"
    assert path.exists()
    audit = json.loads(path.read_text(encoding="utf-8"))
    assert audit["target_alignment"].startswith("PARTIAL_ONLY")
    assert audit["lead_quality_gate"] == "GO"
    assert audit["opportunity_absolute_lift_gate"] == "GO"
    assert audit["quality_lift_top_10pct"] > 1
    assert audit["quality_lift_top_10pct_ci"][0] > 1
    assert audit["opportunity_lift_top_10pct"] > 1
    assert audit["opportunity_lift_top_10pct_ci"][0] > 1
    assert audit["inventory_incremental_gate"] == "NO_GO"
    scores = pd.read_parquet(settings.codexway_root / "outputs" / "predictions" / "lead_opportunity_scores.parquet")
    assert (scores["inventory_serviceability_upper"] >= scores["inventory_serviceability_lower"]).all()
    if audit["system_deployment_gate"] != "GO":
        assert scores["deployment_status"].eq("DIAGNOSTIC_ONLY__SYSTEM_GATE_FAILED").all()


def test_stable_segment_was_selected_without_holdout(settings):
    result = json.loads(
        (settings.codexway_root / "outputs" / "metrics" / "t1_model_metrics.json").read_text(encoding="utf-8")
    )
    assert result["selected_model"] == "stable_segment_logistic"
    assert result["selection"]["promotion_gate_did_not_use_procedural_holdout"] is True
    assert result["selection"]["feature_hypothesis_holdout_blinding"].startswith("NOT_POSSIBLE")
    assert result["selection"]["rolling_folds_above_random"] >= 2
    assert result["selection"]["rolling_mean_lift_top_10pct"] > 1
    assert result["selection"]["rolling_median_lift_top_10pct"] > 1
    assert result["selection"]["validation_metrics"]["lift_top_10pct"] > 1


def test_runtime_source_does_not_reference_external_experiments(settings):
    source = settings.codexway_root / "src" / "spot2_codexway"
    for path in source.glob("*.py"):
        assert "experimentos" not in path.read_text(encoding="utf-8").lower()


def test_experiment_records_are_immutable(tmp_path: Path):
    spec = tmp_path / "E999.json"
    spec.write_text(json.dumps({
        "experiment_id": "E999", "parent_id": None, "contract": "T1",
        "feature_names": [], "change": "fixture", "deployable": True,
        "join_direction": "backward",
    }), encoding="utf-8")
    code = tmp_path / "code.py"; code.write_text("x=1\n", encoding="utf-8")
    records = tmp_path / "records"
    finalize_record(spec, {"x": 1}, {}, "data", [code], records, tmp_path)
    with pytest.raises(FileExistsError):
        finalize_record(spec, {"x": 2}, {}, "data", [code], records, tmp_path)
