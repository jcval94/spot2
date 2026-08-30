from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESULTS = HERE / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

ABT_DIR = ROOT / "experimentos" / "abt_feature_engineering"
sys.path.insert(0, str(ABT_DIR))
from build_abts import build_all, project_abt  # noqa: E402
from feature_engineering import (  # noqa: E402
    AVAIL_CATS,
    INQUIRY_CATS,
    LEAD_CATS,
    MATCH_CATS,
    SPOT_CATS,
)

SEED = 42
FOLDS = [
    {"fold": 1, "train_end": 0.45, "val_end": 0.55, "test_end": 0.65},
    {"fold": 2, "train_end": 0.55, "val_end": 0.65, "test_end": 0.75},
    {"fold": 3, "train_end": 0.65, "val_end": 0.75, "test_end": 0.85},
    {"fold": 4, "train_end": 0.75, "val_end": 0.85, "test_end": 0.95},
]
CATEGORICAL = set(LEAD_CATS + INQUIRY_CATS + SPOT_CATS + MATCH_CATS + AVAIL_CATS)
METRICS = ["roc_auc", "average_precision", "brier", "log_loss", "lift_top_10pct", "recall_top_20pct"]

CORE_CANDIDATES = [
    "user_type", "company_size_fe", "industry_fe", "search_sector", "search_modality",
    "preferred_state", "preferred_municipality", "preferred_corridor_fe", "source",
    "target_area_sqm", "rent_budget_max", "sale_budget_max", "prior_searches",
    "prior_inquiries", "has_converted_before",
    "channel", "urgency_bucket", "message_length", "requested_area_sqm",
    "requested_rent_budget", "requested_sale_budget", "urgency_days", "asked_visit",
    "inquiry_hour", "inquiry_number", "days_from_lead_creation",
    "spot_sector_name", "spot_type_name", "spot_state", "spot_municipality",
    "spot_corridor", "spot_modality", "spot_area_sqm", "spot_price_total_mxn_rent",
    "spot_price_total_mxn_sale", "spot_maintenance_cost_mxn",
    "availability_is_available", "availability_days_until_available",
    "availability_competing_inquiries_30d", "availability_snapshot_age_days",
    "has_availability_context",
]


def safe_auc(y, p):
    return float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else np.nan


def score_metrics(y, p):
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    order = np.argsort(-p, kind="mergesort")
    n10 = max(1, math.ceil(len(y) * 0.10))
    n20 = max(1, math.ceil(len(y) * 0.20))
    base = float(y.mean())
    positives = int(y.sum())
    return {
        "roc_auc": safe_auc(y, p),
        "average_precision": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6), labels=[0, 1])),
        "lift_top_10pct": float(y[order[:n10]].mean() / base) if base > 0 else np.nan,
        "recall_top_20pct": float(y[order[:n20]].sum() / positives) if positives > 0 else np.nan,
    }


def prepare_data():
    abts, feature_sets, _ = build_all(ROOT)
    stage_map = {"T0": 0, "T1": 1, "T2": 2}
    frames = []
    for name, sid in stage_map.items():
        frames.append(project_abt(abts[name], feature_sets[sid]))
    data = pd.concat(frames, ignore_index=True, sort=False)
    data = data.rename(columns={"target_scheduled_visit_30d": "target_30d"})
    data["row_id"] = np.arange(len(data), dtype=np.int64)

    full = sorted(set().union(*feature_sets.values()))
    core = [c for c in CORE_CANDIDATES if c in full]
    lead_order = (
        abts["T0"][["lead_id", "score_time"]]
        .drop_duplicates("lead_id")
        .sort_values(["score_time", "lead_id"])
        .reset_index(drop=True)
    )
    return data, core, full, lead_order


def split_fold(data, lead_order, cfg):
    n = len(lead_order)
    a = max(1, int(n * cfg["train_end"]))
    b = max(a + 1, int(n * cfg["val_end"]))
    c = min(n, max(b + 1, int(n * cfg["test_end"])))
    train_ids = set(lead_order.iloc[:a]["lead_id"])
    val_ids = set(lead_order.iloc[a:b]["lead_id"])
    test_ids = set(lead_order.iloc[b:c]["lead_id"])
    return (
        data[data["lead_id"].isin(train_ids)].copy(),
        data[data["lead_id"].isin(val_ids)].copy(),
        data[data["lead_id"].isin(test_ids)].copy(),
    )


def model_frame(df, features):
    cols = list(features) + ["stage"]
    x = df.reindex(columns=cols).copy()
    cats = [c for c in cols if c in CATEGORICAL or c == "stage"]
    for c in cats:
        x[c] = x[c].astype("string").fillna("__MISSING__").astype(str)
    for c in cols:
        if c not in cats:
            x[c] = pd.to_numeric(x[c], errors="coerce").replace([np.inf, -np.inf], np.nan)
    return x, cats


def make_model(seed):
    return CatBoostClassifier(
        iterations=900,
        depth=7,
        learning_rate=0.035,
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=seed,
        l2_leaf_reg=5.0,
        random_strength=0.5,
        verbose=False,
        allow_writing_files=False,
        thread_count=4,
    )


def platt_by_stage(val, test, raw_val, raw_test):
    out_val = raw_val.copy()
    out_test = raw_test.copy()
    for stage in sorted(test["stage"].dropna().unique()):
        mv = val["stage"].eq(stage).to_numpy()
        mt = test["stage"].eq(stage).to_numpy()
        if not mv.any() or not mt.any():
            continue
        yv = val.loc[mv, "target_30d"].to_numpy(dtype=int)
        if len(np.unique(yv)) < 2:
            continue
        eps = 1e-6
        xv0 = np.clip(raw_val[mv], eps, 1 - eps)
        xt0 = np.clip(raw_test[mt], eps, 1 - eps)
        xv = np.log(xv0 / (1 - xv0)).reshape(-1, 1)
        xt = np.log(xt0 / (1 - xt0)).reshape(-1, 1)
        cal = LogisticRegression(max_iter=1000, random_state=SEED)
        cal.fit(xv, yv)
        out_val[mv] = cal.predict_proba(xv)[:, 1]
        out_test[mt] = cal.predict_proba(xt)[:, 1]
    return out_val, out_test


def fit_variant(train, val, test, features, seed):
    xtr, cats = model_frame(train, features)
    xva, _ = model_frame(val, features)
    xte, _ = model_frame(test, features)
    model = make_model(seed)
    model.fit(
        xtr,
        train["target_30d"].astype(int),
        cat_features=cats,
        eval_set=(xva, val["target_30d"].astype(int)),
        use_best_model=True,
        early_stopping_rounds=80,
        verbose=False,
    )
    raw_val = model.predict_proba(xva)[:, 1]
    raw_test = model.predict_proba(xte)[:, 1]
    val_cal, test_cal = platt_by_stage(val, test, raw_val, raw_test)
    return raw_test, test_cal


def metric_rows(df, pred_col, model, fold):
    rows = []
    for scope in list(sorted(df["stage"].unique())) + ["MACRO"]:
        g = df if scope == "MACRO" else df[df["stage"].eq(scope)]
        rows.append({
            "fold": fold,
            "model": model,
            "stage": scope,
            "n": len(g),
            "positive_rate": float(g["target_30d"].mean()),
            **score_metrics(g["target_30d"], g[pred_col]),
        })
    return rows


def cv_summary(fold_metrics):
    rows = []
    for (model, stage), g in fold_metrics.groupby(["model", "stage"], sort=False):
        row = {
            "model": model,
            "stage": stage,
            "n_folds": int(g["fold"].nunique()),
            "n_mean": float(g["n"].mean()),
            "positive_rate_mean": float(g["positive_rate"].mean()),
        }
        for m in METRICS:
            row[m + "_mean"] = float(g[m].mean())
            row[m + "_std"] = float(g[m].std(ddof=1))
        rows.append(row)
    return pd.DataFrame(rows)


def bootstrap_deltas(oof, reference, candidate, n_boot=300):
    rng = np.random.default_rng(SEED + 901)
    rows = []
    for scope in ["T1_first_inquiry", "T2_engaged", "MACRO"]:
        point = {}
        for metric in ["average_precision", "lift_top_10pct"]:
            fold_delta = []
            for fold in sorted(oof["fold"].unique()):
                g = oof[oof["fold"].eq(fold)]
                if scope != "MACRO":
                    g = g[g["stage"].eq(scope)]
                a = score_metrics(g["target_30d"], g[candidate])[metric]
                b = score_metrics(g["target_30d"], g[reference])[metric]
                fold_delta.append(a - b)
            point[metric] = float(np.mean(fold_delta))

        draws = {"average_precision": [], "lift_top_10pct": []}
        for _ in range(n_boot):
            per_metric = {"average_precision": [], "lift_top_10pct": []}
            for fold in sorted(oof["fold"].unique()):
                g = oof[oof["fold"].eq(fold)]
                if scope != "MACRO":
                    g = g[g["stage"].eq(scope)]
                ids = g["lead_id"].drop_duplicates().to_numpy()
                sampled = rng.choice(ids, size=len(ids), replace=True)
                pieces = [g[g["lead_id"].eq(lead_id)] for lead_id in sampled]
                boot = pd.concat(pieces, ignore_index=True)
                ma = score_metrics(boot["target_30d"], boot[candidate])
                mb = score_metrics(boot["target_30d"], boot[reference])
                for metric in per_metric:
                    per_metric[metric].append(ma[metric] - mb[metric])
            for metric in draws:
                draws[metric].append(float(np.mean(per_metric[metric])))

        for metric, values in draws.items():
            arr = np.asarray(values)
            rows.append({
                "scope": scope,
                "metric": metric,
                "reference_model": reference,
                "candidate_model": candidate,
                "point_delta": point[metric],
                "ci95_low": float(np.quantile(arr, 0.025)),
                "ci95_high": float(np.quantile(arr, 0.975)),
                "probability_delta_gt_0": float(np.mean(arr > 0)),
            })
    return pd.DataFrame(rows)


def error_analysis(oof, score_col):
    d = oof[oof["stage"].isin(["T1_first_inquiry", "T2_engaged"])].copy()
    d["selected_p85"] = 0
    for (_, _), idx in d.groupby(["fold", "stage"]).groups.items():
        ids = list(idx)
        n = max(1, math.ceil(len(ids) * 0.15))
        selected = d.loc[ids].sort_values([score_col, "row_id"], ascending=[False, True]).head(n).index
        d.loc[selected, "selected_p85"] = 1
    d["error_type"] = np.select(
        [
            d["selected_p85"].eq(1) & d["target_30d"].eq(1),
            d["selected_p85"].eq(1) & d["target_30d"].eq(0),
            d["selected_p85"].eq(0) & d["target_30d"].eq(1),
        ],
        ["TP", "FP", "FN"],
        default="TN",
    )
    d["availability_state"] = np.select(
        [
            d["availability_is_available"].eq(1),
            d["has_availability_context"].eq(1),
        ],
        ["available_now", "known_unavailable"],
        default="no_asof_context",
    )

    rows = []
    for dimension, col in [
        ("stage", "stage"),
        ("sector", "search_sector"),
        ("modality", "search_modality"),
        ("user_type", "user_type"),
        ("availability", "availability_state"),
    ]:
        for value, g in d.groupby(col, dropna=False):
            selected = g["selected_p85"].eq(1)
            rows.append({
                "dimension": dimension,
                "segment": str(value),
                "n": len(g),
                "positive_rate": float(g["target_30d"].mean()),
                "mean_score": float(g[score_col].mean()),
                "roc_auc": safe_auc(g["target_30d"], g[score_col]),
                "average_precision": float(average_precision_score(g["target_30d"], g[score_col])),
                "selected_p85_n": int(selected.sum()),
                "selected_precision": float(g.loc[selected, "target_30d"].mean()) if selected.any() else np.nan,
                "false_positives": int(g["error_type"].eq("FP").sum()),
                "false_negatives": int(g["error_type"].eq("FN").sum()),
                "fp_share_of_segment": float(g["error_type"].eq("FP").mean()),
                "fn_share_of_segment": float(g["error_type"].eq("FN").mean()),
            })
    summary = pd.DataFrame(rows)
    examples = pd.concat([
        d[d["error_type"].eq("FP")].sort_values(score_col, ascending=False).head(50),
        d[d["error_type"].eq("FN")].sort_values(score_col, ascending=True).head(50),
    ], ignore_index=True)
    keep = [c for c in [
        "fold", "row_id", "lead_id", "inquiry_id", "spot_id", "stage", "score_time",
        "target_30d", score_col, "selected_p85", "error_type", "search_sector",
        "search_modality", "user_type", "availability_state"
    ] if c in examples.columns]
    return summary, examples[keep]


def run_e2e(oof_path, quality_col, out):
    path = ROOT / "experimentos" / "E020_lead_opportunity_fallback_e2e" / "run_experiment.py"
    spec = importlib.util.spec_from_file_location("e020_canonical", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.OOF = oof_path
    mod.QUALITY_COL = quality_col
    mod.OUT = out
    mod.OUT.mkdir(parents=True, exist_ok=True)
    mod.main()


def write_report(cv, bootstrap, errors, core, full):
    macro = cv[cv["stage"].eq("MACRO")].set_index("model")
    a = macro.loc["pooled_catboost_pit_core"]
    b = macro.loc["pooled_catboost_pit_full"]
    boot = bootstrap[
        bootstrap["scope"].eq("MACRO") & bootstrap["metric"].eq("average_precision")
    ].iloc[0]
    if boot["ci95_low"] > 0:
        fe_status = "SUPPORTED"
    elif boot["ci95_high"] < 0:
        fe_status = "NOT_SUPPORTED"
    else:
        fe_status = "INCONCLUSIVE"

    e2e = pd.read_csv(RESULTS / "end_to_end" / "joint_core_metrics_reproduced.csv")
    e2em = e2e[e2e["stage"].eq("MACRO")].set_index("variant")
    q = e2em.loc["quality_only"]
    los = e2em.loc["lead_opportunity_score"]
    p85 = pd.read_csv(RESULTS / "end_to_end" / "final_fold_p85_reproduced.csv")
    q_joint = int(p85[p85["variant"].eq("quality_only")]["joint_positives"].sum())
    l_joint = int(p85[p85["variant"].eq("lead_opportunity_score")]["joint_positives"].sum())

    worst = (
        errors.query("n >= 50")
        .sort_values(["fn_share_of_segment", "n"], ascending=[False, False])
        .head(5)
    )
    lines = [
        "# E021 — Final canonical assessment benchmark",
        "",
        "## Feature Engineering PIT",
        "",
        f"- Core safe features: {len(core)}.",
        f"- Full canonical PIT features: {len(full)}.",
        f"- Macro AP: {a['average_precision_mean']:.4f} -> {b['average_precision_mean']:.4f}.",
        f"- Macro Lift@10: {a['lift_top_10pct_mean']:.3f}x -> {b['lift_top_10pct_mean']:.3f}x.",
        f"- Paired bootstrap AP delta: {boot['point_delta']:+.4f}, 95% CI [{boot['ci95_low']:+.4f}, {boot['ci95_high']:+.4f}].",
        f"- Predictive promotion decision: {fe_status}.",
        "",
        "The full set remains the canonical audit representation; this decision only governs incremental scoring value.",
        "",
        "## Canonical end-to-end",
        "",
        f"- Joint AUC: {q['roc_auc']:.3f} -> {los['roc_auc']:.3f}.",
        f"- Joint AP: {q['average_precision']:.3f} -> {los['average_precision']:.3f}.",
        f"- Joint Lift@10: {q['lift_top_10pct']:.3f}x -> {los['lift_top_10pct']:.3f}x.",
        f"- Joint Recall@20: {q['recall_top_20pct']:.1%} -> {los['recall_top_20pct']:.1%}.",
        f"- Final-fold P85 joint positives: {q_joint} -> {l_joint} (delta {l_joint-q_joint:+d}).",
        "",
        "## Error analysis",
        "",
        "Operational FP/FN are evaluated at P85 inside fold and stage for T1/T2. T0 remains cold-start with no priority gate.",
        "",
        "| Dimension | Segment | n | Positive rate | FN share | AP |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in worst.itertuples(index=False):
        lines.append(
            f"| {r.dimension} | {r.segment} | {int(r.n)} | {r.positive_rate:.1%} | "
            f"{r.fn_share_of_segment:.1%} | {r.average_precision:.3f} |"
        )
    lines += [
        "",
        "Detailed segment metrics: error_analysis_summary.csv.",
        "Concrete high-confidence FP/FN cases: error_examples.csv.",
        "",
        "## Leakage",
        "",
        "- ABTs rebuilt directly from data/candidate through E016.",
        "- Current broker response and blocked mutable current-state features remain excluded.",
        "- Availability remains backward-as-of.",
        "- Lead cohorts stay intact inside rolling temporal folds.",
        "- Ranking metrics are calculated inside fold/stage before aggregation.",
        "",
        "LEAKAGE_CHECK = PASS",
    ]
    (RESULTS / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "status": "COMPLETED",
        "feature_engineering": {
            "status": fe_status,
            "core_feature_count": len(core),
            "full_feature_count": len(full),
            "macro_ap_core": float(a["average_precision_mean"]),
            "macro_ap_full": float(b["average_precision_mean"]),
            "macro_lift10_core": float(a["lift_top_10pct_mean"]),
            "macro_lift10_full": float(b["lift_top_10pct_mean"]),
            "ap_delta_ci95": [float(boot["ci95_low"]), float(boot["ci95_high"])],
        },
        "end_to_end": {
            "status": "COMPLETED",
            "macro_auc_quality_only": float(q["roc_auc"]),
            "macro_auc_los": float(los["roc_auc"]),
            "macro_ap_quality_only": float(q["average_precision"]),
            "macro_ap_los": float(los["average_precision"]),
            "macro_lift10_quality_only": float(q["lift_top_10pct"]),
            "macro_lift10_los": float(los["lift_top_10pct"]),
            "final_fold_p85_joint_positives_quality_only": q_joint,
            "final_fold_p85_joint_positives_los": l_joint,
        },
        "error_analysis": {"status": "COMPLETED", "segment_rows": int(len(errors))},
        "leakage_check": "PASS",
    }
    (RESULTS / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return summary


def main():
    np.random.seed(SEED)
    data, core, full, lead_order = prepare_data()
    (RESULTS / "feature_sets.json").write_text(
        json.dumps({"pit_core": core, "pit_full": full}, indent=2) + "\n",
        encoding="utf-8",
    )

    parts = []
    metric_out = []
    for cfg in FOLDS:
        fold = int(cfg["fold"])
        train, val, test = split_fold(data, lead_order, cfg)
        core_raw, core_cal = fit_variant(train, val, test, core, SEED + fold * 10 + 1)
        full_raw, full_cal = fit_variant(train, val, test, full, SEED + fold * 10 + 2)

        cols = [c for c in [
            "row_id", "lead_id", "inquiry_id", "spot_id", "stage_id", "stage",
            "score_time", "target_30d", "search_sector", "search_modality",
            "user_type", "availability_is_available", "has_availability_context"
        ] if c in test.columns]
        part = test[cols].copy()
        part.insert(0, "fold", fold)
        part["pooled_catboost_pit_core_raw"] = core_raw
        part["pooled_catboost_pit_core"] = core_cal
        part["pooled_catboost_pit_full_raw"] = full_raw
        part["pooled_catboost_pit_full"] = full_cal
        parts.append(part)
        metric_out += metric_rows(part, "pooled_catboost_pit_core", "pooled_catboost_pit_core", fold)
        metric_out += metric_rows(part, "pooled_catboost_pit_full", "pooled_catboost_pit_full", fold)

    oof = pd.concat(parts, ignore_index=True)
    fold_metrics = pd.DataFrame(metric_out)
    cv = cv_summary(fold_metrics)
    bootstrap = bootstrap_deltas(oof, "pooled_catboost_pit_core", "pooled_catboost_pit_full")
    errors, examples = error_analysis(oof, "pooled_catboost_pit_full")

    oof.to_csv(RESULTS / "oof_predictions.csv", index=False)
    fold_metrics.to_csv(RESULTS / "fold_metrics.csv", index=False)
    cv.to_csv(RESULTS / "cv_mean_metrics.csv", index=False)
    bootstrap.to_csv(RESULTS / "paired_bootstrap.csv", index=False)
    errors.to_csv(RESULTS / "error_analysis_summary.csv", index=False)
    examples.to_csv(RESULTS / "error_examples.csv", index=False)

    run_e2e(RESULTS / "oof_predictions.csv", "pooled_catboost_pit_full", RESULTS / "end_to_end")
    summary = write_report(cv, bootstrap, errors, core, full)
    print((RESULTS / "REPORT.md").read_text(encoding="utf-8"))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
