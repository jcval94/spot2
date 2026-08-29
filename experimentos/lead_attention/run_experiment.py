from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42
WINDOW_DAYS = 30
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

FORBIDDEN_T0 = {
    "lead_score_internal", "broker_response", "broker_response_hours",
    "total_inquiries", "total_views", "days_on_market", "is_active",
}
FORBIDDEN_T1 = {
    "broker_response", "broker_response_hours",
    "total_inquiries", "total_views", "days_on_market", "is_active",
}


def pct(x):
    return "n/a" if pd.isna(x) else f"{100*x:.1f}%"


def temporal_split(df, time_col, train_frac=0.80):
    d = df.sort_values(time_col).copy()
    cut_idx = max(1, min(len(d) - 1, int(len(d) * train_frac)))
    cutoff = d[time_col].iloc[cut_idx]
    train = d[d[time_col] < cutoff].copy()
    test = d[d[time_col] >= cutoff].copy()
    if len(train) < 100 or len(test) < 100:
        train = d.iloc[:cut_idx].copy()
        test = d.iloc[cut_idx:].copy()
        cutoff = test[time_col].min()
    return train, test, cutoff


def metric_bundle(y_true, pred):
    y = np.asarray(y_true, dtype=int)
    pred = np.clip(np.asarray(pred, dtype=float), 1e-6, 1 - 1e-6)
    out = {"n": int(len(y)), "positive_rate": float(y.mean()) if len(y) else math.nan}
    if len(np.unique(y)) < 2:
        for k in ["roc_auc", "average_precision", "brier", "log_loss",
                  "lift_top_10pct", "recall_top_10pct", "lift_top_20pct", "recall_top_20pct"]:
            out[k] = math.nan
        return out
    out["roc_auc"] = float(roc_auc_score(y, pred))
    out["average_precision"] = float(average_precision_score(y, pred))
    out["brier"] = float(brier_score_loss(y, pred))
    out["log_loss"] = float(log_loss(y, pred, labels=[0, 1]))
    order = np.argsort(-pred)
    for frac in (0.10, 0.20):
        k = max(1, int(math.ceil(len(y) * frac)))
        idx = order[:k]
        base = float(y.mean())
        top_rate = float(y[idx].mean())
        key = int(frac * 100)
        out[f"lift_top_{key}pct"] = top_rate / base if base > 0 else math.nan
        out[f"recall_top_{key}pct"] = float(y[idx].sum() / y.sum()) if y.sum() > 0 else math.nan
    return out


def fit_logistic(train, test, target, categorical, numeric):
    categorical = [c for c in categorical if c in train.columns]
    numeric = [c for c in numeric if c in train.columns]
    X_train = train[categorical + numeric].copy()
    X_test = test[categorical + numeric].copy()
    y_train = train[target].astype(int)
    y_test = test[target].astype(int)

    for c in categorical:
        # Cast first so nullable boolean/categorical dtypes can safely accept
        # a textual missing sentinel under pandas 3+.
        X_train[c] = X_train[c].astype("string").fillna("__MISSING__")
        X_test[c] = X_test[c].astype("string").fillna("__MISSING__")

    prep = ColumnTransformer([
        ("cat", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical),
        ("num", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), numeric),
    ])

    model = Pipeline([
        ("prep", prep),
        ("clf", LogisticRegression(
            max_iter=2500, class_weight="balanced", solver="liblinear",
            random_state=RANDOM_STATE,
        )),
    ])
    model.fit(X_train, y_train)
    pred = model.predict_proba(X_test)[:, 1]
    return model, pred, metric_bundle(y_test, pred)


def make_lead_target(leads, inquiries):
    d = inquiries[["lead_id", "inquiry_at", "broker_response"]].merge(
        leads[["lead_id", "created_at"]], on="lead_id", how="left"
    )
    d["delta_days"] = (d["inquiry_at"] - d["created_at"]).dt.total_seconds() / 86400.0
    d["is_success"] = (
        d["broker_response"].eq("scheduled_visit")
        & d["delta_days"].between(0, WINDOW_DAYS, inclusive="both")
    )
    success = d.groupby("lead_id", as_index=False)["is_success"].max()
    out = leads.merge(success, on="lead_id", how="left")
    out["target_30d"] = out["is_success"].fillna(False).astype(int)
    return out.drop(columns=["is_success"])


def make_first_inquiry_target(inquiries):
    first = inquiries.sort_values(["lead_id", "inquiry_at", "inquiry_id"]).drop_duplicates("lead_id").copy()
    first_times = first[["lead_id", "inquiry_at"]].rename(columns={"inquiry_at": "first_inquiry_at"})
    d = inquiries[["lead_id", "inquiry_at", "broker_response"]].merge(first_times, on="lead_id", how="inner")
    d["delta_days"] = (d["inquiry_at"] - d["first_inquiry_at"]).dt.total_seconds() / 86400.0
    d["is_success"] = (
        d["broker_response"].eq("scheduled_visit")
        & d["delta_days"].between(0, WINDOW_DAYS, inclusive="both")
    )
    success = d.groupby("lead_id", as_index=False)["is_success"].max()
    first = first.merge(success, on="lead_id", how="left")
    first["target_30d"] = first["is_success"].fillna(False).astype(int)
    return first.drop(columns=["is_success"])


def add_market_context(leads_df, market):
    d = leads_df.copy()
    d["month"] = d["created_at"].dt.to_period("M").dt.to_timestamp()
    m = market.copy()
    m["month"] = pd.to_datetime(m["month"])
    return d.merge(
        m, how="left",
        left_on=["preferred_state", "preferred_municipality", "preferred_corridor", "search_sector", "month"],
        right_on=["state", "municipality", "corridor", "sector", "month"],
        suffixes=("", "_market"),
    )


def main():
    leads = pd.read_csv("data/candidate/csv/leads.csv", parse_dates=["created_at"])
    inquiries = pd.read_csv("data/candidate/csv/inquiries.csv", parse_dates=["inquiry_at"])
    spots = pd.read_csv("data/candidate/csv/spots.csv", parse_dates=["created_at"])
    market = pd.read_csv("data/candidate/csv/market_context.csv", parse_dates=["month"])

    max_observed = inquiries["inquiry_at"].max()
    censor_cutoff = max_observed - pd.Timedelta(days=WINDOW_DAYS)

    # T0: score at lead creation.
    stage0 = make_lead_target(leads, inquiries)
    stage0 = stage0[stage0["created_at"] <= censor_cutoff].copy()
    stage0["lead_month_num"] = stage0["created_at"].dt.month
    stage0["lead_weekday"] = stage0["created_at"].dt.day_name()

    t0_cat = [
        "user_type", "company_size", "industry", "search_sector", "search_modality",
        "preferred_state", "preferred_municipality", "preferred_corridor", "source", "lead_weekday",
    ]
    t0_num = [
        "target_area_sqm", "min_budget_mxn_rent_monthly", "max_budget_mxn_rent_monthly",
        "min_budget_mxn_sale_total", "max_budget_mxn_sale_total", "lead_month_num",
    ]
    assert not (set(t0_cat + t0_num) & FORBIDDEN_T0)

    train0, test0, cutoff0 = temporal_split(stage0, "created_at")
    _, pred0, metrics0 = fit_logistic(train0, test0, "target_30d", t0_cat, t0_num)

    # T0 + safe market/geographic context matched to the lead month.
    stage0_geo = add_market_context(stage0, market)
    geo_num = [
        "similar_available_spots", "avg_price_sqm_mxn", "recent_occupancy_rate",
        "absorption_velocity_days", "recent_inquiry_volume",
    ]
    train0g = stage0_geo[stage0_geo["created_at"] < cutoff0].copy()
    test0g = stage0_geo[stage0_geo["created_at"] >= cutoff0].copy()
    _, pred0g, metrics0g = fit_logistic(train0g, test0g, "target_30d", t0_cat, t0_num + geo_num)

    # T1: score immediately after the first inquiry arrives, before broker response.
    first = make_first_inquiry_target(inquiries)
    first = first[first["inquiry_at"] <= censor_cutoff].copy()

    spot_cols = [
        "spot_id", "sector_name", "type_name", "state", "municipality", "settlement",
        "corridor", "region", "lat", "lon", "area_sqm", "price_sqm_mxn_rent",
        "price_sqm_mxn_sale", "price_total_mxn_rent", "price_total_mxn_sale",
        "maintenance_cost_mxn", "modality",
    ]
    spot_safe = spots[spot_cols].rename(columns={c: f"spot_{c}" for c in spot_cols if c != "spot_id"})
    stage1 = first.merge(leads, on="lead_id", how="left", suffixes=("", "_lead")).merge(
        spot_safe, on="spot_id", how="left"
    ).copy()

    stage1["lead_month_num"] = stage1["created_at"].dt.month
    stage1["lead_weekday"] = stage1["created_at"].dt.day_name()
    stage1["inquiry_hour"] = stage1["inquiry_at"].dt.hour
    stage1["inquiry_weekday"] = stage1["inquiry_at"].dt.day_name()
    stage1["days_to_first_inquiry"] = (stage1["inquiry_at"] - stage1["created_at"]).dt.total_seconds() / 86400.0
    stage1["requested_to_spot_area_ratio"] = stage1["requested_area_sqm"] / stage1["spot_area_sqm"].replace(0, np.nan)
    stage1["rent_budget_to_price_ratio"] = (
        stage1["requested_budget_mxn_rent_monthly"] / stage1["spot_price_total_mxn_rent"].replace(0, np.nan)
    )
    stage1["sale_budget_to_price_ratio"] = (
        stage1["requested_budget_mxn_sale_total"] / stage1["spot_price_total_mxn_sale"].replace(0, np.nan)
    )
    stage1["same_preferred_municipality"] = (
        stage1["preferred_municipality"].astype("string") == stage1["spot_municipality"].astype("string")
    )
    stage1["same_preferred_corridor"] = (
        stage1["preferred_corridor"].astype("string") == stage1["spot_corridor"].astype("string")
    )

    t1_cat = t0_cat + [
        "channel", "asked_visit", "inquiry_weekday", "spot_sector_name", "spot_type_name",
        "spot_state", "spot_municipality", "spot_settlement", "spot_corridor", "spot_region",
        "spot_modality", "same_preferred_municipality", "same_preferred_corridor",
    ]
    t1_num = t0_num + [
        "message_length", "requested_area_sqm", "requested_budget_mxn_rent_monthly",
        "requested_budget_mxn_sale_total", "urgency_days", "inquiry_hour", "days_to_first_inquiry",
        "spot_lat", "spot_lon", "spot_area_sqm", "spot_price_sqm_mxn_rent",
        "spot_price_sqm_mxn_sale", "spot_price_total_mxn_rent", "spot_price_total_mxn_sale",
        "spot_maintenance_cost_mxn", "requested_to_spot_area_ratio",
        "rent_budget_to_price_ratio", "sale_budget_to_price_ratio",
    ]
    assert not (set(t1_cat + t1_num) & FORBIDDEN_T1)

    train1, test1, cutoff1 = temporal_split(stage1, "inquiry_at")
    _, pred1, metrics1 = fit_logistic(train1, test1, "target_30d", t1_cat, t1_num)

    scored = test1[["lead_id", "inquiry_id", "inquiry_at", "target_30d", "urgency_days"]].copy()
    scored["score_stage1"] = pred1
    urgency_score = 1 - scored["urgency_days"].clip(lower=0, upper=180) / 180.0
    urgency_score = urgency_score.fillna(0.50)
    scored["triage_score"] = 0.80 * scored["score_stage1"] + 0.20 * urgency_score
    triage_metrics = metric_bundle(scored["target_30d"], scored["triage_score"].values)
    scored.to_csv(OUT / "stage1_test_scores.csv", index=False)

    # Diagnostic only: response time is post-inquiry and is never used in T0/T1.
    diag = inquiries[inquiries["broker_response_hours"].notna()].copy()
    diag["scheduled_visit"] = diag["broker_response"].eq("scheduled_visit").astype(int)
    diag["positive_response"] = diag["broker_response"].isin(["accepted", "scheduled_visit"]).astype(int)
    bins = [-np.inf, 2, 6, 12, 24, 48, np.inf]
    labels = ["<=2h", "2-6h", "6-12h", "12-24h", "24-48h", ">48h"]
    diag["response_bucket"] = pd.cut(diag["broker_response_hours"], bins=bins, labels=labels, ordered=True)
    bucket = diag.groupby("response_bucket", observed=True).agg(
        n=("inquiry_id", "size"),
        scheduled_visit_rate=("scheduled_visit", "mean"),
        positive_response_rate=("positive_response", "mean"),
        median_response_hours=("broker_response_hours", "median"),
    ).reset_index()
    bucket.to_csv(OUT / "response_time_buckets.csv", index=False)

    fast = diag[diag["broker_response_hours"] <= 6]
    slow = diag[diag["broker_response_hours"] > 24]
    fast_sched = fast["scheduled_visit"].mean() if len(fast) else math.nan
    slow_sched = slow["scheduled_visit"].mean() if len(slow) else math.nan
    relative_rate = fast_sched / slow_sched if slow_sched and not pd.isna(slow_sched) else math.nan

    diag_model = diag.merge(
        leads[[
            "lead_id", "user_type", "company_size", "industry", "search_sector",
            "search_modality", "preferred_state", "preferred_municipality",
            "preferred_corridor", "source", "target_area_sqm",
        ]],
        on="lead_id", how="left"
    ).copy()
    diag_model["inquiry_weekday"] = diag_model["inquiry_at"].dt.day_name()
    diag_model["inquiry_hour"] = diag_model["inquiry_at"].dt.hour
    diag_model["log_response_hours"] = np.log1p(diag_model["broker_response_hours"].clip(lower=0))

    dcat = [
        "user_type", "company_size", "industry", "search_sector", "search_modality",
        "preferred_state", "preferred_municipality", "preferred_corridor", "source",
        "channel", "asked_visit", "inquiry_weekday",
    ]
    dnum = [
        "target_area_sqm", "message_length", "requested_area_sqm",
        "requested_budget_mxn_rent_monthly", "requested_budget_mxn_sale_total",
        "urgency_days", "inquiry_hour",
    ]
    dtrain, dtest, _ = temporal_split(diag_model, "inquiry_at")
    _, _, dmetrics_base = fit_logistic(dtrain, dtest, "scheduled_visit", dcat, dnum)
    _, _, dmetrics_time = fit_logistic(
        dtrain, dtest, "scheduled_visit", dcat, dnum + ["log_response_hours"]
    )

    metric_rows = []
    for name, m in [
        ("T0 lead creation", metrics0),
        ("T0 + market/geography", metrics0g),
        ("T1 first inquiry", metrics1),
        ("T1 routing proxy", triage_metrics),
        ("Inquiry diagnostic pre-response", dmetrics_base),
        ("Inquiry diagnostic + response hours", dmetrics_time),
    ]:
        metric_rows.append({"model": name, **m})
    metrics_df = pd.DataFrame(metric_rows)
    metrics_df.to_csv(OUT / "metrics.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(bucket["response_bucket"].astype(str), bucket["scheduled_visit_rate"])
    ax.set_ylabel("Scheduled-visit rate")
    ax.set_xlabel("Broker response time")
    ax.set_title("Observed relationship: response time vs scheduled visit")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(OUT / "response_time_vs_scheduled_visit.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    plot_df = metrics_df[metrics_df["model"].isin(
        ["T0 lead creation", "T0 + market/geography", "T1 first inquiry"]
    )]
    x = np.arange(len(plot_df))
    width = 0.36
    ax.bar(x - width / 2, plot_df["roc_auc"], width, label="ROC AUC")
    ax.bar(x + width / 2, plot_df["average_precision"], width, label="Average precision")
    ax.set_xticks(x, plot_df["model"], rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.set_title("Two-stage scoring experiment")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "two_stage_model_metrics.png", dpi=160)
    plt.close(fig)

    t0_auc_gain_geo = metrics0g["roc_auc"] - metrics0["roc_auc"]
    t1_auc_gain = metrics1["roc_auc"] - metrics0["roc_auc"]
    t1_ap_gain = metrics1["average_precision"] - metrics0["average_precision"]
    response_auc_gain = dmetrics_time["roc_auc"] - dmetrics_base["roc_auc"]
    geo_match_rate = float(stage0_geo[geo_num].notna().any(axis=1).mean())

    result = {
        "observation_window_days": WINDOW_DAYS,
        "max_observed_inquiry": str(max_observed),
        "right_censor_cutoff": str(censor_cutoff),
        "stage0_cutoff": str(cutoff0),
        "stage1_cutoff": str(cutoff1),
        "stage0": metrics0,
        "stage0_geo": metrics0g,
        "stage1": metrics1,
        "triage_proxy": triage_metrics,
        "fast_le_6h_scheduled_rate": None if pd.isna(fast_sched) else float(fast_sched),
        "slow_gt_24h_scheduled_rate": None if pd.isna(slow_sched) else float(slow_sched),
        "fast_vs_slow_rate_ratio": None if pd.isna(relative_rate) else float(relative_rate),
        "diagnostic_response_time_auc_gain": float(response_auc_gain),
        "market_context_match_rate": geo_match_rate,
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    ratio_txt = "n/a" if pd.isna(relative_rate) else f"{relative_rate:.2f}x"
    report = f"""# Lead attention + two-stage scoring experiment

## What this tests

1. T0 lead creation: score using only information available when the lead is created.
2. T0 plus market/geography: same model plus time-matched market_context.
3. T1 first inquiry: re-score immediately when the first inquiry arrives, before broker response.
4. Attention-time diagnostic: measure whether broker_response_hours is associated with scheduled visits. It is diagnostic only and is excluded from T0/T1.
5. Routing proxy: estimate the value of intelligent triage by combining T1 with explicit urgency. This is not labeled as an LLM result because raw inquiry text is absent.

Conversion proxy: at least one scheduled_visit within {WINDOW_DAYS} days of the scoring moment. Right-censored records are removed.

## Core results

| Experiment | ROC AUC | Avg Precision | Brier | Lift top 10% | Recall top 20% |
|---|---:|---:|---:|---:|---:|
| T0 lead creation | {metrics0['roc_auc']:.3f} | {metrics0['average_precision']:.3f} | {metrics0['brier']:.3f} | {metrics0['lift_top_10pct']:.2f}x | {pct(metrics0['recall_top_20pct'])} |
| T0 + market/geography | {metrics0g['roc_auc']:.3f} | {metrics0g['average_precision']:.3f} | {metrics0g['brier']:.3f} | {metrics0g['lift_top_10pct']:.2f}x | {pct(metrics0g['recall_top_20pct'])} |
| T1 first inquiry | {metrics1['roc_auc']:.3f} | {metrics1['average_precision']:.3f} | {metrics1['brier']:.3f} | {metrics1['lift_top_10pct']:.2f}x | {pct(metrics1['recall_top_20pct'])} |
| T1 routing proxy | {triage_metrics['roc_auc']:.3f} | {triage_metrics['average_precision']:.3f} | {triage_metrics['brier']:.3f} | {triage_metrics['lift_top_10pct']:.2f}x | {pct(triage_metrics['recall_top_20pct'])} |

Incremental signal after first inquiry: ROC AUC {t1_auc_gain:+.3f}; Average Precision {t1_ap_gain:+.3f} versus T0.

Existing geographic/market signal: ROC AUC {t0_auc_gain_geo:+.3f}; exact month/geography market-context coverage {pct(geo_match_rate)}.

## Does speed of attention matter?

- Scheduled-visit rate with response <= 6h: {pct(fast_sched)} (n={len(fast):,})
- Scheduled-visit rate with response > 24h: {pct(slow_sched)} (n={len(slow):,})
- Fast/slow observed rate ratio: {ratio_txt}

Pre-response diagnostic ROC AUC: {dmetrics_base['roc_auc']:.3f}.
Adding response time: {dmetrics_time['roc_auc']:.3f} ({response_auc_gain:+.3f}).

This is association evidence, not causal proof. Faster brokers may differ in unobserved ways. The correct production validation is a randomized or quasi-randomized routing/SLA experiment.

## Why two models

T0 is an arrival score for deciding whether a brand-new lead deserves immediate attention.
T1 is a dynamic score at first inquiry and safely adds channel, requested area/budget, stated urgency, visit intent, listing fit and inquiry timing.

The experiment deliberately excludes broker_response, broker_response_hours, lead_score_internal and listing aggregates such as total_views, total_inquiries and current-state days_on_market.

A future T2 can update again after an SLA expires or a broker response is observed, using only events that exist by that timestamp.

## LLM role

The strongest LLM use is operational triage, not blindly adding a text score to T0. In production it should read the raw inbound message and return auditable fields such as intent, urgency, recommended SLA, hard constraints, missing information, a concise broker summary and a reason for priority.

The current data does not contain raw inquiry text, so incremental LLM lift cannot honestly be measured. The T1 routing proxy tests whether prioritization itself is valuable. A real LLM A/B test requires the raw messages.

## External geography enrichment

Available now:
- lead: state, municipality, corridor
- spot: state, municipality, settlement, corridor, region, latitude/longitude
- postal code is not provided

High-value candidates:
1. INEGI municipality identifiers and Census indicators: population, density, employment and economic structure.
2. INEGI DENUE: density and mix of establishments around a corridor or spot.
3. SEPOMEX postal-code catalog: settlement + municipality + state can map spots to postal code. Leads need a finer location field or geocoding for CP-level features.
4. OpenStreetMap/transport network: POI density, road access, transit proximity, airport/highway distance from spot lat/lon.
5. CONAPO demographic projections: growth and urbanization at municipality level.
6. Banxico macro series: rates and financing conditions, joined strictly as-of the lead date.

The existing market_context uplift is a sanity check for whether richer geographic context is worth pursuing.

## Leakage rule for external data

Every external feature must be reproducible as of the scoring timestamp. Never join a current external snapshot to historical leads if the information was not available then.

## Recommended product experiment

Randomize incoming leads:
- Control: current/FIFO handling.
- Treatment: T1 priority plus explicit SLA; later augment with LLM-extracted intent and urgency.
- Primary KPI: scheduled visits per 100 leads.
- Secondary: median first-response time, top-decile conversion, broker workload, no-response rate.
- Guardrail: do not use sensitive characteristics or opaque neighborhood proxies to suppress service.
"""
    (OUT / "report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
