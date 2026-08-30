from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

RANDOM_STATE = 42
CONTAMINATION = 0.03
HORIZON_DAYS = 30

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "candidate" / "csv"
OUT = Path(__file__).resolve().parent
RESULTS = OUT / "results"
FIGURES = OUT / "figures"
RESULTS.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)


def load_data() -> dict[str, pd.DataFrame]:
    return {
        "leads": pd.read_csv(BASE / "leads.csv", parse_dates=["created_at"]),
        "inquiries": pd.read_csv(BASE / "inquiries.csv", parse_dates=["inquiry_at"]),
        "spots": pd.read_csv(BASE / "spots.csv", parse_dates=["created_at"]),
        "spot_attributes": pd.read_csv(BASE / "spot_attributes.csv"),
        "market_context": pd.read_csv(BASE / "market_context.csv", parse_dates=["month"]),
        "availability_snapshot": pd.read_csv(BASE / "availability_snapshot.csv", parse_dates=["snapshot_date"]),
    }


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(FIGURES / name, format="svg", bbox_inches="tight")
    plt.close(fig)


def style(ax: plt.Axes, title: str, subtitle: str = "") -> None:
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", pad=18)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color="#6B7280", va="bottom")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)


def numeric_summary(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for table, df in data.items():
        for col in df.select_dtypes(include=[np.number, "bool"]).columns:
            s = pd.to_numeric(df[col], errors="coerce").astype(float)
            v = s.dropna()
            if v.empty:
                continue
            q1, q3 = v.quantile([0.25, 0.75])
            iqr = q3 - q1
            raw_rate = ((v < q1 - 1.5 * iqr) | (v > q3 + 1.5 * iqr)).mean()
            log_rate = np.nan
            pos = v[v > 0]
            if len(pos) >= 30:
                z = np.log1p(pos)
                lq1, lq3 = z.quantile([0.25, 0.75])
                liqr = lq3 - lq1
                log_rate = ((z < lq1 - 1.5 * liqr) | (z > lq3 + 1.5 * liqr)).mean()
            rows.append({
                "table": table, "column": col, "n": len(v), "missing_rate": s.isna().mean(),
                "mean": v.mean(), "std": v.std(), "min": v.min(), "p01": v.quantile(.01),
                "p05": v.quantile(.05), "p25": q1, "median": v.median(), "p75": q3,
                "p95": v.quantile(.95), "p99": v.quantile(.99), "max": v.max(),
                "raw_tukey_outlier_rate": raw_rate, "log_tukey_outlier_rate": log_rate,
            })
    return pd.DataFrame(rows)


def stratified_outliers(df: pd.DataFrame, entity: str, groups: list[str], features: list[str]) -> pd.DataFrame:
    rows = []
    for keys, g in df.groupby(groups, dropna=False):
        keys = keys if isinstance(keys, tuple) else (keys,)
        if len(g) < 50:
            continue
        group_name = " | ".join(f"{k}={v}" for k, v in zip(groups, keys))
        for col in features:
            if col not in g:
                continue
            s = pd.to_numeric(g[col], errors="coerce").dropna()
            if len(s) < 30:
                continue
            q1, q3 = s.quantile([.25, .75])
            iqr = q3 - q1
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            raw = ((s < lo) | (s > hi)).mean()
            log = np.nan
            if (s > 0).sum() >= 30:
                z = np.log1p(s[s > 0])
                a, b = z.quantile([.25, .75])
                zi = b - a
                log = ((z < a - 1.5 * zi) | (z > b + 1.5 * zi)).mean()
            rows.append({
                "entity": entity, "group": group_name, "feature": col, "n": len(s),
                "median": s.median(), "p99": s.quantile(.99), "max": s.max(),
                "raw_outlier_rate": raw, "log_outlier_rate": log,
            })
    return pd.DataFrame(rows).sort_values(["raw_outlier_rate", "n"], ascending=[False, False])


def add_amenities(attrs: pd.DataFrame) -> pd.DataFrame:
    out = attrs.copy()
    def count(v: object) -> float:
        if pd.isna(v):
            return np.nan
        try:
            x = json.loads(str(v))
            return float(len(x)) if isinstance(x, list) else np.nan
        except Exception:
            return np.nan
    out["amenities_count"] = out["amenities"].map(count)
    return out


def prep_matrix(g: pd.DataFrame, features: list[str], log_features: set[str]) -> pd.DataFrame:
    x = pd.DataFrame(index=g.index)
    for col in features:
        s = pd.to_numeric(g[col], errors="coerce")
        if col in log_features:
            s = np.log1p(s.clip(lower=0))
        x[col] = s
        x[f"{col}__missing"] = s.isna().astype(float)
    return x.fillna(x.median()).fillna(0.0)


def explanations(x: pd.DataFrame, idx: pd.Index) -> pd.Series:
    med = x.median()
    mad = (x - med).abs().median().replace(0, np.nan)
    z = ((x - med).abs() / (1.4826 * mad)).replace([np.inf, -np.inf], np.nan).fillna(0)
    out = {}
    for i in idx:
        top = z.loc[i].sort_values(ascending=False).head(3)
        out[i] = "; ".join(f"{k}={v:.1f} MAD" for k, v in top.items() if v > 0)
    return pd.Series(out)


def iforest_by_group(
    df: pd.DataFrame, entity: str, id_col: str, groups: list[str],
    features: list[str], log_features: set[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    scored, summaries = [], []
    for keys, g in df.groupby(groups, dropna=False):
        keys = keys if isinstance(keys, tuple) else (keys,)
        if len(g) < 80:
            continue
        x = prep_matrix(g, features, log_features)
        model = IsolationForest(
            n_estimators=300, max_samples=min(256, len(g)), contamination=CONTAMINATION,
            random_state=RANDOM_STATE, n_jobs=-1,
        )
        pred = model.fit_predict(x)
        score = -model.decision_function(x)
        group_name = " | ".join(f"{k}={v}" for k, v in zip(groups, keys))
        p = g.copy()
        p["entity"] = entity
        p["anomaly_group"] = group_name
        p["anomaly_score"] = score
        p["isolation_forest_flag"] = pred == -1
        p["anomaly_percentile_within_group"] = pd.Series(score, index=g.index).rank(pct=True)
        p["robust_deviation_explanation"] = ""
        flagged = p.index[p["isolation_forest_flag"]]
        if len(flagged):
            p.loc[flagged, "robust_deviation_explanation"] = explanations(x, flagged)
        scored.append(p)
        summaries.append({
            "entity": entity, "group": group_name, "n": len(g), "flagged": int((pred == -1).sum()),
            "flag_rate": float((pred == -1).mean()), "score_p50": np.median(score),
            "score_p95": np.quantile(score, .95), "score_p99": np.quantile(score, .99),
        })
    return pd.concat(scored).sort_values("anomaly_score", ascending=False), pd.DataFrame(summaries)


def cohort_dynamics(leads: pd.DataFrame, inquiries: pd.DataFrame) -> pd.DataFrame:
    by_lead = {k: g.sort_values(["inquiry_at", "inquiry_id"]) for k, g in inquiries.groupby("lead_id")}
    rows = []
    for month, cohort in leads.groupby(leads["created_at"].dt.to_period("M")):
        total = inside = positives = 0
        lags = []
        for _, lead in cohort.iterrows():
            g = by_lead.get(lead["lead_id"])
            if g is None:
                continue
            total += len(g)
            if len(g):
                lags.append((g.iloc[0]["inquiry_at"] - lead["created_at"]).total_seconds() / 86400)
                delta = (g["inquiry_at"] - lead["created_at"]).dt.total_seconds() / 86400
                w = g[delta.between(0, HORIZON_DAYS, inclusive="both")]
                inside += len(w)
                positives += int(w["broker_response"].eq("scheduled_visit").any())
        rows.append({
            "lead_month": str(month), "n_leads": len(cohort), "inquiries_per_lead": total / len(cohort),
            "inquiries_within_30d_per_lead": inside / len(cohort),
            "median_first_inquiry_lag_days": np.median(lags), "scheduled_visit_proxy_30d": positives / len(cohort),
        })
    return pd.DataFrame(rows).sort_values("lead_month")


def deterministic_relationships(leads: pd.DataFrame, inquiries: pd.DataFrame, spots: pd.DataFrame) -> pd.DataFrame:
    d = inquiries.merge(
        leads[["lead_id", "max_budget_mxn_rent_monthly", "max_budget_mxn_sale_total"]], on="lead_id"
    ).merge(spots[["spot_id", "area_sqm"]], on="spot_id")
    area = d["requested_area_sqm"] / d["area_sqm"]
    rent = d["requested_budget_mxn_rent_monthly"] / d["max_budget_mxn_rent_monthly"]
    sale = d["requested_budget_mxn_sale_total"] / d["max_budget_mxn_sale_total"]
    rent_err = (spots["price_total_mxn_rent"] - spots["area_sqm"] * spots["price_sqm_mxn_rent"]).abs() / spots["price_total_mxn_rent"].abs()
    sale_err = (spots["price_total_mxn_sale"] - spots["area_sqm"] * spots["price_sqm_mxn_sale"]).abs() / spots["price_total_mxn_sale"].abs()
    return pd.DataFrame([
        ["area_ratio_near_0_30", np.isclose(area, .30, atol=5e-4).mean()],
        ["area_ratio_near_5_00", np.isclose(area, 5.0, atol=5e-4).mean()],
        ["rent_request_exact_lead_max", np.isclose(rent.dropna(), 1.0, atol=1e-10).mean()],
        ["sale_request_exact_lead_max", np.isclose(sale.dropna(), 1.0, atol=1e-10).mean()],
        ["rent_total_identity_p99_rel_error", rent_err.dropna().quantile(.99)],
        ["sale_total_identity_p99_rel_error", sale_err.dropna().quantile(.99)],
    ], columns=["metric", "value"])


def market_panel(market: pd.DataFrame) -> pd.DataFrame:
    return market.groupby(["state", "municipality", "corridor", "sector"]).agg(
        rows=("month", "size"), first_month=("month", "min"), last_month=("month", "max"),
        observed_months=("month", "nunique"),
    ).reset_index()


def availability_trajectories(av: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for spot_id, g in av.sort_values(["spot_id", "snapshot_date"]).groupby("spot_id"):
        state = g["is_available"].astype(str).str.lower().eq("true").to_numpy()
        trans = int(np.sum(state[1:] != state[:-1])) if len(state) > 1 else 0
        rows.append({
            "spot_id": spot_id, "snapshots": len(g), "transitions": trans, "ever_changes": trans > 0,
            "always_available": state.all(), "always_unavailable": (~state).all(), "available_share": state.mean(),
            "median_competing_inquiries_30d": g["competing_inquiries_30d"].median(),
        })
    return pd.DataFrame(rows)


def match_rates(leads: pd.DataFrame, inquiries: pd.DataFrame, spots: pd.DataFrame) -> pd.DataFrame:
    d = inquiries.merge(
        leads[["lead_id", "preferred_state", "preferred_municipality", "preferred_corridor"]], on="lead_id"
    ).merge(
        spots[["spot_id", "state", "municipality", "corridor", "area_sqm", "price_total_mxn_rent", "price_total_mxn_sale"]],
        on="spot_id", suffixes=("_lead", "_spot")
    )
    d["y"] = d["broker_response"].eq("scheduled_visit").astype(int)
    d["area_ratio"] = d["requested_area_sqm"] / d["area_sqm"]
    d["rent_ratio"] = d["requested_budget_mxn_rent_monthly"] / d["price_total_mxn_rent"]
    d["sale_ratio"] = d["requested_budget_mxn_sale_total"] / d["price_total_mxn_sale"]
    d["same_state"] = d["preferred_state"].eq(d["state"])
    d["same_municipality"] = d["preferred_municipality"].eq(d["municipality"])
    d["same_corridor"] = d["preferred_corridor"].notna() & d["preferred_corridor"].eq(d["corridor"])
    rows = []
    def add(dim: str, s: pd.Series, bins: list[float], labels: list[str]) -> None:
        b = pd.cut(s, bins=bins, labels=labels, right=False, include_lowest=True)
        for key, g in d.groupby(b, observed=True):
            rows.append([dim, str(key), len(g), g["y"].mean()])
    add("area_ratio", d["area_ratio"], [-np.inf,.5,1,2,4,np.inf], ["<0.5","0.5-1","1-2","2-4",">=4"])
    add("rent_budget_to_spot_price", d["rent_ratio"], [-np.inf,.5,.8,1.2,2,np.inf], ["<0.5","0.5-0.8","0.8-1.2","1.2-2",">=2"])
    add("sale_budget_to_spot_price", d["sale_ratio"], [-np.inf,.5,.8,1.2,2,np.inf], ["<0.5","0.5-0.8","0.8-1.2","1.2-2",">=2"])
    for col in ["same_state","same_municipality","same_corridor"]:
        for key, g in d.groupby(col):
            rows.append([col, str(bool(key)), len(g), g["y"].mean()])
    return pd.DataFrame(rows, columns=["dimension","bucket","n","scheduled_visit_rate"])


def broker_summary(spots: pd.DataFrame, inquiries: pd.DataFrame) -> pd.DataFrame:
    d = inquiries.merge(spots[["spot_id","broker_id"]], on="spot_id")
    d["y"] = d["broker_response"].eq("scheduled_visit").astype(int)
    x = d.groupby("broker_id").agg(n=("inquiry_id","size"), rate=("y","mean")).reset_index()
    x = x.merge(spots.groupby("broker_id").size().rename("spots").reset_index(), on="broker_id")
    return x.sort_values("rate", ascending=False)


def hist(series: pd.Series, name: str, title: str, log: bool = False) -> None:
    s = pd.to_numeric(series, errors="coerce").dropna()
    v = np.log10(s.clip(lower=1)) if log else s
    fig, ax = plt.subplots(figsize=(8.6,4.7))
    ax.hist(v, bins=45, color="#2563EB", edgecolor="white", alpha=.86)
    style(ax, title, "log10 scale" if log else "raw scale")
    save(fig, name)


def heatmap(corr: pd.DataFrame, title: str, name: str) -> None:
    fig, ax = plt.subplots(figsize=(8.2,7))
    im = ax.imshow(corr.to_numpy(), vmin=-1, vmax=1, cmap="coolwarm")
    ax.set_xticks(np.arange(len(corr.columns)), corr.columns, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(corr.index)), corr.index)
    for i in range(len(corr)):
        for j in range(len(corr.columns)):
            ax.text(j,i,f"{corr.iloc[i,j]:.2f}",ha="center",va="center",fontsize=8)
    ax.set_title(title,loc="left",fontsize=13,fontweight="bold",pad=18)
    fig.colorbar(im,ax=ax,fraction=.046,pad=.04)
    fig.tight_layout()
    save(fig,name)



def selected_correlations(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    leads = data["leads"]
    inquiries = data["inquiries"]
    spots = data["spots"]
    market = data["market_context"]

    def log_series(s: pd.Series) -> pd.Series:
        return np.log1p(pd.to_numeric(s, errors="coerce").clip(lower=0))

    pairs = [
        ("leads", "prior_searches", "prior_inquiries",
         pd.to_numeric(leads["prior_searches"], errors="coerce"),
         pd.to_numeric(leads["prior_inquiries"], errors="coerce")),
        ("leads", "log_target_area", "log_max_rent_budget",
         log_series(leads["target_area_sqm"]), log_series(leads["max_budget_mxn_rent_monthly"])),
        ("leads", "log_target_area", "log_max_sale_budget",
         log_series(leads["target_area_sqm"]), log_series(leads["max_budget_mxn_sale_total"])),
        ("inquiries", "log_requested_area", "message_length",
         log_series(inquiries["requested_area_sqm"]),
         pd.to_numeric(inquiries["message_length"], errors="coerce")),
        ("inquiries", "urgency_days", "broker_response_hours",
         pd.to_numeric(inquiries["urgency_days"], errors="coerce"),
         pd.to_numeric(inquiries["broker_response_hours"], errors="coerce")),
        ("spots", "log_area", "log_rent_total",
         log_series(spots["area_sqm"]), log_series(spots["price_total_mxn_rent"])),
        ("spots", "log_area", "log_sale_total",
         log_series(spots["area_sqm"]), log_series(spots["price_total_mxn_sale"])),
        ("spots", "total_views", "total_inquiries",
         pd.to_numeric(spots["total_views"], errors="coerce"),
         pd.to_numeric(spots["total_inquiries"], errors="coerce")),
        ("spots", "days_on_market", "total_views",
         pd.to_numeric(spots["days_on_market"], errors="coerce"),
         pd.to_numeric(spots["total_views"], errors="coerce")),
        ("market_context", "recent_occupancy_rate", "absorption_velocity_days",
         pd.to_numeric(market["recent_occupancy_rate"], errors="coerce"),
         pd.to_numeric(market["absorption_velocity_days"], errors="coerce")),
        ("market_context", "recent_occupancy_rate", "avg_price_sqm_mxn",
         pd.to_numeric(market["recent_occupancy_rate"], errors="coerce"),
         pd.to_numeric(market["avg_price_sqm_mxn"], errors="coerce")),
        ("market_context", "recent_inquiry_volume", "similar_available_spots",
         pd.to_numeric(market["recent_inquiry_volume"], errors="coerce"),
         pd.to_numeric(market["similar_available_spots"], errors="coerce")),
    ]
    rows = []
    for table, a_name, b_name, a, b in pairs:
        valid = a.notna() & b.notna()
        rows.append({
            "table": table,
            "variable_a": a_name,
            "variable_b": b_name,
            "n": int(valid.sum()),
            "pearson_r": float(a[valid].corr(b[valid])) if valid.sum() >= 3 else np.nan,
        })
    return pd.DataFrame(rows)


def iforest_univariate_overlap(
    scored: pd.DataFrame, groups: list[str], features: list[str], log_features: set[str]
) -> pd.DataFrame:
    rows = []
    for keys, g in scored.groupby(groups, dropna=False):
        transformed = pd.DataFrame(index=g.index)
        for col in features:
            s = pd.to_numeric(g[col], errors="coerce").astype(float)
            if col in log_features:
                s = np.log1p(s.clip(lower=0))
            transformed[col] = s

        extreme = pd.Series(False, index=g.index)
        for col in transformed:
            s = transformed[col].dropna()
            if len(s) < 30:
                continue
            q1, q3 = s.quantile([.25, .75])
            iqr = q3 - q1
            if not np.isfinite(iqr) or iqr <= 0:
                continue
            extreme |= transformed[col].lt(q1 - 1.5 * iqr) | transformed[col].gt(q3 + 1.5 * iqr)

        for flag, part in g.groupby("isolation_forest_flag"):
            idx = part.index
            rows.append({
                "entity": str(g["entity"].iloc[0]),
                "group": " | ".join(
                    f"{name}={value}" for name, value in zip(
                        groups, keys if isinstance(keys, tuple) else (keys,)
                    )
                ),
                "isolation_forest_flag": bool(flag),
                "n": len(idx),
                "share_with_any_univariate_extreme": float(extreme.loc[idx].mean()),
            })
    return pd.DataFrame(rows)


def aggregate_iforest_overlap(overlap: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (entity, flag), g in overlap.groupby(["entity", "isolation_forest_flag"]):
        weighted = np.average(g["share_with_any_univariate_extreme"], weights=g["n"])
        out.append({
            "entity": entity,
            "isolation_forest_flag": flag,
            "n": int(g["n"].sum()),
            "share_with_any_univariate_extreme": float(weighted),
        })
    return pd.DataFrame(out)



def current_state_consistency(data: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    spots = data["spots"].copy()
    inquiries = data["inquiries"]
    availability = data["availability_snapshot"]
    observation_end = max(inquiries["inquiry_at"].max(), availability["snapshot_date"].max())
    implied_end = spots["created_at"] + pd.to_timedelta(
        pd.to_numeric(spots["days_on_market"], errors="coerce"), unit="D"
    )
    delta = (implied_end - observation_end).dt.total_seconds() / 86400.0
    elapsed = (observation_end - spots["created_at"]).dt.total_seconds() / 86400.0
    days = pd.to_numeric(spots["days_on_market"], errors="coerce")

    observed_inquiries = inquiries.groupby("spot_id").size()
    current_counts = pd.to_numeric(spots["total_inquiries"], errors="coerce")
    observed_counts = spots["spot_id"].map(observed_inquiries).fillna(0)

    metrics = pd.DataFrame([
        ["observation_end", observation_end.isoformat()],
        ["days_on_market_exceeds_elapsed_count", int((days > elapsed).sum())],
        ["days_on_market_exceeds_elapsed_rate", float((days > elapsed).mean())],
        ["implied_end_more_than_365d_after_observation_count", int((delta > 365).sum())],
        ["implied_end_more_than_365d_after_observation_rate", float((delta > 365).mean())],
        ["implied_end_minus_observation_p50_days", float(delta.median())],
        ["implied_end_minus_observation_p95_days", float(delta.quantile(.95))],
        ["implied_end_minus_observation_p99_days", float(delta.quantile(.99))],
        ["implied_end_minus_observation_max_days", float(delta.max())],
        ["total_inquiries_exact_observed_match_rate", float(current_counts.eq(observed_counts).mean())],
    ], columns=["metric", "value"])

    gaps = []
    for _, g in availability.sort_values(["spot_id","snapshot_date"]).groupby("spot_id"):
        d = g["snapshot_date"].diff().dt.total_seconds().div(86400).dropna()
        gaps.extend(d.tolist())
    gap_series = pd.Series(gaps, dtype=float)
    gap_summary = pd.DataFrame([{
        "n_gaps": len(gap_series),
        "min_days": gap_series.min(),
        "p05_days": gap_series.quantile(.05),
        "median_days": gap_series.median(),
        "p95_days": gap_series.quantile(.95),
        "p99_days": gap_series.quantile(.99),
        "max_days": gap_series.max(),
        "same_day_gaps": int(gap_series.eq(0).sum()),
    }])
    return metrics, gap_summary


def missingness_semantics(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    inquiries = data["inquiries"].copy()
    inquiries["scheduled_visit"] = inquiries["broker_response"].eq("scheduled_visit")
    inquiries["urgency_missing"] = inquiries["urgency_days"].isna()
    inquiries["response_hours_missing"] = inquiries["broker_response_hours"].isna()
    rows = []

    for dimension, flag in [
        ("urgency_missing_by_channel", "urgency_missing"),
        ("urgency_missing_by_broker_response", "urgency_missing"),
        ("response_hours_missing_by_broker_response", "response_hours_missing"),
    ]:
        group_col = "channel" if dimension.endswith("channel") else "broker_response"
        for key, g in inquiries.groupby(group_col, dropna=False):
            rows.append({
                "diagnostic": dimension,
                "group": key,
                "n": len(g),
                "rate": float(g[flag].mean()),
            })

    for flag_name in ["urgency_missing", "response_hours_missing"]:
        for flag, g in inquiries.groupby(flag_name):
            rows.append({
                "diagnostic": f"scheduled_visit_by_{flag_name}",
                "group": str(bool(flag)),
                "n": len(g),
                "rate": float(g["scheduled_visit"].mean()),
            })
    return pd.DataFrame(rows)


def iforest_proxy_tail_diagnostic(inq_score: pd.DataFrame) -> pd.DataFrame:
    d = inq_score.copy()
    d["scheduled_visit"] = d["broker_response"].eq("scheduled_visit").astype(int)
    rows = []
    for tail in [.01, .03, .05, .10]:
        threshold = 1.0 - tail
        top = d["anomaly_percentile_within_group"].ge(threshold)
        rows.append({
            "anomaly_tail": tail,
            "threshold_percentile": threshold,
            "n_top": int(top.sum()),
            "top_scheduled_visit_rate": float(d.loc[top, "scheduled_visit"].mean()),
            "rest_scheduled_visit_rate": float(d.loc[~top, "scheduled_visit"].mean()),
            "rate_delta": float(
                d.loc[top, "scheduled_visit"].mean() - d.loc[~top, "scheduled_visit"].mean()
            ),
        })
    return pd.DataFrame(rows)


def current_state_distribution(data: dict[str, pd.DataFrame]) -> pd.Series:
    spots = data["spots"]
    observation_end = max(
        data["inquiries"]["inquiry_at"].max(),
        data["availability_snapshot"]["snapshot_date"].max(),
    )
    implied = spots["created_at"] + pd.to_timedelta(
        pd.to_numeric(spots["days_on_market"], errors="coerce"), unit="D"
    )
    return (implied - observation_end).dt.total_seconds() / 86400.0


def make_figures(data, cohort, rel, market_cov, av_traj, if_summary, matches, broker, if_tail):
    leads, inquiries, spots = data["leads"], data["inquiries"], data["spots"]
    hist(leads["target_area_sqm"], "01_lead_target_area_log_hist.svg", "Lead target area", True)
    hist(inquiries["requested_area_sqm"], "02_inquiry_requested_area_log_hist.svg", "Inquiry requested area", True)
    hist(spots["area_sqm"], "03_spot_area_log_hist.svg", "Spot area", True)
    hist(inquiries["message_length"], "04_message_length_hist.svg", "Inquiry message length")
    hist(inquiries["broker_response_hours"], "05_response_hours_hist.svg", "Broker response hours")
    first = inquiries.sort_values(["lead_id","inquiry_at","inquiry_id"]).drop_duplicates("lead_id").merge(leads[["lead_id","created_at"]],on="lead_id")
    lag = (first["inquiry_at"]-first["created_at"]).dt.total_seconds()/86400
    hist(np.log10(1+lag.clip(lower=0)), "06_first_inquiry_lag_log_hist.svg", "Time to first inquiry")
    fig,ax=plt.subplots(figsize=(8.6,4.7)); ax.hist(leads["prior_searches"],bins=31,alpha=.65,label="prior_searches"); ax.hist(leads["prior_inquiries"].clip(upper=60),bins=31,alpha=.55,label="prior_inquiries <=60"); ax.legend(frameon=False); style(ax,"Prior activity","mass at zero plus heavy component"); save(fig,"07_prior_activity_hist.svg")
    x=inquiries.merge(spots[["spot_id","area_sqm"]],on="spot_id"); ratio=x["requested_area_sqm"]/x["area_sqm"]
    fig,ax=plt.subplots(figsize=(8.6,4.7)); ax.hist(ratio,bins=np.linspace(.25,5.05,60),color="#2563EB",edgecolor="white"); ax.axvline(.3,color="#D4A017",ls="--"); ax.axvline(5,color="#D4A017",ls="--"); style(ax,"Requested area / spot area","boundary mass exposes clipping"); save(fig,"08_area_ratio_clipping_hist.svg")
    b=inquiries.merge(leads[["lead_id","max_budget_mxn_rent_monthly","max_budget_mxn_sale_total"]],on="lead_id"); rr=(b["requested_budget_mxn_rent_monthly"]/b["max_budget_mxn_rent_monthly"]).dropna(); sr=(b["requested_budget_mxn_sale_total"]/b["max_budget_mxn_sale_total"]).dropna()
    fig,ax=plt.subplots(figsize=(8.6,4.7)); ax.hist(rr,bins=np.linspace(.68,1.01,35),alpha=.65,label="rent"); ax.hist(sr,bins=np.linspace(.68,1.01,35),alpha=.55,label="sale"); ax.legend(frameon=False); style(ax,"Requested budget / lead maximum","most values constrained to 70%-100%"); save(fig,"09_requested_budget_to_lead_max_hist.svg")
    pos=np.arange(len(cohort)); fig,ax=plt.subplots(figsize=(10.5,5)); ax.plot(pos,cohort["inquiries_per_lead"],marker="o",label="all"); ax.plot(pos,cohort["inquiries_within_30d_per_lead"],marker="o",label="<=30d"); ax.set_xticks(pos[::2],cohort["lead_month"].iloc[::2],rotation=45,ha="right"); ax.legend(frameon=False); style(ax,"Interaction density by cohort","total stable, 30-day density rises"); save(fig,"10_cohort_interaction_compression.svg")
    fig,ax=plt.subplots(figsize=(10.5,5)); ax.plot(pos,cohort["median_first_inquiry_lag_days"],marker="o",color="#D4A017"); ax.set_xticks(pos[::2],cohort["lead_month"].iloc[::2],rotation=45,ha="right"); style(ax,"Median first-inquiry lag by cohort","later cohorts interact sooner"); save(fig,"11_cohort_first_inquiry_lag.svg")
    fig,ax=plt.subplots(figsize=(8.6,4.7)); ax.hist(market_cov["observed_months"],bins=np.arange(2.5,13.6,1),color="#2563EB",edgecolor="white"); style(ax,"Market-context months per geo-sector key","30 months global; only 3-12 per key"); save(fig,"12_market_panel_coverage.svg")
    fig,ax=plt.subplots(figsize=(8.6,4.7)); ax.hist(av_traj["transitions"],bins=np.arange(-.5,av_traj["transitions"].max()+1.5,1),color="#2563EB",edgecolor="white"); style(ax,"Availability transitions per spot","most spots switch state repeatedly"); save(fig,"13_availability_transitions_hist.svg")
    s=if_summary.groupby("entity").agg(p50=("score_p50","median"),p95=("score_p95","median"),p99=("score_p99","median")).reset_index(); y=np.arange(len(s)); fig,ax=plt.subplots(figsize=(8.6,4.7)); ax.hlines(y,s["p50"],s["p99"],color="#6B7280",lw=5); ax.scatter(s["p95"],y,label="p95"); ax.scatter(s["p99"],y,label="p99"); ax.set_yticks(y,s["entity"]); ax.legend(frameon=False); style(ax,"Isolation Forest score ranges","stratified, 3% diagnostic contamination"); save(fig,"14_iforest_score_ranges.svg")
    m=matches[matches["dimension"].eq("rent_budget_to_spot_price")]; fig,ax=plt.subplots(figsize=(8.6,4.7)); ax.bar(m["bucket"],m["scheduled_visit_rate"],color="#2563EB"); ax.yaxis.set_major_formatter(lambda v,p:f"{v:.0%}"); style(ax,"Scheduled visit by rent-budget / spot-price","near-1 fit is not privileged"); save(fig,"15_match_budget_bucket_rates.svg")
    fig,ax=plt.subplots(figsize=(8.6,4.7)); ax.scatter(broker["n"],broker["rate"],alpha=.55,color="#2563EB"); ax.yaxis.set_major_formatter(lambda v,p:f"{v:.0%}"); style(ax,"Broker rate vs support","descriptive heterogeneity, composition may confound"); save(fig,"16_broker_rate_vs_support.svg")
    spot_cols=["area_sqm","price_sqm_mxn_rent","price_sqm_mxn_sale","price_total_mxn_rent","price_total_mxn_sale","maintenance_cost_mxn","days_on_market","total_inquiries","total_views"]
    heatmap(spots[spot_cols].corr(),"Spot numeric correlations","17_spot_correlation_heatmap.svg")
    market_cols=["avg_price_sqm_mxn","recent_occupancy_rate","absorption_velocity_days","recent_inquiry_volume","similar_available_spots"]
    heatmap(data["market_context"][market_cols].corr(),"Market-context correlations","18_market_correlation_heatmap.svg")
    delta = current_state_distribution(data).dropna()
    fig,ax=plt.subplots(figsize=(8.6,4.7)); ax.hist(delta,bins=55,color="#2563EB",edgecolor="white"); ax.axvline(0,color="#D4A017",ls="--",label="observation end"); ax.legend(frameon=False); style(ax,"Spot days_on_market implied end vs observation end","positive values imply a future end beyond observed data"); save(fig,"19_days_on_market_temporal_consistency.svg")
    fig,ax=plt.subplots(figsize=(8.6,4.7)); pos=np.arange(len(if_tail)); w=.36; ax.bar(pos-w/2,if_tail["top_scheduled_visit_rate"],w,label="anomaly tail",color="#2563EB"); ax.bar(pos+w/2,if_tail["rest_scheduled_visit_rate"],w,label="rest",color="#D4A017"); ax.set_xticks(pos,[f"top {x:.0%}" for x in if_tail["anomaly_tail"]]); ax.yaxis.set_major_formatter(lambda v,p:f"{v:.0%}"); ax.legend(frameon=False); style(ax,"Scheduled visit across anomaly-score tails","outcome is inspected only after outcome-free anomaly fitting"); save(fig,"20_iforest_tail_proxy_diagnostic.svg")


def main():
    data=load_data(); leads=data["leads"]; inquiries=data["inquiries"]; spots=data["spots"]
    attrs=add_amenities(data["spot_attributes"]); spots_static=spots.merge(attrs.drop(columns=["amenities"],errors="ignore"),on="spot_id",how="left")
    inquiry_input=inquiries.merge(leads[["lead_id","search_sector","search_modality"]],on="lead_id",how="left")
    numeric=numeric_summary(data)
    outliers=pd.concat([
        stratified_outliers(leads,"lead",["search_sector","search_modality"],["target_area_sqm","prior_searches","prior_inquiries","min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly","min_budget_mxn_sale_total","max_budget_mxn_sale_total"]),
        stratified_outliers(spots_static,"spot",["sector_name","modality"],["area_sqm","price_sqm_mxn_rent","price_sqm_mxn_sale","maintenance_cost_mxn","floor_level","elevators","vertical_height_m","parking_spaces","amenities_count"]),
        stratified_outliers(inquiry_input,"inquiry",["search_sector","search_modality"],["message_length","requested_area_sqm","requested_budget_mxn_rent_monthly","requested_budget_mxn_sale_total","urgency_days"])
    ],ignore_index=True)
    lead_feat=["target_area_sqm","prior_searches","prior_inquiries","min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly","min_budget_mxn_sale_total","max_budget_mxn_sale_total","has_converted_before"]
    lead_score,lead_sum=iforest_by_group(leads,"lead","lead_id",["search_sector","search_modality"],lead_feat,set(lead_feat)-{"has_converted_before"})
    spot_feat=["area_sqm","price_sqm_mxn_rent","price_sqm_mxn_sale","maintenance_cost_mxn","luminaires","charging_ports","floor_level","elevators","vertical_height_m","parking_spaces","amenities_count"]
    spot_score,spot_sum=iforest_by_group(spots_static,"spot","spot_id",["sector_name","modality"],spot_feat,set(spot_feat))
    inq_feat=["message_length","requested_area_sqm","requested_budget_mxn_rent_monthly","requested_budget_mxn_sale_total","urgency_days","asked_visit"]
    inq_score,inq_sum=iforest_by_group(inquiry_input,"inquiry","inquiry_id",["search_sector","search_modality"],inq_feat,set(inq_feat)-{"asked_visit"})
    if_sum=pd.concat([lead_sum,spot_sum,inq_sum],ignore_index=True)
    if_overlap = pd.concat([
        iforest_univariate_overlap(
            lead_score, ["search_sector","search_modality"], lead_feat,
            set(lead_feat)-{"has_converted_before"}
        ),
        iforest_univariate_overlap(
            spot_score, ["sector_name","modality"], spot_feat, set(spot_feat)
        ),
        iforest_univariate_overlap(
            inq_score, ["search_sector","search_modality"], inq_feat,
            set(inq_feat)-{"asked_visit"}
        ),
    ], ignore_index=True)
    if_overlap_agg = aggregate_iforest_overlap(if_overlap)
    correlations = selected_correlations(data)
    current_state, availability_gaps = current_state_consistency(data)
    missingness_diag = missingness_semantics(data)
    if_tail = iforest_proxy_tail_diagnostic(inq_score)
    cohort=cohort_dynamics(leads,inquiries); rel=deterministic_relationships(leads,inquiries,spots); market_cov=market_panel(data["market_context"]); av=availability_trajectories(data["availability_snapshot"]); matches=match_rates(leads,inquiries,spots); broker=broker_summary(spots,inquiries)
    numeric.to_csv(RESULTS/"numeric_summary.csv",index=False); outliers.to_csv(RESULTS/"stratified_outliers.csv",index=False); rel.to_csv(RESULTS/"deterministic_relationships.csv",index=False); cohort.to_csv(RESULTS/"cohort_dynamics.csv",index=False); market_cov.to_csv(RESULTS/"market_panel_coverage.csv",index=False); av.to_csv(RESULTS/"availability_trajectories.csv",index=False); matches.to_csv(RESULTS/"match_bucket_rates.csv",index=False); broker.to_csv(RESULTS/"broker_summary.csv",index=False); if_sum.to_csv(RESULTS/"iforest_summary.csv",index=False)
    correlations.to_csv(RESULTS/"selected_correlations.csv", index=False)
    if_overlap.to_csv(RESULTS/"iforest_univariate_overlap_by_group.csv", index=False)
    if_overlap_agg.to_csv(RESULTS/"iforest_univariate_overlap.csv", index=False)
    current_state.to_csv(RESULTS/"current_state_temporal_consistency.csv", index=False)
    availability_gaps.to_csv(RESULTS/"availability_snapshot_gap_summary.csv", index=False)
    missingness_diag.to_csv(RESULTS/"missingness_semantics.csv", index=False)
    if_tail.to_csv(RESULTS/"iforest_proxy_tail_diagnostic.csv", index=False)
    lead_score.loc[lead_score["isolation_forest_flag"]].head(250).to_csv(RESULTS/"iforest_lead_anomalies.csv",index=False)
    spot_score.loc[spot_score["isolation_forest_flag"]].head(250).to_csv(RESULTS/"iforest_spot_anomalies.csv",index=False)
    inq_score.loc[inq_score["isolation_forest_flag"]].head(500).to_csv(RESULTS/"iforest_inquiry_anomalies.csv",index=False)
    q=inq_score.copy(); q["scheduled_visit"]=q["broker_response"].eq("scheduled_visit").astype(int); q.groupby("isolation_forest_flag")["scheduled_visit"].agg(["size","mean"]).reset_index().to_csv(RESULTS/"iforest_inquiry_proxy_diagnostic.csv",index=False)
    make_figures(data,cohort,rel,market_cov,av,if_sum,matches,broker,if_tail)
    summary={
        "scope":"deep EDA only; no model fitting or automatic row deletion",
        "datasets":{k:len(v) for k,v in data.items()},
        "cohort_start":cohort.iloc[0].to_dict(),"cohort_end":cohort.iloc[-1].to_dict(),
        "deterministic_relationships":dict(zip(rel.metric,rel.value)),
        "market_panel":{"keys":len(market_cov),"global_months":data["market_context"]["month"].nunique(),"min_months":market_cov.observed_months.min(),"median_months":market_cov.observed_months.median(),"max_months":market_cov.observed_months.max(),"complete_keys":int((market_cov.observed_months==data["market_context"]["month"].nunique()).sum())},
        "availability":{"change_share":av.ever_changes.mean(),"median_transitions":av.transitions.median(),"median_snapshots":av.snapshots.median()},
        "isolation_forest":{
            "contamination":CONTAMINATION,
            "lead_flags":int(lead_score.isolation_forest_flag.sum()),
            "spot_flags":int(spot_score.isolation_forest_flag.sum()),
            "inquiry_flags":int(inq_score.isolation_forest_flag.sum()),
            "univariate_overlap": if_overlap_agg.to_dict(orient="records"),
        },
        "broker_ge50":{"min_rate":broker.loc[broker.n>=50,"rate"].min(),"max_rate":broker.loc[broker.n>=50,"rate"].max()},
        "current_state_temporal_consistency": dict(zip(current_state["metric"], current_state["value"])),
        "availability_snapshot_gaps": availability_gaps.iloc[0].to_dict(),
        "iforest_proxy_tail_diagnostic": if_tail.to_dict(orient="records"),
    }
    (RESULTS/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False,default=str)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,ensure_ascii=False,default=str))


if __name__=="__main__":
    main()
