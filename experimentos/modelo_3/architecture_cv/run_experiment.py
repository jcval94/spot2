from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier

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
    make_preprocessor,
    prepare_inquiries,
    read_data,
    stage_balanced_weights,
)
from models import STAGES, metrics_table, set_seed  # noqa: E402

bench_path = MODEL3 / "benchmark_specialists" / "run_experiment.py"
spec = importlib.util.spec_from_file_location("benchmark_specialists_module", bench_path)
bench = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bench)

SEED = 42
FOLDS = [
    {"fold": 1, "train_end": 0.45, "val_end": 0.55, "test_end": 0.65},
    {"fold": 2, "train_end": 0.55, "val_end": 0.65, "test_end": 0.75},
    {"fold": 3, "train_end": 0.65, "val_end": 0.75, "test_end": 0.85},
    {"fold": 4, "train_end": 0.75, "val_end": 0.85, "test_end": 0.95},
]


def lead_order(snapshots: pd.DataFrame) -> pd.DataFrame:
    return (
        snapshots[["lead_id", "created_at"]]
        .drop_duplicates("lead_id")
        .sort_values(["created_at", "lead_id"])
        .reset_index(drop=True)
    )


def split_fold(snapshots: pd.DataFrame, leads: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    n = len(leads)
    a = max(1, int(n * cfg["train_end"]))
    b = max(a + 1, int(n * cfg["val_end"]))
    c = min(n, max(b + 1, int(n * cfg["test_end"])))
    train_ids = set(leads.iloc[:a]["lead_id"])
    val_ids = set(leads.iloc[a:b]["lead_id"])
    test_ids = set(leads.iloc[b:c]["lead_id"])
    return (
        snapshots[snapshots["lead_id"].isin(train_ids)].copy().reset_index(drop=True),
        snapshots[snapshots["lead_id"].isin(val_ids)].copy().reset_index(drop=True),
        snapshots[snapshots["lead_id"].isin(test_ids)].copy().reset_index(drop=True),
    )


def fit_fold(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    bench.normalize_frames(train, val, test)

    prep = make_preprocessor()
    x_train = np.asarray(prep.fit_transform(train[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)
    x_val = np.asarray(prep.transform(val[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)
    x_test = np.asarray(prep.transform(test[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)

    y_train = train["target_30d"].to_numpy(dtype=np.int64)
    y_val = val["target_30d"].to_numpy(dtype=np.int64)
    s_train = train["stage_id"].to_numpy(dtype=np.int64)
    s_val = val["stage_id"].to_numpy(dtype=np.int64)
    s_test = test["stage_id"].to_numpy(dtype=np.int64)
    weights = stage_balanced_weights(train)

    raw_val, final_test, _, _ = bench.fit_neural_models(
        x_train, y_train, s_train, weights, x_val, y_val, s_val, x_test, s_test
    )

    lv, lt = bench.fit_logistic(x_train, y_train, s_train, x_val, s_val, x_test, s_test)
    raw_val["separate_logistic"] = lv
    final_test["separate_logistic"] = lt

    rv, rt = bench.fit_sklearn_specialists(
        lambda: RandomForestClassifier(
            n_estimators=500,
            min_samples_leaf=12,
            max_features="sqrt",
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=SEED,
        ),
        x_train, y_train, s_train, x_val, y_val, s_val, x_test, s_test,
    )
    bench.add_calibrated(
        "specialist_random_forest_calibrated", rv, rt, y_val, s_val, s_test,
        raw_val, final_test, {}
    )

    ev, et = bench.fit_sklearn_specialists(
        lambda: ExtraTreesClassifier(
            n_estimators=500,
            min_samples_leaf=10,
            max_features="sqrt",
            class_weight="balanced",
            n_jobs=-1,
            random_state=SEED + 17,
        ),
        x_train, y_train, s_train, x_val, y_val, s_val, x_test, s_test,
    )
    bench.add_calibrated(
        "specialist_extra_trees_calibrated", ev, et, y_val, s_val, s_test,
        raw_val, final_test, {}
    )

    gv, gt = bench.fit_lightgbm_specialists(
        x_train, y_train, s_train, x_val, y_val, s_val, x_test, s_test
    )
    bench.add_calibrated(
        "specialist_lightgbm_calibrated", gv, gt, y_val, s_val, s_test,
        raw_val, final_test, {}
    )

    cv, ct = bench.fit_catboost_specialists(train, val, test)
    bench.add_calibrated(
        "specialist_catboost_calibrated", cv, ct, y_val, s_val, s_test,
        raw_val, final_test, {}
    )

    pcv, pct = bench.fit_catboost_pooled(train, val, test)
    bench.add_calibrated(
        "pooled_catboost_calibrated", pcv, pct, y_val, s_val, s_test,
        raw_val, final_test, {}
    )

    selection, _, _ = bench.validation_stage_selection(val, raw_val, final_test)
    final_test["validation_selected_hybrid"] = bench.apply_hybrid(selection, final_test, s_test)
    return final_test, selection


def summarize_fold_metrics(fold_metrics: pd.DataFrame) -> pd.DataFrame:
    metrics = ["roc_auc", "average_precision", "brier", "log_loss", "lift_top_10pct", "recall_top_20pct"]
    rows = []
    for (model, stage), g in fold_metrics.groupby(["model", "stage"]):
        row = {"model": model, "stage": stage, "n_folds": int(g["fold"].nunique())}
        for m in metrics:
            row[f"{m}_mean"] = float(g[m].mean())
            row[f"{m}_std"] = float(g[m].std(ddof=1))
            row[f"{m}_min"] = float(g[m].min())
            row[f"{m}_max"] = float(g[m].max())
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    set_seed()
    leads, inquiries_raw, spots, attrs, availability = read_data(ROOT)
    inquiries = prepare_inquiries(inquiries_raw)
    snapshots = build_snapshots(leads, inquiries, spots, attrs, availability)
    leads_ordered = lead_order(snapshots)

    oof_parts = []
    fold_metric_parts = []
    selections = {}

    for cfg in FOLDS:
        fold = cfg["fold"]
        train, val, test = split_fold(snapshots, leads_ordered, cfg)
        predictions, selection = fit_fold(train, val, test)
        selections[f"fold_{fold}"] = selection

        fold_metrics = metrics_table(test, predictions)
        fold_metrics.insert(0, "fold", fold)
        fold_metric_parts.append(fold_metrics)

        part = test[["row_id", "lead_id", "stage_id", "stage", "score_time", "target_30d"]].copy()
        part.insert(0, "fold", fold)
        for model, pred in predictions.items():
            part[model] = pred
        oof_parts.append(part)

    oof = pd.concat(oof_parts, ignore_index=True)
    fold_metrics = pd.concat(fold_metric_parts, ignore_index=True)
    fold_summary = summarize_fold_metrics(fold_metrics)

    model_cols = [
        c for c in oof.columns
        if c not in {"fold", "row_id", "lead_id", "stage_id", "stage", "score_time", "target_30d"}
    ]
    predictions = {m: oof[m].to_numpy(dtype=float) for m in model_cols}
    oof_metrics = metrics_table(oof, predictions)
    bootstrap = bench.bootstrap_deltas(oof, predictions, reference="multihead_calibrated", n_boot=700)

    oof.to_csv(RESULTS / "oof_predictions.csv", index=False)
    fold_metrics.to_csv(RESULTS / "fold_metrics.csv", index=False)
    fold_summary.to_csv(RESULTS / "fold_metric_summary.csv", index=False)
    oof_metrics.to_csv(RESULTS / "oof_metrics.csv", index=False)
    bootstrap.to_csv(RESULTS / "bootstrap_deltas_vs_multihead.csv", index=False)
    (RESULTS / "fold_stage_selection.json").write_text(
        json.dumps(selections, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    def boot_row(model: str, scope: str, metric: str) -> pd.Series:
        return bootstrap[
            bootstrap["model"].eq(model)
            & bootstrap["scope"].eq(scope)
            & bootstrap["metric"].eq(metric)
        ].iloc[0]

    t1_rf_ap = boot_row("specialist_random_forest_calibrated", "T1_first_inquiry", "average_precision")
    t1_rf_auc = boot_row("specialist_random_forest_calibrated", "T1_first_inquiry", "roc_auc")
    pooled_auc = boot_row("pooled_catboost_calibrated", "MACRO", "roc_auc")
    pooled_ap = boot_row("pooled_catboost_calibrated", "MACRO", "average_precision")

    replicated_t1 = float(t1_rf_ap["ci95_low"]) > 0 and float(t1_rf_auc["ci95_low"]) > 0
    replicated_pooled_auc = float(pooled_auc["ci95_low"]) > 0
    conclusion = "SUPPORTED" if replicated_t1 and replicated_pooled_auc else "INCONCLUSIVE"

    ranking = (
        oof_metrics[oof_metrics["stage"].eq("MACRO")]
        .sort_values("average_precision", ascending=False)
        .reset_index(drop=True)
    )
    ranking.to_csv(RESULTS / "oof_model_ranking.csv", index=False)

    pooled = ranking[ranking["model"].eq("pooled_catboost_calibrated")].iloc[0]
    segment_metrics = {}
    for stage in STAGES.values():
        row = oof_metrics[
            oof_metrics["model"].eq("pooled_catboost_calibrated")
            & oof_metrics["stage"].eq(stage)
        ].iloc[0]
        segment_metrics[stage] = {
            k: float(row[k]) for k in [
                "roc_auc", "average_precision", "brier", "log_loss",
                "lift_top_10pct", "recall_top_20pct"
            ]
        }

    harness_results = {
        "experiment_id": "E006_architecture_rolling_cv",
        "metrics": {
            k: float(pooled[k]) for k in [
                "roc_auc", "average_precision", "brier", "log_loss",
                "lift_top_10pct", "recall_top_20pct"
            ]
        },
        "segment_metrics": segment_metrics,
        "conclusion": conclusion,
        "caveats": [
            "rolling CV changes the validation design relative to E005 and is therefore a robustness study rather than a direct parent delta",
            "scheduled_visit remains a proxy target",
            "the dataset is synthetic",
            "outer test cohorts are disjoint, but expanding training windows reuse older cohorts as later training data by design"
        ],
        "next_experiment": "Add explicit point-in-time trajectory/progression features under the identical rolling CV folds and compare paired OOF deltas."
    }
    (RESULTS / "harness_results.json").write_text(
        json.dumps(harness_results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    summary = {
        "experiment_id": "E006_architecture_rolling_cv",
        "conclusion": conclusion,
        "oof_rows": int(len(oof)),
        "oof_unique_leads": int(oof["lead_id"].nunique()),
        "folds": FOLDS,
        "t1_random_forest_vs_multihead": {
            "ap_delta": float(t1_rf_ap["point_delta"]),
            "ap_ci95": [float(t1_rf_ap["ci95_low"]), float(t1_rf_ap["ci95_high"])],
            "auc_delta": float(t1_rf_auc["point_delta"]),
            "auc_ci95": [float(t1_rf_auc["ci95_low"]), float(t1_rf_auc["ci95_high"])],
        },
        "pooled_catboost_vs_multihead_macro": {
            "ap_delta": float(pooled_ap["point_delta"]),
            "ap_ci95": [float(pooled_ap["ci95_low"]), float(pooled_ap["ci95_high"])],
            "auc_delta": float(pooled_auc["point_delta"]),
            "auc_ci95": [float(pooled_auc["ci95_low"]), float(pooled_auc["ci95_high"])],
        },
        "best_oof_macro_ap_model": str(ranking.iloc[0]["model"]),
        "best_oof_macro_ap": float(ranking.iloc[0]["average_precision"]),
    }
    (RESULTS / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# Rolling temporal CV — arquitectura Modelo 3", "",
        f"**Conclusión pre-registrada tras CV: {conclusion}.**", "",
        f"OOF: {len(oof):,} snapshots, {oof['lead_id'].nunique():,} leads, 4 folds temporales.", "",
        "## Ranking OOF macro", "",
        "| Modelo | AUC | AP | Brier | Log loss | Lift@10% |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in ranking.itertuples():
        lines.append(
            f"| {bench.MODEL_LABELS.get(row.model, row.model)} | {row.roc_auc:.3f} | "
            f"{row.average_precision:.3f} | {row.brier:.3f} | {row.log_loss:.3f} | "
            f"{row.lift_top_10pct:.2f}x |"
        )
    lines += [
        "", "## Replicación de hallazgos E005", "",
        f"- T1 RF vs Multi-Head ΔAP {t1_rf_ap['point_delta']:+.3f}, IC95% [{t1_rf_ap['ci95_low']:+.3f}, {t1_rf_ap['ci95_high']:+.3f}].",
        f"- T1 RF vs Multi-Head ΔAUC {t1_rf_auc['point_delta']:+.3f}, IC95% [{t1_rf_auc['ci95_low']:+.3f}, {t1_rf_auc['ci95_high']:+.3f}].",
        f"- pooled CatBoost vs Multi-Head macro ΔAUC {pooled_auc['point_delta']:+.3f}, IC95% [{pooled_auc['ci95_low']:+.3f}, {pooled_auc['ci95_high']:+.3f}].",
        f"- pooled CatBoost vs Multi-Head macro ΔAP {pooled_ap['point_delta']:+.3f}, IC95% [{pooled_ap['ci95_low']:+.3f}, {pooled_ap['ci95_high']:+.3f}].",
        "",
        "## Regla",
        "",
        "Este reporte completa la cross-validation requerida. El registro final de descubrimientos debe usar estos resultados, no el single holdout de E005 de forma aislada.",
    ]
    report = "\n".join(lines) + "\n"
    (RESULTS / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
