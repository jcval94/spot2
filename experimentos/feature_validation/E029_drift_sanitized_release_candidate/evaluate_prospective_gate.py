from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


SEED = 42
MIN_N = 500
MIN_WEEKS = 8
MAX_WEEKS = 16
MIN_AUC = 0.55
MIN_AUC_CI_LOW = 0.50
MIN_AP_OVER_PREVALENCE = 1.05
MIN_LIFT_10 = 1.10
MIN_TIMESTAMP_COMPLETENESS = 0.995


def metric_bundle(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    if len(np.unique(y)) < 2:
        return {
            "roc_auc": math.nan,
            "average_precision": math.nan,
            "positive_rate": float(y.mean()) if len(y) else math.nan,
            "ap_over_prevalence": math.nan,
            "lift_top_10pct": math.nan,
            "brier": math.nan,
        }
    auc = float(roc_auc_score(y, p))
    ap = float(average_precision_score(y, p))
    prevalence = float(y.mean())
    order = np.argsort(-p)
    n_top = max(1, int(math.ceil(0.10 * len(y))))
    top_rate = float(y[order[:n_top]].mean())
    lift = top_rate / prevalence if prevalence > 0 else math.nan
    return {
        "roc_auc": auc,
        "average_precision": ap,
        "positive_rate": prevalence,
        "ap_over_prevalence": ap / prevalence if prevalence > 0 else math.nan,
        "lift_top_10pct": lift,
        "brier": float(brier_score_loss(y, p)),
    }


def auc_bootstrap(y: np.ndarray, p: np.ndarray, n_boot: int) -> tuple[float, float]:
    rng = np.random.default_rng(SEED)
    vals = []
    n = len(y)
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        ys = y[idx]
        if len(np.unique(ys)) < 2:
            continue
        vals.append(roc_auc_score(ys, p[idx]))
    if len(vals) < max(100, n_boot // 2):
        return math.nan, math.nan
    return float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))


def first_full_week_after(ts: pd.Timestamp) -> pd.Timestamp:
    # Monday 00:00 UTC strictly after the freeze instant.
    normalized = ts.normalize()
    days = (7 - normalized.weekday()) % 7
    candidate = normalized + pd.Timedelta(days=days)
    if candidate <= ts:
        candidate += pd.Timedelta(days=7)
    return candidate


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Matured post-freeze T2 scored/labeled CSV.")
    ap.add_argument("--freeze-at", required=True, help="Artifact freeze timestamp UTC.")
    ap.add_argument("--data-as-of", required=True, help="Outcome/instrumentation data complete through this UTC timestamp.")
    ap.add_argument("--timestamp-completeness", required=True, type=float, help="Real backend scheduled_visit event-time completeness in [0,1].")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    freeze = pd.Timestamp(args.freeze_at)
    data_as_of = pd.Timestamp(args.data_as_of)
    if freeze.tzinfo is None:
        freeze = freeze.tz_localize("UTC")
    else:
        freeze = freeze.tz_convert("UTC")
    if data_as_of.tzinfo is None:
        data_as_of = data_as_of.tz_localize("UTC")
    else:
        data_as_of = data_as_of.tz_convert("UTC")

    d = pd.read_csv(args.input)
    required = [
        "lead_id", "created_at", "score_time", "target_30d",
        "target_status", "e029_leadquality",
    ]
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise SystemExit(f"Missing prospective gate columns: {missing}")

    d["created_at"] = pd.to_datetime(d["created_at"], utc=True, errors="raise")
    d["score_time"] = pd.to_datetime(d["score_time"], utc=True, errors="raise")
    d["target_30d"] = pd.to_numeric(d["target_30d"], errors="coerce")
    d["e029_leadquality"] = pd.to_numeric(d["e029_leadquality"], errors="coerce")

    d = d[
        (d["created_at"] > freeze)
        & d["target_status"].isin(["POSITIVE", "NEGATIVE"])
        & d["target_30d"].notna()
        & d["e029_leadquality"].notna()
    ].copy()
    d = d.sort_values(["lead_id", "score_time"]).drop_duplicates("lead_id", keep="first")

    start = first_full_week_after(freeze)
    eligible_weeks = []
    for k in range(MAX_WEEKS):
        ws = start + pd.Timedelta(days=7 * k)
        we = ws + pd.Timedelta(days=7)
        maturity = we + pd.Timedelta(days=30)
        if maturity <= data_as_of:
            eligible_weeks.append((ws, we))

    selected = pd.DataFrame()
    weeks_used = 0
    for i, (ws, we) in enumerate(eligible_weeks[:MAX_WEEKS], start=1):
        candidate = d[(d["created_at"] >= start) & (d["created_at"] < we)].copy()
        if i >= MIN_WEEKS and len(candidate) >= MIN_N:
            selected = candidate
            weeks_used = i
            break
    if selected.empty and len(eligible_weeks) >= MAX_WEEKS:
        end = eligible_weeks[MAX_WEEKS - 1][1]
        selected = d[(d["created_at"] >= start) & (d["created_at"] < end)].copy()
        weeks_used = MAX_WEEKS

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if len(eligible_weeks) < MIN_WEEKS or len(selected) < MIN_N:
        result = {
            "status": "INCONCLUSIVE_INSUFFICIENT_SAMPLE",
            "n": int(len(selected)),
            "weeks_matured_available": int(len(eligible_weeks)),
            "weeks_used": int(weeks_used),
            "minimum_n": MIN_N,
            "timestamp_completeness": args.timestamp_completeness,
            "reason": "The fixed post-freeze cohort has not reached the pre-registered sample rule. Thresholds are not relaxed.",
        }
        (out_dir / "gate_result.json").write_text(json.dumps(result, indent=2) + "\n")
        selected.to_csv(out_dir / "gate_population.csv", index=False)
        print(json.dumps(result, indent=2))
        return

    y = selected["target_30d"].to_numpy(dtype=int)
    p = selected["e029_leadquality"].to_numpy(dtype=float)
    metrics = metric_bundle(y, p)
    ci_low, ci_high = auc_bootstrap(y, p, args.bootstrap)
    checks = {
        "roc_auc_point": bool(metrics["roc_auc"] >= MIN_AUC),
        "roc_auc_ci_low": bool(np.isfinite(ci_low) and ci_low > MIN_AUC_CI_LOW),
        "ap_over_prevalence": bool(metrics["ap_over_prevalence"] >= MIN_AP_OVER_PREVALENCE),
        "lift_top_10pct": bool(metrics["lift_top_10pct"] >= MIN_LIFT_10),
        "timestamp_completeness": bool(args.timestamp_completeness >= MIN_TIMESTAMP_COMPLETENESS),
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    result = {
        "status": status,
        "n": int(len(selected)),
        "weeks_used": int(weeks_used),
        "cohort_start": str(start),
        "cohort_end_exclusive": str(start + pd.Timedelta(days=7 * weeks_used)),
        "data_as_of": str(data_as_of),
        "metrics": metrics,
        "roc_auc_ci95": [ci_low, ci_high],
        "timestamp_completeness": args.timestamp_completeness,
        "checks": checks,
        "thresholds": {
            "roc_auc_point_min": MIN_AUC,
            "roc_auc_ci_low_strictly_gt": MIN_AUC_CI_LOW,
            "ap_over_prevalence_min": MIN_AP_OVER_PREVALENCE,
            "lift_top_10pct_min": MIN_LIFT_10,
            "timestamp_completeness_min": MIN_TIMESTAMP_COMPLETENESS,
        },
    }
    (out_dir / "gate_result.json").write_text(json.dumps(result, indent=2) + "\n")
    selected.to_csv(out_dir / "gate_population.csv", index=False)
    report = [
        "# E029 prospective gate",
        "",
        f"**Status: {status}**",
        "",
        f"- N: {len(selected):,}",
        f"- Weeks: {weeks_used}",
        f"- AUC: {metrics['roc_auc']:.3f} (95% CI {ci_low:.3f}, {ci_high:.3f})",
        f"- AP/prevalence: {metrics['ap_over_prevalence']:.3f}",
        f"- Lift@10%: {metrics['lift_top_10pct']:.3f}x",
        f"- Timestamp completeness: {args.timestamp_completeness:.3%}",
        "",
        "This script applies the pre-registered gate. It must not be rerun with modified thresholds after outcomes are inspected.",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(report) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
