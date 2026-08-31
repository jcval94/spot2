from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit"


def _load_harness():
    spec = importlib.util.spec_from_file_location("final_audit_harness", AUDIT / "harness.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_stress_specs_are_rejected_in_product_mode() -> None:
    harness = _load_harness()
    for path in sorted((AUDIT / "stress").glob("S00*.json")):
        payload = json.loads(path.read_text())
        assert payload["unsafe"] is True
        assert payload["deployable"] is False
        try:
            harness.assert_product_safe(payload)
        except harness.UnsafePipelineSpec:
            pass
        else:
            raise AssertionError(f"Unsafe stress spec passed product harness: {path.name}")


def test_product_pipeline_does_not_import_stress_modules() -> None:
    product_paths = [
        ROOT / "models" / "lead_quality" / "train.py",
        ROOT / "models" / "lead_quality" / "calibration.py",
        ROOT / "inventory" / "build_inventory.py",
        ROOT / "inventory" / "rank_fallbacks.py",
        ROOT / "opportunity_score" / "build_score.py",
        ROOT / "opportunity_score" / "evaluate_score.py",
    ]
    for path in product_paths:
        text = path.read_text(encoding="utf-8")
        assert "audit.stress" not in text
        assert "audit/stress" not in text
        assert "run_stress_tests" not in text


def test_clean_inventory_does_not_use_nearest_join() -> None:
    text = (ROOT / "inventory" / "build_inventory.py").read_text(encoding="utf-8")
    assert 'strategy="backward"' in text
    assert 'strategy="nearest"' not in text


def test_final_score_excludes_outcomes_and_internal_reference() -> None:
    text = (ROOT / "opportunity_score" / "build_score.py").read_text(encoding="utf-8")
    forbidden = ["broker_response", "broker_response_hours", "lead_score_internal", "target_value"]
    for token in forbidden:
        assert token not in text


def test_leakage_matrix_contains_no_active_blocker() -> None:
    rows = list(csv.DictReader((AUDIT / "LEAKAGE_MATRIX.csv").open(encoding="utf-8")))
    assert rows
    assert not any(r["status"] == "BLOCKER" for r in rows)


def test_final_audit_ready_requires_zero_blockers() -> None:
    payload = json.loads((AUDIT / "final_audit.json").read_text())
    assert payload["status"] == "READY"
    assert payload["severity_counts"]["BLOCKER"] == 0
    assert payload["gate"]["ready_requires_zero_blockers"] is True


def test_claims_policy_bans_independent_holdout_language() -> None:
    text = (AUDIT / "CLAIMS_POLICY.md").read_text(encoding="utf-8").lower()
    for phrase in ("pristine", "truly unseen", "independent final test", "independent confirmation"):
        assert phrase in text
    assert "procedural holdout diagnostic" in text
