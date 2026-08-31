from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


def _top_mask(scores: np.ndarray, fraction: float) -> np.ndarray:
    count = max(1, int(math.ceil(len(scores) * fraction)))
    order = np.argsort(-scores, kind="mergesort")
    mask = np.zeros(len(scores), dtype=bool)
    mask[order[:count]] = True
    return mask


def _tie_aware_top_metrics(y: np.ndarray, scores: np.ndarray, fraction: float) -> tuple[float, float, float]:
    """Expected top-k metrics when the capacity boundary cuts through a score tie.

    Rows strictly above the boundary are selected with probability one. Rows tied
    at the boundary share the remaining capacity uniformly. This makes the metric
    invariant to input row order and matches a fair operational tie-break policy.
    """
    count = max(1, int(math.ceil(len(scores) * fraction)))
    threshold = float(np.partition(scores, len(scores) - count)[len(scores) - count])
    above = scores > threshold
    tied = scores == threshold
    remaining = count - int(above.sum())
    tie_count = int(tied.sum())
    tie_share = remaining / max(1, tie_count)
    expected_positives = float(y[above].sum() + tie_share * y[tied].sum())
    precision = expected_positives / count
    recall = expected_positives / max(1, int(y.sum()))
    lift = precision / max(1e-12, float(y.mean()))
    return precision, recall, lift


def binary_metrics(y_true: Iterable[int], scores: Iterable[float]) -> dict[str, float]:
    y = np.asarray(y_true, dtype=int)
    p = np.clip(np.asarray(scores, dtype=float), 1e-8, 1 - 1e-8)
    if len(np.unique(y)) < 2:
        auc = float("nan")
        ap = float(y.mean())
    else:
        auc = float(roc_auc_score(y, p))
        ap = float(average_precision_score(y, p))
    result = {
        "n": int(len(y)),
        "positive_rate": float(y.mean()),
        "roc_auc": auc,
        "average_precision": ap,
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
    }
    for fraction in (0.05, 0.10, 0.20):
        precision, recall, lift = _tie_aware_top_metrics(y, p, fraction)
        result[f"precision_top_{int(fraction * 100)}pct"] = precision
        result[f"recall_top_{int(fraction * 100)}pct"] = recall
        result[f"lift_top_{int(fraction * 100)}pct"] = lift
    return result


def calibration_table(y_true: Iterable[int], scores: Iterable[float], bins: int = 10) -> pd.DataFrame:
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(scores, dtype=float)
    observed, predicted = calibration_curve(y, p, n_bins=bins, strategy="quantile")
    return pd.DataFrame({"mean_predicted": predicted, "observed_rate": observed})


def gains_table(y_true: Iterable[int], scores: Iterable[float], steps: int = 20) -> pd.DataFrame:
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(scores, dtype=float)
    rows = []
    for fraction in np.linspace(1 / steps, 1.0, steps):
        precision, recall, lift = _tie_aware_top_metrics(y, p, float(fraction))
        rows.append({
            "population_fraction": float(fraction),
            "positive_capture": recall,
            "precision": precision,
            "lift": lift,
        })
    return pd.DataFrame(rows)


def segment_metrics(frame: pd.DataFrame, target: str, score: str, segments: list[str], min_n: int = 100) -> pd.DataFrame:
    rows = []
    for segment in segments:
        for value, group in frame.groupby(segment, dropna=False):
            if len(group) < min_n or group[target].nunique() < 2:
                continue
            metrics = binary_metrics(group[target], group[score])
            rows.append({"segment": segment, "value": str(value), **metrics})
    return pd.DataFrame(rows)


def clustered_bootstrap_delta(
    frame: pd.DataFrame,
    target: str,
    score_a: str,
    score_b: str,
    cluster: str = "lead_id",
    iterations: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    clusters = frame[cluster].drop_duplicates().to_numpy()
    rows = []
    for _ in range(iterations):
        sampled = rng.choice(clusters, size=len(clusters), replace=True)
        sample = pd.concat([frame[frame[cluster].eq(value)] for value in sampled], ignore_index=True)
        a = binary_metrics(sample[target], sample[score_a])
        b = binary_metrics(sample[target], sample[score_b])
        rows.append({metric: b[metric] - a[metric] for metric in ("roc_auc", "average_precision", "brier", "log_loss", "lift_top_10pct", "recall_top_20pct")})
    boot = pd.DataFrame(rows)
    return pd.DataFrame({
        "metric": boot.columns,
        "delta_mean": boot.mean().values,
        "delta_low": boot.quantile(0.025).values,
        "delta_high": boot.quantile(0.975).values,
        "p_delta_positive": (boot > 0).mean().values,
    })


def bootstrap_metric_intervals(
    frame: pd.DataFrame,
    target: str,
    score_columns: list[str],
    iterations: int = 1000,
    seed: int = 42,
) -> pd.DataFrame:
    """Lead-level non-parametric intervals for the ranking/calibration metrics."""
    data = frame[[target, *score_columns]].dropna(subset=[target]).reset_index(drop=True)
    y = data[target].astype(int).to_numpy()
    scores = {column: data[column].to_numpy(dtype=float) for column in score_columns}
    rng = np.random.default_rng(seed)
    keys = [
        "roc_auc", "average_precision", "brier", "log_loss",
        "lift_top_5pct", "lift_top_10pct", "recall_top_10pct", "recall_top_20pct",
    ]
    draws: dict[str, dict[str, list[float]]] = {
        column: {key: [] for key in keys} for column in score_columns
    }
    for _ in range(iterations):
        index = rng.integers(0, len(data), size=len(data))
        sample_y = y[index]
        if sample_y.min() == sample_y.max():
            continue
        for column, values in scores.items():
            metrics = binary_metrics(sample_y, values[index])
            for key in keys:
                draws[column][key].append(metrics[key])
    rows = []
    for column in score_columns:
        estimates = binary_metrics(y, scores[column])
        for key in keys:
            values = np.asarray(draws[column][key], dtype=float)
            rows.append({
                "score": column,
                "metric": key,
                "estimate": estimates[key],
                "ci_low": float(np.quantile(values, 0.025)),
                "ci_high": float(np.quantile(values, 0.975)),
                "bootstrap_iterations": int(len(values)),
            })
    return pd.DataFrame(rows)


def paired_bootstrap_delta(
    frame: pd.DataFrame,
    target: str,
    reference_score: str,
    challenger_score: str,
    iterations: int = 1000,
    seed: int = 42,
) -> pd.DataFrame:
    """Paired uncertainty for a challenger minus its reference on identical leads."""
    data = frame[[target, reference_score, challenger_score]].dropna(subset=[target]).reset_index(drop=True)
    y = data[target].astype(int).to_numpy()
    reference = data[reference_score].to_numpy(dtype=float)
    challenger = data[challenger_score].to_numpy(dtype=float)
    metric_keys = ["roc_auc", "average_precision", "brier", "log_loss", "lift_top_5pct", "lift_top_10pct", "recall_top_10pct"]
    observed_reference = binary_metrics(y, reference)
    observed_challenger = binary_metrics(y, challenger)
    rng = np.random.default_rng(seed)
    draws = {key: [] for key in metric_keys}
    for _ in range(iterations):
        index = rng.integers(0, len(data), size=len(data))
        sample_y = y[index]
        if sample_y.min() == sample_y.max():
            continue
        ref_metrics = binary_metrics(sample_y, reference[index])
        candidate_metrics = binary_metrics(sample_y, challenger[index])
        for key in metric_keys:
            draws[key].append(candidate_metrics[key] - ref_metrics[key])
    rows = []
    for key in metric_keys:
        values = np.asarray(draws[key], dtype=float)
        rows.append({
            "metric": key,
            "reference": reference_score,
            "challenger": challenger_score,
            "reference_estimate": observed_reference[key],
            "challenger_estimate": observed_challenger[key],
            "delta_challenger_minus_reference": observed_challenger[key] - observed_reference[key],
            "delta_ci_low": float(np.quantile(values, 0.025)),
            "delta_ci_high": float(np.quantile(values, 0.975)),
            "probability_delta_positive": float((values > 0).mean()),
            "bootstrap_iterations": int(len(values)),
        })
    return pd.DataFrame(rows)


def compare_system_scores(frame: pd.DataFrame, target: str, score_map: dict[str, str]) -> pd.DataFrame:
    """Comparable holdout metrics for Lead Quality, inventory and combined scores."""
    rows = []
    for label, column in score_map.items():
        metrics = binary_metrics(frame[target].astype(int), frame[column])
        rows.append({"score": label, "column": column, **metrics})
    return pd.DataFrame(rows)


def population_stability_index(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    ref = pd.to_numeric(reference, errors="coerce").dropna()
    cur = pd.to_numeric(current, errors="coerce").dropna()
    if ref.empty or cur.empty:
        return float("nan")
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    ref_hist, _ = np.histogram(ref, bins=edges)
    cur_hist, _ = np.histogram(cur, bins=edges)
    ref_share = np.clip(ref_hist / max(1, ref_hist.sum()), 1e-6, None)
    cur_share = np.clip(cur_hist / max(1, cur_hist.sum()), 1e-6, None)
    return float(np.sum((cur_share - ref_share) * np.log(cur_share / ref_share)))


def categorical_js(reference: pd.Series, current: pd.Series) -> float:
    values = sorted(set(reference.fillna("<missing>").astype(str)) | set(current.fillna("<missing>").astype(str)))
    ref = reference.fillna("<missing>").astype(str).value_counts(normalize=True).reindex(values, fill_value=0).to_numpy()
    cur = current.fillna("<missing>").astype(str).value_counts(normalize=True).reindex(values, fill_value=0).to_numpy()
    return float(jensenshannon(ref, cur, base=2.0) ** 2)


def numeric_drift(reference: pd.Series, current: pd.Series) -> dict[str, float]:
    ref = pd.to_numeric(reference, errors="coerce").dropna()
    cur = pd.to_numeric(current, errors="coerce").dropna()
    scale = max(1e-9, float(ref.quantile(0.75) - ref.quantile(0.25))) if not ref.empty else 1.0
    return {
        "psi": population_stability_index(ref, cur),
        "wasserstein_iqr_scaled": float(wasserstein_distance(ref, cur) / scale) if not ref.empty and not cur.empty else float("nan"),
        "missing_delta": float(current.isna().mean() - reference.isna().mean()),
    }
