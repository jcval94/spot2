from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from spot2_codexway.contracts import load_settings
from spot2_codexway.data import load_all
from spot2_codexway.evaluation import binary_metrics
from spot2_codexway.features import CLEAN_T1_FEATURES, LEAD_CATEGORICAL, INQUIRY_CATEGORICAL
from spot2_codexway.profiles import build_profiles

ROOT = Path(__file__).resolve().parents[1]
ABT = ROOT / "outputs" / "abt" / "abt_t1_first_inquiry.parquet"
OUTDIR = ROOT / "outputs" / "metrics" / "rule_search_300"
TARGET = "target_t1"
DROP_FEATURE = "days_from_lead_creation"
INTERACTION = "industrial_small_or_paid_interaction"
CLUSTERS = ["physical_profile", "location_profile", "broker_service_profile"]
TOP_RF_VARIABLES = 12
MAX_PREDICATES_PER_VARIABLE = 7
MIN_MONTH_N = 10
RNG_SEED = 42


# This search is deliberately rule/pivot based. RF is used only to prioritize
# which raw variables enter the combinatorial search; it does not score rules.
BASE_FEATURES = [f for f in CLEAN_T1_FEATURES if f != DROP_FEATURE] + [INTERACTION]
CATEGORICAL = [f for f in (LEAD_CATEGORICAL + INQUIRY_CATEGORICAL) if f in BASE_FEATURES]
NUMERIC = [f for f in BASE_FEATURES if f not in CATEGORICAL]


def preprocessing() -> ColumnTransformer:
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
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                NUMERIC,
            ),
        ]
    )


def fit_rf(train: pd.DataFrame) -> Pipeline:
    model = Pipeline(
        [
            ("preprocess", preprocessing()),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=800,
                    max_depth=6,
                    min_samples_leaf=20,
                    max_features="sqrt",
                    random_state=RNG_SEED,
                    n_jobs=1,
                ),
            ),
        ]
    )
    model.fit(train[BASE_FEATURES], train[TARGET].astype(int))
    return model


def rf_permutation_importance(model: Pipeline, validation: pd.DataFrame) -> pd.DataFrame:
    base_scores = model.predict_proba(validation[BASE_FEATURES])[:, 1]
    base_ap = average_precision_score(validation[TARGET].astype(int), base_scores)
    base_l10 = binary_metrics(validation[TARGET].astype(int), base_scores)["lift_top_10pct"]
    rng = np.random.default_rng(RNG_SEED)
    rows = []
    for feature in BASE_FEATURES:
        ap_drops, l10_drops = [], []
        for _ in range(5):
            shuffled = validation[BASE_FEATURES].copy()
            shuffled[feature] = rng.permutation(shuffled[feature].to_numpy())
            scores = model.predict_proba(shuffled)[:, 1]
            ap = average_precision_score(validation[TARGET].astype(int), scores)
            l10 = binary_metrics(validation[TARGET].astype(int), scores)["lift_top_10pct"]
            ap_drops.append(base_ap - ap)
            l10_drops.append(base_l10 - l10)
        rows.append(
            {
                "feature": feature,
                "rf_permutation_ap_drop": float(np.mean(ap_drops)),
                "rf_permutation_lift10_drop": float(np.mean(l10_drops)),
            }
        )
    out = pd.DataFrame(rows).sort_values(
        ["rf_permutation_ap_drop", "rf_permutation_lift10_drop"], ascending=False
    ).reset_index(drop=True)
    out["rf_rank"] = np.arange(1, len(out) + 1)
    return out


def add_standardized_numeric_columns(frame: pd.DataFrame, train: pd.DataFrame, numeric_features: list[str]) -> tuple[pd.DataFrame, dict]:
    result = frame.copy()
    metadata = {}
    for feature in numeric_features:
        train_values = pd.to_numeric(train[feature], errors="coerce")
        median = float(train_values.median())
        filled = train_values.fillna(median)
        mean = float(filled.mean())
        std = float(filled.std(ddof=0))
        if not np.isfinite(std) or std <= 1e-12:
            std = 1.0
        all_values = pd.to_numeric(result[feature], errors="coerce").fillna(median)
        zcol = f"__z__{feature}"
        result[zcol] = (all_values - mean) / std
        metadata[feature] = {"median_train": median, "mean_train": mean, "std_train": std, "z_column": zcol}
    return result, metadata


def month_arrays(frame: pd.DataFrame, split_filter: list[str] | None = None) -> dict[str, np.ndarray]:
    selected = frame if split_filter is None else frame[frame["split"].isin(split_filter)]
    months = pd.to_datetime(selected["prediction_timestamp"], utc=True).dt.strftime("%Y-%m")
    return {month: selected.index[months.eq(month)].to_numpy() for month in sorted(months.unique())}


def build_predicates(
    frame: pd.DataFrame,
    train: pd.DataFrame,
    candidate_variables: list[str],
    numeric_meta: dict,
) -> list[dict]:
    predicates: list[dict] = []
    train_idx = train.index

    for variable in candidate_variables:
        if variable in CLUSTERS or variable in CATEGORICAL or variable == INTERACTION:
            series = frame[variable].fillna("<missing>").astype(str)
            train_series = series.loc[train_idx]
            values = train_series.value_counts(dropna=False).head(MAX_PREDICATES_PER_VARIABLE).index.tolist()
            for value in values:
                mask = series.eq(str(value)).to_numpy()
                predicates.append(
                    {
                        "variable": variable,
                        "label": f"{variable}={value}",
                        "kind": "category",
                        "value": str(value),
                        "mask": mask,
                    }
                )
        else:
            zcol = numeric_meta[variable]["z_column"]
            z_train = frame.loc[train_idx, zcol].astype(float)
            cuts = np.unique(np.quantile(z_train, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]))
            if len(cuts) < 3:
                vals = sorted(pd.Series(np.round(z_train, 6)).unique())[:MAX_PREDICATES_PER_VARIABLE]
                for value in vals:
                    mask = np.isclose(frame[zcol].to_numpy(dtype=float), float(value))
                    predicates.append(
                        {
                            "variable": variable,
                            "label": f"z({variable})={value:.3f}",
                            "kind": "numeric_point",
                            "low": float(value),
                            "high": float(value),
                            "mask": mask,
                        }
                    )
            else:
                for i in range(len(cuts) - 1):
                    lo, hi = float(cuts[i]), float(cuts[i + 1])
                    if i == len(cuts) - 2:
                        mask = frame[zcol].ge(lo).to_numpy() & frame[zcol].le(hi).to_numpy()
                        label = f"{lo:.3f}<=z({variable})<={hi:.3f}"
                    else:
                        mask = frame[zcol].ge(lo).to_numpy() & frame[zcol].lt(hi).to_numpy()
                        label = f"{lo:.3f}<=z({variable})<{hi:.3f}"
                    predicates.append(
                        {
                            "variable": variable,
                            "label": label,
                            "kind": "numeric_z_bin",
                            "low": lo,
                            "high": hi,
                            "mask": mask,
                        }
                    )
    return predicates


def lift_for_indices(y: np.ndarray, mask: np.ndarray, indices: np.ndarray) -> tuple[int, float, float]:
    if len(indices) == 0:
        return 0, float("nan"), float("nan")
    m = mask[indices]
    n = int(m.sum())
    base_rate = float(y[indices].mean())
    if n == 0 or base_rate <= 0:
        return n, float("nan"), base_rate
    seg_rate = float(y[indices][m].mean())
    return n, seg_rate / base_rate, base_rate


def evaluate_rule(
    y: np.ndarray,
    mask: np.ndarray,
    discovery_months: dict[str, np.ndarray],
    validation_months: dict[str, np.ndarray],
    test_months: dict[str, np.ndarray],
) -> dict | None:
    disc = {}
    for month, idx in discovery_months.items():
        n, lift, _ = lift_for_indices(y, mask, idx)
        if n < MIN_MONTH_N or not np.isfinite(lift):
            return None
        disc[month] = {"n": n, "lift": lift}

    val = {}
    for month, idx in validation_months.items():
        n, lift, _ = lift_for_indices(y, mask, idx)
        if n < MIN_MONTH_N or not np.isfinite(lift):
            return None
        val[month] = {"n": n, "lift": lift}

    test = {}
    test_support_ok = True
    for month, idx in test_months.items():
        n, lift, _ = lift_for_indices(y, mask, idx)
        test_support_ok = test_support_ok and n >= MIN_MONTH_N and np.isfinite(lift)
        test[month] = {"n": n, "lift": lift}

    disc_lifts = np.array([v["lift"] for v in disc.values()], dtype=float)
    val_lifts = np.array([v["lift"] for v in val.values()], dtype=float)
    test_lifts = np.array([v["lift"] for v in test.values() if np.isfinite(v["lift"])], dtype=float)
    if len(test_lifts) != len(test):
        test_min = float("nan")
        test_mean = float("nan")
    else:
        test_min = float(test_lifts.min())
        test_mean = float(test_lifts.mean())

    return {
        "discovery_min_lift": float(disc_lifts.min()),
        "discovery_mean_lift": float(disc_lifts.mean()),
        "validation_min_lift": float(val_lifts.min()),
        "validation_mean_lift": float(val_lifts.mean()),
        "test_min_lift": test_min,
        "test_mean_lift": test_mean,
        "passes_discovery_all_months_gt1": bool((disc_lifts > 1.0).all()),
        "passes_validation_all_months_gt1": bool((val_lifts > 1.0).all()),
        "passes_test_support": bool(test_support_ok),
        "passes_test_all_months_gt1": bool(test_support_ok and len(test_lifts) == len(test) and (test_lifts > 1.0).all()),
        "discovery_total_n": int(mask[np.concatenate(list(discovery_months.values()))].sum()),
        "test_total_n": int(mask[np.concatenate(list(test_months.values()))].sum()),
        "discovery_month_detail": disc,
        "validation_month_detail": val,
        "test_month_detail": test,
    }


def flatten_row(row: dict, discovery_month_names: list[str], validation_month_names: list[str], test_month_names: list[str]) -> dict:
    flat = {k: v for k, v in row.items() if not k.endswith("_month_detail")}
    for month in discovery_month_names:
        detail = row["discovery_month_detail"].get(month, {})
        flat[f"disc_{month}_n"] = detail.get("n")
        flat[f"disc_{month}_lift"] = detail.get("lift")
    for month in validation_month_names:
        detail = row["validation_month_detail"].get(month, {})
        flat[f"val_{month}_n"] = detail.get("n")
        flat[f"val_{month}_lift"] = detail.get("lift")
    for month in test_month_names:
        detail = row["test_month_detail"].get(month, {})
        flat[f"test_{month}_n"] = detail.get("n")
        flat[f"test_{month}_lift"] = detail.get("lift")
    return flat


def run() -> None:
    settings = load_settings()
    abt = pd.read_parquet(ABT)
    tables = load_all(settings)
    enriched, profiles, profile_metrics = build_profiles(abt, tables["spots"], tables["inquiries"], seed=RNG_SEED)
    mature = enriched[enriched[TARGET].notna()].copy().reset_index(drop=True)
    mature[INTERACTION] = mature[INTERACTION].astype(int)

    train = mature[mature["split"].eq("train")].copy()
    validation = mature[mature["split"].eq("validation")].copy()
    test = mature[mature["split"].eq("test")].copy()

    rf = fit_rf(train)
    importance = rf_permutation_importance(rf, validation)
    top_rf = importance.head(TOP_RF_VARIABLES)["feature"].tolist()
    if INTERACTION not in top_rf:
        top_rf.append(INTERACTION)

    candidate_variables = []
    for variable in top_rf + CLUSTERS:
        if variable not in candidate_variables:
            candidate_variables.append(variable)

    mature, numeric_meta = add_standardized_numeric_columns(
        mature,
        train,
        [v for v in candidate_variables if v in NUMERIC and v != INTERACTION],
    )
    train = mature[mature["split"].eq("train")].copy()
    validation = mature[mature["split"].eq("validation")].copy()
    test = mature[mature["split"].eq("test")].copy()

    discovery_months = month_arrays(mature, ["train", "validation"])
    validation_months = month_arrays(mature, ["validation"])
    test_months = month_arrays(mature, ["test"])
    y = mature[TARGET].astype(int).to_numpy()

    predicates = build_predicates(mature, train, candidate_variables, numeric_meta)
    by_var = {}
    for i, predicate in enumerate(predicates):
        by_var.setdefault(predicate["variable"], []).append(i)

    rf_rank = importance.set_index("feature")["rf_rank"].to_dict()
    cluster_rank = {c: TOP_RF_VARIABLES + 10 + i for i, c in enumerate(CLUSTERS, start=1)}

    rows = []
    candidate_count = 0
    variables = candidate_variables
    for size in (1, 2, 3):
        for variable_tuple in combinations(variables, size):
            predicate_lists = [by_var[v] for v in variable_tuple]
            if size == 1:
                predicate_combos = ((a,) for a in predicate_lists[0])
            elif size == 2:
                predicate_combos = ((a, b) for a in predicate_lists[0] for b in predicate_lists[1])
            else:
                predicate_combos = ((a, b, c) for a in predicate_lists[0] for b in predicate_lists[1] for c in predicate_lists[2])

            for combo in predicate_combos:
                candidate_count += 1
                mask = np.ones(len(mature), dtype=bool)
                labels = []
                for idx in combo:
                    mask &= predicates[idx]["mask"]
                    labels.append(predicates[idx]["label"])
                evaluation = evaluate_rule(y, mask, discovery_months, validation_months, test_months)
                if evaluation is None:
                    continue
                rank_values = [rf_rank.get(v, cluster_rank.get(v, 999)) for v in variable_tuple]
                row = {
                    "rule": " AND ".join(labels),
                    "n_variables": size,
                    "variables": " | ".join(variable_tuple),
                    "max_rf_priority_rank": int(max(rank_values)),
                    "mean_rf_priority_rank": float(np.mean(rank_values)),
                    **evaluation,
                }
                rows.append(row)

    result = pd.DataFrame(rows)
    if result.empty:
        raise RuntimeError("No rules survived minimum monthly support")

    # Ranking is strictly pre-test. Test columns are diagnostic only and never enter sort order.
    result = result.sort_values(
        [
            "passes_validation_all_months_gt1",
            "passes_discovery_all_months_gt1",
            "validation_min_lift",
            "discovery_min_lift",
            "validation_mean_lift",
            "mean_rf_priority_rank",
            "discovery_total_n",
        ],
        ascending=[False, False, False, False, False, True, False],
    ).reset_index(drop=True)
    result["discovery_rank"] = np.arange(1, len(result) + 1)

    # Preserve a test-pass view without using test to order candidates.
    stable_test = result[result["passes_test_all_months_gt1"]].copy()
    stable_all = result[
        result["passes_discovery_all_months_gt1"]
        & result["passes_validation_all_months_gt1"]
        & result["passes_test_all_months_gt1"]
    ].copy()

    OUTDIR.mkdir(parents=True, exist_ok=True)
    flat = pd.DataFrame(
        [
            flatten_row(r.to_dict(), list(discovery_months), list(validation_months), list(test_months))
            for _, r in result.iterrows()
        ]
    )
    flat.to_csv(OUTDIR / "all_ranked_rules.csv", index=False)
    flat.head(300).to_csv(OUTDIR / "top_300_discovery_ranked.csv", index=False)

    stable_test_flat = flat[flat["passes_test_all_months_gt1"].astype(bool)].copy()
    stable_test_flat.head(300).to_csv(OUTDIR / "top_300_that_also_pass_test.csv", index=False)

    stable_all_ranks = set(stable_all["discovery_rank"].astype(int))
    stable_all_flat = flat[flat["discovery_rank"].astype(int).isin(stable_all_ranks)].copy()
    stable_all_flat.head(300).to_csv(OUTDIR / "top_300_all_periods_gt1.csv", index=False)

    importance.to_csv(OUTDIR / "rf_permutation_importance.csv", index=False)
    profile_metrics.to_csv(OUTDIR / "cluster_profile_metrics.csv", index=False)
    pd.DataFrame(
        [
            {k: v for k, v in p.items() if k != "mask"}
            for p in predicates
        ]
    ).to_csv(OUTDIR / "predicate_dictionary.csv", index=False)

    summary = {
        "methodology": {
            "target": TARGET,
            "dropped": DROP_FEATURE,
            "standardization": "all numeric rule inputs are z-scored with train-only mean/std after train-median imputation; RF one-hot indicators variance-scaled",
            "rule_metric": "monthly segment lift = segment target rate / whole-month target rate",
            "rf_role": "prioritize raw variables only; no model score used in rule ranking",
            "clusters_included": CLUSTERS,
            "cluster_note": "only previously stable physical/location/broker-service profiles included",
            "max_variables_per_rule": 3,
            "min_segment_n_each_month": MIN_MONTH_N,
            "ranking_uses_test": False,
            "ranking": "validation all-month pass, discovery all-month pass, validation min lift, discovery min lift, validation mean lift, RF priority, support",
            "test": "diagnostic only",
        },
        "counts": {
            "raw_candidates_considered": candidate_count,
            "rules_surviving_monthly_support": int(len(result)),
            "rules_passing_discovery_all_months_gt1": int(result["passes_discovery_all_months_gt1"].sum()),
            "rules_passing_validation_all_months_gt1": int(result["passes_validation_all_months_gt1"].sum()),
            "rules_that_also_pass_test_all_months_gt1": int(result["passes_test_all_months_gt1"].sum()),
            "rules_passing_discovery_validation_and_test_all_months_gt1": int(len(stable_all)),
        },
        "candidate_variables": candidate_variables,
        "top_rf_importance": importance.head(TOP_RF_VARIABLES).to_dict(orient="records"),
        "cluster_metrics": profile_metrics[profile_metrics["family"].isin(CLUSTERS)].to_dict(orient="records"),
        "top_20_discovery_ranked": [
            {k: v for k, v in r.items() if not k.endswith("_month_detail")}
            for r in result.head(20).to_dict(orient="records")
        ],
        "top_20_all_periods_gt1": [
            {k: v for k, v in r.items() if not k.endswith("_month_detail")}
            for r in stable_all.head(20).to_dict(orient="records")
        ],
    }
    (OUTDIR / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
