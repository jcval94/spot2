from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import average_precision_score

from .contracts import Settings
from .evaluation import binary_metrics, bootstrap_metric_intervals, calibration_table, gains_table, segment_metrics
from .features import (
    CLEAN_T1_FEATURES,
    INQUIRY_CATEGORICAL,
    INQUIRY_NUMERIC,
    LEAD_CATEGORICAL,
    LEAD_NUMERIC,
    STABLE_SEGMENT_FEATURES,
    validate_clean_features,
)
from .targets import first_inquiries, sensitivity_targets


@dataclass
class ModelBundle:
    name: str
    model: Any
    features: list[str]
    categorical: list[str]
    calibrator: LogisticRegression | None = None


def _prepare_catboost(frame: pd.DataFrame, features: list[str], categorical: list[str]) -> pd.DataFrame:
    result = frame[features].copy()
    for column in categorical:
        result[column] = result[column].fillna("<missing>").astype(str)
    for column in set(features) - set(categorical):
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def _logistic_pipeline(features: list[str], categorical: list[str], settings: Settings) -> Pipeline:
    numeric = [column for column in features if column not in categorical]
    transformer = ColumnTransformer([
        ("cat", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=5)),
        ]), categorical),
        ("num", Pipeline([
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
        ]), numeric),
    ])
    return Pipeline([
        ("preprocess", transformer),
        ("model", LogisticRegression(C=float(settings.raw["model"]["logistic_c"]), max_iter=2000, random_state=settings.seed)),
    ])


def fit_logistic(train: pd.DataFrame, features: list[str], categorical: list[str], target: str, settings: Settings) -> ModelBundle:
    validate_clean_features(features, settings.codexway_root / "config" / "feature_policy.yaml")
    model = _logistic_pipeline(features, categorical, settings)
    model.fit(train[features], train[target].astype(int))
    return ModelBundle("logistic", model, features, categorical)


def fit_catboost(train: pd.DataFrame, features: list[str], categorical: list[str], target: str, settings: Settings, validation: pd.DataFrame | None = None) -> ModelBundle:
    from catboost import CatBoostClassifier

    validate_clean_features(features, settings.codexway_root / "config" / "feature_policy.yaml")
    params = settings.raw["model"]
    model = CatBoostClassifier(
        iterations=int(params["catboost_iterations"]),
        depth=int(params["catboost_depth"]),
        learning_rate=float(params["catboost_learning_rate"]),
        l2_leaf_reg=float(params["catboost_l2_leaf_reg"]),
        loss_function="Logloss",
        eval_metric="PRAUC",
        random_seed=settings.seed,
        thread_count=1,
        verbose=False,
        allow_writing_files=False,
    )
    fit_args: dict[str, Any] = {"cat_features": categorical}
    if validation is not None and not validation.empty:
        fit_args["eval_set"] = (_prepare_catboost(validation, features, categorical), validation[target].astype(int))
        fit_args["early_stopping_rounds"] = int(params["catboost_early_stopping_rounds"])
    model.fit(_prepare_catboost(train, features, categorical), train[target].astype(int), **fit_args)
    return ModelBundle("catboost", model, features, categorical)


def predict(bundle: ModelBundle, frame: pd.DataFrame, *, calibrated: bool = True) -> np.ndarray:
    if bundle.name == "catboost":
        raw = bundle.model.predict_proba(_prepare_catboost(frame, bundle.features, bundle.categorical))[:, 1]
    else:
        raw = bundle.model.predict_proba(frame[bundle.features])[:, 1]
    if calibrated and bundle.calibrator is not None:
        raw = bundle.calibrator.predict_proba(_logit_frame(raw))[:, 1]
    return np.clip(raw, 1e-8, 1 - 1e-8)


def _logit_frame(probabilities: np.ndarray) -> np.ndarray:
    p = np.clip(probabilities, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p)).reshape(-1, 1)


def fit_platt(bundle: ModelBundle, validation: pd.DataFrame, target: str, settings: Settings) -> tuple[ModelBundle, dict[str, Any]]:
    raw = predict(bundle, validation, calibrated=False)
    calibrator = LogisticRegression(random_state=settings.seed).fit(_logit_frame(raw), validation[target].astype(int))
    calibrated = calibrator.predict_proba(_logit_frame(raw))[:, 1]
    before, after = binary_metrics(validation[target], raw), binary_metrics(validation[target], calibrated)
    keep = after["brier"] < before["brier"] or after["log_loss"] < before["log_loss"]
    bundle.calibrator = calibrator if keep else None
    return bundle, {"kept": keep, "before": before, "after": after}


def business_rule_score(frame: pd.DataFrame) -> np.ndarray:
    asked = frame["asked_visit"].fillna(False).astype(bool).astype(int)
    urgent = pd.to_numeric(frame["urgency_days"], errors="coerce").le(30).fillna(False).astype(int)
    area = pd.to_numeric(frame["area_request_to_target_ratio"], errors="coerce").between(0.75, 1.25).fillna(False).astype(int)
    rent = pd.to_numeric(frame["rent_request_to_lead_budget_ratio"], errors="coerce").le(1).fillna(False)
    sale = pd.to_numeric(frame["sale_request_to_lead_budget_ratio"], errors="coerce").le(1).fillna(False)
    budget = (rent | sale).astype(int)
    return (2 * asked + urgent + area + budget).to_numpy(dtype=float) / 5.0


def rolling_folds(train: pd.DataFrame, timestamp: str = "prediction_timestamp") -> list[tuple[pd.Index, pd.Index]]:
    ordered = train.sort_values(timestamp)
    times = ordered[timestamp].drop_duplicates().sort_values().reset_index(drop=True)
    positions = [0.40, 0.55, 0.70, 0.85, 1.0]
    boundaries = [times.iloc[min(len(times) - 1, int(len(times) * value))] for value in positions]
    folds = []
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        train_idx = train.index[train[timestamp] < start]
        val_idx = train.index[(train[timestamp] >= start + pd.Timedelta(days=7)) & (train[timestamp] <= end)]
        if len(train_idx) and len(val_idx):
            folds.append((train_idx, val_idx))
    return folds


def compare_models_rolling(train: pd.DataFrame, settings: Settings) -> tuple[pd.DataFrame, str]:
    features = CLEAN_T1_FEATURES
    categorical = LEAD_CATEGORICAL + INQUIRY_CATEGORICAL
    rows = []
    for fold_id, (train_idx, val_idx) in enumerate(rolling_folds(train), start=1):
        fit, val = train.loc[train_idx], train.loc[val_idx]
        logistic = fit_logistic(fit, features, categorical, "target_t1", settings)
        catboost = fit_catboost(fit, features, categorical, "target_t1", settings, validation=val)
        predictions = {
            bundle.name: predict(bundle, val, calibrated=False) for bundle in (logistic, catboost)
        }
        collapse = False
        for segment in ["search_sector", "source", "channel"]:
            for _, group in val.groupby(segment, dropna=False):
                if len(group) < 100 or group["target_t1"].nunique() < 2:
                    continue
                positions = val.index.get_indexer(group.index)
                logistic_ap = average_precision_score(group["target_t1"], predictions["logistic"][positions])
                catboost_ap = average_precision_score(group["target_t1"], predictions["catboost"][positions])
                collapse = collapse or catboost_ap < logistic_ap - 0.02
        for bundle in (logistic, catboost):
            metrics = binary_metrics(val["target_t1"], predictions[bundle.name])
            rows.append({"fold": fold_id, "model": bundle.name, "catboost_segment_collapse": collapse, **metrics})
    result = pd.DataFrame(rows)
    pivot_ap = result.pivot(index="fold", columns="model", values="average_precision")
    pivot_brier = result.pivot(index="fold", columns="model", values="brier")
    deltas = pivot_ap["catboost"] - pivot_ap["logistic"]
    promote = (
        deltas.mean() > 0
        and int((deltas >= 0).sum()) >= min(3, len(deltas))
        and float((pivot_brier["catboost"] - pivot_brier["logistic"]).mean()) <= float(settings.raw["model"]["promotion_max_brier_loss"])
        and not result["catboost_segment_collapse"].any()
    )
    return result, "catboost" if promote else "logistic"


def evaluate_stable_segment_rolling(train: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    """Temporal evidence for the parsimonious capacity-ranking challenger."""
    rows = []
    for fold_id, (train_idx, val_idx) in enumerate(rolling_folds(train), start=1):
        fit, val = train.loc[train_idx], train.loc[val_idx]
        bundle = fit_logistic(fit, STABLE_SEGMENT_FEATURES, [], "target_t1", settings)
        metrics = binary_metrics(val["target_t1"], predict(bundle, val, calibrated=False))
        rows.append({
            "fold": fold_id,
            "model": "stable_segment_logistic",
            "catboost_segment_collapse": False,
            **metrics,
        })
    return pd.DataFrame(rows)


def train_evaluate_t1(abt: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    output = settings.codexway_root / "outputs"
    (output / "metrics").mkdir(parents=True, exist_ok=True)
    (output / "predictions").mkdir(parents=True, exist_ok=True)
    (output / "tables").mkdir(parents=True, exist_ok=True)
    model_dir = output / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    mature = abt[abt["target_t1"].notna()].copy()
    train = mature[mature["split"].eq("train")]
    validation = mature[mature["split"].eq("validation")]
    test = mature[mature["split"].eq("test")]
    rolling_base, base_winner = compare_models_rolling(train, settings)
    stable_rolling = evaluate_stable_segment_rolling(train, settings)
    rolling = pd.concat([rolling_base, stable_rolling], ignore_index=True)
    rolling.to_csv(output / "metrics" / "rolling_model_comparison.csv", index=False)

    features = CLEAN_T1_FEATURES
    categorical = LEAD_CATEGORICAL + INQUIRY_CATEGORICAL
    lead_features = LEAD_CATEGORICAL + LEAD_NUMERIC
    no_asked_features = [feature for feature in features if feature != "asked_visit"]
    no_asked_categorical = [feature for feature in categorical if feature != "asked_visit"]
    bundles = {
        "logistic_lead_only": fit_logistic(train, lead_features, LEAD_CATEGORICAL, "target_t1", settings),
        "logistic": fit_logistic(train, features, categorical, "target_t1", settings),
        "logistic_no_asked_visit": fit_logistic(train, no_asked_features, no_asked_categorical, "target_t1", settings),
        "catboost": fit_catboost(train, features, categorical, "target_t1", settings, validation=validation),
        "stable_segment_logistic": fit_logistic(train, STABLE_SEGMENT_FEATURES, [], "target_t1", settings),
    }
    stable_validation = binary_metrics(
        validation["target_t1"], predict(bundles["stable_segment_logistic"], validation, calibrated=False)
    )
    validation_constant = binary_metrics(
        validation["target_t1"], np.repeat(train["target_t1"].mean(), len(validation))
    )
    stable_config = settings.raw["model"]
    stable_gate = bool(
        stable_rolling["lift_top_10pct"].mean() > float(stable_config["stable_segment_min_mean_lift_10pct"])
        and stable_rolling["lift_top_10pct"].median() > float(stable_config["stable_segment_min_median_lift_10pct"])
        and int(stable_rolling["lift_top_10pct"].gt(1.0).sum())
        >= int(stable_config["stable_segment_min_folds_above_random"])
        and stable_validation["lift_top_10pct"] > float(stable_config["stable_segment_require_validation_lift_10pct"])
        and stable_validation["brier"] <= validation_constant["brier"] + float(stable_config["promotion_max_brier_loss"])
    )
    winner = "stable_segment_logistic" if stable_gate else base_winner
    selection = {
        "base_model_winner": base_winner,
        "stable_segment_promoted": stable_gate,
        "rolling_mean_lift_top_10pct": float(stable_rolling["lift_top_10pct"].mean()),
        "rolling_median_lift_top_10pct": float(stable_rolling["lift_top_10pct"].median()),
        "rolling_folds_above_random": int(stable_rolling["lift_top_10pct"].gt(1.0).sum()),
        "rolling_fold_count": int(len(stable_rolling)),
        "validation_metrics": stable_validation,
        "validation_constant_brier": validation_constant["brier"],
        "promotion_gate_did_not_use_procedural_holdout": True,
        "feature_hypothesis_holdout_blinding": "NOT_POSSIBLE__HOLDOUT_ALREADY_GLOBALLY_CONSUMED",
    }
    selected, calibration = fit_platt(bundles[winner], validation, "target_t1", settings)
    scores = pd.DataFrame({
        "lead_id": test["lead_id"].to_numpy(),
        "prediction_timestamp": test["prediction_timestamp"].to_numpy(),
        "target_t1": test["target_t1"].astype(int).to_numpy(),
        "positive_rate": np.repeat(train["target_t1"].mean(), len(test)),
        "business_rule": business_rule_score(test),
        "logistic_lead_only": predict(bundles["logistic_lead_only"], test, calibrated=False),
        "logistic": predict(bundles["logistic"], test, calibrated=False),
        "logistic_no_asked_visit": predict(bundles["logistic_no_asked_visit"], test, calibrated=False),
        "catboost": predict(bundles["catboost"], test, calibrated=False),
        "stable_segment_logistic": predict(bundles["stable_segment_logistic"], test, calibrated=False),
        "selected_calibrated": predict(selected, test),
    })
    for column in ("search_sector", "search_modality", "user_type", "source", "channel"):
        scores[column] = test[column].astype(str).to_numpy()
    scores.to_parquet(output / "predictions" / "t1_holdout_predictions.parquet", index=False)

    model_metrics = {
        name: binary_metrics(scores["target_t1"], scores[name])
        for name in (
            "positive_rate", "business_rule", "logistic_lead_only", "logistic",
            "logistic_no_asked_visit", "catboost", "selected_calibrated",
            "stable_segment_logistic",
        )
    }
    baseline = model_metrics["positive_rate"]
    for fraction in (5, 10, 20):
        baseline[f"precision_top_{fraction}pct"] = baseline["positive_rate"]
        baseline[f"recall_top_{fraction}pct"] = fraction / 100
        baseline[f"lift_top_{fraction}pct"] = 1.0
    (output / "metrics" / "t1_model_metrics.json").write_text(json.dumps({
        "selected_model": winner,
        "ranking_tie_policy": "FRACTIONAL_EXPECTATION_AT_CAPACITY_BOUNDARY",
        "selection": selection,
        "calibration": calibration,
        "calibration_vs_constant_baseline": {
            "brier_skill_score": 1 - model_metrics["selected_calibrated"]["brier"] / max(1e-12, model_metrics["positive_rate"]["brier"]),
            "log_loss_improvement": model_metrics["positive_rate"]["log_loss"] - model_metrics["selected_calibrated"]["log_loss"],
        },
        "metrics": model_metrics,
    }, indent=2) + "\n", encoding="utf-8")
    bootstrap_metric_intervals(
        scores, "target_t1", ["positive_rate", "selected_calibrated"], iterations=1000, seed=settings.seed
    ).to_csv(output / "metrics" / "t1_metric_intervals.csv", index=False)
    calibration_table(scores["target_t1"], scores["selected_calibrated"]).to_csv(output / "tables" / "calibration.csv", index=False)
    gains_table(scores["target_t1"], scores["selected_calibrated"]).to_csv(output / "tables" / "gains.csv", index=False)
    segment_metrics(scores, "target_t1", "selected_calibrated", ["search_sector", "search_modality", "user_type", "source", "channel"]).to_csv(
        output / "tables" / "segment_metrics.csv", index=False
    )
    joblib.dump(selected, model_dir / "t1_model_bundle.joblib")
    return {
        "bundle": selected, "winner": winner, "calibration": calibration,
        "selection": selection, "metrics": model_metrics, "holdout": scores,
    }


def train_evaluate_sensitivities(t0: pd.DataFrame, t2: pd.DataFrame, t1: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    """Small Logistic-only T0/T2 challengers; never used to select the T1 model."""
    output = settings.codexway_root / "outputs" / "metrics"
    output.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}

    t0m = t0[t0["target_t0_30d"].notna()].copy()
    t0m["split"] = np.select(
        [
            t0m["prediction_timestamp"].lt(settings.split.train_end_exclusive),
            t0m["prediction_timestamp"].ge(settings.split.validation_start) & t0m["prediction_timestamp"].lt(settings.split.validation_end_exclusive),
            t0m["prediction_timestamp"].ge(settings.split.test_start) & t0m["prediction_timestamp"].lt(settings.split.test_end_exclusive),
        ],
        ["train", "validation", "test"],
        default="purge",
    )
    t0_train, t0_test = t0m[t0m["split"].eq("train")], t0m[t0m["split"].eq("test")]
    if len(t0_train) and len(t0_test):
        t0_model = _logistic_pipeline(LEAD_CATEGORICAL + LEAD_NUMERIC, LEAD_CATEGORICAL, settings)
        t0_model.fit(t0_train[LEAD_CATEGORICAL + LEAD_NUMERIC], t0_train["target_t0_30d"].astype(int))
        pred = t0_model.predict_proba(t0_test[LEAD_CATEGORICAL + LEAD_NUMERIC])[:, 1]
        results["T0_logistic_30d"] = binary_metrics(t0_test["target_t0_30d"], pred)

    lead_split = t1[["lead_id", "split"]].drop_duplicates("lead_id")
    t2m = t2[t2["target_t2"].notna()].merge(lead_split, on="lead_id", how="left", validate="many_to_one")
    history = [
        "hist_prior_inquiry_count", "hist_days_since_first", "hist_days_since_previous",
        "hist_prior_message_mean", "hist_prior_urgency_mean", "hist_prior_requested_area_mean",
        "hist_area_change_from_previous", "hist_same_spot_as_previous",
    ]
    t2_features = LEAD_CATEGORICAL + LEAD_NUMERIC + INQUIRY_CATEGORICAL + INQUIRY_NUMERIC + history
    t2_categorical = LEAD_CATEGORICAL + INQUIRY_CATEGORICAL
    t2_train, t2_test = t2m[t2m["split"].eq("train")], t2m[t2m["split"].eq("test")]
    if len(t2_train) and len(t2_test):
        t2_model = _logistic_pipeline(t2_features, t2_categorical, settings)
        t2_model.fit(t2_train[t2_features], t2_train["target_t2"].astype(int))
        pred = t2_model.predict_proba(t2_test[t2_features])[:, 1]
        results["T2_logistic_trajectory"] = binary_metrics(t2_test["target_t2"], pred)
        results["T2_entity_overlap_train_test"] = int(
            len(set(t2_train["lead_id"]) & set(t2_test["lead_id"]))
        )
    (output / "t0_t2_sensitivity_metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def train_evaluate_target_sensitivities(
    t1: pd.DataFrame,
    inquiries: pd.DataFrame,
    settings: Settings,
) -> dict[str, Any]:
    """Evaluate alternative business proxies without changing the main model contract."""
    targets = sensitivity_targets(first_inquiries(inquiries), inquiries, settings).rename(
        columns={"inquiry_at": "sensitivity_prediction_timestamp"}
    )
    frame = t1.merge(
        targets.drop(columns=["broker_response"]),
        on=["lead_id", "inquiry_id"], how="left", validate="one_to_one",
    )
    features = CLEAN_T1_FEATURES
    categorical = LEAD_CATEGORICAL + INQUIRY_CATEGORICAL
    target_names = ["target_t1", "accepted_or_scheduled", "any_scheduled_inquiry_30d"]
    rows: list[dict[str, Any]] = []
    for target in target_names:
        eligible = frame[frame[target].notna()].copy()
        train = eligible[eligible["split"].eq("train")]
        test = eligible[eligible["split"].eq("test")]
        if train.empty or test.empty or train[target].nunique() < 2 or test[target].nunique() < 2:
            continue
        bundle = fit_logistic(train, features, categorical, target, settings)
        predictions = predict(bundle, test, calibrated=False)
        metrics = binary_metrics(test[target].astype(int), predictions)
        monthly = eligible.assign(month=eligible["prediction_timestamp"].dt.strftime("%Y-%m")).groupby("month")[target].mean()
        x = np.arange(len(monthly), dtype=float)
        slope = float(np.polyfit(x, monthly.to_numpy(dtype=float), 1)[0]) if len(monthly) > 1 else 0.0
        rows.append({
            "target": target,
            "train_n": int(len(train)),
            "test_n": int(len(test)),
            "train_positive_rate": float(train[target].mean()),
            "test_positive_rate": float(test[target].mean()),
            "monthly_rate_min": float(monthly.min()),
            "monthly_rate_max": float(monthly.max()),
            "monthly_linear_slope": slope,
            **metrics,
        })
    maturity_rows = []
    for days in (7, 14, 30):
        target = f"scheduled_first_{days}d"
        eligible = frame[frame[target].notna()]
        maturity_rows.append({
            "maturity_days": days,
            "eligible_n": int(len(eligible)),
            "excluded_right_censored_n": int(len(frame) - len(eligible)),
            "positive_rate": float(eligible[target].astype(float).mean()),
        })
    metrics_frame = pd.DataFrame(rows)
    maturity_frame = pd.DataFrame(maturity_rows)
    output = settings.codexway_root / "outputs"
    metrics_frame.to_csv(output / "metrics" / "target_sensitivity_metrics.csv", index=False)
    maturity_frame.to_csv(output / "tables" / "target_maturity_sensitivity.csv", index=False)
    frame[[
        "lead_id", "inquiry_id", "split", "accepted_or_scheduled",
        "any_scheduled_inquiry_30d", "inquiry_exposure_30d",
        "scheduled_first_7d", "scheduled_first_14d", "scheduled_first_30d",
    ]].to_parquet(output / "abt" / "t1_target_sensitivities.parquet", index=False)
    result = {
        "status": "SENSITIVITY_ONLY__MAIN_CONTRACT_UNCHANGED",
        "model_metrics": metrics_frame.to_dict(orient="records"),
        "maturity": maturity_frame.to_dict(orient="records"),
        "warning": "The 30-day any-visit proxy changes exposure and is not equivalent to first-contact success.",
    }
    (output / "metrics" / "target_sensitivity_summary.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result
