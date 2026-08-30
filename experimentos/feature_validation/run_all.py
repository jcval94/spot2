from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import (
    AVAIL_NUM,
    CONTEXT_NUM,
    CORE_METRICS,
    HISTORY_NUM,
    INQUIRY_NUM,
    LEAD_NUM,
    MATCH_NUM,
    SPOT_NUM,
    STAGES,
    add_availability_guardrail,
    add_broker_history,
    bootstrap_delta,
    core_metrics_dict,
    ensure_dir,
    feature_lists,
    fit_iforest_by_regime,
    load_snapshot_data,
    macro_row,
    metric_bundle,
    metrics_for,
    psi_numeric,
    rf_specialist_predictions,
    stage_metrics_dict,
    write_harness_results,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT_METRICS = ROOT / "experimentos" / "modelo_3" / "benchmark_specialists" / "results" / "metrics_by_stage.csv"
SEED = 42

EXPERIMENTS = {
    "E021_temporal_drift_stress": HERE / "E021_temporal_drift_stress",
    "E022_temporal_feature_ablation": HERE / "E022_temporal_feature_ablation",
    "E023_availability_staleness": HERE / "E023_availability_staleness",
    "E024_outlier_handling": HERE / "E024_outlier_handling",
    "E025_redundancy_ablation": HERE / "E025_redundancy_ablation",
    "E026_prior_history_ablation": HERE / "E026_prior_history_ablation",
    "E027_broker_prior_point_in_time": HERE / "E027_broker_prior_point_in_time",
}


def save_csv(df: pd.DataFrame, out: Path, name: str) -> None:
    ensure_dir(out)
    df.to_csv(out / name, index=False)


def save_json(payload: dict, out: Path, name: str) -> None:
    ensure_dir(out)
    (out / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


def combine_metrics(items: list[tuple[str, pd.DataFrame]]) -> pd.DataFrame:
    frames = []
    for label, m in items:
        x = m.copy()
        x["variant"] = label
        frames.append(x)
    return pd.concat(frames, ignore_index=True)


def report_metric_table(metrics: pd.DataFrame) -> str:
    macro = metrics[metrics["stage"].eq("MACRO")].copy()
    lines = [
        "| Variante | ROC-AUC | AP | Brier | Log loss | Lift@10% | Recall@20% |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in macro.itertuples():
        label = getattr(r, "variant", r.model)
        lines.append(
            f"| {label} | {r.roc_auc:.3f} | {r.average_precision:.3f} | "
            f"{r.brier:.3f} | {r.log_loss:.3f} | {r.lift_top_10pct:.2f}x | "
            f"{r.recall_top_20pct:.3f} |"
        )
    return "\n".join(lines)


def standard_baseline(split: pd.DataFrame):
    train = split[split["split"].eq("train")].copy().reset_index(drop=True)
    val = split[split["split"].eq("val")].copy().reset_index(drop=True)
    test = split[split["split"].eq("test")].copy().reset_index(drop=True)
    cats, nums = feature_lists()
    pred, _, meta = rf_specialist_predictions(train, val, test, cats, nums)
    metrics = metrics_for(test, "rf_full", pred)
    return train, val, test, pred, metrics, meta


def reconcile_parent(metrics: pd.DataFrame, out: Path) -> dict:
    parent = pd.read_csv(PARENT_METRICS)
    p = parent[
        parent["model"].eq("specialist_random_forest_calibrated")
        & parent["stage"].eq("MACRO")
    ].iloc[0]
    ours = macro_row(metrics, "rf_full")
    diffs = {m: float(ours[m] - p[m]) for m in CORE_METRICS}
    max_abs = max(abs(v) for v in diffs.values())
    payload = {
        "parent_model": "specialist_random_forest_calibrated",
        "max_abs_metric_difference": float(max_abs),
        "metric_differences": diffs,
        "status": "MATCH" if max_abs < 1e-10 else "MISMATCH",
    }
    save_json(payload, out, "baseline_reconciliation.json")
    if payload["status"] != "MATCH":
        raise RuntimeError(f"RF baseline does not reproduce E005: {payload}")
    return payload


def run_e007_drift(snapshots: pd.DataFrame) -> None:
    exp = EXPERIMENTS["E021_temporal_drift_stress"]
    out = ensure_dir(exp / "results")
    charts = ensure_dir(out / "charts")
    d = snapshots.copy()
    d["lead_month"] = d["created_at"].dt.to_period("M").astype(str)
    months = sorted(d["lead_month"].unique())
    fold_rows = []
    oof_frames, oof_preds = [], []

    candidate_val_indices = list(range(8, max(8, len(months) - 2), 2))
    for fold_no, val_idx in enumerate(candidate_val_indices, start=1):
        if val_idx + 2 >= len(months):
            break
        val_month = months[val_idx]
        test_months = months[val_idx + 1: val_idx + 3]
        train_months = months[:val_idx]
        tr = d[d["lead_month"].isin(train_months)].copy().reset_index(drop=True)
        va = d[d["lead_month"].eq(val_month)].copy().reset_index(drop=True)
        te = d[d["lead_month"].isin(test_months)].copy().reset_index(drop=True)
        if min(len(tr), len(va), len(te)) == 0:
            continue
        cats, nums = feature_lists()
        pred, _, meta = rf_specialist_predictions(
            tr, va, te, cats, nums, seed=SEED
        )
        m = metrics_for(te, f"fold_{fold_no}", pred)
        for r in m.to_dict("records"):
            fold_rows.append({
                "fold": fold_no,
                "train_end_month": train_months[-1],
                "validation_month": val_month,
                "test_months": ",".join(test_months),
                **r,
                "ap_over_prevalence": (
                    r["average_precision"] / r["positive_rate"]
                    if r["positive_rate"] and np.isfinite(r["average_precision"])
                    else np.nan
                ),
                "n_train": len(tr),
                "n_val": len(va),
                "n_test": len(te),
                "n_encoded_features": meta["n_encoded_features"],
            })
        x = te.copy()
        x["fold"] = fold_no
        oof_frames.append(x)
        oof_preds.append(pred)

    fold_metrics = pd.DataFrame(fold_rows)
    if not oof_frames:
        raise RuntimeError("No rolling drift folds were produced")
    oof = pd.concat(oof_frames, ignore_index=True)
    pred = np.concatenate(oof_preds)
    oof_metrics = metrics_for(oof, "rolling_rf", pred)
    save_csv(fold_metrics, out, "fold_metrics.csv")
    save_csv(oof_metrics, out, "oof_metrics.csv")

    cohort = (
        d.groupby(["lead_month", "stage"], as_index=False)
        .agg(n=("row_id", "size"), positive_rate=("target_30d", "mean"))
        .sort_values(["lead_month", "stage"])
    )
    save_csv(cohort, out, "cohort_target_rates.csv")

    drift_features = [
        "days_from_lead_creation",
        "inquiry_number",
        "days_since_first_inquiry",
        "availability_snapshot_age_days",
        "target_area_sqm",
        "prior_searches",
        "prior_inquiries",
        "requested_area_sqm",
    ]
    periods = sorted(d["lead_month"].unique())
    cut = max(1, len(periods) // 2)
    early_months, late_months = periods[:cut], periods[cut:]
    psi_rows = []
    for sid, stage in STAGES.items():
        early = d[d["stage_id"].eq(sid) & d["lead_month"].isin(early_months)]
        late = d[d["stage_id"].eq(sid) & d["lead_month"].isin(late_months)]
        for feature in drift_features:
            psi_rows.append({
                "stage": stage,
                "feature": feature,
                "n_early": len(early),
                "n_late": len(late),
                "psi": psi_numeric(early[feature], late[feature]),
            })
    psi = pd.DataFrame(psi_rows).sort_values("psi", ascending=False)
    save_csv(psi, out, "feature_psi_early_vs_late.csv")

    macro_folds = fold_metrics[fold_metrics["stage"].eq("MACRO")].copy()
    variability = {
        "n_folds": int(macro_folds["fold"].nunique()),
        "positive_rate_min": float(macro_folds["positive_rate"].min()),
        "positive_rate_max": float(macro_folds["positive_rate"].max()),
        "positive_rate_range": float(
            macro_folds["positive_rate"].max() - macro_folds["positive_rate"].min()
        ),
        "roc_auc_min": float(macro_folds["roc_auc"].min()),
        "roc_auc_max": float(macro_folds["roc_auc"].max()),
        "roc_auc_range": float(
            macro_folds["roc_auc"].max() - macro_folds["roc_auc"].min()
        ),
        "ap_over_prevalence_min": float(macro_folds["ap_over_prevalence"].min()),
        "ap_over_prevalence_max": float(macro_folds["ap_over_prevalence"].max()),
        "max_psi": float(psi["psi"].max()),
        "median_psi": float(psi["psi"].median()),
    }
    save_json(variability, out, "drift_summary.json")

    conclusion = (
        "SUPPORTED"
        if variability["positive_rate_range"] >= 0.10
        or variability["roc_auc_range"] >= 0.05
        or variability["max_psi"] >= 0.25
        else "INCONCLUSIVE"
    )
    core = core_metrics_dict(oof_metrics, "rolling_rf")
    segments = stage_metrics_dict(oof_metrics, "rolling_rf")
    write_harness_results(
        out,
        "E021_temporal_drift_stress",
        core,
        segments,
        conclusion,
        [
            "Rolling folds deliberately change the validation design relative to E005, so comparison is NON_EQUIVALENT.",
            "Average Precision is prevalence-sensitive; AP/prevalence and ROC-AUC are reported alongside AP.",
            "The dataset is synthetic and the target is scheduled_visit within 30 days.",
        ],
        "Remove drift-sensitive timing/progress variables under the original frozen E005 split and quantify the performance delta.",
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    for stage, g in cohort.groupby("stage"):
        ax.plot(g["lead_month"], g["positive_rate"], marker="o", label=stage)
    ax.set_title("Target rate by lead cohort and stage")
    ax.set_ylabel("Positive rate")
    ax.tick_params(axis="x", rotation=60)
    ax.legend()
    fig.tight_layout()
    fig.savefig(charts / "cohort_target_rate.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    p = psi.head(15).sort_values("psi")
    ax.barh(p["stage"] + " · " + p["feature"], p["psi"])
    ax.set_title("Largest early-vs-late feature PSI")
    ax.set_xlabel("PSI")
    fig.tight_layout()
    fig.savefig(charts / "feature_psi.png", dpi=170)
    plt.close(fig)

    report = f"""# E021 - Temporal drift stress test

## Pregunta

El proceso y el rendimiento del modelo son estables a traves del tiempo, o una parte material de la senal esta asociada al regimen/cohorte?

## Resultado

**Conclusion: {conclusion}.**

- Rango de positive rate macro entre folds: {variability['positive_rate_range']:.3f}.
- Rango de ROC-AUC macro: {variability['roc_auc_range']:.3f}.
- PSI maximo early vs late: {variability['max_psi']:.3f}.
- PSI mediano: {variability['median_psi']:.3f}.

El punto importante no es que una metrica cambie por si sola: el target, variables de progreso y el regimen de interaccion se desplazan simultaneamente. Por eso cualquier modelo que use clocks de funnel debe validarse fuera de tiempo y por cohortes.

## OOF metrics

{report_metric_table(oof_metrics.assign(variant="rolling_rf"))}

## Por que importa

Un feature puede ser perfectamente point-in-time y aun asi ser peligroso: puede aprender cuando fue generado el dato en lugar de una relacion estable con la intencion comercial. Eso no es leakage clasico, pero si riesgo de generalizacion.

## Evidencia

- fold_metrics.csv
- cohort_target_rates.csv
- feature_psi_early_vs_late.csv
- drift_summary.json
- charts/cohort_target_rate.png
- charts/feature_psi.png
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")


def run_e008_temporal_ablation(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    baseline_pred: np.ndarray,
    baseline_metrics: pd.DataFrame,
) -> None:
    exp = EXPERIMENTS["E022_temporal_feature_ablation"]
    out = ensure_dir(exp / "results")
    temporal_cat = ["score_weekday"]
    temporal_num = [
        "score_hour",
        "score_month",
        "days_from_lead_creation",
        "inquiry_number",
        "days_since_first_inquiry",
    ]
    cats, nums = feature_lists(remove_cat=temporal_cat, remove_num=temporal_num)
    no_temp_pred, _, meta = rf_specialist_predictions(train, val, test, cats, nums)
    no_temp_metrics = metrics_for(test, "no_temporal", no_temp_pred)

    time_cats = ["score_weekday"]
    time_nums = temporal_num + ["lead_cohort_index", "score_time_index"]
    time_pred, _, _ = rf_specialist_predictions(train, val, test, time_cats, time_nums)
    time_metrics = metrics_for(test, "time_proxy_only", time_pred)

    all_metrics = combine_metrics([
        ("full_reference", baseline_metrics),
        ("no_temporal", no_temp_metrics),
        ("time_proxy_only", time_metrics),
    ])
    save_csv(all_metrics, out, "metrics_by_variant.csv")

    boots = []
    for metric in ["average_precision", "roc_auc", "lift_top_10pct"]:
        boots.append(bootstrap_delta(test, baseline_pred, no_temp_pred, metric=metric))
        for sid in STAGES:
            boots.append(
                bootstrap_delta(
                    test, baseline_pred, no_temp_pred, metric=metric, stage_id=sid
                )
            )
    boot = pd.DataFrame(boots)
    save_csv(boot, out, "bootstrap_full_minus_no_temporal.csv")

    ap = boot[
        boot["metric"].eq("average_precision") & boot["stage"].eq("MACRO")
    ].iloc[0]
    full_minus = float(ap["point_delta"])
    time_macro = macro_row(time_metrics, "time_proxy_only")
    if float(ap["ci95_low"]) > 0 and full_minus >= 0.005:
        conclusion = "SUPPORTED"
    elif float(ap["ci95_high"]) < 0:
        conclusion = "NOT_SUPPORTED"
    else:
        conclusion = "INCONCLUSIVE"

    write_harness_results(
        out,
        "E022_temporal_feature_ablation",
        core_metrics_dict(no_temp_metrics, "no_temporal"),
        stage_metrics_dict(no_temp_metrics, "no_temporal"),
        conclusion,
        [
            "The experiment removes calendar/progress clocks but retains availability snapshot age, which is audited separately in E023.",
            "The time-proxy-only model is diagnostic and includes lead_cohort_index and score_time_index; it is not proposed for production.",
            "Bootstrap resamples complete leads to preserve dependence among T2 snapshots.",
        ],
        "Audit availability snapshot age separately, because it is point-in-time safe but may behave as a regime/staleness proxy.",
    )
    save_json(
        {
            "conclusion": conclusion,
            "full_minus_no_temporal_ap": full_minus,
            "full_minus_no_temporal_ap_ci95": [
                float(ap["ci95_low"]),
                float(ap["ci95_high"]),
            ],
            "time_proxy_only_macro_auc": float(time_macro["roc_auc"]),
            "time_proxy_only_macro_ap": float(time_macro["average_precision"]),
            "n_encoded_features_no_temporal": meta["n_encoded_features"],
        },
        out,
        "summary.json",
    )

    report = f"""# E022 - Temporal feature ablation

## Hipotesis

Si el modelo esta dependiendo materialmente de clocks de cohorte/progreso, removerlos debe reducir desempeno fuera de tiempo.

**Conclusion: {conclusion}.**

- Full - no-temporal AP: {full_minus:+.4f}.
- IC95% bootstrap por lead: [{float(ap['ci95_low']):+.4f}, {float(ap['ci95_high']):+.4f}].
- Time-proxy-only macro AUC: {float(time_macro['roc_auc']):.3f}.
- Time-proxy-only macro AP: {float(time_macro['average_precision']):.3f}.

## Que se removio

- score_weekday
- score_hour
- score_month
- days_from_lead_creation
- inquiry_number
- days_since_first_inquiry

availability_snapshot_age_days se mantiene para no mezclar dos hipotesis; E023 lo audita aparte.

## Metricas

{report_metric_table(all_metrics)}

## Lectura

Una variable temporal puede ser legitimamente observable y aun capturar drift. La pregunta aqui no es leakage, sino cuanto de la discriminacion depende de un reloj cuya distribucion cambia de cohorte a cohorte.
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")


def age_bucket_metrics(
    test: pd.DataFrame, variants: dict[str, np.ndarray]
) -> pd.DataFrame:
    age = pd.to_numeric(test["availability_snapshot_age_days"], errors="coerce")
    buckets = (
        pd.cut(
            age,
            [-np.inf, 7, 30, 90, np.inf],
            labels=["0-7d", "8-30d", "31-90d", ">90d"],
        )
        .astype("string")
        .fillna("missing")
    )
    rows = []
    for name, pred in variants.items():
        for bucket in ["0-7d", "8-30d", "31-90d", ">90d", "missing"]:
            mask = buckets.eq(bucket).to_numpy()
            if mask.sum() < 30:
                continue
            b = metric_bundle(test.loc[mask, "target_30d"], pred[mask])
            rows.append({"variant": name, "age_bucket": bucket, **b})
    return pd.DataFrame(rows)


def run_e009_availability(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    baseline_pred: np.ndarray,
    baseline_metrics: pd.DataFrame,
) -> None:
    exp = EXPERIMENTS["E023_availability_staleness"]
    out = ensure_dir(exp / "results")

    cats_drop, nums_drop = feature_lists(
        remove_num=["availability_snapshot_age_days"]
    )
    drop_pred, _, _ = rf_specialist_predictions(
        train, val, test, cats_drop, nums_drop
    )
    drop_metrics = metrics_for(test, "drop_raw_age", drop_pred)

    tr_g, va_g, te_g = map(add_availability_guardrail, [train, val, test])
    cats_g, nums_g = feature_lists(
        remove_num=["availability_snapshot_age_days"],
        add_cat=["availability_staleness_bucket"],
        add_num=["availability_snapshot_age_log1p", "availability_stale_gt90"],
    )
    guard_pred, _, _ = rf_specialist_predictions(
        tr_g, va_g, te_g, cats_g, nums_g
    )
    guard_metrics = metrics_for(test, "guarded_staleness", guard_pred)

    all_metrics = combine_metrics([
        ("full_raw_age", baseline_metrics),
        ("drop_raw_age", drop_metrics),
        ("guarded_staleness", guard_metrics),
    ])
    save_csv(all_metrics, out, "metrics_by_variant.csv")

    boots = []
    for name, pred in [
        ("drop_raw_age", drop_pred),
        ("guarded_staleness", guard_pred),
    ]:
        for metric in ["average_precision", "roc_auc"]:
            b = bootstrap_delta(test, pred, baseline_pred, metric=metric)
            b["candidate"] = name
            boots.append(b)
            for sid in STAGES:
                x = bootstrap_delta(
                    test, pred, baseline_pred, metric=metric, stage_id=sid
                )
                x["candidate"] = name
                boots.append(x)
    boot = pd.DataFrame(boots)
    save_csv(boot, out, "bootstrap_delta_vs_raw_age.csv")
    seg = age_bucket_metrics(
        test,
        {
            "full_raw_age": baseline_pred,
            "drop_raw_age": drop_pred,
            "guarded_staleness": guard_pred,
        },
    )
    save_csv(seg, out, "metrics_by_snapshot_age_bucket.csv")

    b = boot[
        boot["candidate"].eq("guarded_staleness")
        & boot["metric"].eq("average_precision")
        & boot["stage"].eq("MACRO")
    ].iloc[0]
    if float(b["ci95_low"]) >= -0.01:
        conclusion = "SUPPORTED"
    elif float(b["point_delta"]) < -0.02 and float(b["ci95_high"]) < 0:
        conclusion = "NOT_SUPPORTED"
    else:
        conclusion = "INCONCLUSIVE"

    write_harness_results(
        out,
        "E023_availability_staleness",
        core_metrics_dict(guard_metrics, "guarded_staleness"),
        stage_metrics_dict(guard_metrics, "guarded_staleness"),
        conclusion,
        [
            "Non-inferiority margin for macro AP was declared as -0.01 before reading the result.",
            "A stale snapshot is not equivalent to an unavailable spot; >90d is treated as unknown context, not false availability.",
            "Snapshot age is point-in-time safe but can still proxy temporal regime.",
        ],
        "Test training-row anomaly handling without contaminating the held-out test population.",
    )

    report = f"""# E023 - Availability staleness

**Conclusion: {conclusion}.**

La version protegida reemplaza la edad cruda por log-age + bucket y trata snapshots >90 dias como contexto de disponibilidad desconocido.

- Guarded - raw AP: {float(b['point_delta']):+.4f}.
- IC95%: [{float(b['ci95_low']):+.4f}, {float(b['ci95_high']):+.4f}].
- Margen de no inferioridad declarado: -0.010 AP.

## Metricas

{report_metric_table(all_metrics)}

## Por que

E020 mostro gaps de snapshots de hasta 319 dias. Una fecha de snapshot anterior al score hace la feature legal point-in-time, pero no necesariamente confiable. La representacion protegida separa availability de freshness.
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")


def run_e010_outliers(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    baseline_pred: np.ndarray,
    baseline_metrics: pd.DataFrame,
) -> None:
    exp = EXPERIMENTS["E024_outlier_handling"]
    out = ensure_dir(exp / "results")
    excluded_clocks = {
        "score_hour",
        "score_month",
        "days_from_lead_creation",
        "inquiry_number",
        "days_since_first_inquiry",
        "availability_snapshot_age_days",
    }
    anomaly_num = []
    for c in (
        LEAD_NUM
        + INQUIRY_NUM
        + SPOT_NUM
        + MATCH_NUM
        + AVAIL_NUM
        + HISTORY_NUM
        + CONTEXT_NUM
    ):
        if c not in excluded_clocks and c not in anomaly_num:
            anomaly_num.append(c)

    tr_i, va_i, te_i, if_summary = fit_iforest_by_regime(
        train, val, test, anomaly_num
    )
    save_csv(if_summary, out, "iforest_split_summary.csv")

    cats, nums = feature_lists()
    keep = tr_i["iforest_anomaly_flag"].eq(0).to_numpy()
    drop_pred, _, drop_meta = rf_specialist_predictions(
        tr_i, va_i, te_i, cats, nums, train_keep=keep
    )
    drop_metrics = metrics_for(test, "drop_train_anomalies", drop_pred)

    cats_i, nums_i = feature_lists(
        add_num=["iforest_anomaly_score", "iforest_anomaly_flag"]
    )
    indicator_pred, _, _ = rf_specialist_predictions(
        tr_i, va_i, te_i, cats_i, nums_i
    )
    indicator_metrics = metrics_for(test, "anomaly_indicator", indicator_pred)

    all_metrics = combine_metrics([
        ("keep_all", baseline_metrics),
        ("drop_train_anomalies", drop_metrics),
        ("anomaly_indicator", indicator_metrics),
    ])
    save_csv(all_metrics, out, "metrics_by_variant.csv")

    boots = []
    for name, pred in [
        ("drop_train_anomalies", drop_pred),
        ("anomaly_indicator", indicator_pred),
    ]:
        for metric in ["average_precision", "roc_auc"]:
            b = bootstrap_delta(test, pred, baseline_pred, metric=metric)
            b["candidate"] = name
            boots.append(b)
    boot = pd.DataFrame(boots)
    save_csv(boot, out, "bootstrap_delta_vs_keep_all.csv")

    flag = te_i["iforest_anomaly_flag"].eq(1).to_numpy()
    seg_rows = []
    for name, pred in [
        ("keep_all", baseline_pred),
        ("drop_train_anomalies", drop_pred),
        ("anomaly_indicator", indicator_pred),
    ]:
        for label, mask in [("iforest_flag", flag), ("normal", ~flag)]:
            if mask.sum() < 30:
                continue
            seg_rows.append({
                "variant": name,
                "segment": label,
                **metric_bundle(test.loc[mask, "target_30d"], pred[mask]),
            })
    save_csv(pd.DataFrame(seg_rows), out, "metrics_by_anomaly_segment.csv")

    b = boot[
        boot["candidate"].eq("drop_train_anomalies")
        & boot["metric"].eq("average_precision")
    ].iloc[0]
    if float(b["ci95_low"]) > 0 and float(b["point_delta"]) >= 0.005:
        conclusion = "SUPPORTED"
    elif float(b["point_delta"]) <= 0 or float(b["ci95_high"]) <= 0:
        conclusion = "NOT_SUPPORTED"
    else:
        conclusion = "INCONCLUSIVE"

    write_harness_results(
        out,
        "E024_outlier_handling",
        core_metrics_dict(drop_metrics, "drop_train_anomalies"),
        stage_metrics_dict(drop_metrics, "drop_train_anomalies"),
        conclusion,
        [
            "Isolation Forest is fit only on training data, outcome-free, with stage/sector/modality regimes and stage fallback.",
            "Temporal clocks and availability snapshot age are intentionally excluded from anomaly detection so anomaly does not simply mean late cohort.",
            "Held-out validation and test rows are never deleted.",
        ],
        "Remove deterministic Spot price-total redundancy while keeping the held-out population fixed.",
    )

    save_json(
        {
            "conclusion": conclusion,
            "train_rows_removed": int((~keep).sum()),
            "train_removed_rate": float((~keep).mean()),
            "drop_minus_keep_ap": float(b["point_delta"]),
            "drop_minus_keep_ap_ci95": [
                float(b["ci95_low"]),
                float(b["ci95_high"]),
            ],
            "drop_train_fit_rows": drop_meta["n_train_after_filter"],
        },
        out,
        "summary.json",
    )

    report = f"""# E024 - Outlier handling

## Hipotesis

Eliminar del entrenamiento el 3% de casos mas anomalos, definidos sin outcome, deberia mejorar generalizacion si realmente son ruido perjudicial.

**Conclusion: {conclusion}.**

- Train rows eliminadas: {int((~keep).sum()):,} ({float((~keep).mean()):.2%}).
- Drop - keep AP: {float(b['point_delta']):+.4f}.
- IC95%: [{float(b['ci95_low']):+.4f}, {float(b['ci95_high']):+.4f}].

## Metricas

{report_metric_table(all_metrics)}

El test permanece intacto. Por tanto, si borrar anomalies no mejora, no existe respaldo predictivo para limpiar esas filas solo por rareza.
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")


def run_e011_redundancy(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    baseline_pred: np.ndarray,
    baseline_metrics: pd.DataFrame,
) -> None:
    exp = EXPERIMENTS["E025_redundancy_ablation"]
    out = ensure_dir(exp / "results")
    removed = ["spot_price_total_mxn_rent", "spot_price_total_mxn_sale"]
    cats, nums = feature_lists(remove_num=removed)
    pred, _, _ = rf_specialist_predictions(train, val, test, cats, nums)
    metrics = metrics_for(test, "no_spot_price_totals", pred)
    all_metrics = combine_metrics([
        ("full", baseline_metrics),
        ("no_price_totals", metrics),
    ])
    save_csv(all_metrics, out, "metrics_by_variant.csv")

    boots = []
    for metric in ["average_precision", "roc_auc"]:
        boots.append(bootstrap_delta(test, pred, baseline_pred, metric=metric))
        for sid in STAGES:
            boots.append(
                bootstrap_delta(
                    test, pred, baseline_pred, metric=metric, stage_id=sid
                )
            )
    boot = pd.DataFrame(boots)
    save_csv(boot, out, "bootstrap_no_totals_minus_full.csv")
    ap = boot[
        boot["metric"].eq("average_precision") & boot["stage"].eq("MACRO")
    ].iloc[0]
    auc = boot[
        boot["metric"].eq("roc_auc") & boot["stage"].eq("MACRO")
    ].iloc[0]
    conclusion = (
        "SUPPORTED"
        if float(ap["ci95_low"]) >= -0.01
        and float(auc["ci95_low"]) >= -0.01
        else (
            "NOT_SUPPORTED"
            if float(ap["ci95_high"]) < -0.01
            else "INCONCLUSIVE"
        )
    )

    write_harness_results(
        out,
        "E025_redundancy_ablation",
        core_metrics_dict(metrics, "no_spot_price_totals"),
        stage_metrics_dict(metrics, "no_spot_price_totals"),
        conclusion,
        [
            "Non-inferiority margin is -0.01 for macro AP and macro ROC-AUC.",
            "Lead-Spot budget ratios are retained; the experiment tests direct redundancy of raw Spot total-price columns, not the value of economic fit.",
        ],
        "Ablate prior_searches and prior_inquiries separately to test whether their near-zero correlation corresponds to distinct predictive signal.",
    )

    report = f"""# E025 - Deterministic price redundancy

**Conclusion: {conclusion}.**

Se eliminan solo spot_price_total_mxn_rent y spot_price_total_mxn_sale, porque E020 mostro que son practicamente area x price_per_sqm.

- No totals - full AP: {float(ap['point_delta']):+.4f}, IC95% [{float(ap['ci95_low']):+.4f}, {float(ap['ci95_high']):+.4f}].
- No totals - full AUC: {float(auc['point_delta']):+.4f}, IC95% [{float(auc['ci95_low']):+.4f}, {float(auc['ci95_high']):+.4f}].

{report_metric_table(all_metrics)}
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")


def run_e012_prior_history(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    baseline_pred: np.ndarray,
    baseline_metrics: pd.DataFrame,
) -> None:
    exp = EXPERIMENTS["E026_prior_history_ablation"]
    out = ensure_dir(exp / "results")
    variants = {}
    metrics_items = [("full", baseline_metrics)]

    for name, removed in [
        ("drop_prior_searches", ["prior_searches"]),
        ("drop_prior_inquiries", ["prior_inquiries"]),
        ("drop_both", ["prior_searches", "prior_inquiries"]),
    ]:
        cats, nums = feature_lists(remove_num=removed)
        pred, _, _ = rf_specialist_predictions(train, val, test, cats, nums)
        variants[name] = pred
        metrics_items.append((name, metrics_for(test, name, pred)))

    all_metrics = combine_metrics(metrics_items)
    save_csv(all_metrics, out, "metrics_by_variant.csv")

    boots = []
    for name, pred in variants.items():
        for metric in ["average_precision", "roc_auc"]:
            b = bootstrap_delta(test, baseline_pred, pred, metric=metric)
            b["ablation"] = name
            boots.append(b)
            for sid in STAGES:
                x = bootstrap_delta(
                    test, baseline_pred, pred, metric=metric, stage_id=sid
                )
                x["ablation"] = name
                boots.append(x)
    boot = pd.DataFrame(boots)
    save_csv(boot, out, "bootstrap_full_minus_ablation.csv")

    a = boot[
        boot["ablation"].eq("drop_prior_searches")
        & boot["metric"].eq("average_precision")
        & boot["stage"].eq("MACRO")
    ].iloc[0]
    b = boot[
        boot["ablation"].eq("drop_prior_inquiries")
        & boot["metric"].eq("average_precision")
        & boot["stage"].eq("MACRO")
    ].iloc[0]

    if float(a["ci95_low"]) > 0 and float(b["ci95_low"]) > 0:
        conclusion = "SUPPORTED"
    elif float(a["point_delta"]) <= 0 and float(b["point_delta"]) <= 0:
        conclusion = "NOT_SUPPORTED"
    else:
        conclusion = "INCONCLUSIVE"

    drop_both_metrics = metrics_items[-1][1]
    write_harness_results(
        out,
        "E026_prior_history_ablation",
        core_metrics_dict(drop_both_metrics, "drop_both"),
        stage_metrics_dict(drop_both_metrics, "drop_both"),
        conclusion,
        [
            "Near-zero raw correlation does not imply redundancy; this experiment uses predictive ablation to test incremental contribution.",
            "Both fields are fixed lead-intake information and point-in-time safe at T0/T1/T2.",
        ],
        "Add a strictly point-in-time smoothed broker history prior without using broker identity itself.",
    )

    report = f"""# E026 - prior_searches vs prior_inquiries

**Conclusion: {conclusion}.**

La pregunta no es si ambas variables estan correlacionadas - E020 mostro que no - sino si cada una aporta senal incremental distinta.

- Full - drop prior_searches AP: {float(a['point_delta']):+.4f}, IC95% [{float(a['ci95_low']):+.4f}, {float(a['ci95_high']):+.4f}].
- Full - drop prior_inquiries AP: {float(b['point_delta']):+.4f}, IC95% [{float(b['ci95_low']):+.4f}, {float(b['ci95_high']):+.4f}].

{report_metric_table(all_metrics)}
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")


def broker_support_metrics(test: pd.DataFrame, pred: np.ndarray) -> pd.DataFrame:
    n = pd.to_numeric(test["broker_hist_responses"], errors="coerce")
    bucket = (
        pd.cut(
            n,
            [-np.inf, 0, 5, 20, 100, np.inf],
            labels=["0", "1-5", "6-20", "21-100", ">100"],
        )
        .astype("string")
        .fillna("missing")
    )
    rows = []
    for label in ["missing", "0", "1-5", "6-20", "21-100", ">100"]:
        mask = bucket.eq(label).to_numpy()
        if mask.sum() < 30:
            continue
        rows.append({
            "broker_history_bucket": label,
            **metric_bundle(test.loc[mask, "target_30d"], pred[mask]),
        })
    return pd.DataFrame(rows)


def run_e013_broker(
    split: pd.DataFrame,
    raw_data: tuple[pd.DataFrame, ...],
    baseline_pred: np.ndarray,
    baseline_metrics: pd.DataFrame,
) -> None:
    exp = EXPERIMENTS["E027_broker_prior_point_in_time"]
    out = ensure_dir(exp / "results")
    _, inquiries, spots, _, _ = raw_data
    d = add_broker_history(split, inquiries, spots)
    train = d[d["split"].eq("train")].copy().reset_index(drop=True)
    val = d[d["split"].eq("val")].copy().reset_index(drop=True)
    test = d[d["split"].eq("test")].copy().reset_index(drop=True)

    added = [
        "broker_hist_responses",
        "broker_hist_scheduled_visits",
        "broker_hist_scheduled_rate_laplace",
        "broker_hist_log_responses",
        "broker_hist_days_since_first_response",
    ]
    cats, nums = feature_lists(add_num=added)
    pred, _, _ = rf_specialist_predictions(train, val, test, cats, nums)
    metrics = metrics_for(test, "broker_prior", pred)

    all_metrics = combine_metrics([
        ("full_no_broker_prior", baseline_metrics),
        ("broker_prior", metrics),
    ])
    save_csv(all_metrics, out, "metrics_by_variant.csv")
    save_csv(
        broker_support_metrics(test, pred),
        out,
        "broker_prior_metrics_by_support.csv",
    )

    boots = []
    for metric in ["average_precision", "roc_auc"]:
        boots.append(bootstrap_delta(test, pred, baseline_pred, metric=metric))
        for sid in STAGES:
            boots.append(
                bootstrap_delta(
                    test, pred, baseline_pred, metric=metric, stage_id=sid
                )
            )
    boot = pd.DataFrame(boots)
    save_csv(boot, out, "bootstrap_broker_prior_minus_baseline.csv")

    ap = boot[
        boot["metric"].eq("average_precision") & boot["stage"].eq("MACRO")
    ].iloc[0]
    if float(ap["ci95_low"]) > 0:
        conclusion = "SUPPORTED"
    elif float(ap["ci95_high"]) < 0:
        conclusion = "NOT_SUPPORTED"
    else:
        conclusion = "INCONCLUSIVE"

    write_harness_results(
        out,
        "E027_broker_prior_point_in_time",
        core_metrics_dict(metrics, "broker_prior"),
        stage_metrics_dict(metrics, "broker_prior"),
        conclusion,
        [
            "Broker history uses only response_event_at strictly before score_time; the current inquiry response can never enter its own features.",
            "Laplace smoothing is fixed Beta(1,1) and does not use future/full-dataset target prevalence.",
            "This is predictive association, not a causal broker-quality estimate.",
            "T0 has no current spot/broker assignment, so broker-history features are missing there by design.",
        ],
        "If broker prior is promising, validate it on a later cohort and test routing causally; otherwise retain broker only as an analysis dimension.",
    )

    report = f"""# E027 - Point-in-time broker prior

**Conclusion: {conclusion}.**

- Broker prior - baseline AP: {float(ap['point_delta']):+.4f}.
- IC95% bootstrap por lead: [{float(ap['ci95_low']):+.4f}, {float(ap['ci95_high']):+.4f}].

El prior no usa broker_id como identidad categorica. Solo usa historial ya realizado antes del score: volumen de respuestas, scheduled visits previas y una tasa suavizada.

{report_metric_table(all_metrics)}

Incluso una mejora predictiva no probaria que reasignar un lead a ese broker cause mayor conversion; eso requeriria diseno de routing/experimento.
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")


def main() -> None:
    snapshots, split, raw_data = load_snapshot_data()
    train, val, test, baseline_pred, baseline_metrics, baseline_meta = (
        standard_baseline(split)
    )

    base_out = ensure_dir(HERE / "results")
    reconcile = reconcile_parent(baseline_metrics, base_out)
    save_csv(baseline_metrics, base_out, "frozen_rf_baseline_metrics.csv")
    save_json(baseline_meta, base_out, "frozen_rf_baseline_meta.json")

    run_e007_drift(snapshots)
    run_e008_temporal_ablation(
        train, val, test, baseline_pred, baseline_metrics
    )
    run_e009_availability(
        train, val, test, baseline_pred, baseline_metrics
    )
    run_e010_outliers(
        train, val, test, baseline_pred, baseline_metrics
    )
    run_e011_redundancy(
        train, val, test, baseline_pred, baseline_metrics
    )
    run_e012_prior_history(
        train, val, test, baseline_pred, baseline_metrics
    )
    run_e013_broker(
        split, raw_data, baseline_pred, baseline_metrics
    )

    summary = {
        "baseline_reconciliation": reconcile,
        "experiments": list(EXPERIMENTS),
    }
    save_json(summary, base_out, "suite_summary.json")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
