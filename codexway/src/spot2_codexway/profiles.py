from __future__ import annotations

import math
import os
import warnings
from dataclasses import dataclass
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
warnings.filterwarnings(
    "ignore",
    message=".*known to have a memory leak on Windows with MKL.*",
    category=UserWarning,
    module="sklearn.cluster.*",
)
from sklearn.cluster import BisectingKMeans, KMeans
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.metrics import adjusted_rand_score, silhouette_score
from statsmodels.stats.multitest import multipletests


@dataclass
class ClusterProfile:
    family: str
    transformer: ColumnTransformer
    model: Any
    categorical: list[str]
    numeric: list[str]
    prefix: str
    metrics: dict[str, float]
    label_map: dict[int, str]


def _preprocessor(categorical: list[str], numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("cat", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), categorical),
        ("num", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", RobustScaler()),
        ]), numeric),
    ], sparse_threshold=0.0)


def _cluster_metrics(matrix: np.ndarray, labels: np.ndarray, labels_2: np.ndarray) -> dict[str, float]:
    shares = pd.Series(labels).value_counts(normalize=True)
    entropy = float(-(shares * np.log(shares)).sum() / np.log(len(shares))) if len(shares) > 1 else 0.0
    sample = np.arange(len(matrix))
    if len(sample) > 3000:
        sample = np.random.default_rng(42).choice(sample, 3000, replace=False)
    return {
        "silhouette": float(silhouette_score(matrix[sample], labels[sample])) if len(np.unique(labels[sample])) > 1 else float("nan"),
        "stability_ari": float(adjusted_rand_score(labels, labels_2)),
        "min_cluster_share": float(shares.min()),
        "max_cluster_share": float(shares.max()),
        "normalized_entropy": entropy,
        "balance_ok": bool(shares.min() >= 0.05 and shares.max() <= 0.65),
    }


def fit_profile(
    frame: pd.DataFrame,
    *,
    family: str,
    categorical: list[str],
    numeric: list[str],
    method: str,
    k: int,
    prefix: str,
    seed: int = 42,
) -> ClusterProfile:
    transformer = _preprocessor(categorical, numeric)
    matrix = transformer.fit_transform(frame[categorical + numeric]).astype(float)
    if method == "kmeans":
        model = KMeans(n_clusters=k, n_init=20, random_state=seed).fit(matrix)
        alternate = KMeans(n_clusters=k, n_init=20, random_state=seed + 17).fit_predict(matrix)
        labels = model.labels_
    elif method == "bisecting":
        model = BisectingKMeans(n_clusters=k, random_state=seed).fit(matrix)
        alternate = BisectingKMeans(n_clusters=k, random_state=seed + 17).fit_predict(matrix)
        labels = model.labels_
    elif method == "gmm":
        model = GaussianMixture(n_components=k, random_state=seed, covariance_type="diag", n_init=3).fit(matrix)
        labels = model.predict(matrix)
        alternate = GaussianMixture(n_components=k, random_state=seed + 17, covariance_type="diag", n_init=3).fit_predict(matrix)
    else:
        raise ValueError(f"Unsupported clustering method: {method}")
    metrics = _cluster_metrics(matrix, labels, alternate)
    label_map = {int(label): f"{prefix}{position + 1}" for position, label in enumerate(sorted(np.unique(labels)))}
    return ClusterProfile(family, transformer, model, categorical, numeric, prefix, metrics, label_map)


def assign_profile(profile: ClusterProfile, frame: pd.DataFrame) -> pd.Series:
    matrix = profile.transformer.transform(frame[profile.categorical + profile.numeric]).astype(float)
    if hasattr(profile.model, "predict"):
        labels = profile.model.predict(matrix)
    else:
        labels = profile.model.labels_
    return pd.Series([profile.label_map[int(value)] for value in labels], index=frame.index, name=profile.family)


def _rename_search_need(profile: ClusterProfile, train: pd.DataFrame) -> None:
    assigned = assign_profile(profile, train)
    stats = train.assign(_cluster=assigned).groupby("_cluster")["search_modality"].agg(lambda s: s.mode().iat[0])
    names: dict[str, str] = {}
    rent = stats[stats.eq("rent")].index.tolist()
    sale = stats[stats.eq("sale")].index.tolist()
    both = stats[stats.eq("both")].index.tolist()
    if rent:
        names[rent[0]] = "N1"
    if sale:
        names[sale[0]] = "N2"
    if both:
        names[both[0]] = "N3"
    for old in stats.index:
        names.setdefault(old, f"N{len(names) + 1}")
    profile.label_map = {raw: names[label] for raw, label in profile.label_map.items()}


def build_profiles(t1: pd.DataFrame, spots: pd.DataFrame, inquiries: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, dict[str, ClusterProfile], pd.DataFrame]:
    train = t1[t1["split"].eq("train")].copy()
    need = fit_profile(
        train, family="need_profile", categorical=["search_sector", "search_modality"],
        numeric=["target_area_sqm", "max_budget_mxn_rent_monthly", "max_budget_mxn_sale_total"],
        method="kmeans", k=3, prefix="N", seed=seed,
    )
    _rename_search_need(need, train)
    dynamic = fit_profile(
        train, family="dynamic_need_profile", categorical=["search_modality", "channel", "asked_visit"],
        numeric=["requested_area_sqm", "requested_budget_mxn_rent_monthly", "requested_budget_mxn_sale_total", "urgency_days", "message_length", "area_request_to_target_ratio"],
        method="kmeans", k=5, prefix="DN", seed=seed,
    )

    spot_train = spots[spots["created_at"] < train["prediction_timestamp"].max()].copy()
    physical = fit_profile(
        spot_train, family="physical_profile", categorical=["sector_name", "type_name", "modality"],
        numeric=["area_sqm", "price_sqm_mxn_rent", "price_sqm_mxn_sale"],
        method="gmm", k=4, prefix="PH", seed=seed,
    )
    location = fit_profile(
        spot_train, family="location_profile", categorical=["state", "municipality", "corridor", "region"],
        numeric=["lat", "lon"], method="kmeans", k=7, prefix="LOC", seed=seed,
    )

    broker_history = inquiries[inquiries["inquiry_at"] < train["prediction_timestamp"].max() - pd.Timedelta(days=7)].merge(
        spots[["spot_id", "broker_id"]], on="spot_id", how="left", validate="many_to_one"
    )
    broker_history["scheduled"] = broker_history["broker_response"].eq("scheduled_visit").astype(float)
    broker_history["accepted"] = broker_history["broker_response"].eq("accepted").astype(float)
    broker_history["rejected"] = broker_history["broker_response"].eq("rejected").astype(float)
    broker_history["no_response"] = broker_history["broker_response"].eq("no_response").astype(float)
    broker = broker_history.groupby("broker_id").agg(
        n_inquiries=("inquiry_id", "size"),
        scheduled_rate=("scheduled", "mean"),
        accepted_rate=("accepted", "mean"),
        rejected_rate=("rejected", "mean"),
        no_response_rate=("no_response", "mean"),
        mean_message_length=("message_length", "mean"),
        median_urgency=("urgency_days", "median"),
    ).reset_index()
    service = fit_profile(
        broker, family="broker_service_profile", categorical=[],
        numeric=["n_inquiries", "scheduled_rate", "accepted_rate", "rejected_rate", "no_response_rate", "mean_message_length", "median_urgency"],
        method="bisecting", k=3, prefix="BSV", seed=seed,
    )

    enriched = t1.copy()
    enriched["need_profile"] = assign_profile(need, enriched)
    enriched["dynamic_need_profile"] = assign_profile(dynamic, enriched)
    spot_assign = spots[["spot_id", "broker_id"]].copy()
    spot_assign["physical_profile"] = assign_profile(physical, spots)
    spot_assign["location_profile"] = assign_profile(location, spots)
    broker["broker_service_profile"] = assign_profile(service, broker)
    enriched = enriched.merge(spot_assign, on="spot_id", how="left", validate="many_to_one", suffixes=("", "_profile"))
    enriched = enriched.merge(broker[["broker_id", "broker_service_profile"]], on="broker_id", how="left", validate="many_to_one")
    profiles = {p.family: p for p in (need, dynamic, physical, location, service)}
    metrics = pd.DataFrame([{"family": family, **profile.metrics} for family, profile in profiles.items()])
    return enriched, profiles, metrics


def _wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denominator
    return center - margin, center + margin


def compatibility_cells(
    enriched: pd.DataFrame,
    split: str = "validation",
    min_n: int = 50,
    prior_strength: int = 20,
    families: list[str] | None = None,
) -> pd.DataFrame:
    data = enriched[enriched["split"].eq(split) & enriched["target_t1"].notna()].copy()
    global_rate = float(data["target_t1"].mean())
    families = families or ["dynamic_need_profile", "location_profile", "physical_profile", "broker_service_profile"]
    rows = []
    for size in (2, 3):
        for group_columns in combinations(families, size):
            for values, group in data.groupby(list(group_columns), dropna=False):
                if len(group) < min_n:
                    continue
                values = values if isinstance(values, tuple) else (values,)
                positives = int(group["target_t1"].sum())
                raw = positives / len(group)
                smooth = (positives + prior_strength * global_rate) / (len(group) + prior_strength)
                low, high = _wilson(positives, len(group))
                # One-sided normal approximation against the global rate, used only for multiplicity ranking.
                se = math.sqrt(max(1e-12, global_rate * (1 - global_rate) / len(group)))
                z_score = (raw - global_rate) / se
                p_value = 0.5 * math.erfc(z_score / math.sqrt(2))
                row = {
                    "interaction": " x ".join(group_columns), "n": len(group), "positives": positives,
                    "visit_rate": raw, "smoothed_rate": smooth, "lift_vs_global": smooth / global_rate,
                    "wilson_low": low, "wilson_high": high, "p_value_one_sided": p_value,
                }
                row.update(dict(zip(group_columns, values)))
                rows.append(row)
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["fdr_reject_10pct"] = multipletests(result["p_value_one_sided"], alpha=0.10, method="fdr_bh")[0]
    return result.sort_values(["lift_vs_global", "n"], ascending=[False, False]).reset_index(drop=True)
