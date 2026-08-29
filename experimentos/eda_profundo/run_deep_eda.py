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


def make_figures(data, cohort, rel, market_cov, av_traj, if_summary, matches, broker):
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
    cohort=cohort_dynamics(leads,inquiries); rel=deterministic_relationships(leads,inquiries,spots); market_cov=market_panel(data["market_context"]); av=availability_trajectories(data["availability_snapshot"]); matches=match_rates(leads,inquiries,spots); broker=broker_summary(spots,inquiries)
    numeric.to_csv(RESULTS/"numeric_summary.csv",index=False); outliers.to_csv(RESULTS/"stratified_outliers.csv",index=False); rel.to_csv(RESULTS/"deterministic_relationships.csv",index=False); cohort.to_csv(RESULTS/"cohort_dynamics.csv",index=False); market_cov.to_csv(RESULTS/"market_panel_coverage.csv",index=False); av.to_csv(RESULTS/"availability_trajectories.csv",index=False); matches.to_csv(RESULTS/"match_bucket_rates.csv",index=False); broker.to_csv(RESULTS/"broker_summary.csv",index=False); if_sum.to_csv(RESULTS/"iforest_summary.csv",index=False)
    lead_score.loc[lead_score["isolation_forest_flag"]].head(250).to_csv(RESULTS/"iforest_lead_anomalies.csv",index=False)
    spot_score.loc[spot_score["isolation_forest_flag"]].head(250).to_csv(RESULTS/"iforest_spot_anomalies.csv",index=False)
    inq_score.loc[inq_score["isolation_forest_flag"]].head(500).to_csv(RESULTS/"iforest_inquiry_anomalies.csv",index=False)
    q=inq_score.copy(); q["scheduled_visit"]=q["broker_response"].eq("scheduled_visit").astype(int); q.groupby("isolation_forest_flag")["scheduled_visit"].agg(["size","mean"]).reset_index().to_csv(RESULTS/"iforest_inquiry_proxy_diagnostic.csv",index=False)
    make_figures(data,cohort,rel,market_cov,av,if_sum,matches,broker)
    summary={
        "scope":"deep EDA only; no model fitting or automatic row deletion",
        "datasets":{k:len(v) for k,v in data.items()},
        "cohort_start":cohort.iloc[0].to_dict(),"cohort_end":cohort.iloc[-1].to_dict(),
        "deterministic_relationships":dict(zip(rel.metric,rel.value)),
        "market_panel":{"keys":len(market_cov),"global_months":data["market_context"]["month"].nunique(),"min_months":market_cov.observed_months.min(),"median_months":market_cov.observed_months.median(),"max_months":market_cov.observed_months.max(),"complete_keys":int((market_cov.observed_months==data["market_context"]["month"].nunique()).sum())},
        "availability":{"change_share":av.ever_changes.mean(),"median_transitions":av.transitions.median(),"median_snapshots":av.snapshots.median()},
        "isolation_forest":{"contamination":CONTAMINATION,"lead_flags":int(lead_score.isolation_forest_flag.sum()),"spot_flags":int(spot_score.isolation_forest_flag.sum()),"inquiry_flags":int(inq_score.isolation_forest_flag.sum())},
        "broker_ge50":{"min_rate":broker.loc[broker.n>=50,"rate"].min(),"max_rate":broker.loc[broker.n>=50,"rate"].max()},
    }
    (RESULTS/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False,default=str)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,ensure_ascii=False,default=str))


if __name__=="__main__":
    main()
