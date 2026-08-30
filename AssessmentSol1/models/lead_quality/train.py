from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import polars as pl
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression

HERE = Path(__file__).resolve().parent
ASSESSMENT_ROOT = HERE.parents[1]
FEATURE_DIR = ASSESSMENT_ROOT / "features"
if str(FEATURE_DIR) not in sys.path:
    sys.path.insert(0, str(FEATURE_DIR))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from build_features import build_feature_artifacts
from transformers import (
    FeatureRegistryGate,
    GuardedPreprocessor,
    classify_columns,
    feature_registry_sha256,
)
from evaluate import (
    evaluate_by_fold,
    macro_fold_metrics,
    paired_bootstrap_delta,
    save_evaluation,
    segment_analysis,
)


RANDOM_SEED = 20260830

LOGISTIC_CONFIG = {
    "C": 1.0,
    "penalty": "l2",
    "solver": "liblinear",
    "max_iter": 2000,
    "random_state": RANDOM_SEED,
}

CATBOOST_CONFIG = {
    "iterations": 400,
    "depth": 6,
    "learning_rate": 0.05,
    "l2_leaf_reg": 5.0,
    "loss_function": "Logloss",
    "eval_metric": "Logloss",
    "random_seed": RANDOM_SEED,
    "random_strength": 1.0,
    "border_count": 64,
    "allow_writing_files": False,
    "verbose": False,
    "thread_count": 4,
}


@dataclass
class FittedLogistic:
    features: list[str]
    numeric_features: list[str]
    categorical_features: list[str]
    preprocessor: GuardedPreprocessor
    model: LogisticRegression

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        x = self.preprocessor.transform(frame[self.features])
        return self.model.predict_proba(x)[:, 1]


@dataclass
class FittedCatBoost:
    features: list[str]
    categorical_features: list[str]
    model: CatBoostClassifier

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        x = _catboost_frame(frame[self.features], self.categorical_features)
        return self.model.predict_proba(x)[:, 1]


def _load_groups() -> dict:
    return json.loads((FEATURE_DIR / "feature_groups.json").read_text())


def _load_plan() -> dict:
    return json.loads((FEATURE_DIR / "ablation_plan.json").read_text())


def _variant_features(variant_id: str) -> list[str]:
    groups = _load_groups()
    plan = _load_plan()
    variants = {v["id"]: v for v in plan["variants"]}
    if variant_id not in variants:
        raise KeyError(f"Unknown ablation variant: {variant_id}")
    spec = variants[variant_id]

    if "base" in spec:
        base = _variant_features(spec["base"])
        return [f for f in base if f not in set(spec.get("remove_features", []))]

    out: list[str] = []
    for group_name in spec.get("groups", []):
        if group_name not in groups["t1"]:
            raise KeyError(f"Unknown T1 feature group: {group_name}")
        out.extend(groups["t1"][group_name])
    # Stable de-duplication.
    return list(dict.fromkeys(out))


def _load_t1_development(repo_root: Path) -> pd.DataFrame:
    build_feature_artifacts(repo_root, scope="development")
    feature_path = FEATURE_DIR / "artifacts" / "t1_features_with_selected_spot_challenger.parquet"
    frame = pd.DataFrame(pl.read_parquet(feature_path).to_dicts())
    frame["score_time"] = pd.to_datetime(frame["score_time"], utc=True)

    split = pd.read_csv(
        ASSESSMENT_ROOT / "splits" / "split_assignments_t1.csv"
    )
    split["lead_id"] = pd.to_numeric(split["lead_id"])
    frame["lead_id"] = pd.to_numeric(frame["lead_id"])
    frame = frame.merge(
        split[
            [
                "lead_id",
                "primary_partition",
                "F1_role",
                "F2_role",
                "F3_role",
                "F4_role",
            ]
        ],
        on="lead_id",
        how="inner",
        validate="one_to_one",
    )
    frame = frame.loc[
        frame["primary_partition"].eq("DEVELOPMENT")
        & frame["target_status"].isin(["POSITIVE", "NEGATIVE"])
        & frame["target_value"].notna()
    ].copy()

    if frame["lead_id"].duplicated().any():
        raise AssertionError("T1 modeling frame must remain one row per lead")
    if frame["score_time"].ge(pd.Timestamp("2026-05-01T00:00:00Z")).any():
        raise AssertionError("Non-development score entered model selection")
    return frame


def _temporal_cohort(score_time: pd.Series) -> pd.Series:
    t = pd.to_datetime(score_time, utc=True)
    return pd.Series(
        np.select(
            [
                t.lt(pd.Timestamp("2025-07-01T00:00:00Z")),
                t.lt(pd.Timestamp("2026-01-01T00:00:00Z")),
                t.lt(pd.Timestamp("2026-04-01T00:00:00Z")),
            ],
            ["2025H1", "2025H2", "2026Q1"],
            default="2026APR",
        ),
        index=score_time.index,
        dtype="object",
    )


def _prediction_base(part: pd.DataFrame, fold: str) -> pd.DataFrame:
    keep = [
        "score_id",
        "lead_id",
        "score_time",
        "target_value",
        "search_sector",
        "search_modality",
        "user_type",
        "source",
    ]
    out = part[keep].copy()
    out["fold"] = fold
    out["temporal_cohort"] = _temporal_cohort(out["score_time"])
    return out


def _normalize_bool_columns(frame: pd.DataFrame) -> pd.DataFrame:
    x = frame.copy()
    for c in x.columns:
        if pd.api.types.is_bool_dtype(x[c]):
            x[c] = x[c].astype(float)
    return x


def fit_logistic(
    train: pd.DataFrame,
    features: list[str],
) -> FittedLogistic:
    x = _normalize_bool_columns(train[features])
    numeric, categorical = classify_columns(x, features)
    preprocessor = GuardedPreprocessor(
        numeric,
        categorical,
        scale_numeric=True,
    )
    y = train["target_value"].astype(int)
    preprocessor.fit(
        x,
        y,
        fit_roles=["TRAIN"] * len(train),
    )
    matrix = preprocessor.transform(x)
    model = LogisticRegression(**LOGISTIC_CONFIG)
    model.fit(matrix, y)
    return FittedLogistic(
        features=features,
        numeric_features=numeric,
        categorical_features=categorical,
        preprocessor=preprocessor,
        model=model,
    )


def _catboost_frame(
    frame: pd.DataFrame,
    categorical_features: list[str],
) -> pd.DataFrame:
    x = frame.copy()
    for c in x.columns:
        if pd.api.types.is_bool_dtype(x[c]):
            x[c] = x[c].astype(int)
    for c in categorical_features:
        x[c] = x[c].astype("object").where(x[c].notna(), "__UNKNOWN__").astype(str)
    return x


def _catboost_categoricals(
    train: pd.DataFrame,
    features: list[str],
) -> list[str]:
    out: list[str] = []
    for f in features:
        dtype = train[f].dtype
        if (
            pd.api.types.is_object_dtype(dtype)
            or isinstance(dtype, pd.CategoricalDtype)
            or pd.api.types.is_string_dtype(dtype)
        ):
            out.append(f)
    return out


def fit_catboost(
    train: pd.DataFrame,
    features: list[str],
) -> FittedCatBoost:
    categorical = _catboost_categoricals(train, features)
    x = _catboost_frame(train[features], categorical)
    model = CatBoostClassifier(**CATBOOST_CONFIG)
    model.fit(
        x,
        train["target_value"].astype(int),
        cat_features=categorical,
    )
    return FittedCatBoost(
        features=features,
        categorical_features=categorical,
        model=model,
    )


def business_rule_probability(
    train: pd.DataFrame,
    score_frame: pd.DataFrame,
) -> np.ndarray:
    """Fixed, interpretable development-only business baseline.

    Score points are frozen and never optimized:
      +2 asked_visit
      +1 urgency <= 30 days
      +1 inquiry completeness >= 0.80
      +1 budget/modality consistent
      +1 requested/target area ratio in [0.80, 1.25]

    Probability mapping uses only the fold TRAIN base rate:
      logit(p) = logit(train_prevalence) + 0.30 * (points - 2)
    """
    points = (
        2 * score_frame["asked_visit"].fillna(False).astype(int)
        + score_frame["urgency_days"].le(30).fillna(False).astype(int)
        + score_frame["inquiry_completeness_rate"].ge(0.80).fillna(False).astype(int)
        + score_frame["budget_modality_consistent"].fillna(False).astype(int)
        + score_frame["requested_to_target_area_ratio"]
        .between(0.80, 1.25, inclusive="both")
        .fillna(False)
        .astype(int)
    )
    prevalence = float(train["target_value"].mean())
    prevalence = float(np.clip(prevalence, 1e-6, 1 - 1e-6))
    intercept = math.log(prevalence / (1 - prevalence))
    logit = intercept + 0.30 * (points.to_numpy(dtype=float) - 2.0)
    return 1.0 / (1.0 + np.exp(-logit))


def _fold_masks(
    frame: pd.DataFrame,
    fold: str,
) -> tuple[pd.Series, pd.Series]:
    col = f"{fold}_role"
    train = frame[col].eq("TRAIN")
    validation = frame[col].eq("VALIDATION")
    if not train.any() or not validation.any():
        raise AssertionError(f"{fold} missing TRAIN or VALIDATION rows")
    if set(frame.loc[train, "lead_id"]).intersection(
        set(frame.loc[validation, "lead_id"])
    ):
        raise AssertionError(f"{fold} lead isolation failed")
    max_train = frame.loc[train, "score_time"].max()
    min_valid = frame.loc[validation, "score_time"].min()
    if not max_train < min_valid:
        raise AssertionError(f"{fold} temporal ordering failed")
    return train, validation


def run_baselines(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base_rate_rows: list[pd.DataFrame] = []
    rule_rows: list[pd.DataFrame] = []
    for fold in ("F1", "F2", "F3", "F4"):
        train_mask, val_mask = _fold_masks(frame, fold)
        train = frame.loc[train_mask]
        val = frame.loc[val_mask]
        base = _prediction_base(val, fold)

        base_pred = base.copy()
        base_pred["probability"] = float(train["target_value"].mean())
        base_pred["model_family"] = "BASE_RATE"
        base_pred["variant"] = "NA"
        base_rate_rows.append(base_pred)

        rule = base.copy()
        rule["probability"] = business_rule_probability(train, val)
        rule["model_family"] = "BUSINESS_RULE"
        rule["variant"] = "FIXED_V1"
        rule_rows.append(rule)

    return {
        "base_rate": pd.concat(base_rate_rows, ignore_index=True),
        "business_rule": pd.concat(rule_rows, ignore_index=True),
    }


def run_model_cv(
    frame: pd.DataFrame,
    *,
    variant: str,
    model_family: str,
    registry_gate: FeatureRegistryGate,
) -> pd.DataFrame:
    features = _variant_features(variant)
    if variant == "E":
        registry_gate.assert_allowed(
            features,
            stage="T1",
            model_roles=("LEAD_QUALITY", "MATCHING", "INVENTORY"),
            statuses=("REQUIRED", "SUPPORTED", "EXPERIMENTAL"),
        )
    else:
        registry_gate.assert_allowed(
            features,
            stage="T1",
            model_roles=("LEAD_QUALITY",),
            statuses=("REQUIRED", "SUPPORTED"),
        )

    missing = sorted(set(features) - set(frame.columns))
    if missing:
        raise ValueError(f"{variant} materialized features missing: {missing}")

    rows: list[pd.DataFrame] = []
    for fold in ("F1", "F2", "F3", "F4"):
        train_mask, val_mask = _fold_masks(frame, fold)
        train = frame.loc[train_mask].copy()
        val = frame.loc[val_mask].copy()

        if model_family == "LOGISTIC":
            fitted = fit_logistic(train, features)
        elif model_family == "CATBOOST":
            fitted = fit_catboost(train, features)
        else:
            raise ValueError(model_family)

        pred = _prediction_base(val, fold)
        pred["probability"] = fitted.predict_proba(
            _normalize_bool_columns(val) if model_family == "LOGISTIC" else val
        )
        pred["model_family"] = model_family
        pred["variant"] = variant
        rows.append(pred)
    return pd.concat(rows, ignore_index=True)


def _macro_summary(pred: pd.DataFrame) -> dict:
    return macro_fold_metrics(evaluate_by_fold(pred))


def _select_core_variant(
    logistic_predictions: dict[str, pd.DataFrame],
) -> dict:
    order = ["A", "B", "C"]
    summaries = {v: _macro_summary(logistic_predictions[v]) for v in order}

    best_ap = max(summaries[v]["macro_average_precision"] for v in order)
    within_tie = [
        v
        for v in order
        if best_ap - summaries[v]["macro_average_precision"] < 0.002
    ]
    selected = within_tie[0]  # simplicity tie-break

    # Allow the explicitly pre-registered Lift exception to promote a more
    # complex set within the AP tie zone.
    for candidate in order[order.index(selected) + 1 :]:
        prev = order[order.index(candidate) - 1]
        ap_gain = (
            summaries[candidate]["macro_average_precision"]
            - summaries[prev]["macro_average_precision"]
        )
        lift_gain = (
            summaries[candidate]["macro_lift_at_10pct"]
            - summaries[prev]["macro_lift_at_10pct"]
        )
        brier_delta = (
            summaries[candidate]["macro_brier"]
            - summaries[prev]["macro_brier"]
        )
        if ap_gain >= 0.002 or (
            ap_gain > -0.002
            and lift_gain >= 0.10
            and brier_delta <= 0.003
        ):
            selected = candidate

    # asked_visit sensitivity is pre-registered on C. It can only replace C.
    if selected == "C":
        with_pred = logistic_predictions["D_WITH_ASKED_VISIT"]
        without_pred = logistic_predictions["D_WITHOUT_ASKED_VISIT"]
        with_summary = _macro_summary(with_pred)
        without_summary = _macro_summary(without_pred)
        if (
            without_summary["macro_average_precision"]
            - with_summary["macro_average_precision"]
            >= 0.005
        ):
            selected = "D_WITHOUT_ASKED_VISIT"

    return {
        "selected_core_variant": selected,
        "selection_reference_model": "LOGISTIC",
        "summaries": summaries,
        "asked_visit_sensitivity": {
            "with": _macro_summary(logistic_predictions["D_WITH_ASKED_VISIT"]),
            "without": _macro_summary(
                logistic_predictions["D_WITHOUT_ASKED_VISIT"]
            ),
        },
        "selected_spot_challenger": _macro_summary(logistic_predictions["E"]),
    }


def _fold_ap_wins(
    logistic: pd.DataFrame,
    catboost: pd.DataFrame,
) -> int:
    l = evaluate_by_fold(logistic).set_index("fold")
    c = evaluate_by_fold(catboost).set_index("fold")
    return int(
        (c["average_precision"] >= l["average_precision"]).sum()
    )


def _systematic_segment_collapse(
    logistic: pd.DataFrame,
    catboost: pd.DataFrame,
) -> dict:
    dimensions = [
        "search_sector",
        "search_modality",
        "user_type",
        "source",
        "temporal_cohort",
    ]
    counts: dict[str, int] = {}
    details: list[dict[str, Any]] = []
    for fold in sorted(logistic["fold"].unique()):
        lfold = logistic.loc[logistic["fold"].eq(fold)]
        cfold = catboost.loc[catboost["fold"].eq(fold)]
        for dim in dimensions:
            for value, lp in lfold.groupby(dim, dropna=False):
                cp = cfold.loc[cfold[dim].eq(value)]
                if len(lp) < 100 or len(cp) != len(lp):
                    continue
                lm = segment_analysis(
                    lp,
                    segment_columns=(dim,),
                    minimum_n=100,
                )
                cm = segment_analysis(
                    cp,
                    segment_columns=(dim,),
                    minimum_n=100,
                )
                if lm.empty or cm.empty:
                    continue
                ap_delta = float(
                    cm.iloc[0]["average_precision"]
                    - lm.iloc[0]["average_precision"]
                )
                brier_delta = float(cm.iloc[0]["brier"] - lm.iloc[0]["brier"])
                bad = ap_delta < -0.03 or brier_delta > 0.02
                key = f"{dim}={value}"
                if bad:
                    counts[key] = counts.get(key, 0) + 1
                details.append(
                    {
                        "fold": fold,
                        "segment": key,
                        "n": len(lp),
                        "ap_delta_catboost_minus_logistic": ap_delta,
                        "brier_delta_catboost_minus_logistic": brier_delta,
                        "material_collapse": bad,
                    }
                )
    systematic = sorted(k for k, n in counts.items() if n >= 2)
    return {
        "systematic_segments": systematic,
        "details": details,
    }


def select_architecture(
    logistic: pd.DataFrame,
    catboost: pd.DataFrame,
) -> dict:
    lm = _macro_summary(logistic)
    cm = _macro_summary(catboost)
    ap_delta = cm["macro_average_precision"] - lm["macro_average_precision"]
    brier_delta = cm["macro_brier"] - lm["macro_brier"]
    lift_delta = cm["macro_lift_at_10pct"] - lm["macro_lift_at_10pct"]
    wins = _fold_ap_wins(logistic, catboost)

    boot_ap = paired_bootstrap_delta(
        logistic,
        catboost,
        metric="average_precision",
        n_resamples=2000,
        seed=RANDOM_SEED,
    )
    boot_brier = paired_bootstrap_delta(
        logistic,
        catboost,
        metric="brier",
        n_resamples=2000,
        seed=RANDOM_SEED + 1,
    )
    boot_lift = paired_bootstrap_delta(
        logistic,
        catboost,
        metric="lift_at_10pct",
        n_resamples=2000,
        seed=RANDOM_SEED + 2,
    )
    collapse = _systematic_segment_collapse(logistic, catboost)

    conditions = {
        "macro_delta_ap_gt_0": ap_delta > 0,
        "fold_stability": wins >= 3
        or boot_ap["probability_delta_gt_0"] >= 0.80,
        "brier_guardrail": brier_delta <= 0.005,
        "segment_guardrail": not collapse["systematic_segments"],
        "operational_magnitude": ap_delta >= 0.005 or lift_delta >= 0.10,
    }
    promoted = all(conditions.values())
    return {
        "champion_family": "CATBOOST" if promoted else "LOGISTIC",
        "conditions": conditions,
        "fold_ap_wins_catboost": wins,
        "macro_logistic": lm,
        "macro_catboost": cm,
        "deltas_catboost_minus_logistic": {
            "average_precision": ap_delta,
            "brier": brier_delta,
            "lift_at_10pct": lift_delta,
        },
        "paired_bootstrap": {
            "average_precision": boot_ap,
            "brier": boot_brier,
            "lift_at_10pct": boot_lift,
        },
        "segment_collapse": collapse,
    }


def fit_full_development_model(
    frame: pd.DataFrame,
    *,
    variant: str,
    model_family: str,
    registry_gate: FeatureRegistryGate,
):
    features = _variant_features(variant)
    roles = (
        ("LEAD_QUALITY", "MATCHING", "INVENTORY")
        if variant == "E"
        else ("LEAD_QUALITY",)
    )
    statuses = (
        ("REQUIRED", "SUPPORTED", "EXPERIMENTAL")
        if variant == "E"
        else ("REQUIRED", "SUPPORTED")
    )
    registry_gate.assert_allowed(
        features,
        stage="T1",
        model_roles=roles,
        statuses=statuses,
    )
    if model_family == "LOGISTIC":
        return fit_logistic(frame, features)
    return fit_catboost(frame, features)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()

    promotion = json.loads((HERE / "MODEL_PROMOTION_RULE.json").read_text())
    if not promotion.get("frozen_before_model_results"):
        raise RuntimeError("MODEL_PROMOTION_RULE must be frozen before training")

    registry_path = FEATURE_DIR / "FEATURE_REGISTRY.csv"
    registry_gate = FeatureRegistryGate(registry_path)
    frame = _load_t1_development(repo_root)

    pred_dir = HERE / "predictions"
    metric_dir = HERE / "metrics"
    artifact_dir = HERE / "artifacts"
    for d in (pred_dir, metric_dir, artifact_dir):
        d.mkdir(parents=True, exist_ok=True)

    baselines = run_baselines(frame)
    for name, pred in baselines.items():
        pred.to_csv(pred_dir / f"{name}_development_oof.csv", index=False)
        save_evaluation(
            pred,
            metric_dir,
            name=f"{name}_development",
        )

    variants = [
        "A",
        "B",
        "C",
        "D_WITH_ASKED_VISIT",
        "D_WITHOUT_ASKED_VISIT",
        "E",
    ]
    all_predictions: dict[tuple[str, str], pd.DataFrame] = {}
    for variant in variants:
        for family in ("LOGISTIC", "CATBOOST"):
            pred = run_model_cv(
                frame,
                variant=variant,
                model_family=family,
                registry_gate=registry_gate,
            )
            all_predictions[(family, variant)] = pred
            stem = f"{family.lower()}_{variant.lower()}_development"
            pred.to_csv(pred_dir / f"{stem}_oof.csv", index=False)
            save_evaluation(pred, metric_dir, name=stem)

    logistic_predictions = {
        v: all_predictions[("LOGISTIC", v)] for v in variants
    }
    core_selection = _select_core_variant(logistic_predictions)
    selected_variant = core_selection["selected_core_variant"]

    architecture = select_architecture(
        all_predictions[("LOGISTIC", selected_variant)],
        all_predictions[("CATBOOST", selected_variant)],
    )
    selected_family = architecture["champion_family"]

    fitted = fit_full_development_model(
        frame,
        variant=selected_variant,
        model_family=selected_family,
        registry_gate=registry_gate,
    )
    model_path = artifact_dir / "development_champion_raw.joblib"
    joblib.dump(fitted, model_path)

    selection = {
        "status": "DEVELOPMENT_ARCHITECTURE_SELECTED",
        "target_version": promotion["target_version"],
        "split_version": promotion["split_version"],
        "feature_registry_sha256": feature_registry_sha256(registry_path),
        "ablation_plan_version": _load_plan()["version"],
        "core_feature_selection": core_selection,
        "architecture_selection": architecture,
        "selected_core_variant": selected_variant,
        "selected_features": _variant_features(selected_variant),
        "selected_model_family": selected_family,
        "logistic_config": LOGISTIC_CONFIG,
        "catboost_config": CATBOOST_CONFIG,
        "random_seed": RANDOM_SEED,
        "development_rows": int(len(frame)),
        "development_leads": int(frame["lead_id"].nunique()),
        "calibration_used": False,
        "procedural_holdout_opened": False,
        "development_model_artifact": str(model_path.relative_to(ASSESSMENT_ROOT)),
    }
    (artifact_dir / "development_selection.json").write_text(
        json.dumps(selection, indent=2) + "\n"
    )
    print(json.dumps(selection, indent=2))


if __name__ == "__main__":
    main()
