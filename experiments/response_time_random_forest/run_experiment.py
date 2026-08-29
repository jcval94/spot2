from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "candidate" / "csv"
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
WINDOW_DAYS = 30
FAST_HOURS = 6
SLOW_HOURS = 24
CF_FAST_HOURS = 2
CF_SLOW_HOURS = 36

LEAD_CAT = [
    "user_type", "company_size", "industry", "search_sector", "search_modality",
    "preferred_state", "preferred_municipality", "preferred_corridor", "source",
]
LEAD_NUM = [
    "target_area_sqm",
    "min_budget_mxn_rent_monthly", "max_budget_mxn_rent_monthly",
    "min_budget_mxn_sale_total", "max_budget_mxn_sale_total",
]
INQUIRY_CAT = ["channel", "asked_visit", "inquiry_weekday"]
INQUIRY_NUM = [
    "message_length", "requested_area_sqm",
    "requested_budget_mxn_rent_monthly", "requested_budget_mxn_sale_total",
    "urgency_days", "inquiry_hour",
]
SPOT_CAT = [
    "spot_sector_name", "spot_type_name", "spot_state", "spot_municipality",
    "spot_corridor", "spot_region", "spot_modality",
]
SPOT_NUM = [
    "spot_lat", "spot_lon", "spot_area_sqm",
    "spot_price_sqm_mxn_rent", "spot_price_sqm_mxn_sale",
    "spot_price_total_mxn_rent", "spot_price_total_mxn_sale",
    "spot_maintenance_cost_mxn",
]
ENGINEERED_NUM = ["area_fit_ratio", "rent_budget_fit", "sale_budget_fit"]
BASE_CAT = LEAD_CAT + INQUIRY_CAT + SPOT_CAT
BASE_NUM = LEAD_NUM + INQUIRY_NUM + SPOT_NUM + ENGINEERED_NUM
RESPONSE_FEATURE = "response_time_log1p"

FORBIDDEN = {
    "lead_score_internal", "broker_response", "broker_response_hours",
    "total_inquiries", "total_views", "days_on_market", "is_active",
    "prior_searches", "prior_inquiries", "has_converted_before",
}


def safe_ratio(a: pd.Series, b: pd.Series) -> pd.Series:
    b = b.replace(0, np.nan)
    return a / b


def metric_bundle(y_true: pd.Series, pred: np.ndarray) -> dict:
    y = np.asarray(y_true, dtype=int)
    p = np.clip(np.asarray(pred, dtype=float), 1e-8, 1 - 1e-8)
    base = float(y.mean())
    order = np.argsort(-p)
    k = max(1, int(math.ceil(len(y) * 0.10)))
    top_rate = float(y[order[:k]].mean())
    return {
        "n": int(len(y)),
        "positive_rate": base,
        "roc_auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else math.nan,
        "average_precision": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "lift_top_10pct": float(top_rate / base) if base > 0 else math.nan,
    }


def temporal_split(df: pd.DataFrame, time_col: str, frac: float = 0.80):
    d = df.sort_values(time_col).reset_index(drop=True)
    cut = max(1, min(len(d) - 1, int(len(d) * frac)))
    return d.iloc[:cut].copy(), d.iloc[cut:].copy(), d.iloc[cut][time_col]


def load_data():
    leads = pd.read_csv(DATA / "leads.csv", parse_dates=["created_at"])
    inquiries = pd.read_csv(DATA / "inquiries.csv", parse_dates=["inquiry_at"])
    spots = pd.read_csv(DATA / "spots.csv", parse_dates=["created_at"])
    return leads, inquiries, spots


def build_joined_inquiries(leads, inquiries, spots):
    spot_cols = [
        "spot_id", "sector_name", "type_name", "state", "municipality", "corridor",
        "region", "lat", "lon", "area_sqm", "price_sqm_mxn_rent",
        "price_sqm_mxn_sale", "price_total_mxn_rent", "price_total_mxn_sale",
        "maintenance_cost_mxn", "modality",
    ]
    spot = spots[spot_cols].rename(
        columns={c: f"spot_{c}" for c in spot_cols if c != "spot_id"}
    )

    d = inquiries.merge(leads, on="lead_id", how="left", suffixes=("", "_lead"))
    d = d.merge(spot, on="spot_id", how="left")

    d["inquiry_weekday"] = d["inquiry_at"].dt.day_name()
    d["inquiry_hour"] = d["inquiry_at"].dt.hour
    d["area_fit_ratio"] = safe_ratio(d["requested_area_sqm"], d["spot_area_sqm"])
    d["rent_budget_fit"] = safe_ratio(
        d["requested_budget_mxn_rent_monthly"], d["spot_price_total_mxn_rent"]
    )
    d["sale_budget_fit"] = safe_ratio(
        d["requested_budget_mxn_sale_total"], d["spot_price_total_mxn_sale"]
    )
    d[RESPONSE_FEATURE] = np.log1p(d["broker_response_hours"].clip(lower=0))
    return d


def make_immediate_dataset(joined):
    d = joined[joined["broker_response_hours"].notna()].copy()
    d["target"] = d["broker_response"].eq("scheduled_visit").astype(int)
    d["analysis_target"] = "same_inquiry_scheduled_visit"
    return d


def make_future_dataset(joined):
    max_observed = joined["inquiry_at"].max()
    censor_cutoff = max_observed - pd.Timedelta(days=WINDOW_DAYS)

    first = (
        joined.sort_values(["lead_id", "inquiry_at", "inquiry_id"])
        .drop_duplicates("lead_id", keep="first")
        .copy()
    )
    first = first[
        first["broker_response_hours"].notna()
        & (first["inquiry_at"] <= censor_cutoff)
    ].copy()

    future = joined[
        ["lead_id", "inquiry_id", "inquiry_at", "broker_response"]
    ].merge(
        first[["lead_id", "inquiry_id", "inquiry_at"]].rename(
            columns={
                "inquiry_id": "first_inquiry_id",
                "inquiry_at": "first_inquiry_at",
            }
        ),
        on="lead_id",
        how="inner",
    )
    future["delta_days"] = (
        future["inquiry_at"] - future["first_inquiry_at"]
    ).dt.total_seconds() / 86400.0
    future["future_success"] = (
        future["broker_response"].eq("scheduled_visit")
        & (future["inquiry_id"] != future["first_inquiry_id"])
        & future["delta_days"].between(0, WINDOW_DAYS, inclusive="both")
    )
    target = future.groupby("lead_id", as_index=False)["future_success"].max()

    first = first.merge(target, on="lead_id", how="left")
    first["target"] = first["future_success"].fillna(False).astype(int)
    first["analysis_target"] = "future_scheduled_visit_30d_after_first_inquiry"
    return first.drop(columns=["future_success"])


def make_pipeline(cat_cols, num_cols):
    prep = ColumnTransformer(
        transformers=[
            (
                "cat",
                Pipeline([
                    ("impute", SimpleImputer(strategy="most_frequent")),
                    (
                        "onehot",
                        OneHotEncoder(
                            handle_unknown="ignore",
                            min_frequency=10,
                            sparse_output=True,
                        ),
                    ),
                ]),
                cat_cols,
            ),
            (
                "num",
                Pipeline([("impute", SimpleImputer(strategy="median"))]),
                num_cols,
            ),
        ],
        remainder="drop",
    )
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=25,
        max_features="sqrt",
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )
    return Pipeline([("prep", prep), ("rf", rf)])


def fit_variant(train, test, include_response):
    cat = list(BASE_CAT)
    num = list(BASE_NUM) + ([RESPONSE_FEATURE] if include_response else [])
    used = set(cat + num)
    assert not (used & FORBIDDEN), f"Forbidden features found: {used & FORBIDDEN}"

    model = make_pipeline(cat, num)
    model.fit(train[cat + num], train["target"])
    pred = model.predict_proba(test[cat + num])[:, 1]
    return model, pred, metric_bundle(test["target"], pred), cat, num


def raw_permutation_importance(model, X, y, features, scoring, repeats=5):
    result = permutation_importance(
        model,
        X[features],
        y,
        scoring=scoring,
        n_repeats=repeats,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    return pd.DataFrame(
        {
            "feature": features,
            f"{scoring}_drop_mean": result.importances_mean,
            f"{scoring}_drop_std": result.importances_std,
        }
    )


def counterfactual_predictions(model, X, features, hours):
    z = X[features].copy()
    z[RESPONSE_FEATURE] = np.log1p(float(hours))
    return model.predict_proba(z)[:, 1]


def add_segment_columns(d):
    out = d.copy()
    out["urgency_bucket"] = pd.cut(
        out["urgency_days"],
        bins=[-np.inf, 7, 30, 90, np.inf],
        labels=["<=7d", "8-30d", "31-90d", ">90d"],
    ).astype("string").fillna("missing")
    out["message_length_bucket"] = pd.cut(
        out["message_length"],
        bins=[-np.inf, 149, 299, np.inf],
        labels=["<150", "150-299", ">=300"],
    ).astype("string").fillna("missing")
    return out


def subgroup_analysis(model, test, features, min_n=50):
    test = add_segment_columns(test).reset_index(drop=True)
    p2 = counterfactual_predictions(model, test, features, CF_FAST_HOURS)
    p36 = counterfactual_predictions(model, test, features, CF_SLOW_HOURS)

    dimensions = [
        "channel", "asked_visit", "user_type", "company_size", "search_sector",
        "search_modality", "source", "urgency_bucket", "message_length_bucket",
        "spot_region", "spot_modality",
    ]
    rows = []
    rng = np.random.default_rng(RANDOM_STATE)

    for dim in dimensions:
        for group, idx in test.groupby(dim, dropna=False).groups.items():
            idx = np.asarray(list(idx), dtype=int)
            if len(idx) < min_n:
                continue

            sub = test.loc[idx].copy()
            y = sub["target"].to_numpy()
            base_pred = model.predict_proba(sub[features])[:, 1]
            if len(np.unique(y)) == 2:
                base_auc = roc_auc_score(y, base_pred)
                drops = []
                for _ in range(4):
                    xp = sub[features].copy()
                    xp[RESPONSE_FEATURE] = rng.permutation(
                        xp[RESPONSE_FEATURE].to_numpy()
                    )
                    pp = model.predict_proba(xp)[:, 1]
                    drops.append(base_auc - roc_auc_score(y, pp))
                perm_auc_drop = float(np.mean(drops))
            else:
                perm_auc_drop = math.nan

            fast = sub[sub["broker_response_hours"] <= FAST_HOURS]
            slow = sub[sub["broker_response_hours"] > SLOW_HOURS]
            rows.append(
                {
                    "dimension": dim,
                    "group": str(group),
                    "n": int(len(sub)),
                    "positive_rate": float(sub["target"].mean()),
                    "observed_fast_n": int(len(fast)),
                    "observed_fast_rate": (
                        float(fast["target"].mean()) if len(fast) else math.nan
                    ),
                    "observed_slow_n": int(len(slow)),
                    "observed_slow_rate": (
                        float(slow["target"].mean()) if len(slow) else math.nan
                    ),
                    "model_p_2h": float(np.mean(p2[idx])),
                    "model_p_36h": float(np.mean(p36[idx])),
                    "model_2h_minus_36h_pp": float(
                        100 * np.mean(p2[idx] - p36[idx])
                    ),
                    "response_time_permutation_auc_drop": perm_auc_drop,
                }
            )
    return pd.DataFrame(rows)


def extract_response_splits(model):
    prep = model.named_steps["prep"]
    forest = model.named_steps["rf"]
    names = np.asarray(prep.get_feature_names_out())
    matches = np.flatnonzero(np.char.find(names.astype(str), RESPONSE_FEATURE) >= 0)
    if len(matches) != 1:
        return pd.DataFrame()
    response_idx = int(matches[0])

    rows = []
    for tree_id, estimator in enumerate(forest.estimators_):
        tree = estimator.tree_

        def walk(node, depth, path):
            if tree.children_left[node] == tree.children_right[node]:
                return
            fidx = int(tree.feature[node])
            fname = str(names[fidx])
            threshold = float(tree.threshold[node])
            left = int(tree.children_left[node])
            right = int(tree.children_right[node])

            if fidx == response_idx:
                parent_features = [p["feature"] for p in path[-3:]]
                rows.append(
                    {
                        "tree_id": tree_id,
                        "node_id": node,
                        "depth": depth,
                        "threshold_hours": float(np.expm1(threshold)),
                        "node_samples": int(tree.n_node_samples[node]),
                        "parent_1": parent_features[-1] if parent_features else "",
                        "parent_2": parent_features[-2] if len(parent_features) >= 2 else "",
                        "parent_3": parent_features[-3] if len(parent_features) >= 3 else "",
                    }
                )

            walk(
                left,
                depth + 1,
                path + [{"feature": fname, "op": "<=", "threshold": threshold}],
            )
            walk(
                right,
                depth + 1,
                path + [{"feature": fname, "op": ">", "threshold": threshold}],
            )

        walk(0, 0, [])
    return pd.DataFrame(rows)


def plot_importance(importance, target_name):
    col = "roc_auc_drop_mean"
    d = importance.sort_values(col, ascending=False).head(20).sort_values(col)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(d["feature"], d[col])
    ax.set_xlabel("ROC AUC drop after permutation")
    ax.set_title(f"Random Forest permutation importance — {target_name}")
    fig.tight_layout()
    fig.savefig(OUT / f"{target_name}_permutation_importance.png", dpi=160)
    plt.close(fig)


def plot_counterfactual(model, test, features, target_name):
    grid = [1, 2, 6, 12, 24, 36, 48, 72]
    means = [
        float(np.mean(counterfactual_predictions(model, test, features, h)))
        for h in grid
    ]
    pd.DataFrame(
        {"response_hours": grid, "mean_predicted_probability": means}
    ).to_csv(OUT / f"{target_name}_response_curve.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(grid, means, marker="o")
    ax.set_xlabel("Counterfactual broker response hours")
    ax.set_ylabel("Mean predicted probability")
    ax.set_title(f"RF response-time sensitivity — {target_name}")
    fig.tight_layout()
    fig.savefig(OUT / f"{target_name}_response_curve.png", dpi=160)
    plt.close(fig)


def analyze_dataset(df, target_name):
    train, test, cutoff = temporal_split(df, "inquiry_at")

    base_model, base_pred, base_metrics, base_cat, base_num = fit_variant(
        train, test, include_response=False
    )
    full_model, full_pred, full_metrics, full_cat, full_num = fit_variant(
        train, test, include_response=True
    )

    features = full_cat + full_num
    importance = raw_permutation_importance(
        full_model, test, test["target"], features, "roc_auc"
    )
    importance["target"] = target_name
    importance["rank_auc"] = (
        importance["roc_auc_drop_mean"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    importance.to_csv(
        OUT / f"{target_name}_feature_importance.csv", index=False
    )

    subgroups = subgroup_analysis(full_model, test, features)
    subgroups["target"] = target_name
    subgroups.to_csv(
        OUT / f"{target_name}_response_subgroups.csv", index=False
    )

    splits = extract_response_splits(full_model)
    if not splits.empty:
        splits["target"] = target_name
    splits.to_csv(OUT / f"{target_name}_response_tree_splits.csv", index=False)

    plot_importance(importance, target_name)
    plot_counterfactual(full_model, test, features, target_name)

    response_row = importance[importance["feature"].eq(RESPONSE_FEATURE)]
    response_importance = (
        response_row.iloc[0].to_dict() if len(response_row) else {}
    )

    p2 = counterfactual_predictions(full_model, test, features, CF_FAST_HOURS)
    p36 = counterfactual_predictions(full_model, test, features, CF_SLOW_HOURS)

    return {
        "target": target_name,
        "cutoff": str(cutoff),
        "base": base_metrics,
        "with_response_time": full_metrics,
        "delta": {
            k: float(full_metrics[k] - base_metrics[k])
            for k in ["roc_auc", "average_precision", "brier", "lift_top_10pct"]
        },
        "response_feature_importance": response_importance,
        "counterfactual": {
            "mean_p_2h": float(np.mean(p2)),
            "mean_p_36h": float(np.mean(p36)),
            "mean_2h_minus_36h_pp": float(100 * np.mean(p2 - p36)),
        },
        "response_tree_split_count": int(len(splits)),
        "response_tree_split_depths": (
            splits["depth"].value_counts().sort_index().to_dict()
            if len(splits)
            else {}
        ),
        "strongest_model_segments": (
            subgroups.assign(
                abs_delta=subgroups["model_2h_minus_36h_pp"].abs()
            )
            .sort_values("abs_delta", ascending=False)
            .drop(columns=["abs_delta"])
            .head(12)
            .to_dict(orient="records")
        ),
    }


def main():
    leads, inquiries, spots = load_data()
    joined = build_joined_inquiries(leads, inquiries, spots)

    immediate = make_immediate_dataset(joined)
    future = make_future_dataset(joined)

    results = [
        analyze_dataset(immediate, "immediate_scheduled_visit"),
        analyze_dataset(future, "future_visit_30d"),
    ]
    payload = {
        "method": {
            "model": "RandomForestClassifier",
            "n_estimators": 300,
            "max_depth": 10,
            "min_samples_leaf": 25,
            "validation": "80/20 temporal split",
            "response_feature": RESPONSE_FEATURE,
            "notes": [
                "broker_response_hours is used only in a diagnostic model after response time exists",
                "lead_score_internal and current aggregate listing fields are excluded",
                "future_visit_30d excludes the first inquiry itself",
            ],
        },
        "results": results,
    }
    (OUT / "results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    summary_rows = []
    for r in results:
        summary_rows.append(
            {
                "target": r["target"],
                "base_auc": r["base"]["roc_auc"],
                "with_hours_auc": r["with_response_time"]["roc_auc"],
                "delta_auc": r["delta"]["roc_auc"],
                "base_ap": r["base"]["average_precision"],
                "with_hours_ap": r["with_response_time"]["average_precision"],
                "delta_ap": r["delta"]["average_precision"],
                "counterfactual_2h_minus_36h_pp": r["counterfactual"][
                    "mean_2h_minus_36h_pp"
                ],
                "response_tree_split_count": r["response_tree_split_count"],
                "response_permutation_auc_drop": r[
                    "response_feature_importance"
                ].get("roc_auc_drop_mean", math.nan),
                "response_permutation_rank": r[
                    "response_feature_importance"
                ].get("rank_auc", math.nan),
            }
        )
    pd.DataFrame(summary_rows).to_csv(OUT / "summary_metrics.csv", index=False)

    report_lines = [
        "# Random Forest: broker response-time interaction experiment",
        "",
        "This experiment tests response time jointly with lead, inquiry and spot variables.",
        "It deliberately distinguishes two targets:",
        "",
        "1. immediate_scheduled_visit: whether the same inquiry response is a scheduled visit.",
        "2. future_visit_30d: whether a later inquiry becomes a scheduled visit within 30 days after the first inquiry; the first inquiry itself is excluded.",
        "",
        "For each target, compare a leakage-safe multivariable Random Forest without response time against the same model plus log1p(broker_response_hours).",
        "The response-time model is diagnostic only: response hours do not exist before the broker responds.",
        "",
        "## Results",
        "",
        "| Target | Base AUC | + hours AUC | Δ AUC | Permutation AUC drop for hours | 2h vs 36h model delta |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        pi = r["response_feature_importance"].get("roc_auc_drop_mean", math.nan)
        report_lines.append(
            f"| {r['target']} | {r['base']['roc_auc']:.3f} | "
            f"{r['with_response_time']['roc_auc']:.3f} | "
            f"{r['delta']['roc_auc']:+.3f} | {pi:+.4f} | "
            f"{r['counterfactual']['mean_2h_minus_36h_pp']:+.2f} pp |"
        )

    report_lines += [
        "",
        "## How to interpret feature importance",
        "",
        "Do not rely on Random Forest impurity importance alone. Continuous variables can receive many possible split points and look important even when they do not improve out-of-sample ranking.",
        "The primary evidence for broker_response_hours is therefore:",
        "",
        "- incremental temporal test performance when response time is added,",
        "- raw-feature permutation importance on the temporal test set,",
        "- counterfactual sensitivity at 2h versus 36h,",
        "- subgroup-specific permutation/sensitivity,",
        "- and the tree paths where response time is actually used.",
        "",
        "See the CSV files in this results directory for subgroup and tree-branch detail.",
    ]
    (OUT / "report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()
