from __future__ import annotations

import pandas as pd

from spot2_codexway.abt import assign_t1_split, attach_availability_backward, build_t1_abt
from spot2_codexway.data import load_all
from spot2_codexway.targets import add_t1_target, first_inquiries


def test_backward_asof_never_selects_future():
    rows = pd.DataFrame({
        "row_id": [1, 2], "spot_id": [10, 10],
        "prediction_timestamp": pd.to_datetime(["2025-01-05", "2025-01-11"], utc=True),
    })
    snapshots = pd.DataFrame({
        "snapshot_id": [1, 2], "spot_id": [10, 10],
        "snapshot_date": pd.to_datetime(["2025-01-01", "2025-01-10"], utc=True),
        "is_available": [False, True], "days_until_available": [20, 0],
    })
    result = attach_availability_backward(rows, snapshots, row_key="row_id")
    assert result["snapshot_id"].tolist() == [1, 2]
    assert (result["snapshot_date"] <= result["prediction_timestamp"]).all()


def test_t1_target_maturity_and_exact_counts(settings):
    tables = load_all(settings)
    target = add_t1_target(first_inquiries(tables["inquiries"]), settings)
    assert len(target) == 5000
    assert target["target_t1"].notna().sum() == 4898
    assert int(target["target_t1"].sum()) == 1001
    assert target["target_t1"].isna().sum() == 102
    assert not target["broker_response_hours"].isna().all()  # field exists, but maturity ignores it


def test_t1_abt_is_point_in_time_and_unique(settings):
    abt = build_t1_abt(settings)
    assert abt["lead_id"].is_unique
    assert abt["inquiry_id"].is_unique
    assert len(abt) == 5000
    assert not (abt["spot_created_at"] > abt["prediction_timestamp"]).any()
    assert not (abt["snapshot_date"] > abt["prediction_timestamp"]).fillna(False).any()


def test_temporal_split_exact_populations(settings):
    abt = assign_t1_split(build_t1_abt(settings), settings)
    expected = {"train": 2191, "validation": 847, "test": 1711, "censored": 102}
    counts = abt["split"].value_counts().to_dict()
    for name, n in expected.items():
        assert counts[name] == n
    assert abt.loc[abt["split"].eq("train"), "prediction_timestamp"].max() < settings.split.train_end_exclusive
    assert abt.loc[abt["split"].eq("validation"), "prediction_timestamp"].min() >= settings.split.validation_start
    assert abt.loc[abt["split"].eq("test"), "prediction_timestamp"].min() >= settings.split.test_start

