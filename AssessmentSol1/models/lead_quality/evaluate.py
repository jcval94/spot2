from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    auc,
    brier_score_loss,
    log_loss,
    precision_recall_curve,
    roc_auc_score,
)


METRIC_COLUMNS = [
    "roc_auc",
    "average_precision",
    "pr_auc",
    "log_loss",
    "brier",
    "calibration_intercept",
    "calibration_slope",
    "lift_at_5pct",
    "lift_at_10pct",
    "lift_at_20pct",
    "precision_at_10pct",
    "recall_at_10pct",
    "recall_at_20pct",
    "positive_rate",
    "n",
    "n_leads",
]


def _safe_binary_metric(fn, y: np.ndarray, p: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    try:
        return float(fn(y, p))
    except Exception:
        return float("nan")


def _top_fraction_indices(p: np.ndarray, fraction: float) -> np.ndarray:
    n = len(p)
    if n == 0:
        return np.asarray([], dtype=int)
    k = max(1, int(math.ceil(n * fraction)))
    # Stable ordering makes ties deterministic.
    return np.argsort(-p, kind="mergesort")[:k]


def _lift(y: np.ndarray, p: np.ndarray, fraction: float) -> float:
    base = float(np.mean(y)) if len(y) else float("nan")
    if not np.isfinite(base) or base <= 0:
        return float("nan")
    idx = _top_fraction_indices(p, fraction)
    return float(np.mean(y[idx]) / base)


def _precision_at(y: np.ndarray, p: np.ndarray, fraction: float) -> float:
    idx = _top_fraction_indices(p, fraction)
    return float(np.mean(y[idx])) if len(idx) else float("nan")


def _recall_at(y: np.ndarray, p: np.ndarray, fraction: float) -> float:
    positives = float(np.sum(y))
    if positives <= 0:
        return float("nan")
    idx = _top_fraction_indices(p, fraction)
    return float(np.sum(y[idx]) / positives)


def calibration_intercept_slope(
    y: np.ndarray, p: np.ndarray
) -> tuple[float, float]:
    if len(np.unique(y)) < 2:
        return float("nan"), float("nan")
    eps = 1e-6
    p = np.clip(p.astype(float), eps, 1 - eps)
    logit = np.log(p / (1 - p)).reshape(-1, 1)
    try:
        model = LogisticRegression(
            penalty=None,
            solver="lbfgs",
            max_iter=2000,
        )
        model.fit(logit, y)
        return float(model.intercept_[0]), float(model.coef_[0, 0])
    except Exception:
        return float("nan"), float("nan")


def metric_bundle(
    y_true: Iterable[int],
    probability: Iterable[float],
    *,
    lead_ids: Iterable | None = None,
) -> dict[str, float]:
    y = np.asarray(list(y_true), dtype=int)
    p = np.asarray(list(probability), dtype=float)
    if len(y) != len(p):
        raise ValueError("y_true and probability lengths differ")
    if len(y) == 0:
        return {k: float("nan") for k in METRIC_COLUMNS}

    roc = _safe_binary_metric(roc_auc_score, y, p)
    ap = _safe_binary_metric(average_precision_score, y, p)
    try:
        precision, recall, _ = precision_recall_curve(y, p)
        pr = float(auc(recall, precision))
    except Exception:
        pr = float("nan")
    ll = _safe_binary_metric(
        lambda yt, prb: log_loss(yt, np.clip(prb, 1e-6, 1 - 1e-6)),
        y,
        p,
    )
    brier = float(brier_score_loss(y, p))
    intercept, slope = calibration_intercept_slope(y, p)

    leads = list(lead_ids) if lead_ids is not None else list(range(len(y)))
    return {
        "roc_auc": roc,
        "average_precision": ap,
        "pr_auc": pr,
        "log_loss": ll,
        "brier": brier,
        "calibration_intercept": intercept,
        "calibration_slope": slope,
        "lift_at_5pct": _lift(y, p, 0.05),
        "lift_at_10pct": _lift(y, p, 0.10),
        "lift_at_20pct": _lift(y, p, 0.20),
        "precision_at_10pct": _precision_at(y, p, 0.10),
        "recall_at_10pct": _recall_at(y, p, 0.10),
        "recall_at_20pct": _recall_at(y, p, 0.20),
        "positive_rate": float(np.mean(y)),
        "n": int(len(y)),
        "n_leads": int(pd.Series(leads).nunique()),
    }


def evaluate_by_fold(
    predictions: pd.DataFrame,
    *,
    probability_col: str = "probability",
) -> pd.DataFrame:
    required = {"fold", "target_value", "lead_id", "score_time", probability_col}
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"Prediction frame missing: {sorted(missing)}")

    rows: list[dict] = []
    for fold, part in predictions.groupby("fold", sort=True):
        metrics = metric_bundle(
            part["target_value"].astype(int),
            part[probability_col].astype(float),
            lead_ids=part["lead_id"],
        )
        score_time = pd.to_datetime(part["score_time"], utc=True)
        rows.append(
            {
                "fold": fold,
                "window_start": score_time.min().isoformat(),
                "window_end": score_time.max().isoformat(),
                **metrics,
            }
        )
    return pd.DataFrame(rows)


def macro_fold_metrics(fold_metrics: pd.DataFrame) -> dict:
    metrics = [
        c
        for c in METRIC_COLUMNS
        if c not in {"n", "n_leads", "positive_rate"}
        and c in fold_metrics.columns
    ]
    out = {f"macro_{c}": float(fold_metrics[c].mean()) for c in metrics}
    out["folds"] = int(len(fold_metrics))
    out["total_validation_rows"] = int(fold_metrics["n"].sum())
    out["mean_positive_rate"] = float(fold_metrics["positive_rate"].mean())
    return out


def oof_global_diagnostic(
    predictions: pd.DataFrame,
    *,
    probability_col: str = "probability",
) -> dict:
    """Global OOF diagnostic.

    Architecture/ablation selection must use macro within-fold metrics, not this
    cross-fold rank, because independently fitted folds can have different
    probability scales.
    """
    return metric_bundle(
        predictions["target_value"].astype(int),
        predictions[probability_col].astype(float),
        lead_ids=predictions["lead_id"],
    )


def segment_analysis(
    predictions: pd.DataFrame,
    *,
    probability_col: str = "probability",
    segment_columns: Iterable[str] = (
        "search_sector",
        "search_modality",
        "user_type",
        "source",
        "temporal_cohort",
    ),
    minimum_n: int = 100,
) -> pd.DataFrame:
    rows: list[dict] = []
    for segment_col in segment_columns:
        if segment_col not in predictions.columns:
            continue
        for value, part in predictions.groupby(segment_col, dropna=False):
            if len(part) < minimum_n:
                continue
            metrics = metric_bundle(
                part["target_value"].astype(int),
                part[probability_col].astype(float),
                lead_ids=part["lead_id"],
            )
            rows.append(
                {
                    "segment_dimension": segment_col,
                    "segment_value": "__MISSING__" if pd.isna(value) else value,
                    **metrics,
                }
            )
    return pd.DataFrame(rows)


def paired_bootstrap_delta(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    metric: str,
    left_probability_col: str = "probability",
    right_probability_col: str = "probability",
    n_resamples: int = 2000,
    seed: int = 20260830,
) -> dict:
    """Paired lead-group bootstrap for a metric delta: right - left."""
    key = ["fold", "lead_id"]
    a = left[
        key + ["target_value", left_probability_col]
    ].rename(columns={left_probability_col: "prob_left"})
    b = right[
        key + ["target_value", right_probability_col]
    ].rename(columns={right_probability_col: "prob_right"})
    merged = a.merge(
        b,
        on=key,
        how="inner",
        suffixes=("_left", "_right"),
        validate="one_to_one",
    )
    if len(merged) != len(a) or len(merged) != len(b):
        raise ValueError("Paired comparison populations differ")
    if not np.array_equal(
        merged["target_value_left"].to_numpy(),
        merged["target_value_right"].to_numpy(),
    ):
        raise ValueError("Paired comparison target mismatch")

    metric_map = {
        "average_precision": lambda d, p: metric_bundle(
            d["target_value_left"], p, lead_ids=d["lead_id"]
        )["average_precision"],
        "brier": lambda d, p: metric_bundle(
            d["target_value_left"], p, lead_ids=d["lead_id"]
        )["brier"],
        "lift_at_10pct": lambda d, p: metric_bundle(
            d["target_value_left"], p, lead_ids=d["lead_id"]
        )["lift_at_10pct"],
    }
    if metric not in metric_map:
        raise ValueError(f"Unsupported paired-bootstrap metric: {metric}")

    rng = np.random.default_rng(seed)
    deltas: list[float] = []
    # Resample leads inside each fold, then macro-average fold deltas.
    grouped = {
        fold: part.reset_index(drop=True)
        for fold, part in merged.groupby("fold", sort=True)
    }
    for _ in range(n_resamples):
        fold_deltas: list[float] = []
        for _, part in grouped.items():
            leads = part["lead_id"].unique()
            sampled = rng.choice(leads, size=len(leads), replace=True)
            # T1 is one row/lead. General implementation keeps repeated sampled
            # lead groups by concatenating each sampled group.
            pieces = [part.loc[part["lead_id"].eq(lead)] for lead in sampled]
            boot = pd.concat(pieces, ignore_index=True)
            fn = metric_map[metric]
            ml = fn(boot, boot["prob_left"])
            mr = fn(boot, boot["prob_right"])
            if np.isfinite(ml) and np.isfinite(mr):
                fold_deltas.append(float(mr - ml))
        if fold_deltas:
            deltas.append(float(np.mean(fold_deltas)))

    arr = np.asarray(deltas, dtype=float)
    if arr.size == 0:
        return {
            "metric": metric,
            "delta": float("nan"),
            "ci95_low": float("nan"),
            "ci95_high": float("nan"),
            "probability_delta_gt_0": float("nan"),
            "n_resamples": 0,
        }

    # Point estimate uses the same fold-macro definition.
    fold_point: list[float] = []
    for _, part in grouped.items():
        fn = metric_map[metric]
        fold_point.append(
            float(fn(part, part["prob_right"]) - fn(part, part["prob_left"]))
        )
    return {
        "metric": metric,
        "delta": float(np.mean(fold_point)),
        "ci95_low": float(np.quantile(arr, 0.025)),
        "ci95_high": float(np.quantile(arr, 0.975)),
        "probability_delta_gt_0": float(np.mean(arr > 0)),
        "n_resamples": int(arr.size),
    }


def save_evaluation(
    predictions: pd.DataFrame,
    output_dir: Path,
    *,
    name: str,
    probability_col: str = "probability",
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    fold = evaluate_by_fold(predictions, probability_col=probability_col)
    macro = macro_fold_metrics(fold)
    global_diag = oof_global_diagnostic(
        predictions, probability_col=probability_col
    )
    segments = segment_analysis(
        predictions, probability_col=probability_col
    )

    fold.to_csv(output_dir / f"{name}_fold_metrics.csv", index=False)
    segments.to_csv(output_dir / f"{name}_segment_metrics.csv", index=False)
    payload = {
        "name": name,
        "selection_authority": "MACRO_WITHIN_FOLD",
        "macro": macro,
        "oof_global_diagnostic_only": global_diag,
    }
    (output_dir / f"{name}_summary.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    return payload
