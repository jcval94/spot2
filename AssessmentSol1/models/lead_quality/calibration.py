from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import polars as pl
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

HERE = Path(__file__).resolve().parent
ASSESSMENT_ROOT = HERE.parents[1]
FEATURE_DIR = ASSESSMENT_ROOT / "features"
if str(FEATURE_DIR) not in sys.path:
    sys.path.insert(0, str(FEATURE_DIR))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from build_features import build_feature_artifacts
from evaluate import metric_bundle
from transformers import feature_registry_sha256
from train import RANDOM_SEED, _catboost_frame, _normalize_bool_columns


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_calibration(repo_root: Path) -> pd.DataFrame:
    build_feature_artifacts(repo_root, scope="calibration_inclusive")
    path = (
        FEATURE_DIR
        / "artifacts"
        / "t1_features_calibration_inclusive_with_selected_spot_challenger.parquet"
    )
    frame = pd.DataFrame(pl.read_parquet(path).to_dicts())
    frame["score_time"] = pd.to_datetime(frame["score_time"], utc=True)

    split = pd.read_csv(ASSESSMENT_ROOT / "splits" / "split_assignments_t1.csv")
    split["lead_id"] = pd.to_numeric(split["lead_id"])
    frame["lead_id"] = pd.to_numeric(frame["lead_id"])
    frame = frame.merge(
        split[["lead_id", "primary_partition"]],
        on="lead_id",
        how="inner",
        validate="one_to_one",
    )
    frame = frame.loc[
        frame["primary_partition"].eq("CALIBRATION")
        & frame["target_status"].isin(["POSITIVE", "NEGATIVE"])
        & frame["target_value"].notna()
    ].copy()
    if frame["score_time"].ge(pd.Timestamp("2026-06-01T00:00:00Z")).any():
        raise AssertionError("Procedural holdout entered calibration")
    return frame


def predict_raw(model_payload: dict, frame: pd.DataFrame) -> np.ndarray:
    if model_payload["model_family"] == "BASE_RATE":
        return np.full(
            len(frame),
            float(model_payload["constant_probability"]),
            dtype=float,
        )
    features = list(model_payload["features"])
    if model_payload["model_family"] == "LOGISTIC":
        x = _normalize_bool_columns(frame[features])
        matrix = model_payload["preprocessor"].transform(x)
        return model_payload["model"].predict_proba(matrix)[:, 1]
    if model_payload["model_family"] == "CATBOOST":
        x = _catboost_frame(
            frame[features],
            list(model_payload["categorical_features"]),
        )
        return model_payload["model"].predict_proba(x)[:, 1]
    raise ValueError(f"Unknown model family: {model_payload['model_family']}")


def _raw_logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p)).reshape(-1, 1)


def fit_calibrator(method: str, p: np.ndarray, y: np.ndarray) -> dict:
    if method == "raw":
        return {"method": "raw", "model": None}
    if method == "platt":
        model = LogisticRegression(
            penalty=None,
            solver="lbfgs",
            max_iter=2000,
            random_state=RANDOM_SEED,
        )
        model.fit(_raw_logit(p), y)
        return {"method": "platt", "model": model}
    if method == "isotonic":
        model = IsotonicRegression(out_of_bounds="clip")
        model.fit(p, y)
        return {"method": "isotonic", "model": model}
    raise ValueError(method)


def apply_calibrator(calibrator: dict, p: np.ndarray) -> np.ndarray:
    method = calibrator["method"]
    if method == "raw":
        return np.asarray(p, dtype=float)
    if method == "platt":
        return calibrator["model"].predict_proba(_raw_logit(p))[:, 1]
    if method == "isotonic":
        return np.asarray(calibrator["model"].predict(p), dtype=float)
    raise ValueError(method)


def _cross_calibration_predictions(
    raw_probability: np.ndarray,
    y: np.ndarray,
    *,
    include_isotonic: bool,
) -> dict[str, np.ndarray]:
    methods = ["platt"] + (["isotonic"] if include_isotonic else [])
    out = {"raw": np.asarray(raw_probability, dtype=float)}
    for method in methods:
        out[method] = np.full(len(y), np.nan, dtype=float)

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=RANDOM_SEED,
    )
    for fit_idx, val_idx in cv.split(raw_probability, y):
        for method in methods:
            cal = fit_calibrator(
                method,
                raw_probability[fit_idx],
                y[fit_idx],
            )
            out[method][val_idx] = apply_calibrator(
                cal,
                raw_probability[val_idx],
            )
    for method, p in out.items():
        if np.isnan(p).any():
            raise AssertionError(f"Calibration OOF incomplete for {method}")
    return out


def _select_method(metrics: dict[str, dict]) -> tuple[str, dict]:
    raw = metrics["raw"]
    eligible: list[tuple[str, float]] = []
    rationale: dict[str, Any] = {}
    for method in ("platt", "isotonic"):
        if method not in metrics:
            continue
        m = metrics[method]
        brier_gain = raw["brier"] - m["brier"]
        logloss_gain = raw["log_loss"] - m["log_loss"]
        qualifies = (
            max(brier_gain, logloss_gain) > 0
            and min(brier_gain, logloss_gain) >= -0.005
        )
        composite = brier_gain + logloss_gain
        rationale[method] = {
            "brier_gain": brier_gain,
            "log_loss_gain": logloss_gain,
            "qualifies": qualifies,
            "composite_gain": composite,
        }
        if qualifies:
            eligible.append((method, composite))

    if not eligible:
        return "raw", rationale

    eligible.sort(key=lambda x: x[1], reverse=True)
    best_method, best_score = eligible[0]
    if len(eligible) > 1:
        second_method, second_score = eligible[1]
        if abs(best_score - second_score) < 0.001:
            # Frozen preference: Platt before isotonic in a practical tie.
            if "platt" in {best_method, second_method}:
                best_method = "platt"
    return best_method, rationale


def _package_versions() -> dict[str, str]:
    names = [
        "polars",
        "numpy",
        "pandas",
        "scikit-learn",
        "scipy",
        "catboost",
        "joblib",
    ]
    out = {}
    for name in names:
        try:
            out[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            out[name] = "NOT_FOUND"
    return out


def _write_docs(
    selection: dict,
    calibration_summary: dict,
    frozen_config: dict,
) -> None:
    arch = selection["architecture_selection"]
    core = selection["core_feature_selection"]
    md = f"""# MODEL_SELECTION — T1 DEVELOPMENT decision

**Status:** architecture and feature set selected on DEVELOPMENT only.  
**Procedural holdout opened:** NO.

## Frozen feature-set decision

Selected core variant: **{selection['selected_core_variant']}**.

Reference model for feature-family selection: Logistic Regression.

The selected-Spot Ablation E remained a challenger only and could not redefine core LeadQuality regardless of its score.

## Architecture decision

Champion family before calibration: **{selection['selected_model_family']}**.

CatBoost-minus-Logistic deltas on the selected core:
- ΔAP: {arch['deltas_catboost_minus_logistic']['average_precision']:.6f}
- ΔBrier: {arch['deltas_catboost_minus_logistic']['brier']:.6f}
- ΔLift@10%: {arch['deltas_catboost_minus_logistic']['lift_at_10pct']:.6f}

Promotion conditions:
{chr(10).join(f"- {k}: **{v}**" for k, v in arch['conditions'].items())}

The promotion rule was frozen before these results. No new model family or feature variant was added after inspection.
"""
    (HERE / "MODEL_SELECTION.md").write_text(md)

    cal = calibration_summary
    cal_md = f"""# CALIBRATION — T1

Calibration partition only; it was not used for feature or architecture selection.

Selected method: **{cal['selected_method']}**.

| Method | N | Positive rate | Brier | Log Loss | Slope | Intercept |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(f"| {m} | {int(v['n'])} | {v['positive_rate']:.4f} | {v['brier']:.6f} | {v['log_loss']:.6f} | {v['calibration_slope']:.4f} | {v['calibration_intercept']:.4f} |" for m, v in cal['cross_calibration_metrics'].items())}

Isotonic eligibility: **{cal['isotonic_eligible']}**.

Selection used calibration-internal OOF predictions; the selected calibrator was then refit on all calibration rows. The procedural holdout was not inspected.
"""
    (HERE / "CALIBRATION.md").write_text(cal_md)

    card = f"""# MODEL_CARD — T1 Lead Quality

## Intended use

Rank/probability estimate for the frozen T1 question: **will the deterministic first inquiry eventually be recorded as scheduled_visit?**

This is not final commercial conversion and is not interchangeable with T0 or T2 probability.

## Frozen configuration

- Target: `{frozen_config['target_version']}`
- Split: `{frozen_config['split_version']}`
- Feature variant: **{frozen_config['feature_variant']}**
- Model family: **{frozen_config['model_family']}**
- Calibrator: **{frozen_config['calibrator']}**
- Random seed: {frozen_config['random_seed']}
- Feature count: {len(frozen_config['features'])}

## Data boundaries

Architecture selection used DEVELOPMENT only. Calibration used CALIBRATION only. The procedural holdout remains sealed until explicitly consumed once.

## Feature governance

Core features are intake/current-inquiry/refinement only. Matching/Inventory are excluded from the champion core. Outcome fields, current-state Spot fields, Market Context, semantic-rule scoring features and `llm_*` are excluded.

## Limitations

- scheduled_visit is a proxy outcome, not commercial conversion;
- historical source/snapshot coverage changes over time;
- no causal interpretation is attached to coefficients/SHAP;
- production deployment would require monitoring, outcome instrumentation and refreshed validation.
"""
    (HERE / "MODEL_CARD.md").write_text(card)


def run_calibration(repo_root: Path) -> dict:
    selection_path = HERE / "artifacts" / "development_selection.json"
    model_path = HERE / "artifacts" / "development_champion_raw.joblib"
    if not selection_path.exists() or not model_path.exists():
        raise RuntimeError("Run train.py before calibration.py")

    selection = json.loads(selection_path.read_text())
    if selection.get("procedural_holdout_opened"):
        raise RuntimeError("Invalid development selection state")
    model_payload = joblib.load(model_path)
    frame = _load_calibration(repo_root)
    y = frame["target_value"].astype(int).to_numpy()
    raw_p = predict_raw(model_payload, frame)

    positives = int(np.sum(y))
    negatives = int(len(y) - positives)
    isotonic_eligible = len(y) >= 300 and positives >= 50 and negatives >= 50
    cross = _cross_calibration_predictions(
        raw_p,
        y,
        include_isotonic=isotonic_eligible,
    )
    metrics = {
        method: metric_bundle(
            y,
            p,
            lead_ids=frame["lead_id"],
        )
        for method, p in cross.items()
    }
    selected_method, rationale = _select_method(metrics)
    final_calibrator = fit_calibrator(
        selected_method,
        raw_p,
        y,
    )
    selected_p = apply_calibrator(final_calibrator, raw_p)

    pred = frame[
        [
            "score_id",
            "lead_id",
            "score_time",
            "target_value",
            "search_sector",
            "search_modality",
            "user_type",
            "source",
        ]
    ].copy()
    pred["population"] = "CALIBRATION"
    pred["raw_probability"] = raw_p
    pred["calibrated_probability"] = selected_p
    pred["calibrator"] = selected_method
    pred.to_csv(
        HERE / "predictions" / "calibration_predictions.csv",
        index=False,
    )

    calibrator_path = HERE / "artifacts" / "calibrator.joblib"
    joblib.dump(final_calibrator, calibrator_path)

    summary = {
        "status": "CALIBRATION_SELECTED",
        "n": int(len(frame)),
        "positives": positives,
        "negatives": negatives,
        "isotonic_eligible": isotonic_eligible,
        "cross_calibration_metrics": metrics,
        "selection_rationale": rationale,
        "selected_method": selected_method,
        "final_fit_population": "ALL_CALIBRATION",
        "procedural_holdout_opened": False,
    }
    (HERE / "metrics" / "calibration_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )

    split_contract = json.loads(
        (ASSESSMENT_ROOT / "splits" / "split_contract.json").read_text()
    )
    registry_path = FEATURE_DIR / "FEATURE_REGISTRY.csv"
    ablation_path = FEATURE_DIR / "ablation_plan.json"
    frozen = {
        "status": "FROZEN",
        "frozen_before_procedural_holdout": True,
        "target_version": selection["target_version"],
        "split_version": selection["split_version"],
        "split_contract_sha256": _sha256(
            ASSESSMENT_ROOT / "splits" / "split_contract.json"
        ),
        "feature_registry_sha256": feature_registry_sha256(registry_path),
        "ablation_plan_sha256": _sha256(ablation_path),
        "feature_variant": (
            "BASE_RATE_NO_FEATURES"
            if selection["selected_model_family"] == "BASE_RATE"
            else selection["selected_core_variant"]
        ),
        "features": selection["selected_features"],
        "model_family": selection["selected_model_family"],
        "hyperparameters": (
            {"constant_source": "DEVELOPMENT prevalence"}
            if selection["selected_model_family"] == "BASE_RATE"
            else (
                selection["logistic_config"]
                if selection["selected_model_family"] == "LOGISTIC"
                else selection["catboost_config"]
            )
        ),
        "calibrator": selected_method,
        "random_seed": selection["random_seed"],
        "package_versions": _package_versions(),
        "development_model_artifact": str(model_path.relative_to(ASSESSMENT_ROOT)),
        "development_model_sha256": _sha256(model_path),
        "calibrator_artifact": str(calibrator_path.relative_to(ASSESSMENT_ROOT)),
        "calibrator_sha256": _sha256(calibrator_path),
        "development_end_exclusive": split_contract["development_end_exclusive"],
        "calibration_start": split_contract["calibration_start"],
        "calibration_end_exclusive": split_contract["calibration_end_exclusive"],
        "procedural_holdout_start": split_contract["procedural_holdout_start"],
        "procedural_holdout_end_exclusive": split_contract[
            "procedural_holdout_end_exclusive"
        ],
        "procedural_holdout_consumed": False,
    }
    (HERE / "FROZEN_MODEL_CONFIG.json").write_text(
        json.dumps(frozen, indent=2) + "\n"
    )
    _write_docs(selection, summary, frozen)
    return {"selection": selection, "calibration": summary, "frozen": frozen}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    args = parser.parse_args()
    result = run_calibration(args.repo_root.resolve())
    print(json.dumps(result["calibration"], indent=2))
    print("FROZEN_MODEL_CONFIG.json written; procedural holdout may now be consumed once.")


if __name__ == "__main__":
    main()
