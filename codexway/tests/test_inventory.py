from __future__ import annotations

import json

import numpy as np
import pandas as pd

from spot2_codexway.inventory import build_inventory_candidates, combine_opportunity


def test_inventory_output_has_no_future_snapshots_and_bounded_recommendations(settings):
    assert (settings.codexway_root / "outputs" / "abt" / "abt_t1_first_inquiry.parquet").exists()
    t1 = pd.read_parquet(settings.codexway_root / "outputs" / "abt" / "abt_t1_first_inquiry.parquet").head(25)
    spots = pd.read_parquet(settings.data_dir / "spots.parquet")
    spots["created_at"] = pd.to_datetime(spots["created_at"], utc=True)
    availability = pd.read_parquet(settings.data_dir / "availability_snapshot.parquet")
    availability["snapshot_date"] = pd.to_datetime(availability["snapshot_date"], utc=True)
    candidates, scores = build_inventory_candidates(t1, spots, availability, settings)
    assert not (candidates["snapshot_date"] > candidates["prediction_timestamp"]).fillna(False).any()
    assert scores["lead_id"].is_unique
    assert scores["fallback_spot_ids"].map(lambda value: len(json.loads(value)) <= 5).all()
    assert (scores["inventory_serviceability_upper"] >= scores["inventory_serviceability_lower"]).all()
    unknown = candidates["availability_state"].eq("unknown_missing_or_stale")
    assert unknown.any()
    assert (candidates.loc[unknown, "availability_fit_lower"] == 0).all()
    assert (candidates.loc[unknown, "availability_fit_upper"] == 1).all()


def test_opportunity_formula_and_validation_thresholds(settings):
    t1 = pd.DataFrame({
        "lead_id": [1, 2, 3, 4], "inquiry_id": [11, 12, 13, 14],
        "prediction_timestamp": pd.to_datetime(["2025-10-01"] * 4, utc=True),
        "prediction_stage": ["T1"] * 4, "split": ["validation"] * 4,
    })
    inventory = pd.DataFrame({
        "lead_id": [1, 2, 3, 4], "score_id": [11, 12, 13, 14],
        "inventory_serviceability": [0.5, 0.5, 1.0, 0.0], "inventory_confidence": [1.0] * 4,
        "exact_spot_available": [True, False, True, False], "eligible_candidate_count": [1] * 4,
        "attendable_alternative_count": [0] * 4, "fallback_spot_ids": ["[]"] * 4,
        "fallback_reason_codes": ["[]"] * 4,
    })
    result = combine_opportunity(t1, np.array([0.2, 0.4, 0.6, 0.8]), inventory, settings)
    np.testing.assert_allclose(result["opportunity_probability"], [0.1, 0.2, 0.6, 0.0])
    assert result["opportunity_score_0_100"].between(0, 100).all()
