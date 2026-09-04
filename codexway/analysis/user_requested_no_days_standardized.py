from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from spot2_codexway.evaluation import binary_metrics
from spot2_codexway.features import CLEAN_T1_FEATURES, LEAD_CATEGORICAL, INQUIRY_CATEGORICAL

ROOT = Path(__file__).resolve().parents[1]
ABT = ROOT / "outputs" / "abt" / "abt_t1_first_inquiry.parquet"
OUT = ROOT / "outputs" / "metrics" / "user_requested_no_days_standardized.json"

TARGET = "target_t1"
DROP_FEATURE = "days_from_lead_creation"
INTERACTION = "industrial_small_or_paid_interaction"
FEATURES = [f for f in CLEAN_T1_FEATURES if f != DROP_FEATURE] + [INTERACTION]
CATEGORICAL = [f for f in (LEAD_CATEGORICAL + INQUIRY_CATEGORICAL) if f in FEATURES]
NUMERIC = [f for f in FEATURES if f not in CATEGORICAL]


def preprocessing() -> ColumnTransformer:
    # Every model sees the same standardized design matrix. Numeric features are
    # median-imputed then z-scaled. One-hot indicators are variance-scaled too;
    # with_mean=False preserves sparsity while still putting columns on a common scale.
    return ColumnTransformer(
        [
            (
                "cat",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=5)),
                        ("scale", StandardScaler(with_mean=False)),
                    ]
                ),
                CATEGORICAL,
            ),
            (
                "num",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                        ("scale", StandardScaler()),
                    ]
                ),
                NUMERIC,
            ),
        ]
    )


def monthly_metrics(frame: pd.DataFrame, score_col: str) -> list[dict]:
    scored = frame.copy()
    scored["month"] = pd.to_datetime(scored["prediction_timestamp"], utc=True).dt.strftime("%Y-%m")
    rows = []
    for month, group in scored.groupby("month", sort=True):
        m = binary_metrics(group[TARGET].astype(int), group[score_col])
        rows.append({"month": month, **m})
    return rows


def run() -> None:
    abt = pd.read_parquet(ABT)
    mature = abt[abt[TARGET].notna()].copy()
    train = mature[mature["split"].eq("train")].copy()
    validation = mature[mature["split"].eq("validation")].copy()
    test = mature[mature["split"].eq("test")].copy()

    base_preprocess = preprocessing()
    models = {
        "logistic_no_days_standardized": Pipeline(
            [
                ("preprocess", clone(base_preprocess)),
                ("model", LogisticRegression(C=1.0, max_iter=3000, random_state=42)),
            ]
        ),
        # Deliberately constrained a priori to reduce small-sample overfit; no test tuning.
        "random_forest_no_days_standardized": Pipeline(
            [
                ("preprocess", clone(base_preprocess)),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=800,
                        max_depth=6,
                        min_samples_leaf=20,
                        max_features="sqrt",
                        random_state=42,
                        n_jobs=1,
                    ),
                ),
            ]
        ),
    }

    result = {
        "method": {
            "abt": str(ABT.relative_to(ROOT)),
            "target": TARGET,
            "dropped_feature": DROP_FEATURE,
            "included_stable_interaction": INTERACTION,
            "features": FEATURES,
            "categorical": CATEGORICAL,
            "numeric": NUMERIC,
            "standardization": "fit on train only; numeric z-score; one-hot variance-scaled with_mean=False",
            "test_not_used_for_selection_or_tuning": True,
            "rf_parameters_fixed_before_test": True,
        },
        "splits": {
            "train": {"n": len(train), "prevalence": float(train[TARGET].mean())},
            "validation": {"n": len(validation), "prevalence": float(validation[TARGET].mean())},
            "test": {"n": len(test), "prevalence": float(test[TARGET].mean())},
        },
        "models": {},
    }

    for name, model in models.items():
        model.fit(train[FEATURES], train[TARGET].astype(int))
        val_score = model.predict_proba(validation[FEATURES])[:, 1]
        test_score = model.predict_proba(test[FEATURES])[:, 1]
        validation[name] = val_score
        test[name] = test_score
        result["models"][name] = {
            "validation": binary_metrics(validation[TARGET].astype(int), val_score),
            "test": binary_metrics(test[TARGET].astype(int), test_score),
            "test_monthly": monthly_metrics(test, name),
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
