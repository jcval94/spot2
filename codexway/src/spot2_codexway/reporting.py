"""Reproducible figures, model card, business protocol and PDF deliverables."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from .contracts import Settings
from .evaluation import binary_metrics, categorical_js, population_stability_index


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def create_core_figures(t0: pd.DataFrame, t1: pd.DataFrame, scores: pd.DataFrame, settings: Settings) -> list[Path]:
    figures = settings.codexway_root / "outputs" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    t0m = t0[t0["target_t0_30d"].notna()].copy()
    t0m["month"] = t0m["prediction_timestamp"].dt.strftime("%Y-%m")
    t1m = t1[t1["target_t1"].notna()].copy()
    t1m["month"] = t1m["prediction_timestamp"].dt.strftime("%Y-%m")
    drift = t0m.groupby("month")["target_t0_30d"].mean().rename("T0 any visit in 30d").to_frame().join(
        t1m.groupby("month")["target_t1"].mean().rename("T1 first inquiry visit"), how="outer"
    )
    fig, ax = plt.subplots(figsize=(10, 4.5))
    drift.plot(marker="o", ax=ax)
    ax.set(title="Target drift: T0 exposure vs stable T1 proxy", xlabel="Month", ylabel="Positive rate")
    ax.tick_params(axis="x", rotation=45)
    path = figures / "target_drift.png"; _save(fig, path); paths.append(path)

    coverage = t1.assign(
        month=t1["prediction_timestamp"].dt.strftime("%Y-%m"),
        historical_snapshot=t1["snapshot_date"].notna(),
        fresh_snapshot=t1["availability_snapshot_age_days"].le(settings.availability_freshness_days),
    ).groupby("month")[["historical_snapshot", "fresh_snapshot"]].mean()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    coverage.plot(marker="o", ax=ax)
    ax.set(title="Availability coverage under strict backward as-of", xlabel="Month", ylabel="Coverage")
    ax.tick_params(axis="x", rotation=45)
    path = figures / "availability_coverage.png"; _save(fig, path); paths.append(path)

    fig, ax = plt.subplots(figsize=(6, 5))
    ordered = scores.sort_values("selected_calibrated", ascending=False).reset_index(drop=True)
    ordered["population_share"] = (np.arange(len(ordered)) + 1) / len(ordered)
    positives = max(1, ordered["target_t1"].sum())
    ordered["cumulative_positive_share"] = ordered["target_t1"].cumsum() / positives
    ax.plot(ordered["population_share"], ordered["cumulative_positive_share"], label="Selected score")
    ax.plot([0, 1], [0, 1], linestyle="--", color="grey", label="Random")
    ax.set(title="Cumulative gains — procedural holdout", xlabel="Leads worked", ylabel="Positive outcomes captured")
    ax.legend()
    path = figures / "gains_curve.png"; _save(fig, path); paths.append(path)

    fig, ax = plt.subplots(figsize=(6, 5))
    cal = pd.qcut(scores["selected_calibrated"], q=min(10, scores["selected_calibrated"].nunique()), duplicates="drop")
    calibration = scores.assign(bin=cal).groupby("bin", observed=True).agg(
        predicted=("selected_calibrated", "mean"), observed=("target_t1", "mean")
    )
    ax.plot(calibration["predicted"], calibration["observed"], marker="o")
    ax.plot([0, 1], [0, 1], linestyle="--", color="grey")
    ax.set(title="Calibration — procedural holdout", xlabel="Mean predicted", ylabel="Observed")
    path = figures / "calibration_plot.png"; _save(fig, path); paths.append(path)
    return paths


def write_online_protocol(scores: pd.DataFrame, settings: Settings) -> Path:
    baseline = float(scores["target_t1"].mean())
    alpha, power, relative_mde = 0.05, 0.80, 0.10
    p2 = min(0.999, baseline * (1 + relative_mde))
    z_alpha, z_power = 1.96, 0.8416
    pooled = (baseline + p2) / 2
    n_arm = math.ceil(
        (z_alpha * math.sqrt(2 * pooled * (1 - pooled)) + z_power * math.sqrt(baseline * (1 - baseline) + p2 * (1 - p2))) ** 2
        / max(1e-12, (p2 - baseline) ** 2)
    )
    protocol = {
        "activation_status": (
            "ELIGIBLE_AFTER_NEW_FORWARD_SHADOW_VALIDATION"
            if binary_metrics(scores["target_t1"], scores["selected_calibrated"])["lift_top_10pct"] > 1
            else "FUTURE_PROTOCOL_NOT_APPROVED_BY_CURRENT_OFFLINE_GATE"
        ),
        "power_estimate_status": "ILLUSTRATIVE_RECALCULATE_WITH_MATURE_30D_PILOT_RATE",
        "assumptions": {"offline_first_inquiry_proxy_rate": baseline, "relative_mde": relative_mde, "alpha": alpha, "power": power, "illustrative_n_per_arm": n_arm},
        "opportunity_ranking_test": {
            "unit": "lead_id", "allocation": "50/50 sticky", "analysis": "intention_to_treat",
            "treatment": "work leads by Opportunity Score top-down", "control": "current operational ordering",
            "primary_metric": "scheduled_visit within 30 days", "guardrails": ["time_to_first_contact", "contact_attempts", "broker workload", "opt_out_rate"],
            "strata": ["search_sector", "source", "calendar_week"], "horizon_days": 30,
        },
        "fallback_routing_test": {
            "unit": "lead_id", "allocation": "50/50 sticky", "analysis": "intention_to_treat",
            "treatment": "ranked backward-as-of fallback recommendations", "control": "current fallback process",
            "primary_metric": "accepted alternative or scheduled visit within 30 days",
            "guardrails": ["recommendation_latency", "no_result_rate", "distance_relaxation", "complaint_rate"],
        },
        "validity_checks": ["sample_ratio_mismatch", "sticky_assignment", "pre-treatment eligibility", "censoring maturity"],
    }
    path = settings.codexway_root / "outputs" / "tables" / "online_ab_protocol.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(protocol, indent=2), encoding="utf-8")
    return path


def write_model_card(model_result: dict[str, Any], settings: Settings) -> Path:
    metrics = model_result["metrics"]["selected_calibrated"]
    ranking_go = metrics["average_precision"] > metrics["positive_rate"] and metrics["lift_top_10pct"] > 1
    system_path = settings.codexway_root / "outputs" / "metrics" / "system_evaluation.json"
    system = json.loads(system_path.read_text(encoding="utf-8")) if system_path.exists() else {}
    intervals_path = settings.codexway_root / "outputs" / "metrics" / "t1_metric_intervals.csv"
    intervals = pd.read_csv(intervals_path) if intervals_path.exists() else pd.DataFrame()
    auc_interval = intervals[(intervals.get("score") == "selected_calibrated") & (intervals.get("metric") == "roc_auc")]
    auc_ci = (
        f"[{auc_interval.iloc[0]['ci_low']:.4f}, {auc_interval.iloc[0]['ci_high']:.4f}]"
        if len(auc_interval) else "not available"
    )
    text = f"""# T1 model card

## Intended use

Rank one lead at its first inquiry, before broker response. This is a first-contact
progress proxy, not true conversion probability.

## Model

Selected by the E113 rolling-CV/validation promotion gate:
**{model_result['winner']}**. Calibration decision:
`{model_result['calibration']['kept']}`. The feature hypothesis is retrospective
because the historical holdout had already been globally consumed; E115 requires
new forward confirmation.

Offline ranking gate: **{'GO' if ranking_go else 'NO-GO'}**. The score artifact is
generated for reproducibility, but must not automate routing when this gate fails.

## Procedural holdout

- ROC-AUC: {metrics['roc_auc']:.4f}
- ROC-AUC bootstrap 95% CI: {auc_ci}
- PR-AUC: {metrics['average_precision']:.4f}
- Log Loss: {metrics['log_loss']:.4f}
- Brier: {metrics['brier']:.4f}
- Recall@5/10/20%: {metrics['recall_top_5pct']:.3f} / {metrics['recall_top_10pct']:.3f} / {metrics['recall_top_20pct']:.3f}
- Lift@5/10%: {metrics['lift_top_5pct']:.3f} / {metrics['lift_top_10pct']:.3f}

## Non-negotiable exclusions

Broker response/time, internal score, future inquiries, mutable spot counters,
future/nearest snapshots, market context and LLM text features.

## System-level decision

Combined Opportunity gate: **{system.get('system_deployment_gate', 'NOT_EVALUATED')}**.
The conservative combination has AP {system.get('opportunity_average_precision', float('nan')):.4f}
versus {system.get('quality_average_precision', float('nan')):.4f} for Lead Quality.
It remains diagnostic because the observed T1 target does not measure fallback success.

## Limitations

Synthetic/small data, imperfect outcome proxy, globally consumed historical
holdout, unversioned listing state and observational offline evaluation. A GO is
eligibility for new forward validation, not permission for automatic deployment.
"""
    path = settings.codexway_root / "outputs" / "MODEL_CARD.md"
    path.write_text(text, encoding="utf-8")
    return path


def write_model_diagnostics(
    t1: pd.DataFrame,
    quality_probabilities: np.ndarray,
    model_result: dict[str, Any],
    settings: Settings,
) -> dict[str, Path]:
    """Importance, error analysis, monthly stability and an explicit GO/NO-GO gate."""
    tables = settings.codexway_root / "outputs" / "tables"; tables.mkdir(parents=True, exist_ok=True)
    metrics_dir = settings.codexway_root / "outputs" / "metrics"; metrics_dir.mkdir(parents=True, exist_ok=True)
    bundle = model_result["bundle"]
    if bundle.name == "logistic":
        preprocess = bundle.model.named_steps["preprocess"]
        names = preprocess.get_feature_names_out()
        coefficients = bundle.model.named_steps["model"].coef_[0]
        importance = pd.DataFrame({"feature": names, "importance": np.abs(coefficients), "signed_effect": coefficients})
        importance["method"] = "absolute_standardized_logistic_coefficient"
    else:
        importance = pd.DataFrame({
            "feature": bundle.features,
            "importance": bundle.model.get_feature_importance(),
            "signed_effect": np.nan,
            "method": "catboost_prediction_values_change",
        })
    importance = importance.sort_values("importance", ascending=False)
    importance_path = tables / "feature_importance.csv"; importance.to_csv(importance_path, index=False)

    scored = t1[["lead_id", "prediction_timestamp", "split", "target_t1", "search_sector", "source", "channel"]].copy()
    scored["score"] = quality_probabilities
    val_threshold = float(scored.loc[scored["split"].eq("validation"), "score"].quantile(0.90))
    test = scored[scored["split"].eq("test")].copy()
    test["predicted_priority"] = test["score"] >= val_threshold
    test["error_type"] = np.select(
        [test["predicted_priority"] & test["target_t1"].eq(0), ~test["predicted_priority"] & test["target_t1"].eq(1)],
        ["false_positive", "false_negative"], default="correct_or_nonpriority_negative",
    )
    errors = test[test["error_type"].isin(["false_positive", "false_negative"])].copy()
    errors_path = tables / "error_analysis.csv"; errors.to_csv(errors_path, index=False)

    test["month"] = test["prediction_timestamp"].dt.strftime("%Y-%m")
    monthly_rows = []
    for month, group in test.groupby("month"):
        if group["target_t1"].nunique() < 2:
            continue
        monthly_rows.append({"month": month, **binary_metrics(group["target_t1"].astype(int), group["score"])})
    monthly = pd.DataFrame(monthly_rows)
    monthly_path = tables / "monthly_model_stability.csv"; monthly.to_csv(monthly_path, index=False)

    train = t1[t1["split"].eq("train")]
    holdout = t1[t1["split"].eq("test")]
    drift_rows = []
    for feature in bundle.features:
        if feature in bundle.categorical:
            drift_rows.append({"feature": feature, "metric": "jensen_shannon", "value": categorical_js(train[feature], holdout[feature])})
        else:
            drift_rows.append({"feature": feature, "metric": "psi", "value": population_stability_index(train[feature], holdout[feature])})
    drift = pd.DataFrame(drift_rows)
    drift_path = tables / "feature_drift.csv"; drift.to_csv(drift_path, index=False)

    holdout_metrics = model_result["metrics"]["selected_calibrated"]
    readiness = {
        "decision": "GO" if holdout_metrics["average_precision"] > holdout_metrics["positive_rate"] and holdout_metrics["lift_top_10pct"] > 1 else "NO_GO",
        "gate": "PR-AUC > prevalence and Lift@10% > 1 on procedural holdout",
        "average_precision": holdout_metrics["average_precision"],
        "positive_rate": holdout_metrics["positive_rate"],
        "lift_top_10pct": holdout_metrics["lift_top_10pct"],
        "validation_priority_threshold": val_threshold,
        "recommendation": "Do not automate ranking; collect a stronger downstream outcome and new predictive features." if holdout_metrics["lift_top_10pct"] <= 1 else "Proceed only with guarded monitoring and randomized evaluation.",
        "shap_status": "NOT_NEEDED_LOGISTIC_SELECTED" if bundle.name == "logistic" else "AVAILABLE_ON_REQUEST_CATBOOST",
    }
    readiness_path = metrics_dir / "deployment_readiness.json"
    readiness_path.write_text(json.dumps(readiness, indent=2), encoding="utf-8")
    return {"importance": importance_path, "errors": errors_path, "monthly": monthly_path, "drift": drift_path, "readiness": readiness_path}


def _page(title: str, bullets: list[str], footer: str = "Spot2 · codexway") -> plt.Figure:
    fig = plt.figure(figsize=(13.333, 7.5))
    fig.patch.set_facecolor("#F7F8FA")
    fig.text(0.06, 0.88, title, fontsize=25, fontweight="bold", color="#14213D")
    y = 0.77
    for bullet in bullets:
        fig.text(0.075, y, f"• {bullet}", fontsize=15, color="#263238", wrap=True)
        y -= 0.105
    fig.text(0.06, 0.04, footer, fontsize=9, color="#607D8B")
    return fig


def _image_slide(title: str, image_path: Path, bullets: list[str], footer: str = "Spot2 · codexway") -> plt.Figure:
    fig = plt.figure(figsize=(13.333, 7.5)); fig.patch.set_facecolor("#F7F8FA")
    fig.text(0.055, 0.90, title, fontsize=24, fontweight="bold", color="#14213D")
    ax = fig.add_axes([0.055, 0.15, 0.57, 0.67]); ax.axis("off")
    if image_path.exists():
        ax.imshow(plt.imread(image_path)); ax.set_aspect("auto")
    y = 0.76
    for bullet in bullets:
        fig.text(0.67, y, f"• {bullet}", fontsize=13.2, color="#263238", wrap=True)
        y -= 0.14
    fig.text(0.055, 0.045, footer, fontsize=9, color="#607D8B")
    return fig


def render_pdfs(
    model_result: dict[str, Any],
    opportunity: pd.DataFrame,
    llm_status: dict[str, Any],
    settings: Settings,
    *,
    system_evaluation: dict[str, Any] | None = None,
) -> list[Path]:
    reports = settings.codexway_root / "reports"; reports.mkdir(parents=True, exist_ok=True)
    metrics = model_result["metrics"]["selected_calibrated"]
    ranking_go = metrics["average_precision"] > metrics["positive_rate"] and metrics["lift_top_10pct"] > 1
    system_evaluation = system_evaluation or {}
    system_go = system_evaluation.get("system_deployment_gate") == "GO"
    recommendation = "Guarded pilot eligible" if system_go else "Do not automate prioritization"
    system_csv = settings.codexway_root / "outputs" / "metrics" / "system_score_metrics.csv"
    system_metrics = pd.read_csv(system_csv).set_index("score") if system_csv.exists() else pd.DataFrame()
    quality_lift = float(metrics["lift_top_10pct"])
    opportunity_lift = float(system_metrics.loc["opportunity_lower_bound", "lift_top_10pct"]) if not system_metrics.empty else float("nan")

    # One-page executive brief with an actual decision graphic.
    one = plt.figure(figsize=(11.69, 8.27)); one.patch.set_facecolor("#F7F8FA")
    one.text(0.055, 0.92, "Lead Opportunity Score — decision brief", fontsize=24, fontweight="bold", color="#14213D")
    decision_color = "#B42318" if not system_go else "#027A48"
    one.text(0.055, 0.845, recommendation.upper(), fontsize=17, fontweight="bold", color="white",
             bbox={"boxstyle": "round,pad=0.55", "facecolor": decision_color, "edgecolor": decision_color})
    ax = one.add_axes([0.06, 0.48, 0.40, 0.27])
    ax.bar(["Random", "Lead quality", "Opportunity"], [1.0, quality_lift, opportunity_lift], color=["#98A2B3", "#6C63FF", "#00A6A6"])
    ax.axhline(1, color="#344054", linewidth=1); ax.set_ylabel("Lift in top 10%")
    ax.set_title("What happens when capacity is limited")
    for index, value in enumerate([1.0, quality_lift, opportunity_lift]): ax.text(index, value + 0.025, f"{value:.2f}x", ha="center", fontsize=10)
    one.text(0.52, 0.72, "What we learned", fontsize=16, fontweight="bold", color="#14213D")
    findings = ([
        f"Lead Quality reaches {quality_lift:.2f}x lift in the top 10%.",
        f"Opportunity retains {opportunity_lift:.2f}x after inventory constraints.",
        "Inventory reduces lift versus quality alone; incremental value is unproven.",
        "A future snapshot is never used; missing history stays unknown.",
    ] if system_go else [
        "The clean model does not beat random prioritization reliably.",
        "Adding inventory makes ranking worse on the observed proxy.",
        "A future snapshot is never used; missing history stays unknown.",
        "Fallback remains a product hypothesis, not a proven outcome model.",
    ])
    y = 0.665
    for finding in findings:
        one.text(0.52, y, f"• {finding}", fontsize=11.7, color="#263238", wrap=True); y -= 0.075
    one.text(0.06, 0.375, "Recommended next move", fontsize=16, fontweight="bold", color="#14213D")
    next_move = (
        "Run a forward shadow period, then a guarded randomized pilot; do not automate from this retrospectively consumed holdout alone."
        if system_go else
        "Keep current workflow. Instrument downstream conversion and historical listing versions; then rerun the temporal gate."
    )
    one.text(0.06, 0.325, next_move, fontsize=12.5, color="#263238", wrap=True)
    one.text(0.06, 0.24, "Safe operational view", fontsize=16, fontweight="bold", color="#14213D")
    one.text(0.06, 0.19, "Show Lead Quality and Inventory Confidence as separate axes; the combined score passes the absolute lift gate but inventory incremental value is not proven.", fontsize=12.5, color="#263238", wrap=True)
    llm_brief = "controlled synthetic test complete; natural review pending" if llm_status.get("status", "").startswith("CONTROLLED_") else llm_status.get("status", "not run")
    score_status = "forward-validation candidate" if system_go else "diagnostic only"
    one.text(0.06, 0.09, f"Contract: first inquiry before broker response · maturity: 7 days · LLM QA: {llm_brief} · score status: {score_status}", fontsize=9.5, color="#667085")
    one_path = reports / "one_pager.pdf"; one.savefig(one_path, format="pdf", bbox_inches="tight"); plt.close(one)

    slides_path = reports / "slides.pdf"
    with PdfPages(slides_path) as pdf:
        fig = _page("Lead Opportunity — executive decision", [
            recommendation,
            f"Lead Quality lift@10: {quality_lift:.2f}x; combined Opportunity: {opportunity_lift:.2f}x.",
            "The code gate uses rolling CV and validation; evidence remains retrospective.",
            "Retain two axes because inventory incremental value is still unproven.",
        ]); pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)
        image_pages = [
            ("Why the contract is T1", "target_drift.png", ["T0 changes with inquiry exposure.", "T1 scores one lead at first inquiry.", "Recent outcomes remain censored."]),
            ("Point-in-time inventory", "availability_coverage.png", ["Backward as-of only.", "Unknown history is not unavailability.", "Listing fields remain conditionally historical."]),
            ("Demand and data context", "eda_lead_mix.png", ["Mix differs by sector and modality.", "Market context is EDA-only.", "No mutable spot counters enter the model."]),
            ("Ranking on the procedural holdout", "gains_curve.png", [f"Top 10% captures {metrics['recall_top_10pct']:.1%} of positives.", f"Lift@10 is {quality_lift:.2f}x.", "Bootstrap intervals include random ranking."]),
            ("Probability calibration", "calibration_plot.png", [f"Brier: {metrics['brier']:.3f}.", "Calibration is assessed against the train-rate baseline.", "Ranking lift and probability calibration are separate gates."]),
        ]
        for title, name, bullets in image_pages:
            fig = _image_slide(title, settings.codexway_root / "outputs" / "figures" / name, bullets)
            pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)
        fig = _page("Recommendation and product roadmap", [
            "Run a new forward shadow period before changing lead routing.",
            "Version listing state and log offer/recommendation exposure.",
            "Measure scheduled visit and downstream conversion at 30 days.",
            f"LLM semantic QA: {llm_brief}; keep it outside historical scoring.",
            "Then run a guarded randomized pilot with downstream outcomes.",
        ]); pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)
    return [one_path, slides_path]
