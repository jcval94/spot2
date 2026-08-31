"""Deliberately unsafe comparisons kept outside the deployable pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .contracts import Settings
from .evaluation import binary_metrics


def _single_feature_model(train: pd.DataFrame, test: pd.DataFrame, feature: str) -> np.ndarray:
    pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("model", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    pipe.fit(train[[feature]], train["target_t1"].astype(int))
    return pipe.predict_proba(test[[feature]])[:, 1]


def _nearest_snapshot(rows: pd.DataFrame, availability: pd.DataFrame) -> pd.DataFrame:
    right = availability[["spot_id", "snapshot_date", "is_available"]].copy()
    result = pd.merge_asof(
        rows.sort_values(["prediction_timestamp", "spot_id"]),
        right.sort_values(["snapshot_date", "spot_id"]),
        left_on="prediction_timestamp",
        right_on="snapshot_date",
        by="spot_id",
        direction="nearest",
    )
    result["nearest_is_available"] = result["is_available"].astype(float)
    result["snapshot_is_future"] = result["snapshot_date"] > result["prediction_timestamp"]
    return result.sort_index()


def run_stress_tests(
    abt: pd.DataFrame,
    inquiries: pd.DataFrame,
    availability: pd.DataFrame,
    clean_holdout: pd.DataFrame,
    settings: Settings,
) -> dict[str, Any]:
    mature = abt[abt["target_t1"].notna()].copy()
    train = mature[mature["split"].eq("train")].copy()
    test = mature[mature["split"].eq("test")].copy()
    rows: list[dict[str, Any]] = [{
        "condition": "clean_selected",
        "label": "DEPLOYABLE",
        **binary_metrics(clean_holdout["target_t1"], clean_holdout["selected_calibrated"]),
    }]

    internal_pred = _single_feature_model(train, test, "lead_score_internal")
    rows.append({
        "condition": "S001_lead_score_internal",
        "label": "NON_DEPLOYABLE_UNKNOWN_PROVENANCE",
        **binary_metrics(test["target_t1"], internal_pred),
    })

    future = inquiries.groupby("lead_id").agg(
        future_inquiry_count=("inquiry_id", "size"),
        future_scheduled_visit=("broker_response", lambda s: int(s.eq("scheduled_visit").any())),
    ).reset_index()
    train_future = train.merge(future, on="lead_id", validate="one_to_one")
    test_future = test.merge(future, on="lead_id", validate="one_to_one")
    unsafe = LogisticRegression(max_iter=1000, random_state=settings.seed).fit(
        train_future[["future_inquiry_count", "future_scheduled_visit"]], train_future["target_t1"].astype(int)
    )
    future_pred = unsafe.predict_proba(test_future[["future_inquiry_count", "future_scheduled_visit"]])[:, 1]
    rows.append({
        "condition": "S002_future_inquiry_information",
        "label": "NON_DEPLOYABLE_DIRECT_FUTURE_LEAKAGE",
        **binary_metrics(test_future["target_t1"], future_pred),
    })

    train_nearest = _nearest_snapshot(train[["lead_id", "spot_id", "prediction_timestamp", "target_t1"]], availability)
    test_nearest = _nearest_snapshot(test[["lead_id", "spot_id", "prediction_timestamp", "target_t1"]], availability)
    nearest_pred = _single_feature_model(train_nearest, test_nearest, "nearest_is_available")
    rows.append({
        "condition": "S003_nearest_availability_snapshot",
        "label": "NON_DEPLOYABLE_FUTURE_SNAPSHOTS",
        "future_snapshot_rate": float(test_nearest["snapshot_is_future"].mean()),
        **binary_metrics(test_nearest["target_t1"], nearest_pred),
    })

    output = settings.codexway_root / "outputs" / "metrics"
    output.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(rows)
    table.to_csv(output / "leakage_stress_test.csv", index=False)
    summary = {
        "status": "DIAGNOSTIC_ONLY",
        "warning": "No stress model is eligible for deployment or model selection.",
        "comparisons": table.to_dict(orient="records"),
    }
    (output / "leakage_stress_test.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary

