from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from spot2_codexway.contracts import load_settings
from spot2_codexway.data import load_all
from spot2_codexway.evaluation import binary_metrics
from spot2_codexway.profiles import build_profiles


def _logistic_numeric(train: pd.DataFrame, features: list[str], target: str, c: float, seed: int) -> Pipeline:
    model = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(C=c, max_iter=2000, random_state=seed)),
    ])
    model.fit(train[features], train[target].astype(int))
    return model


def _logistic_categorical(train: pd.DataFrame, features: list[str], target: str, c: float, seed: int) -> Pipeline:
    pre = ColumnTransformer([
        ("cat", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=5)),
        ]), features),
    ])
    model = Pipeline([
        ("preprocess", pre),
        ("model", LogisticRegression(C=c, max_iter=2000, random_state=seed)),
    ])
    model.fit(train[features], train[target].astype(int))
    return model


def _metrics(model: Pipeline, frame: pd.DataFrame, features: list[str]) -> dict:
    score = model.predict_proba(frame[features])[:, 1]
    return binary_metrics(frame["target_t1"].astype(int), score)


def _lift_only(metrics: dict) -> dict:
    return {
        "n": int(metrics["n"]),
        "positive_rate": float(metrics["positive_rate"]),
        "roc_auc": float(metrics["roc_auc"]),
        "average_precision": float(metrics["average_precision"]),
        "lift_top_5pct": float(metrics["lift_top_5pct"]),
        "lift_top_10pct": float(metrics["lift_top_10pct"]),
        "lift_top_20pct": float(metrics["lift_top_20pct"]),
    }


def _psi(reference: pd.Series, comparison: pd.Series, eps: float = 1e-6) -> float:
    a = reference.fillna("<missing>").astype(str)
    b = comparison.fillna("<missing>").astype(str)
    cats = sorted(set(a.unique()).union(set(b.unique())))
    p = a.value_counts(normalize=True).reindex(cats, fill_value=0.0).to_numpy(dtype=float)
    q = b.value_counts(normalize=True).reindex(cats, fill_value=0.0).to_numpy(dtype=float)
    p = np.clip(p, eps, None)
    q = np.clip(q, eps, None)
    return float(np.sum((q - p) * np.log(q / p)))


def test_user_requested_challengers() -> None:
    settings = load_settings()
    c = float(settings.raw["model"]["logistic_c"])
    abt_path = settings.codexway_root / "outputs" / "abt" / "abt_t1_first_inquiry.parquet"
    t1 = pd.read_parquet(abt_path)
    mature = t1[t1["target_t1"].notna()].copy()

    # Explicitly decompose the winning rule into both its elementary pieces and
    # the two clauses hidden inside Industrial AND (small OR paid).
    mature["is_industrial"] = mature["search_sector"].eq("Industrial").astype(int)
    mature["is_small"] = mature["company_size"].eq("small").astype(int)
    mature["is_paid"] = mature["source"].eq("paid").astype(int)
    mature["industrial_small"] = (mature["is_industrial"].eq(1) & mature["is_small"].eq(1)).astype(int)
    mature["industrial_paid"] = (mature["is_industrial"].eq(1) & mature["is_paid"].eq(1)).astype(int)
    mature["industrial_small_or_paid"] = (
        mature["is_industrial"].eq(1) & (mature["is_small"].eq(1) | mature["is_paid"].eq(1))
    ).astype(int)

    train = mature[mature["split"].eq("train")].copy()
    validation = mature[mature["split"].eq("validation")].copy()
    test = mature[mature["split"].eq("test")].copy()

    numeric_candidates = {
        "winner_rebuilt_one_interaction": ["industrial_small_or_paid"],
        "split_original_clauses": ["industrial_small", "industrial_paid"],
        "three_component_flags": ["is_industrial", "is_small", "is_paid"],
        "industrial_only": ["is_industrial"],
        "small_only": ["is_small"],
        "paid_only": ["is_paid"],
        "industrial_small_only": ["industrial_small"],
        "industrial_paid_only": ["industrial_paid"],
    }
    feature_results: dict[str, dict] = {}
    for name, features in numeric_candidates.items():
        model = _logistic_numeric(train, features, "target_t1", c, settings.seed)
        feature_results[name] = {
            "features": features,
            "validation": _lift_only(_metrics(model, validation, features)),
            "test": _lift_only(_metrics(model, test, features)),
        }

    raw_features = ["search_sector", "company_size", "source"]
    raw_model = _logistic_categorical(train, raw_features, "target_t1", c, settings.seed)
    feature_results["three_raw_categoricals"] = {
        "features": raw_features,
        "validation": _lift_only(_metrics(raw_model, validation, raw_features)),
        "test": _lift_only(_metrics(raw_model, test, raw_features)),
    }

    # Build the pre-existing profile families exactly as the project does.
    tables = load_all(settings)
    enriched, profiles, profile_metrics = build_profiles(t1, tables["spots"], tables["inquiries"], seed=settings.seed)
    enriched = enriched[enriched["target_t1"].notna()].copy()
    cluster_train = enriched[enriched["split"].eq("train")].copy()
    cluster_validation = enriched[enriched["split"].eq("validation")].copy()
    cluster_test = enriched[enriched["split"].eq("test")].copy()

    # Existing cluster stability gate: balanced family + high refit ARI.
    # Added temporal gate for this requested challenger: PSI train->validation <= .20.
    requested_families = ["physical_profile", "location_profile", "broker_service_profile"]
    metric_by_family = profile_metrics.set_index("family")
    drift = {}
    eligible = []
    for family in requested_families:
        psi_validation = _psi(cluster_train[family], cluster_validation[family])
        psi_test = _psi(cluster_train[family], cluster_test[family])
        ari = float(metric_by_family.loc[family, "stability_ari"])
        balance_ok = bool(metric_by_family.loc[family, "balance_ok"])
        passes = bool(balance_ok and ari >= 0.80 and psi_validation <= 0.20)
        drift[family] = {
            "stability_ari": ari,
            "balance_ok": balance_ok,
            "psi_train_validation": psi_validation,
            "psi_train_test_diagnostic_only": psi_test,
            "passes_pre_holdout_gate": passes,
        }
        if passes:
            eligible.append(family)

    if not eligible:
        raise AssertionError(f"No cluster family passed pre-holdout stability gate: {drift}")

    # Choose cluster subset using validation Lift@10 only; favor parsimony on ties.
    cluster_candidates = []
    for size in range(1, len(eligible) + 1):
        for subset_tuple in combinations(eligible, size):
            subset = list(subset_tuple)
            model = _logistic_categorical(cluster_train, subset, "target_t1", c, settings.seed)
            val = _lift_only(_metrics(model, cluster_validation, subset))
            cluster_candidates.append({"features": subset, "validation": val})
    cluster_candidates.sort(
        key=lambda row: (row["validation"]["lift_top_10pct"], -len(row["features"])),
        reverse=True,
    )
    selected_cluster_features = cluster_candidates[0]["features"]
    selected_cluster_model = _logistic_categorical(
        cluster_train, selected_cluster_features, "target_t1", c, settings.seed
    )
    selected_cluster_test = _lift_only(_metrics(selected_cluster_model, cluster_test, selected_cluster_features))

    result = {
        "methodology": {
            "target": "target_t1",
            "selection_uses_test": False,
            "primary_validation_metric": "lift_top_10pct",
            "lift_function": "spot2_codexway.evaluation.binary_metrics",
            "cluster_temporal_gate": "balance_ok AND ARI>=0.80 AND PSI(train,validation)<=0.20",
        },
        "split_counts": {
            "train": int(len(train)),
            "validation": int(len(validation)),
            "test": int(len(test)),
        },
        "separate_feature_models": feature_results,
        "cluster_drift": drift,
        "eligible_cluster_families": eligible,
        "cluster_validation_candidates": cluster_candidates,
        "selected_cluster_model": {
            "features": selected_cluster_features,
            "test": selected_cluster_test,
        },
    }

    out = settings.codexway_root / "outputs" / "metrics" / "user_requested_challengers.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    assert out.exists()
