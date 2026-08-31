from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from harness.experiment_harness import validate_spec
from spot2_codexway.features import FORBIDDEN, add_clean_t2_history, add_t1_features, validate_clean_features


def test_forbidden_features_rejected(settings):
    for feature in FORBIDDEN:
        with pytest.raises(ValueError):
            validate_clean_features([feature], settings.codexway_root / "config" / "feature_policy.yaml")


def test_t2_history_is_strictly_shifted():
    inquiries = pd.DataFrame({
        "lead_id": [1, 1, 1], "inquiry_id": [1, 2, 3], "spot_id": [5, 6, 7],
        "inquiry_at": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"], utc=True),
        "message_length": [10, 20, 30], "urgency_days": [30, 20, 10], "requested_area_sqm": [100, 200, 300],
    })
    result = add_clean_t2_history(inquiries)
    assert result["hist_prior_inquiry_count"].tolist() == [0, 1, 2]
    assert pd.isna(result.loc[0, "hist_prior_message_mean"])
    assert result.loc[1, "hist_prior_message_mean"] == 10
    assert result.loc[2, "hist_prior_message_mean"] == 15


def test_stable_segment_interaction_uses_only_t0_fields():
    frame = pd.DataFrame({
        "search_sector": ["Industrial", "Industrial", "Office"],
        "company_size": ["small", "large", "small"],
        "source": ["organic", "paid", "paid"],
        "prediction_timestamp": pd.to_datetime(["2025-01-02"] * 3, utc=True),
        "lead_created_at": pd.to_datetime(["2025-01-01"] * 3, utc=True),
        "requested_area_sqm": [100] * 3, "target_area_sqm": [100] * 3,
        "requested_budget_mxn_rent_monthly": [100] * 3,
        "max_budget_mxn_rent_monthly": [100] * 3,
        "requested_budget_mxn_sale_total": [pd.NA] * 3,
        "max_budget_mxn_sale_total": [pd.NA] * 3,
    })
    result = add_t1_features(frame)
    assert result["industrial_small_or_paid_interaction"].tolist() == [1, 1, 0]
    validate_clean_features(
        ["industrial_small_or_paid_interaction"],
        Path(__file__).resolve().parents[1] / "config" / "feature_policy.yaml",
    )


def test_clean_specs_pass_and_stress_specs_are_non_deployable(settings):
    for path in (settings.codexway_root / "experiments" / "specs").glob("*.json"):
        spec = json.loads(path.read_text(encoding="utf-8"))
        assert validate_spec(spec) == []
    for path in (settings.codexway_root / "experiments" / "stress").glob("*.json"):
        spec = json.loads(path.read_text(encoding="utf-8"))
        assert spec["deployable"] is False
        assert spec["label"] == "NON_DEPLOYABLE"
        assert validate_spec(spec)
