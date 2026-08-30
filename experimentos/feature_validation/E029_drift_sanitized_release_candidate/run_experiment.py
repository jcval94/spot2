from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

HERE = Path(__file__).resolve().parent
FV = HERE.parent
ROOT = HERE.parents[2]
E028 = FV / "E028_definitive_opportunity_score_abt"
for p in [FV, E028]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from common import (  # noqa: E402
    AVAIL_CAT,
    AVAIL_NUM,
    feature_lists,
    load_snapshot_data,
    make_preprocessor,
    metric_bundle,
    normalize_frames,
    psi_numeric,
)
from target_contract import TARGET_NAME, label_scoring_snapshots  # noqa: E402

SEED = 42
N_BOOT = 1000
RESULTS = HERE / "results"
ARTIFACTS = HERE / "artifacts"
RESULTS.mkdir(parents=True, exist_ok=True)
ARTIFACTS.mkdir(parents=True, exist_ok=True)

REMOVE_CAT = ["score_weekday", *AVAIL_CAT]
REMOVE_NUM = [
    "score_hour",
    "score_month",
    "days_from_lead_creation",
    "inquiry_number",
    "days_since_first_inquiry",
    "prior_searches",
    *AVAIL_NUM,
    "has_availability_context",
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def corrected_t2() -> tuple[pd.DataFrame, dict[str, object]]:
    snapshots, _, raw = load_snapshot_data()
    _, inquiries, _, _, _ = raw

    labeled = label_scoring_snapshots(snapshots, inquiries)
    audit = (
        labeled["target_status"]
        .value_counts(dropna=False)
        .rename_axis("target_status")
        .reset_index(name="n")
    )
    audit["share"] = audit["n"] / len(labeled)
    audit.to_csv(RESULTS / "target_status_audit.csv", index=False)

    eligible = labeled[
        labeled["stage_id"].eq(2)
        & labeled["target_status"].isin(["POSITIVE", "NEGATIVE"])
    ].copy()
    eligible["target_30d"] = pd.to_numeric(eligible[TARGET_NAME], errors="raise").astype(int)
    eligible["lead_month"] = eligible["created_at"].dt.to_period("M").astype(str)
    eligible = eligible.sort_values(["created_at", "lead_id", "score_time", "row_id"]).reset_index(drop=True)

    first_t2 = eligible.sort_values(["lead_id", "score_time", "row_id"]).drop_duplicates("lead_id")
    summary = {
        "all_snapshots_before_canonical_filter": int(len(labeled)),
        "eligible_t2_snapshots": int(len(eligible)),
        "eligible_t2_unique_leads": int(eligible["lead_id"].nunique()),
        "first_t2_unique_leads": int(len(first_t2)),
        "positive_rate_t2_all": float(eligible["target_30d"].mean()) if len(eligible) else None,
        "positive_rate_first_t2": float(first_t2["target_30d"].mean()) if len(first_t2) else None,
        "target_observation_end": str(labeled["target_observation_end"].iloc[0]) if len(labeled) else None,
        "ambiguous_rows_all_stages": int(labeled["target_status"].eq("AMBIGUOUS_UNKNOWN_EVENT_TIME").sum()),
        "ambiguous_share_all_stages": float(labeled["target_status"].eq("AMBIGUOUS_UNKNOWN_EVENT_TIME").mean()),
    }
    return eligible, summary


def feature_policy() -> tuple[list[str], list[str]]:
    cats, nums = feature_lists(remove_cat=REMOVE_CAT, remove_num=REMOVE_NUM)
    forbidden = set(REMOVE_CAT + REMOVE_NUM)
    overlap = forbidden & set(cats + nums)
    if overlap:
        raise RuntimeError(f"Blocked features survived feature policy: {sorted(overlap)}")
    if any(c.startswith("broker_hist_") for c in cats + nums):
        raise RuntimeError("Broker prior leaked into E029")
    return cats, nums


def fit_rf(
    train: pd.DataFrame,
    calibration: pd.DataFrame,
    score: pd.DataFrame,
    cat_cols: list[str],
    num_cols: list[str],
) -> tuple[np.ndarray, object, RandomForestClassifier, object, dict[str, object]]:
    tr = train.copy().reset_index(drop=True)
    ca = calibration.copy().reset_index(drop=True)
    sc = score.copy().reset_index(drop=True)
    normalize_frames([tr, ca, sc], cat_cols, num_cols)

    prep = make_preprocessor(cat_cols, num_cols)
    x_train = np.asarray(prep.fit_transform(tr[cat_cols + num_cols]), dtype=np.float32)
    x_cal = np.asarray(prep.transform(ca[cat_cols + num_cols]), dtype=np.float32)
    x_score = np.asarray(prep.transform(sc[cat_cols + num_cols]), dtype=np.float32)

    y_train = tr["target_30d"].to_numpy(dtype=int)
    y_cal = ca["target_30d"].to_numpy(dtype=int)

    model = RandomForestClassifier(
        n_estimators=500,
        min_samples_leaf=12,
        max_features="sqrt",
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=SEED,
    )
    model.fit(x_train, y_train)
    cal_raw = np.clip(model.predict_proba(x_cal)[:, 1], 1e-6, 1 - 1e-6)
    score_raw = np.clip(model.predict_proba(x_score)[:, 1], 1e-6, 1 - 1e-6)

    if len(ca) >= 40 and len(np.unique(y_cal)) == 2:
        cal_logit = np.log(cal_raw / (1 - cal_raw)).reshape(-1, 1)
        score_logit = np.log(score_raw / (1 - score_raw)).reshape(-1, 1)
        calibrator = LogisticRegression(solver="lbfgs", C=1e6, max_iter=2000)
        calibrator.fit(cal_logit, y_cal)
        pred = calibrator.predict_proba(score_logit)[:, 1]
        cal_meta = {
            "status": "platt",
            "intercept": float(calibrator.intercept_[0]),
            "coefficient": float(calibrator.coef_[0, 0]),
        }
    else:
        calibrator = None
        pred = score_raw
        cal_meta = {"status": "identity"}

    meta = {
        "n_train": int(len(tr)),
        "n_calibration": int(len(ca)),
        "n_score": int(len(sc)),
        "n_encoded_features": int(x_train.shape[1]),
        "calibration": cal_meta,
    }
    return pred, prep, model, calibrator, meta


def first_t2_rows(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.sort_values(["lead_id", "score_time", "row_id"])
        .drop_duplicates("lead_id")
        .reset_index(drop=True)
    )


def metric_with_ratios(df: pd.DataFrame, pred: np.ndarray) -> dict[str, float]:
    m = metric_bundle(df["target_30d"], pred)
    p = m["positive_rate"]
    m["ap_over_prevalence"] = float(m["average_precision"] / p) if p and np.isfinite(m["average_precision"]) else np.nan
    return m


def bootstrap_ci(df: pd.DataFrame, pred: np.ndarray, n_boot: int = N_BOOT) -> pd.DataFrame:
    frame = df.reset_index(drop=True)
    pred = np.asarray(pred, dtype=float)
    groups = {lead: np.asarray(idx, dtype=int) for lead, idx in frame.groupby("lead_id").indices.items()}
    leads = np.asarray(list(groups), dtype=object)
    rng = np.random.default_rng(SEED)
    rows = []
    for _ in range(n_boot):
        sampled = rng.choice(leads, size=len(leads), replace=True)
        idx = np.concatenate([groups[x] for x in sampled])
        m = metric_with_ratios(frame.iloc[idx].reset_index(drop=True), pred[idx])
        rows.append({
            "roc_auc": m["roc_auc"],
            "average_precision": m["average_precision"],
            "ap_over_prevalence": m["ap_over_prevalence"],
            "lift_top_10pct": m["lift_top_10pct"],
            "brier": m["brier"],
        })
    b = pd.DataFrame(rows)
    out = []
    point = metric_with_ratios(frame, pred)
    for metric in b.columns:
        out.append({
            "metric": metric,
            "point": float(point[metric]),
            "ci95_low": float(b[metric].quantile(0.025)),
            "ci95_high": float(b[metric].quantile(0.975)),
            "n_boot": n_boot,
        })
    return pd.DataFrame(out)


def chronological_train_cal(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    leads = (
        df[["lead_id", "created_at"]]
        .drop_duplicates("lead_id")
        .sort_values(["created_at", "lead_id"])
        .reset_index(drop=True)
    )
    cut = max(1, min(len(leads) - 1, int(len(leads) * 0.80)))
    train_ids = set(leads.iloc[:cut]["lead_id"])
    cal_ids = set(leads.iloc[cut:]["lead_id"])
    return (
        df[df["lead_id"].isin(train_ids)].copy(),
        df[df["lead_id"].isin(cal_ids)].copy(),
    )


def rolling_diagnostic(df: pd.DataFrame, cat_cols: list[str], num_cols: list[str]) -> pd.DataFrame:
    months = sorted(df["lead_month"].unique())
    rows = []
    # Post-selection diagnostic only. Test windows are disjoint.
    candidates = list(range(6, max(6, len(months) - 2), 2))
    for fold, val_idx in enumerate(candidates, start=1):
        if val_idx + 2 >= len(months):
            break
        train_months = months[:val_idx]
        val_month = months[val_idx]
        test_months = months[val_idx + 1:val_idx + 3]
        tr = df[df["lead_month"].isin(train_months)].copy()
        va = df[df["lead_month"].eq(val_month)].copy()
        te = df[df["lead_month"].isin(test_months)].copy()
        if min(tr["lead_id"].nunique(), va["lead_id"].nunique(), te["lead_id"].nunique()) < 30:
            continue
        te_first = first_t2_rows(te)
        pred_all, _, _, _, meta = fit_rf(tr, va, te_first, cat_cols, num_cols)
        m = metric_with_ratios(te_first, pred_all)
        rows.append({
            "fold": fold,
            "train_end_month": train_months[-1],
            "validation_month": val_month,
            "test_months": ",".join(test_months),
            "n_train_leads": tr["lead_id"].nunique(),
            "n_validation_leads": va["lead_id"].nunique(),
            "n_test_leads": te_first["lead_id"].nunique(),
            **m,
            "n_encoded_features": meta["n_encoded_features"],
        })
    return pd.DataFrame(rows)


def feature_psi_table(train: pd.DataFrame, current: pd.DataFrame, num_cols: list[str]) -> pd.DataFrame:
    rows = []
    for col in num_cols:
        rows.append({
            "feature": col,
            "psi": psi_numeric(train[col], current[col]),
            "train_non_null": int(pd.to_numeric(train[col], errors="coerce").notna().sum()),
            "current_non_null": int(pd.to_numeric(current[col], errors="coerce").notna().sum()),
        })
    return pd.DataFrame(rows).sort_values("psi", ascending=False)


def main() -> None:
    t2, label_summary = corrected_t2()
    if t2["lead_id"].nunique() < 300:
        raise RuntimeError("Insufficient corrected-label T2 leads to build E029 artifact")

    cats, nums = feature_policy()
    _json(RESULTS / "label_audit.json", label_summary)
    _json(RESULTS / "feature_policy.json", {
        "categorical_features": cats,
        "numeric_features": nums,
        "removed_categorical": REMOVE_CAT,
        "removed_numeric": REMOVE_NUM,
        "leadquality_excludes_all_availability": True,
        "stage_policy": {"T0": "neutral", "T1": "neutral", "T2": "frozen_candidate_pending_prospective_gate"},
    })

    rolling = rolling_diagnostic(t2, cats, nums)
    rolling.to_csv(RESULTS / "rolling_post_selection_diagnostic.csv", index=False)

    train, cal = chronological_train_cal(t2)
    cal_first = first_t2_rows(cal)
    pred, prep, model, calibrator, fit_meta = fit_rf(train, cal, cal_first, cats, nums)
    diag = metric_with_ratios(cal_first, pred)
    ci = bootstrap_ci(cal_first, pred)
    pd.DataFrame([diag]).to_csv(RESULTS / "historical_calibration_partition_metrics.csv", index=False)
    ci.to_csv(RESULTS / "historical_calibration_partition_bootstrap.csv", index=False)

    # This is only a sanity check, never the prospective release gate.
    sanity_pass = bool(
        diag["roc_auc"] > 0.50
        and diag["ap_over_prevalence"] > 1.00
        and diag["lift_top_10pct"] > 1.00
    )

    # Drift diagnostic between early artifact fit and late calibration partition.
    psi = feature_psi_table(train, cal, nums)
    psi.to_csv(RESULTS / "feature_psi_train_vs_calibration.csv", index=False)

    prep_path = ARTIFACTS / "preprocessor.joblib"
    model_path = ARTIFACTS / "rf_t2.joblib"
    cal_path = ARTIFACTS / "platt_calibrator.joblib"
    joblib.dump(prep, prep_path)
    joblib.dump(model, model_path)
    joblib.dump(calibrator, cal_path)

    schema = {
        "categorical_features": cats,
        "numeric_features": nums,
        "target": TARGET_NAME,
        "stage": "T2_engaged",
        "blocked_inputs": sorted(set(REMOVE_CAT + REMOVE_NUM)),
    }
    schema_path = ARTIFACTS / "feature_schema.json"
    _json(schema_path, schema)

    prospective = {
        "status": "AWAITING_POST_FREEZE_COHORT",
        "unit": "first eligible T2 snapshot per lead",
        "start_rule": "lead created strictly after artifact freeze/data cutoff",
        "window_rule": "first 8 complete post-freeze lead-created weeks; if <500 matured first-T2 leads, extend by whole weeks until 500, maximum 16 weeks",
        "extension_depends_only_on_sample_size": True,
        "minimum_matured_leads": 500,
        "pass_rule": {
            "roc_auc_point_min": 0.55,
            "roc_auc_ci95_low_strictly_gt": 0.50,
            "ap_over_prevalence_min": 1.05,
            "lift_top_10pct_min": 1.10,
            "scheduled_visit_timestamp_completeness_min": 0.995,
            "leakage_or_instrumentation_failure": "automatic fail",
        },
        "peeking": "No outcome inspection before the gate cohort closes.",
        "if_less_than_500_after_16_weeks": "INCONCLUSIVE_INSUFFICIENT_SAMPLE; do not relax thresholds post hoc",
    }
    _json(HERE / "prospective_gate.json", prospective)

    treatment_policy = E028 / "TREATMENT_POLICY.md"
    manifest = {
        "experiment_id": "E029_drift_sanitized_release_candidate",
        "artifact_status": "FROZEN_AWAITING_PROSPECTIVE_GATE" if sanity_pass else "REJECTED_HISTORICAL_SANITY_CHECK",
        "launch_eligible": False,
        "github_sha": os.environ.get("GITHUB_SHA", "LOCAL"),
        "historical_data_end_score_time": str(t2["score_time"].max()),
        "historical_target_observation_end": label_summary["target_observation_end"],
        "historical_diagnostic_is_confirmatory": False,
        "fit_meta": fit_meta,
        "historical_sanity_metrics": diag,
        "hashes": {
            "preprocessor_sha256": _sha256(prep_path),
            "model_sha256": _sha256(model_path),
            "calibrator_sha256": _sha256(cal_path),
            "feature_schema_sha256": _sha256(schema_path),
            "treatment_policy_sha256": _sha256(treatment_policy),
        },
        "stage_policy": {
            "T0": "neutral",
            "T1": "neutral",
            "T2": "candidate only after prospective gate PASS",
        },
        "prospective_gate": prospective,
    }
    _json(ARTIFACTS / "release_manifest_candidate.json", manifest)

    rolling_summary = {}
    if not rolling.empty:
        rolling_summary = {
            "n_folds": int(len(rolling)),
            "auc_min": float(rolling["roc_auc"].min()),
            "auc_mean": float(rolling["roc_auc"].mean()),
            "auc_max": float(rolling["roc_auc"].max()),
            "ap_over_prevalence_min": float(rolling["ap_over_prevalence"].min()),
            "lift_top10_min": float(rolling["lift_top_10pct"].min()),
        }
    _json(RESULTS / "summary.json", {
        "label_audit": label_summary,
        "historical_sanity_pass": sanity_pass,
        "historical_calibration_partition_metrics": diag,
        "rolling_post_selection_summary": rolling_summary,
        "max_numeric_psi_train_vs_calibration": float(psi["psi"].max()) if len(psi) else None,
        "artifact_status": manifest["artifact_status"],
        "launch_eligible": False,
        "reason_launch_not_eligible": "No genuinely post-freeze matured cohort exists in the candidate package; prospective gate is mandatory.",
    })

    harness = {
        "experiment_id": "E029_drift_sanitized_release_candidate",
        "metrics": {
            "roc_auc": float(diag["roc_auc"]),
            "average_precision": float(diag["average_precision"]),
            "brier": float(diag["brier"]),
            "log_loss": float(diag["log_loss"]),
            "lift_top_10pct": float(diag["lift_top_10pct"]),
            "recall_top_20pct": float(diag["recall_top_20pct"]),
        },
        "segment_metrics": {
            "T2_engaged_historical_post_selection": {
                "roc_auc": float(diag["roc_auc"]),
                "average_precision": float(diag["average_precision"]),
                "brier": float(diag["brier"]),
                "log_loss": float(diag["log_loss"]),
                "lift_top_10pct": float(diag["lift_top_10pct"]),
                "recall_top_20pct": float(diag["recall_top_20pct"]),
            }
        },
        "conclusion": "INCONCLUSIVE" if sanity_pass else "NOT_SUPPORTED",
        "caveats": [
            "Historical diagnostics are post-selection because E021-E027 already used this dataset to choose the feature policy.",
            "Canonical ambiguous event-time labels are excluded rather than coerced to zero.",
            "T0/T1 are deliberately neutral; this artifact is T2-only.",
            "No Availability fields or drift-sensitive clocks enter LeadQuality.",
            "Launch requires a genuinely post-freeze cohort and production A/A instrumentation."
        ],
        "next_experiment": "Apply prospective_gate.json to the first post-freeze matured cohort; if PASS, complete E028 release manifest and productive A/A."
    }
    _json(RESULTS / "harness_results.json", harness)

    report = f"""# E029 — Drift-sanitized release candidate

## Estado

**{manifest['artifact_status']}**

El artifact queda congelado, pero **launch_eligible=false** hasta observar una cohorte posterior al freeze.

## Target corregida

- T2 snapshots elegibles: {label_summary['eligible_t2_snapshots']:,}
- leads T2 únicos: {label_summary['eligible_t2_unique_leads']:,}
- ambiguos detectados en todos los stages: {label_summary['ambiguous_rows_all_stages']:,} ({label_summary['ambiguous_share_all_stages']:.2%})

Los ambiguos no se convierten en 0.

## Diagnóstico histórico post-selección

Calibration partition, primera T2 por lead:

- AUC: {diag['roc_auc']:.3f}
- AP: {diag['average_precision']:.3f}
- prevalencia: {diag['positive_rate']:.3f}
- AP/prevalencia: {diag['ap_over_prevalence']:.3f}
- Lift@10%: {diag['lift_top_10pct']:.3f}x
- Brier: {diag['brier']:.3f}

Esto **no** es el gate prospectivo porque la política de features ya fue elegida usando este histórico.

## Feature policy

Bloqueados:

- calendario/progreso;
- prior_searches;
- Availability completa dentro de LeadQuality;
- broker prior;
- current-state Spot inseguro por el pipeline base.

T0/T1 quedan neutrales. Sólo T2 tiene artifact predictivo.

## Gate real

Ver `prospective_gate.json`.

El primer gate válido empieza después del freeze y exige al menos 500 leads maduros first-T2, AUC >=0.55 con lower CI >0.50, AP/prevalencia >=1.05, Lift@10 >=1.10 y timestamp de scheduled_visit >=99.5%.

No se relajarán thresholds después de mirar outcomes.
"""
    (RESULTS / "REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps(json.loads((RESULTS / "summary.json").read_text()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
