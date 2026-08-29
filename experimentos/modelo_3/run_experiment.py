from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from data_pipeline import (
    CAT_FEATURES, FORBIDDEN_COLUMNS, NUM_FEATURES, STAGES, build_snapshots, make_preprocessor,
    prepare_inquiries, read_data, stage_balanced_weights, temporal_split,
)
from models import (
    CORE_METRICS, PooledStageModel, SharedMultiHead, calibrate_by_stage, metrics_table, predict,
    separate_logistic_predictions, set_seed, train_model,
)

EXPERIMENT_ID = "E003_modelo_3_multihead"
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "results"
ART = Path(__file__).resolve().parent / "artifacts"
OUT.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)


def render_summary(snapshots, metrics, conclusion, reason, split_counts) -> str:
    lines = [
        "# Modelo 3 — shared backbone + stage heads", "", "## Decision", "",
        f"**{conclusion}** — {reason}", "",
        "- T0_cold: lead creation.",
        "- T1_first_inquiry: first observable intent event.",
        "- T2_engaged: second and later inquiries before conversion.", "",
        "Target: future \`scheduled_visit\` response event within 30 days from each scoring timestamp.", "",
        "## Test metrics", "",
        "| Model | Stage | ROC AUC | Avg Precision | Brier | Log loss | Lift@10% |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for model in ["multihead_calibrated", "pooled_calibrated", "separate_logistic"]:
        for stage in [*STAGES.values(), "MACRO"]:
            s = metrics[(metrics.model == model) & (metrics.stage == stage)]
            if s.empty:
                continue
            r = s.iloc[0]
            lines.append(
                f"| {model} | {stage} | {r.roc_auc:.3f} | {r.average_precision:.3f} | "
                f"{r.brier:.3f} | {r.log_loss:.3f} | {r.lift_top_10pct:.2f}x |"
            )
    lines += ["", "## Population", "",
              f"- Eligible snapshots: {len(snapshots):,}.",
              f"- Unique leads: {snapshots.lead_id.nunique():,}.",
              "- All snapshots for a lead stay in the same temporal cohort.", "",
              "| Split | Stage | Rows | Positive rate |", "|---|---|---:|---:|"]
    for r in split_counts.to_dict("records"):
        lines.append(f"| {r['split']} | {r['stage']} | {int(r['n']):,} | {r['positive_rate']:.1%} |")
    lines += [
        "", "## Leakage controls", "",
        "- \`lead_score_internal\` is blocked.",
        "- Current/future broker response outcome and response time are not model inputs.",
        "- Historical response features require response_event_at <= scoring time.",
        "- Mutable spot snapshot fields (\`total_views\`, \`total_inquiries\`, \`days_on_market\`, \`is_active\`) are excluded.",
        "- Availability uses only the latest snapshot at or before scoring time.",
        "- Right-censored snapshots and post-conversion snapshots are excluded.", "",
        "## Interpretation", "",
        "This directly tests the architectural question: whether stage-specific heads add value beyond a single model that simply receives stage as a feature. "
        "A win for multi-head supports stage-specific decision/calibration behavior while retaining shared statistical strength.", "",
        "The dataset is synthetic and \`scheduled_visit\` is a proxy, so this supports a predictive architecture decision rather than a causal claim.",
    ]
    return "\n".join(lines) + "\n"


def macro_row(metrics: pd.DataFrame, model: str) -> pd.Series:
    return metrics[(metrics.model == model) & (metrics.stage == "MACRO")].iloc[0]


def main() -> None:
    set_seed()
    leads, inquiries_raw, spots, attrs, availability = read_data(ROOT)
    inquiries = prepare_inquiries(inquiries_raw)
    snapshots = temporal_split(build_snapshots(leads, inquiries, spots, attrs, availability))

    forbidden = FORBIDDEN_COLUMNS & set(CAT_FEATURES + NUM_FEATURES)
    if forbidden:
        raise RuntimeError(f"Forbidden leakage features: {sorted(forbidden)}")
    missing = set(CAT_FEATURES + NUM_FEATURES + ["stage_id", "target_30d", "split"]) - set(snapshots.columns)
    if missing:
        raise RuntimeError(f"Missing engineered columns: {sorted(missing)}")

    train = snapshots[snapshots.split == "train"].copy().reset_index(drop=True)
    val = snapshots[snapshots.split == "val"].copy().reset_index(drop=True)
    test = snapshots[snapshots.split == "test"].copy().reset_index(drop=True)
    if min(map(len, [train, val, test])) == 0:
        raise RuntimeError("Temporal split produced an empty partition")
    for frame in [train, val, test]:
        for c in CAT_FEATURES:
            frame[c] = frame[c].astype("object")
            frame[c] = frame[c].where(frame[c].notna(), np.nan)

    prep = make_preprocessor()
    x_train = np.asarray(prep.fit_transform(train[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)
    x_val = np.asarray(prep.transform(val[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)
    x_test = np.asarray(prep.transform(test[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)
    y_train, y_val, y_test = [f.target_30d.to_numpy(dtype=np.int64) for f in [train, val, test]]
    s_train, s_val, s_test = [f.stage_id.to_numpy(dtype=np.int64) for f in [train, val, test]]
    weights = stage_balanced_weights(train)

    set_seed(); multi = SharedMultiHead(x_train.shape[1])
    multi, mh_hist = train_model(multi, x_train, y_train, s_train, weights, x_val, y_val, s_val)
    mh_val, mh_test = predict(multi, x_val, s_val), predict(multi, x_test, s_test)
    mh_cal, mh_params = calibrate_by_stage(mh_val, y_val, s_val, mh_test, s_test)

    set_seed(); pooled = PooledStageModel(x_train.shape[1])
    pooled, pool_hist = train_model(pooled, x_train, y_train, s_train, weights, x_val, y_val, s_val)
    pool_val, pool_test = predict(pooled, x_val, s_val), predict(pooled, x_test, s_test)
    pool_cal, pool_params = calibrate_by_stage(pool_val, y_val, s_val, pool_test, s_test)

    logit = separate_logistic_predictions(x_train, y_train, s_train, x_test, s_test)
    predictions = {
        "multihead_raw": mh_test, "multihead_calibrated": mh_cal,
        "pooled_raw": pool_test, "pooled_calibrated": pool_cal, "separate_logistic": logit,
    }
    metrics = metrics_table(test, predictions)
    mh, pool, lg = [macro_row(metrics, m) for m in ["multihead_calibrated", "pooled_calibrated", "separate_logistic"]]
    ap_delta = float(mh.average_precision - pool.average_precision)
    auc_delta = float(mh.roc_auc - pool.roc_auc)
    brier_delta = float(mh.brier - pool.brier)

    if ap_delta >= 0.005 and auc_delta >= -0.01:
        conclusion = "SUPPORTED"
        reason = f"multi-head improves macro AP vs pooled by {ap_delta:+.3f}, with ROC-AUC delta {auc_delta:+.3f}."
    elif ap_delta <= -0.01 and auc_delta <= -0.01:
        conclusion = "NOT_SUPPORTED"
        reason = f"multi-head underperforms pooled on macro AP ({ap_delta:+.3f}) and ROC-AUC ({auc_delta:+.3f})."
    else:
        conclusion = "INCONCLUSIVE"
        reason = f"multi-head and pooled are close: AP {ap_delta:+.3f}, ROC-AUC {auc_delta:+.3f}, Brier {brier_delta:+.3f}."

    metrics.to_csv(OUT / "metrics_by_stage.csv", index=False)
    mh_hist.to_csv(OUT / "training_history_multihead.csv", index=False)
    pool_hist.to_csv(OUT / "training_history_pooled.csv", index=False)
    split_counts = snapshots.groupby(["split", "stage"], as_index=False).agg(
        n=("row_id", "size"), positive_rate=("target_30d", "mean")
    ).sort_values(["split", "stage"])
    split_counts.to_csv(OUT / "population_by_stage.csv", index=False)
    (OUT / "calibration.json").write_text(json.dumps(
        {"multihead": mh_params, "pooled": pool_params}, indent=2, ensure_ascii=False
    ) + "\n", encoding="utf-8")

    summary = {
        "experiment_id": EXPERIMENT_ID,
        "architecture": {"backbone": [128, 64], "heads": STAGES, "horizon_days": 30},
        "population": {
            "eligible_snapshots": int(len(snapshots)), "unique_leads": int(snapshots.lead_id.nunique()),
            "observation_end": str(snapshots.observation_end.iloc[0]), "censor_cutoff": str(snapshots.censor_cutoff.iloc[0]),
        },
        "comparison": {
            "multihead_vs_pooled_macro_ap_delta": ap_delta,
            "multihead_vs_pooled_macro_auc_delta": auc_delta,
            "multihead_vs_pooled_macro_brier_delta": brier_delta,
            "multihead_vs_separate_logistic_macro_ap_delta": float(mh.average_precision - lg.average_precision),
        },
        "conclusion": conclusion, "reason": reason,
        "macro_metrics": {
            "multihead_calibrated": {m: float(mh[m]) for m in CORE_METRICS},
            "pooled_calibrated": {m: float(pool[m]) for m in CORE_METRICS},
            "separate_logistic": {m: float(lg[m]) for m in CORE_METRICS},
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary_md = render_summary(snapshots, metrics, conclusion, reason, split_counts)
    (OUT / "summary.md").write_text(summary_md, encoding="utf-8")

    pred_df = test[["lead_id", "stage", "score_time", "target_30d", "inquiry_id", "spot_id"]].copy()
    for name, values in predictions.items(): pred_df[name] = values
    pred_df.to_csv(ART / "test_predictions.csv", index=False)
    torch.save({"model_state_dict": multi.state_dict(), "input_dim": x_train.shape[1], "stages": STAGES}, ART / "multihead_model.pt")

    harness = {
        "experiment_id": EXPERIMENT_ID,
        "metrics": {m: float(mh[m]) for m in CORE_METRICS},
        "segment_metrics": {
            stage: {m: float(metrics[(metrics.model == "multihead_calibrated") & (metrics.stage == stage)].iloc[0][m]) for m in CORE_METRICS}
            for stage in STAGES.values()
        },
        "conclusion": conclusion,
        "caveats": [
            "scheduled_visit is a supervised proxy for commercial conversion, not the hidden final outcome",
            "the dataset is synthetic, so architecture conclusions need production validation",
            "T2 contains repeated pre-conversion scoring events; train/test isolation is enforced at lead level",
            "broker response timing is used only to establish when historical information became observable",
        ],
        "next_experiment": "Compare the winning stage architecture with a lead-by-spot ranking model and head-specific Growth thresholds."
    }
    (OUT / "harness_results.json").write_text(json.dumps(harness, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(summary_md)


if __name__ == "__main__":
    main()
