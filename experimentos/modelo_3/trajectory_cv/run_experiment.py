from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HERE = Path(__file__).resolve().parent
MODEL3 = HERE.parent
ROOT = MODEL3.parents[1]
RESULTS = HERE / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(MODEL3))
from data_pipeline import (  # noqa: E402
    CAT_FEATURES,
    NUM_FEATURES,
    build_snapshots,
    prepare_inquiries,
    read_data,
    stage_balanced_weights,
)
from models import (  # noqa: E402
    STAGES,
    SharedMultiHead,
    calibrate_by_stage,
    metrics_table,
    predict,
    set_seed,
    train_model,
)

def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

bench = load_module("benchmark_specialists_module", MODEL3 / "benchmark_specialists" / "run_experiment.py")
arch = load_module("architecture_cv_module", MODEL3 / "architecture_cv" / "run_experiment.py")

SEED = 42
BASELINE_OOF = MODEL3 / "architecture_cv" / "results" / "oof_predictions.csv"

TRAJ_FEATURES = [
    "traj_days_since_last_inquiry",
    "traj_mean_inquiry_gap_days",
    "traj_std_inquiry_gap_days",
    "traj_inquiry_velocity_30d",
    "traj_days_since_last_realized_response",
    "traj_days_since_last_accept",
    "traj_response_coverage",
    "traj_unresolved_prior_inquiries",
    "traj_inquiries_after_last_accept",
    "traj_spot_diversity_ratio",
    "traj_current_spot_prior_count",
    "traj_current_spot_seen_before",
    "traj_area_change_vs_first",
    "traj_rent_budget_change_vs_first",
    "traj_sale_budget_change_vs_first",
    "traj_urgency_change_vs_first",
    "traj_message_length_change_vs_first",
    "traj_asked_visit_escalated",
    "traj_channel_changed_from_first",
]

PAIRINGS = {
    "multihead_trajectory": "multihead_calibrated",
    "specialist_random_forest_trajectory": "specialist_random_forest_calibrated",
    "specialist_catboost_trajectory": "specialist_catboost_calibrated",
    "pooled_catboost_trajectory": "pooled_catboost_calibrated",
}


def as_bool(value: object) -> float:
    if pd.isna(value):
        return math.nan
    if isinstance(value, str):
        return float(value.strip().lower() in {"true", "1", "yes"})
    return float(bool(value))


def relative_change(current: object, first: object) -> float:
    a = pd.to_numeric(pd.Series([current]), errors="coerce").iloc[0]
    b = pd.to_numeric(pd.Series([first]), errors="coerce").iloc[0]
    if pd.isna(a) or pd.isna(b) or float(b) == 0.0:
        return math.nan
    return float((a - b) / abs(b))


def trajectory_table(inquiries: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, g in inquiries.groupby("lead_id", sort=False):
        g = g.sort_values(["inquiry_at", "inquiry_id"]).reset_index(drop=True)
        first = g.iloc[0]
        for pos, row in g.iterrows():
            t = row["inquiry_at"]
            prior = g.iloc[:pos].copy()
            known = prior[
                prior["response_event_at"].notna()
                & (prior["response_event_at"] <= t)
            ]
            accepted = known[known["broker_response"].eq("accepted")]

            all_times = list(prior["inquiry_at"]) + [t]
            gaps = (
                pd.Series(all_times).sort_values().diff().dropna().dt.total_seconds().to_numpy() / 86400.0
                if len(all_times) > 1 else np.array([], dtype=float)
            )
            elapsed = max((t - first["inquiry_at"]).total_seconds() / 86400.0, 0.0)
            denominator_days = max(elapsed, 1.0)

            last_response = known["response_event_at"].max() if len(known) else pd.NaT
            last_accept = accepted["response_event_at"].max() if len(accepted) else pd.NaT

            current_spot_prior_count = int(prior["spot_id"].eq(row["spot_id"]).sum()) if len(prior) else 0
            spots_seen = pd.concat([prior["spot_id"], pd.Series([row["spot_id"]])], ignore_index=True)
            spot_diversity = float(spots_seen.nunique(dropna=True) / max(1, len(spots_seen)))

            if pd.isna(last_accept):
                inquiries_after_accept = math.nan
            else:
                inquiries_after_accept = int((prior["inquiry_at"] > last_accept).sum()) + 1

            current_asked = as_bool(row.get("asked_visit"))
            first_asked = as_bool(first.get("asked_visit"))
            asked_escalated = (
                float(current_asked == 1.0 and first_asked == 0.0)
                if not pd.isna(current_asked) and not pd.isna(first_asked) else math.nan
            )
            current_channel = row.get("channel")
            first_channel = first.get("channel")
            channel_changed = (
                float(str(current_channel) != str(first_channel))
                if not pd.isna(current_channel) and not pd.isna(first_channel) else math.nan
            )

            rows.append({
                "inquiry_id": row["inquiry_id"],
                "traj_days_since_last_inquiry": (
                    (t - prior["inquiry_at"].iloc[-1]).total_seconds() / 86400.0 if len(prior) else math.nan
                ),
                "traj_mean_inquiry_gap_days": float(np.mean(gaps)) if len(gaps) else math.nan,
                "traj_std_inquiry_gap_days": float(np.std(gaps)) if len(gaps) > 1 else math.nan,
                "traj_inquiry_velocity_30d": float((pos + 1) / denominator_days * 30.0),
                "traj_days_since_last_realized_response": (
                    (t - last_response).total_seconds() / 86400.0 if not pd.isna(last_response) else math.nan
                ),
                "traj_days_since_last_accept": (
                    (t - last_accept).total_seconds() / 86400.0 if not pd.isna(last_accept) else math.nan
                ),
                "traj_response_coverage": float(len(known) / len(prior)) if len(prior) else math.nan,
                "traj_unresolved_prior_inquiries": float(len(prior) - len(known)),
                "traj_inquiries_after_last_accept": float(inquiries_after_accept) if not pd.isna(inquiries_after_accept) else math.nan,
                "traj_spot_diversity_ratio": spot_diversity,
                "traj_current_spot_prior_count": float(current_spot_prior_count),
                "traj_current_spot_seen_before": float(current_spot_prior_count > 0),
                "traj_area_change_vs_first": relative_change(row.get("requested_area_sqm"), first.get("requested_area_sqm")),
                "traj_rent_budget_change_vs_first": relative_change(
                    row.get("requested_budget_mxn_rent_monthly"), first.get("requested_budget_mxn_rent_monthly")
                ),
                "traj_sale_budget_change_vs_first": relative_change(
                    row.get("requested_budget_mxn_sale_total"), first.get("requested_budget_mxn_sale_total")
                ),
                "traj_urgency_change_vs_first": (
                    pd.to_numeric(pd.Series([row.get("urgency_days")]), errors="coerce").iloc[0]
                    - pd.to_numeric(pd.Series([first.get("urgency_days")]), errors="coerce").iloc[0]
                ),
                "traj_message_length_change_vs_first": relative_change(
                    row.get("message_length"), first.get("message_length")
                ),
                "traj_asked_visit_escalated": asked_escalated,
                "traj_channel_changed_from_first": channel_changed,
            })
    return pd.DataFrame(rows)


def attach_trajectory(snapshots: pd.DataFrame, inquiries: pd.DataFrame) -> pd.DataFrame:
    features = trajectory_table(inquiries)
    out = snapshots.merge(features, on="inquiry_id", how="left", validate="many_to_one")
    for col in TRAJ_FEATURES:
        out[col] = pd.to_numeric(out[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
    return out


def make_trajectory_preprocessor() -> ColumnTransformer:
    cat = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=5, sparse_output=False, dtype=np.float32)),
    ])
    num = Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
    ])
    return ColumnTransformer(
        [("cat", cat, CAT_FEATURES), ("num", num, NUM_FEATURES + TRAJ_FEATURES)],
        remainder="drop", sparse_threshold=0.0,
    )


def normalize_frames(*frames: pd.DataFrame) -> None:
    bench.normalize_frames(*frames)
    for frame in frames:
        for col in TRAJ_FEATURES:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").replace([np.inf, -np.inf], np.nan)


def catboost_frame(frame: pd.DataFrame, include_stage: bool = False) -> pd.DataFrame:
    x = bench.catboost_frame(frame, include_stage=include_stage)
    for col in TRAJ_FEATURES:
        x[col] = pd.to_numeric(frame[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
    return x


def fit_catboost_specialists(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    val_pred = np.full(len(val), np.nan)
    test_pred = np.full(len(test), np.nan)
    cat_cols = list(CAT_FEATURES)
    for sid in STAGES:
        tr = train["stage_id"].eq(sid).to_numpy()
        va = val["stage_id"].eq(sid).to_numpy()
        te = test["stage_id"].eq(sid).to_numpy()
        xtr, xva, xte = catboost_frame(train.loc[tr]), catboost_frame(val.loc[va]), catboost_frame(test.loc[te])
        model = bench.make_catboost(SEED + 300 + sid)
        model.fit(
            xtr, train.loc[tr, "target_30d"].to_numpy(dtype=int),
            cat_features=cat_cols,
            eval_set=(xva, val.loc[va, "target_30d"].to_numpy(dtype=int)),
            use_best_model=True, early_stopping_rounds=50, verbose=False,
        )
        val_pred[va] = model.predict_proba(xva)[:, 1]
        test_pred[te] = model.predict_proba(xte)[:, 1]
    return val_pred, test_pred


def fit_catboost_pooled(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    xtr = catboost_frame(train, include_stage=True)
    xva = catboost_frame(val, include_stage=True)
    xte = catboost_frame(test, include_stage=True)
    model = bench.make_catboost(SEED + 391)
    model.fit(
        xtr, train["target_30d"].to_numpy(dtype=int),
        cat_features=list(CAT_FEATURES) + ["stage_name"],
        eval_set=(xva, val["target_30d"].to_numpy(dtype=int)),
        use_best_model=True, early_stopping_rounds=50, verbose=False,
    )
    return model.predict_proba(xva)[:, 1], model.predict_proba(xte)[:, 1]


def choose_hybrid(val: pd.DataFrame, raw_val: dict[str, np.ndarray], final_test: dict[str, np.ndarray], s_test: np.ndarray) -> tuple[dict[str, str], np.ndarray]:
    candidates = list(raw_val)
    selection = {}
    y = val["target_30d"].to_numpy(dtype=int)
    s = val["stage_id"].to_numpy(dtype=int)
    for sid, stage_name in STAGES.items():
        mask = s == sid
        scores = {m: float(average_precision_score(y[mask], raw_val[m][mask])) for m in candidates}
        selection[stage_name] = max(scores, key=scores.get)
    out = np.full(len(s_test), np.nan)
    for sid, stage_name in STAGES.items():
        mask = s_test == sid
        out[mask] = final_test[selection[stage_name]][mask]
    return selection, out


def fit_fold(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame):
    normalize_frames(train, val, test)
    prep = make_trajectory_preprocessor()
    cols = CAT_FEATURES + NUM_FEATURES + TRAJ_FEATURES
    x_train = np.asarray(prep.fit_transform(train[cols]), dtype=np.float32)
    x_val = np.asarray(prep.transform(val[cols]), dtype=np.float32)
    x_test = np.asarray(prep.transform(test[cols]), dtype=np.float32)

    y_train = train["target_30d"].to_numpy(dtype=np.int64)
    y_val = val["target_30d"].to_numpy(dtype=np.int64)
    s_train = train["stage_id"].to_numpy(dtype=np.int64)
    s_val = val["stage_id"].to_numpy(dtype=np.int64)
    s_test = test["stage_id"].to_numpy(dtype=np.int64)
    weights = stage_balanced_weights(train)

    raw_val, final_test = {}, {}

    set_seed()
    multi = SharedMultiHead(x_train.shape[1])
    multi, _ = train_model(multi, x_train, y_train, s_train, weights, x_val, y_val, s_val)
    mv, mt = predict(multi, x_val, s_val), predict(multi, x_test, s_test)
    mt_cal, _ = calibrate_by_stage(mv, y_val, s_val, mt, s_test)
    raw_val["multihead_trajectory"] = mv
    final_test["multihead_trajectory"] = mt_cal

    rv, rt = bench.fit_sklearn_specialists(
        lambda: RandomForestClassifier(
            n_estimators=500, min_samples_leaf=12, max_features="sqrt",
            class_weight="balanced_subsample", n_jobs=-1, random_state=SEED + 211,
        ),
        x_train, y_train, s_train, x_val, y_val, s_val, x_test, s_test,
    )
    rt_cal, _ = calibrate_by_stage(rv, y_val, s_val, rt, s_test)
    raw_val["specialist_random_forest_trajectory"] = rv
    final_test["specialist_random_forest_trajectory"] = rt_cal

    cv, ct = fit_catboost_specialists(train, val, test)
    ct_cal, _ = calibrate_by_stage(cv, y_val, s_val, ct, s_test)
    raw_val["specialist_catboost_trajectory"] = cv
    final_test["specialist_catboost_trajectory"] = ct_cal

    pv, pt = fit_catboost_pooled(train, val, test)
    pt_cal, _ = calibrate_by_stage(pv, y_val, s_val, pt, s_test)
    raw_val["pooled_catboost_trajectory"] = pv
    final_test["pooled_catboost_trajectory"] = pt_cal

    selection, hybrid = choose_hybrid(val, raw_val, final_test, s_test)
    final_test["trajectory_validation_hybrid"] = hybrid
    return final_test, selection


def paired_bootstrap(oof: pd.DataFrame, predictions: dict[str, np.ndarray]) -> pd.DataFrame:
    parts = []
    for candidate, reference in PAIRINGS.items():
        subset = {reference: predictions[reference], candidate: predictions[candidate]}
        b = bench.bootstrap_deltas(oof, subset, reference=reference, n_boot=800)
        b = b[b["model"].eq(candidate)].copy()
        b.insert(1, "reference_model", reference)
        parts.append(b)
    return pd.concat(parts, ignore_index=True)


def main() -> None:
    if not BASELINE_OOF.exists():
        raise FileNotFoundError("E006 OOF predictions are required before E007.")

    set_seed()
    leads, inquiries_raw, spots, attrs, availability = read_data(ROOT)
    inquiries = prepare_inquiries(inquiries_raw)
    snapshots = attach_trajectory(build_snapshots(leads, inquiries, spots, attrs, availability), inquiries)
    leads_ordered = arch.lead_order(snapshots)

    parts, fold_metric_parts, selections = [], [], {}
    for cfg in arch.FOLDS:
        fold = cfg["fold"]
        train, val, test = arch.split_fold(snapshots, leads_ordered, cfg)
        preds, selection = fit_fold(train, val, test)
        selections[f"fold_{fold}"] = selection
        fm = metrics_table(test, preds)
        fm.insert(0, "fold", fold)
        fold_metric_parts.append(fm)

        part = test[["row_id", "lead_id", "stage_id", "stage", "score_time", "target_30d"]].copy()
        part.insert(0, "fold", fold)
        for model, pred in preds.items():
            part[model] = pred
        parts.append(part)

    traj_oof = pd.concat(parts, ignore_index=True)
    baseline = pd.read_csv(BASELINE_OOF, parse_dates=["score_time"])
    keys = ["fold", "row_id", "lead_id", "stage_id", "stage", "score_time", "target_30d"]
    merged = baseline.merge(
        traj_oof,
        on=keys,
        how="inner",
        validate="one_to_one",
        suffixes=("", "_trajdup"),
    )
    if len(merged) != len(baseline) or len(merged) != len(traj_oof):
        raise RuntimeError("E006 and E007 OOF populations do not align exactly.")

    model_cols = [
        *PAIRINGS.values(),
        *PAIRINGS.keys(),
        "trajectory_validation_hybrid",
    ]
    predictions = {m: merged[m].to_numpy(dtype=float) for m in model_cols}
    oof_metrics = metrics_table(merged, predictions)
    fold_metrics = pd.concat(fold_metric_parts, ignore_index=True)
    paired = paired_bootstrap(merged, predictions)

    merged.to_csv(RESULTS / "oof_predictions.csv", index=False)
    oof_metrics.to_csv(RESULTS / "oof_metrics.csv", index=False)
    fold_metrics.to_csv(RESULTS / "fold_metrics.csv", index=False)
    paired.to_csv(RESULTS / "paired_bootstrap.csv", index=False)
    (RESULTS / "fold_stage_selection.json").write_text(
        json.dumps(selections, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    t2 = paired[
        paired["scope"].eq("T2_engaged")
        & paired["metric"].eq("average_precision")
    ].copy().sort_values("point_delta", ascending=False)

    if (t2["ci95_low"] > 0).any():
        conclusion = "SUPPORTED"
    elif (t2["ci95_high"] < 0).all():
        conclusion = "NOT_SUPPORTED"
    else:
        conclusion = "INCONCLUSIVE"

    trajectory_models = list(PAIRINGS.keys()) + ["trajectory_validation_hybrid"]
    ranking = (
        oof_metrics[
            oof_metrics["stage"].eq("MACRO")
            & oof_metrics["model"].isin(trajectory_models)
        ]
        .sort_values("average_precision", ascending=False)
        .reset_index(drop=True)
    )
    ranking.to_csv(RESULTS / "trajectory_model_ranking.csv", index=False)

    best_model = str(ranking.iloc[0]["model"])
    best = ranking.iloc[0]
    segment_metrics = {}
    for stage in STAGES.values():
        row = oof_metrics[
            oof_metrics["model"].eq(best_model)
            & oof_metrics["stage"].eq(stage)
        ].iloc[0]
        segment_metrics[stage] = {
            k: float(row[k]) for k in [
                "roc_auc", "average_precision", "brier", "log_loss",
                "lift_top_10pct", "recall_top_20pct"
            ]
        }

    harness_results = {
        "experiment_id": "E007_trajectory_progression_cv",
        "metrics": {
            k: float(best[k]) for k in [
                "roc_auc", "average_precision", "brier", "log_loss",
                "lift_top_10pct", "recall_top_20pct"
            ]
        },
        "segment_metrics": segment_metrics,
        "conclusion": conclusion,
        "caveats": [
            "trajectory features are evaluated by rolling temporal OOF predictions rather than a single holdout",
            "scheduled_visit remains a proxy target",
            "the dataset is synthetic",
            "the exploratory trajectory hybrid is selected repeatedly on fold validation sets and should not be treated as a production winner without further temporal confirmation"
        ],
        "next_experiment": "If trajectory features are supported, ablate the winning trajectory family and audit temporal stability of the strongest individual progression signals."
    }
    (RESULTS / "harness_results.json").write_text(
        json.dumps(harness_results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    best_t2 = t2.iloc[0]
    summary = {
        "experiment_id": "E007_trajectory_progression_cv",
        "conclusion": conclusion,
        "primary_metric": "T2_average_precision",
        "best_t2_candidate": str(best_t2["model"]),
        "best_t2_reference": str(best_t2["reference_model"]),
        "best_t2_delta_ap": float(best_t2["point_delta"]),
        "best_t2_delta_ap_ci95": [float(best_t2["ci95_low"]), float(best_t2["ci95_high"])],
        "best_macro_trajectory_model": best_model,
        "best_macro_trajectory_ap": float(best["average_precision"]),
        "features": TRAJ_FEATURES,
    }
    (RESULTS / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# Trajectory / progression features — rolling temporal CV", "",
        f"**Conclusión: {conclusion}.**", "",
        "## Paired T2 Average Precision deltas", "",
        "| Modelo + trajectory | Baseline | ΔAP | IC95% | P(Δ>0) |",
        "|---|---|---:|---:|---:|",
    ]
    for row in t2.itertuples():
        lines.append(
            f"| {row.model} | {row.reference_model} | {row.point_delta:+.4f} | "
            f"[{row.ci95_low:+.4f}, {row.ci95_high:+.4f}] | {row.probability_delta_gt_0:.1%} |"
        )

    lines += ["", "## Macro trajectory ranking", "",
              "| Modelo | AUC | AP | Brier | Log loss | Lift@10% |",
              "|---|---:|---:|---:|---:|---:|"]
    for row in ranking.itertuples():
        lines.append(
            f"| {row.model} | {row.roc_auc:.3f} | {row.average_precision:.3f} | "
            f"{row.brier:.3f} | {row.log_loss:.3f} | {row.lift_top_10pct:.2f}x |"
        )

    lines += [
        "", "## Leakage", "",
        "Todas las variables response-derived usan exclusivamente respuestas de inquiries previas cuyo "
        "\`response_event_at <= score_time\`. La respuesta de la inquiry actual no se usa.",
        "",
        "## Registro", "",
        "Este experimento sólo debe promoverse a descubrimiento acumulado después de revisar conjuntamente E006 y E007.",
    ]
    report = "\n".join(lines) + "\n"
    (RESULTS / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
