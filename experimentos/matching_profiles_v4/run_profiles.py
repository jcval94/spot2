from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import BisectingKMeans, KMeans
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    adjusted_rand_score,
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

SEED = 20260829
BOOT = 400
MIN_CELL = 50

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
DATA = ROOT / "data" / "candidate" / "csv"
PARENT_PROF = ROOT / "experimentos" / "profile_clustering_v2" / "results"
PARENT_AB = ROOT / "experimentos" / "matching_ab_v3" / "results"

def jdump(obj):
    def clean(x):
        if isinstance(x, (np.integer,)): return int(x)
        if isinstance(x, (np.floating,)): return None if np.isnan(x) else float(x)
        if isinstance(x, pd.Timestamp): return x.isoformat()
        if isinstance(x, np.bool_): return bool(x)
        raise TypeError(type(x).__name__)
    return json.dumps(obj, indent=2, ensure_ascii=False, default=clean)

def load():
    leads = pd.read_csv(DATA / "leads.csv", parse_dates=["created_at"])
    spots = pd.read_csv(DATA / "spots.csv", parse_dates=["created_at"])
    attrs = pd.read_csv(DATA / "spot_attributes.csv")
    iq = pd.read_csv(DATA / "inquiries.csv", parse_dates=["inquiry_at"])
    av = pd.read_csv(DATA / "availability_snapshot.csv", parse_dates=["snapshot_date"])
    return leads, spots, attrs, iq, av

def preprocessor(cat_cols, num_cols):
    parts = []
    if cat_cols:
        parts.append(("cat", Pipeline([
            ("imp", SimpleImputer(strategy="most_frequent")),
            ("oh", OneHotEncoder(handle_unknown="ignore"))
        ]), cat_cols))
    if num_cols:
        parts.append(("num", Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc", RobustScaler())
        ]), num_cols))
    return ColumnTransformer(parts)

def norm_entropy(labels):
    s = pd.Series(labels).value_counts(normalize=True).values
    return float(-(s * np.log(s)).sum() / np.log(len(s))) if len(s) > 1 else 0.0

def select_clusterer(ref, all_df, cat_cols, num_cols, prefix, family):
    prep = preprocessor(cat_cols, num_cols)
    xr = prep.fit_transform(ref[cat_cols + num_cols])
    xa = prep.transform(all_df[cat_cols + num_cols])
    xr = xr.toarray() if hasattr(xr, "toarray") and xr.shape[1] < 250 else xr
    xa = xa.toarray() if hasattr(xa, "toarray") and xa.shape[1] < 250 else xa
    rows, fitted = [], {}
    for method in ["kmeans", "bisecting", "gmm"]:
        for k in range(3, 8):
            if method == "kmeans":
                m = KMeans(n_clusters=k, n_init=20, random_state=SEED)
                lab = m.fit_predict(xr)
                all_lab = m.predict(xa)
                m2 = KMeans(n_clusters=k, n_init=20, random_state=SEED + 17)
                lab2 = m2.fit_predict(xr)
            elif method == "bisecting":
                m = BisectingKMeans(n_clusters=k, random_state=SEED)
                lab = m.fit_predict(xr)
                all_lab = m.predict(xa)
                m2 = BisectingKMeans(n_clusters=k, random_state=SEED + 17)
                lab2 = m2.fit_predict(xr)
            else:
                dense_r = np.asarray(xr)
                dense_a = np.asarray(xa)
                m = GaussianMixture(
                    n_components=k, covariance_type="diag", reg_covar=1e-5,
                    random_state=SEED, n_init=3
                )
                lab = m.fit_predict(dense_r)
                all_lab = m.predict(dense_a)
                m2 = GaussianMixture(
                    n_components=k, covariance_type="diag", reg_covar=1e-5,
                    random_state=SEED + 17, n_init=3
                )
                lab2 = m2.fit_predict(dense_r)
            shares = pd.Series(lab).value_counts(normalize=True)
            sil = float(silhouette_score(
                xr, lab, sample_size=min(1800, len(ref)), random_state=SEED
            ))
            ari = float(adjusted_rand_score(lab, lab2))
            ent = norm_entropy(lab)
            mn, mx = float(shares.min()), float(shares.max())
            balance = mn >= 0.05 and mx <= 0.65
            score = sil + 0.22 * ent + 0.18 * ari + (0.10 if balance else -0.25)
            rows.append({
                "profile_family": family, "method": method, "k": k,
                "silhouette": sil, "normalized_entropy": ent,
                "stability_ari": ari, "min_cluster_share": mn,
                "max_cluster_share": mx, "balance_ok": balance,
                "selection_score": score
            })
            fitted[(method, k)] = (lab, all_lab)
    bench = pd.DataFrame(rows)
    pool = bench[bench.balance_ok] if bench.balance_ok.any() else bench
    best = pool.sort_values(
        ["selection_score", "stability_ari", "normalized_entropy"],
        ascending=False
    ).iloc[0]
    method, k = str(best.method), int(best.k)
    lab, all_lab = fitted[(method, k)]
    order = pd.Series(lab).value_counts().index.tolist()
    remap = {raw: i + 1 for i, raw in enumerate(order)}
    ref_ids = pd.Series([f"{prefix}{remap[x]}" for x in lab], index=ref.index)
    all_ids = pd.Series([f"{prefix}{remap[x]}" for x in all_lab], index=all_df.index)
    bench["selected"] = bench.method.eq(method) & bench.k.eq(k)
    return ref_ids, all_ids, bench

def describe_profiles(df, profile_col, cat_cols, num_cols, family):
    rows = []
    for pid, g in df.groupby(profile_col):
        signals = []
        for c in cat_cols:
            mode = g[c].dropna().astype(str).mode()
            if len(mode):
                v = mode.iloc[0]
                share = float(g[c].astype(str).eq(v).mean())
                overall = float(df[c].astype(str).eq(v).mean())
                signals.append((abs(share - overall), f"{c}={v} ({share:.0%}; {share-overall:+.0%}pp)"))
        for c in num_cols:
            med = pd.to_numeric(g[c], errors="coerce").median()
            all_med = pd.to_numeric(df[c], errors="coerce").median()
            iqr = pd.to_numeric(df[c], errors="coerce").quantile(.75) - pd.to_numeric(df[c], errors="coerce").quantile(.25)
            if pd.notna(med) and pd.notna(all_med):
                z = 0.0 if not pd.notna(iqr) or iqr == 0 else float((med - all_med) / iqr)
                signals.append((abs(z), f"{c} median={med:.3g} ({z:+.2f} IQR)"))
        signals = [s for _, s in sorted(signals, key=lambda x: x[0], reverse=True)[:5]]
        rows.append({
            "profile_family": family, "profile_id": pid, "n_reference": len(g),
            "share_reference": len(g) / len(df), "top_signals": " | ".join(signals)
        })
    return pd.DataFrame(rows)

def build_behavioral_persona(leads, cutoff):
    d = leads.copy()
    d["has_converted_before"] = d["has_converted_before"].astype(str)
    cat = ["user_type", "company_size", "industry", "has_converted_before"]
    num = ["prior_searches", "prior_inquiries"]
    ref = d[d.created_at < cutoff].copy()
    rid, aid, bench = select_clusterer(ref, d, cat, num, "BP", "behavioral_persona")
    ref["behavioral_profile"] = rid
    d["behavioral_profile"] = aid
    interp = describe_profiles(ref, "behavioral_profile", cat, num, "behavioral_persona")
    return d[["lead_id", "source", "behavioral_profile"]], bench, interp

def derive_dynamic_need(iq, leads):
    lead_cols = [
        "lead_id", "target_area_sqm",
        "min_budget_mxn_rent_monthly", "max_budget_mxn_rent_monthly",
        "min_budget_mxn_sale_total", "max_budget_mxn_sale_total"
    ]
    d = iq.merge(leads[lead_cols], on="lead_id", how="left", validate="many_to_one")
    rent = d.requested_budget_mxn_rent_monthly.notna()
    sale = d.requested_budget_mxn_sale_total.notna()
    d["request_modality"] = np.select(
        [rent & sale, rent, sale], ["both", "rent", "sale"], default="unspecified"
    )
    d["asked_visit_cat"] = d.asked_visit.astype(str)
    d["log_requested_area"] = np.log1p(pd.to_numeric(d.requested_area_sqm, errors="coerce"))
    d["log_rent_budget"] = np.log1p(pd.to_numeric(d.requested_budget_mxn_rent_monthly, errors="coerce"))
    d["log_sale_budget"] = np.log1p(pd.to_numeric(d.requested_budget_mxn_sale_total, errors="coerce"))

    def safe_log_ratio(a, b):
        a = pd.to_numeric(a, errors="coerce")
        b = pd.to_numeric(b, errors="coerce")
        return np.log((a.clip(lower=0) + 1) / (b.clip(lower=0) + 1))

    rent_mid = (d.min_budget_mxn_rent_monthly + d.max_budget_mxn_rent_monthly) / 2
    sale_mid = (d.min_budget_mxn_sale_total + d.max_budget_mxn_sale_total) / 2
    d["area_log_ratio"] = safe_log_ratio(d.requested_area_sqm, d.target_area_sqm)
    d["rent_budget_log_ratio"] = safe_log_ratio(d.requested_budget_mxn_rent_monthly, rent_mid)
    d["sale_budget_log_ratio"] = safe_log_ratio(d.requested_budget_mxn_sale_total, sale_mid)
    return d

def build_dynamic_need(iq, leads, cutoff):
    d = derive_dynamic_need(iq, leads)
    cat = ["request_modality", "channel", "asked_visit_cat"]
    num = [
        "log_requested_area", "log_rent_budget", "log_sale_budget",
        "urgency_days", "message_length",
        "area_log_ratio", "rent_budget_log_ratio", "sale_budget_log_ratio"
    ]
    ref = d[d.inquiry_at < cutoff].copy()
    rid, aid, bench = select_clusterer(ref, d, cat, num, "DN", "dynamic_need_t1")
    ref["dynamic_need_profile"] = rid
    d["dynamic_need_profile"] = aid
    interp = describe_profiles(ref, "dynamic_need_profile", cat, num, "dynamic_need_t1")
    return d[["inquiry_id", "dynamic_need_profile"]], bench, interp

def shares(frame, index, col, prefix):
    t = pd.crosstab(frame[index], frame[col], normalize="index")
    t.columns = [f"{prefix}_{str(c).lower().replace(' ', '_')}" for c in t.columns]
    return t

def build_broker_features(spots, iq, cutoff):
    brokers = pd.DataFrame({"broker_id": sorted(spots.broker_id.dropna().unique())})
    s = spots[spots.created_at < cutoff].copy()
    base = s.groupby("broker_id").agg(
        n_spots=("spot_id", "size"),
        median_area=("area_sqm", "median"),
        median_rent=("price_sqm_mxn_rent", "median"),
        median_sale=("price_sqm_mxn_sale", "median"),
    )
    supply = base.join(shares(s, "broker_id", "sector_name", "sector"), how="outer")
    supply = supply.join(shares(s, "broker_id", "modality", "modality"), how="outer")
    supply = supply.join(shares(s, "broker_id", "region", "region"), how="outer")
    supply = brokers.merge(supply.reset_index(), on="broker_id", how="left").fillna(0)

    hi = iq[iq.inquiry_at < cutoff].merge(
        spots[["spot_id", "broker_id"]], on="spot_id", how="left", validate="many_to_one"
    )
    hi["asked_visit_num"] = hi.asked_visit.astype(str).str.lower().isin(["true", "1", "yes"]).astype(float)
    service = hi.groupby("broker_id").agg(
        n_inquiries=("inquiry_id", "size"),
        scheduled_rate=("broker_response", lambda x: float((x == "scheduled_visit").mean())),
        accepted_rate=("broker_response", lambda x: float((x == "accepted").mean())),
        rejected_rate=("broker_response", lambda x: float((x == "rejected").mean())),
        no_response_rate=("broker_response", lambda x: float((x == "no_response").mean())),
        asked_visit_rate=("asked_visit_num", "mean"),
        median_urgency=("urgency_days", "median"),
        mean_message_length=("message_length", "mean"),
    )
    service = service.join(shares(hi, "broker_id", "channel", "channel"), how="outer")
    service = brokers.merge(service.reset_index(), on="broker_id", how="left").fillna(0)
    return supply, service

def cluster_numeric_profiles(df, prefix, family):
    cols = [c for c in df.columns if c != "broker_id"]
    rid, aid, bench = select_clusterer(df, df, [], cols, prefix, family)
    d = df.copy()
    d[f"{family}_profile"] = aid
    interp = describe_profiles(d, f"{family}_profile", [], cols, family)
    return d[["broker_id", f"{family}_profile"]], bench, interp


def _entropy_from_cols(row, cols):
    vals = pd.to_numeric(row[cols], errors="coerce").fillna(0).to_numpy(float)
    vals = vals[vals > 0]
    if len(vals) <= 1:
        return 0.0
    p = vals / vals.sum()
    return float(-(p * np.log(p)).sum() / np.log(len(cols)))

def _dominant_from_cols(row, cols, prefix):
    vals = pd.to_numeric(row[cols], errors="coerce").fillna(0)
    if float(vals.sum()) <= 0:
        return "none"
    col = str(vals.idxmax())
    return col[len(prefix) + 1:] if col.startswith(prefix + "_") else col

def _winsorize(df, cols, qlo=.02, qhi=.98):
    z = df.copy()
    for c in cols:
        lo, hi = z[c].quantile(qlo), z[c].quantile(qhi)
        if pd.notna(lo) and pd.notna(hi) and hi > lo:
            z[c] = z[c].clip(lo, hi)
    return z

def build_compact_broker_views(supply, service):
    s = supply.copy()
    sector_cols = [c for c in s.columns if c.startswith("sector_")]
    modality_cols = [c for c in s.columns if c.startswith("modality_")]
    region_cols = [c for c in s.columns if c.startswith("region_")]
    s["dominant_sector"] = s.apply(lambda r: _dominant_from_cols(r, sector_cols, "sector"), axis=1)
    s["dominant_modality"] = s.apply(lambda r: _dominant_from_cols(r, modality_cols, "modality"), axis=1)
    s["dominant_region"] = s.apply(lambda r: _dominant_from_cols(r, region_cols, "region"), axis=1)
    s["sector_entropy"] = s.apply(lambda r: _entropy_from_cols(r, sector_cols), axis=1)
    s["modality_entropy"] = s.apply(lambda r: _entropy_from_cols(r, modality_cols), axis=1)
    s["region_entropy"] = s.apply(lambda r: _entropy_from_cols(r, region_cols), axis=1)
    for src, dst in [
        ("n_spots", "log_n_spots"),
        ("median_area", "log_median_area"),
        ("median_rent", "log_median_rent"),
        ("median_sale", "log_median_sale"),
    ]:
        s[dst] = np.log1p(pd.to_numeric(s[src], errors="coerce").clip(lower=0))
    supply_cat = ["dominant_sector", "dominant_modality", "dominant_region"]
    supply_num = [
        "log_n_spots", "log_median_area", "log_median_rent", "log_median_sale",
        "sector_entropy", "modality_entropy", "region_entropy"
    ]
    s = _winsorize(s, supply_num)

    v = service.copy()
    response_cols = ["scheduled_rate", "accepted_rate", "rejected_rate", "no_response_rate"]
    channel_cols = [c for c in v.columns if c.startswith("channel_")]
    v["dominant_response"] = v.apply(lambda r: _dominant_from_cols(r, response_cols, ""), axis=1)
    # _dominant_from_cols with empty prefix returns the column name; simplify labels.
    v["dominant_response"] = v["dominant_response"].str.replace("_rate", "", regex=False)
    v["dominant_channel"] = v.apply(lambda r: _dominant_from_cols(r, channel_cols, "channel"), axis=1)
    v["response_entropy"] = v.apply(lambda r: _entropy_from_cols(r, response_cols), axis=1)
    v["channel_entropy"] = v.apply(lambda r: _entropy_from_cols(r, channel_cols), axis=1)
    v["log_n_inquiries"] = np.log1p(pd.to_numeric(v["n_inquiries"], errors="coerce").clip(lower=0))
    v["log_median_urgency"] = np.log1p(pd.to_numeric(v["median_urgency"], errors="coerce").clip(lower=0))
    v["log_mean_message_length"] = np.log1p(pd.to_numeric(v["mean_message_length"], errors="coerce").clip(lower=0))
    service_cat = ["dominant_response", "dominant_channel"]
    service_num = [
        "log_n_inquiries", "scheduled_rate", "accepted_rate", "rejected_rate",
        "no_response_rate", "asked_visit_rate", "log_median_urgency",
        "log_mean_message_length", "response_entropy", "channel_entropy"
    ]
    v = _winsorize(v, service_num)
    return s[["broker_id"] + supply_cat + supply_num], supply_cat, supply_num, v[["broker_id"] + service_cat + service_num], service_cat, service_num

def cluster_compact_broker(df, cat_cols, num_cols, prefix, family, require_balance=True):
    rid, aid, bench = select_clusterer(df, df, cat_cols, num_cols, prefix, family)
    selected = bench[bench.selected].iloc[0]
    passed = bool(selected.balance_ok)
    d = df.copy()
    profile_col = f"{family}_profile"
    d[profile_col] = aid
    interp = describe_profiles(d, profile_col, cat_cols, num_cols, family)
    if require_balance and not passed:
        return d[["broker_id", profile_col]], bench, interp, {
            "passed": False,
            "min_cluster_share": float(selected.min_cluster_share),
            "max_cluster_share": float(selected.max_cluster_share),
            "method": str(selected.method),
            "k": int(selected.k),
        }
    return d[["broker_id", profile_col]], bench, interp, {
        "passed": passed,
        "min_cluster_share": float(selected.min_cluster_share),
        "max_cluster_share": float(selected.max_cluster_share),
        "method": str(selected.method),
        "k": int(selected.k),
    }

def add_interactions_v2(df):
    z = df.copy()
    pairs = {
        "dynamic_need_x_physical_v2": ["dynamic_need_profile", "physical_profile"],
        "dynamic_need_x_location_v2": ["dynamic_need_profile", "location_profile"],
        "dynamic_need_x_broker_supply_v2": ["dynamic_need_profile", "broker_supply_balanced_profile"],
        "dynamic_need_x_broker_service_v2": ["dynamic_need_profile", "broker_service_balanced_profile"],
        "need_transition_x_physical_v2": ["need_transition", "physical_profile"],
        "need_transition_x_broker_service_v2": ["need_transition", "broker_service_balanced_profile"],
        "physical_x_broker_supply_v2": ["physical_profile", "broker_supply_balanced_profile"],
        "location_x_broker_supply_v2": ["location_profile", "broker_supply_balanced_profile"],
        "dynamic_need_x_physical_x_broker_service_v2": ["dynamic_need_profile", "physical_profile", "broker_service_balanced_profile"],
    }
    for name, cols in pairs.items():
        z[name] = z[cols].astype(str).agg("x".join, axis=1)
    return z, list(pairs)


def add_service_interactions(df):
    z = df.copy()
    pairs = {
        "dynamic_need_x_physical_service": ["dynamic_need_profile", "physical_profile"],
        "dynamic_need_x_location_service": ["dynamic_need_profile", "location_profile"],
        "dynamic_need_x_broker_service": ["dynamic_need_profile", "broker_service_balanced_profile"],
        "need_transition_x_broker_service": ["need_transition", "broker_service_balanced_profile"],
        "physical_x_broker_service": ["physical_profile", "broker_service_balanced_profile"],
        "dynamic_need_x_physical_x_service": ["dynamic_need_profile", "physical_profile", "broker_service_balanced_profile"],
    }
    for name, cols in pairs.items():
        z[name] = z[cols].astype(str).agg("x".join, axis=1)
    return z, list(pairs)

def service_compatibility_cells(test, global_rate):
    specs = [
        (["dynamic_need_profile", "broker_service_balanced_profile"], "dynamic_need_x_broker_service"),
        (["dynamic_need_profile", "physical_profile"], "dynamic_need_x_physical"),
        (["dynamic_need_profile", "location_profile"], "dynamic_need_x_location"),
        (["need_transition", "broker_service_balanced_profile"], "need_transition_x_broker_service"),
        (["physical_profile", "broker_service_balanced_profile"], "physical_x_broker_service"),
        (["dynamic_need_profile", "physical_profile", "broker_service_balanced_profile"], "dynamic_need_x_physical_x_service"),
        (["dynamic_need_profile", "location_profile", "broker_service_balanced_profile"], "dynamic_need_x_location_x_service"),
    ]
    rows = []
    for cols, label in specs:
        for keys, g in test.groupby(cols):
            if len(g) < MIN_CELL:
                continue
            if not isinstance(keys, tuple):
                keys = (keys,)
            k, n = int(g.visit.sum()), len(g)
            smooth = (k + 30 * global_rate) / (n + 30)
            lo, hi = wilson(k, n)
            row = {
                "interaction": label, "n": n, "visit_rate": k/n,
                "smoothed_rate": smooth, "lift_vs_global": smooth/global_rate,
                "wilson_low": lo, "wilson_high": hi, "wilson_low_lift": lo/global_rate
            }
            row.update(dict(zip(cols, keys)))
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["lift_vs_global","n"], ascending=[False,False]).reset_index(drop=True)

def compatibility_cells_v2(test, global_rate):
    specs = [
        (["dynamic_need_profile", "physical_profile"], "dynamic_need_x_physical_v2"),
        (["dynamic_need_profile", "location_profile"], "dynamic_need_x_location_v2"),
        (["dynamic_need_profile", "broker_supply_balanced_profile"], "dynamic_need_x_broker_supply_v2"),
        (["dynamic_need_profile", "broker_service_balanced_profile"], "dynamic_need_x_broker_service_v2"),
        (["need_transition", "physical_profile"], "need_transition_x_physical_v2"),
        (["need_transition", "broker_service_balanced_profile"], "need_transition_x_broker_service_v2"),
        (["physical_profile", "broker_supply_balanced_profile"], "physical_x_broker_supply_v2"),
        (["location_profile", "broker_supply_balanced_profile"], "location_x_broker_supply_v2"),
        (["dynamic_need_profile", "physical_profile", "broker_service_balanced_profile"], "dynamic_need_x_physical_x_broker_service_v2"),
        (["dynamic_need_profile", "location_profile", "broker_service_balanced_profile"], "dynamic_need_x_location_x_broker_service_v2"),
    ]
    rows = []
    for cols, label in specs:
        for keys, g in test.groupby(cols):
            if len(g) < MIN_CELL:
                continue
            if not isinstance(keys, tuple):
                keys = (keys,)
            k, n = int(g.visit.sum()), len(g)
            smooth = (k + 30 * global_rate) / (n + 30)
            lo, hi = wilson(k, n)
            row = {
                "interaction": label, "n": n, "visit_rate": k/n,
                "smoothed_rate": smooth, "lift_vs_global": smooth/global_rate,
                "wilson_low": lo, "wilson_high": hi, "wilson_low_lift": lo/global_rate
            }
            row.update(dict(zip(cols, keys)))
            rows.append(row)
    return pd.DataFrame(rows).sort_values(
        ["lift_vs_global", "n"], ascending=[False, False]
    ).reset_index(drop=True)

def availability_features(iq, av):
    left = iq[["inquiry_id", "spot_id", "inquiry_at"]].sort_values(["inquiry_at", "spot_id"]).copy()
    right = av[["spot_id", "snapshot_date", "is_available"]].sort_values(["snapshot_date", "spot_id"]).copy()
    a = pd.merge_asof(
        left, right, left_on="inquiry_at", right_on="snapshot_date", by="spot_id",
        direction="backward", allow_exact_matches=True
    )
    a["lag_days"] = (a.inquiry_at - a.snapshot_date).dt.total_seconds() / 86400
    flag = a.is_available.astype(str).str.lower().isin(["true", "1", "yes"])
    a["availability_state"] = np.where(
        a.snapshot_date.isna(), "missing", np.where(flag, "available", "not_available")
    )
    a["availability_lag_bucket"] = pd.cut(
        a.lag_days, [-np.inf, 7, 30, 90, np.inf],
        labels=["0-7d", "8-30d", "31-90d", ">90d"]
    ).astype(str)
    return a[["inquiry_id", "availability_state", "availability_lag_bucket"]]

def fit_score(train, test, cols):
    model = Pipeline([
        ("oh", OneHotEncoder(handle_unknown="ignore", min_frequency=10)),
        ("lr", LogisticRegression(C=.5, max_iter=4000, random_state=SEED))
    ])
    model.fit(train[cols].astype(str).fillna("missing"), train.visit.astype(int))
    return model.predict_proba(test[cols].astype(str).fillna("missing"))[:, 1]

def metrics(y, p):
    y = np.asarray(y, int)
    p = np.clip(np.asarray(p, float), 1e-8, 1 - 1e-8)
    top = max(1, int(math.ceil(len(y) * .10)))
    top20 = max(1, int(math.ceil(len(y) * .20)))
    i10 = np.argsort(-p)[:top]
    i20 = np.argsort(-p)[:top20]
    return {
        "roc_auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "lift_top_10pct": float(y[i10].mean() / y.mean()),
        "recall_top_20pct": float(y[i20].sum() / y.sum()),
    }

def lead_metrics(test, p):
    z = pd.DataFrame({"lead_id": test.lead_id.values, "y": test.visit.values, "p": p})
    g = z.groupby("lead_id").agg(y=("y", "max"), p=("p", "max"))
    return metrics(g.y, g.p), len(g), float(g.y.mean())

def bootstrap_delta(test, pa, pb, n=BOOT):
    rng = np.random.default_rng(SEED)
    lead_arr = test.lead_id.to_numpy()
    leads = pd.unique(lead_arr)
    vals = []
    for _ in range(n):
        sample = rng.choice(leads, size=len(leads), replace=True)
        idx = np.concatenate([np.flatnonzero(lead_arr == x) for x in sample])
        y = test.visit.to_numpy()[idx]
        if len(np.unique(y)) < 2:
            continue
        ma, mb = metrics(y, pa[idx]), metrics(y, pb[idx])
        vals.append([
            mb["roc_auc"] - ma["roc_auc"],
            mb["average_precision"] - ma["average_precision"],
            mb["lift_top_10pct"] - ma["lift_top_10pct"],
            mb["recall_top_20pct"] - ma["recall_top_20pct"],
        ])
    arr = np.asarray(vals)
    names = ["delta_auc", "delta_ap", "delta_lift10", "delta_recall20"]
    out = {}
    for i, name in enumerate(names):
        out[name] = float(arr[:, i].mean())
        out[name + "_low"] = float(np.quantile(arr[:, i], .025))
        out[name + "_high"] = float(np.quantile(arr[:, i], .975))
        out[name + "_p_positive"] = float((arr[:, i] > 0).mean())
    return out

def conclusion(delta):
    if delta["delta_ap_low"] > 0:
        return "SUPPORTED"
    if delta["delta_ap_high"] < 0:
        return "NOT_SUPPORTED"
    return "INCONCLUSIVE"

def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    p = k / n
    den = 1 + z*z/n
    ctr = (p + z*z/(2*n)) / den
    half = z * math.sqrt((p*(1-p) + z*z/(4*n))/n) / den
    return ctr-half, ctr+half

def add_interactions(df):
    z = df.copy()
    pairs = {
        "behavioral_x_dynamic_need": ["behavioral_profile", "dynamic_need_profile"],
        "need_transition_x_physical": ["need_transition", "physical_profile"],
        "dynamic_need_x_physical": ["dynamic_need_profile", "physical_profile"],
        "dynamic_need_x_location": ["dynamic_need_profile", "location_profile"],
        "dynamic_need_x_broker_supply": ["dynamic_need_profile", "broker_supply_profile"],
        "dynamic_need_x_broker_service": ["dynamic_need_profile", "broker_service_profile"],
        "physical_x_broker_supply": ["physical_profile", "broker_supply_profile"],
        "location_x_broker_supply": ["location_profile", "broker_supply_profile"],
        "dynamic_need_x_physical_x_broker_supply": ["dynamic_need_profile", "physical_profile", "broker_supply_profile"],
    }
    for name, cols in pairs.items():
        z[name] = z[cols].astype(str).agg("x".join, axis=1)
    return z, list(pairs)

def compatibility_cells(test, global_rate):
    specs = [
        (["behavioral_profile", "dynamic_need_profile"], "behavioral_x_dynamic_need"),
        (["need_transition", "physical_profile"], "need_transition_x_physical"),
        (["dynamic_need_profile", "physical_profile"], "dynamic_need_x_physical"),
        (["dynamic_need_profile", "location_profile"], "dynamic_need_x_location"),
        (["dynamic_need_profile", "broker_supply_profile"], "dynamic_need_x_broker_supply"),
        (["dynamic_need_profile", "broker_service_profile"], "dynamic_need_x_broker_service"),
        (["physical_profile", "broker_supply_profile"], "physical_x_broker_supply"),
        (["location_profile", "broker_supply_profile"], "location_x_broker_supply"),
        (["dynamic_need_profile", "physical_profile", "broker_supply_profile"], "dynamic_need_x_physical_x_broker_supply"),
        (["dynamic_need_profile", "location_profile", "broker_supply_profile"], "dynamic_need_x_location_x_broker_supply"),
    ]
    rows = []
    for cols, label in specs:
        for keys, g in test.groupby(cols):
            if len(g) < MIN_CELL:
                continue
            if not isinstance(keys, tuple):
                keys = (keys,)
            k, n = int(g.visit.sum()), len(g)
            smooth = (k + 30 * global_rate) / (n + 30)
            lo, hi = wilson(k, n)
            row = {
                "interaction": label, "n": n, "visit_rate": k/n,
                "smoothed_rate": smooth, "lift_vs_global": smooth/global_rate,
                "wilson_low": lo, "wilson_high": hi,
                "wilson_low_lift": lo/global_rate
            }
            row.update(dict(zip(cols, keys)))
            rows.append(row)
    return pd.DataFrame(rows).sort_values(
        ["lift_vs_global", "n"], ascending=[False, False]
    ).reset_index(drop=True)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    leads, spots, attrs, iq, av = load()
    summary = json.loads((PARENT_PROF / "summary.json").read_text())
    profile_cutoff = pd.Timestamp(summary["profile_cutoff"])
    test_cutoff = pd.Timestamp(summary["test_cutoff"])

    # Reuse only parent representations whose construction is already governed.
    la = pd.read_csv(PARENT_PROF / "lead_assignments.csv")
    old_b = pd.read_csv(PARENT_PROF / "broker_assignments.csv")
    spot_profiles = pd.read_csv(PARENT_AB / "spot_decomposed_assignments.csv")

    # 1) Persona decomposition: acquisition source direct + behavioral maturity cluster.
    persona_assign, b1, i1 = build_behavioral_persona(leads, profile_cutoff)

    # 2) Dynamic T1 need, intentionally excluding weekday.
    dyn_assign, b2, i2 = build_dynamic_need(iq, leads, profile_cutoff)

    # 3) First clean Broker attempt; retained as E010 evidence even if clustering collapses.
    supply, service = build_broker_features(spots, iq, profile_cutoff)
    broker_supply, b3, i3 = cluster_numeric_profiles(supply, "BS", "broker_supply")
    broker_service, b4, i4 = cluster_numeric_profiles(service, "BV", "broker_service")

    # 4) Balanced Broker challenger: compress specialization, winsorize scale and enforce balance.
    supply_c, supply_cat, supply_num, service_c, service_cat, service_num = build_compact_broker_views(supply, service)
    broker_supply_bal, b5, i5, supply_gate = cluster_compact_broker(
        supply_c, supply_cat, supply_num, "BSP", "broker_supply_balanced"
    )
    broker_service_bal, b6, i6, service_gate = cluster_compact_broker(
        service_c, service_cat, service_num, "BSV", "broker_service_balanced"
    )
    (OUT / "broker_supply_balance_gate.json").write_text(jdump(supply_gate), encoding="utf-8")
    (OUT / "broker_service_balance_gate.json").write_text(jdump(service_gate), encoding="utf-8")

    all_bench = pd.concat([b1, b2, b3, b4, b5, b6], ignore_index=True)
    all_bench.to_csv(OUT / "clustering_benchmark.csv", index=False)
    all_bench.query("selected").to_csv(OUT / "selected_clusterers.csv", index=False)
    interp = pd.concat([i1, i2, i3, i4, i5, i6], ignore_index=True)
    interp.to_csv(OUT / "profile_interpretability.csv", index=False)
    persona_assign.to_csv(OUT / "behavioral_persona_assignments.csv", index=False)
    dyn_assign.to_csv(OUT / "dynamic_need_assignments.csv", index=False)
    broker_supply.to_csv(OUT / "broker_supply_assignments.csv", index=False)
    broker_service.to_csv(OUT / "broker_service_assignments.csv", index=False)
    broker_supply_bal.to_csv(OUT / "broker_supply_balanced_assignments.csv", index=False)
    broker_service_bal.to_csv(OUT / "broker_service_balanced_assignments.csv", index=False)

    # Assemble one analysis table and assert one-row-per-inquiry preservation.
    x = iq.merge(la[["lead_id", "persona_profile", "need_profile"]], on="lead_id", how="left", validate="many_to_one")
    x = x.merge(persona_assign, on="lead_id", how="left", validate="many_to_one")
    x = x.merge(leads[["lead_id", "user_type", "search_sector", "search_modality"]], on="lead_id", how="left", validate="many_to_one")
    x = x.merge(spot_profiles, on="spot_id", how="left", validate="many_to_one")
    x = x.merge(old_b, on="broker_id", how="left", validate="many_to_one")
    x = x.merge(broker_supply, on="broker_id", how="left", validate="many_to_one")
    x = x.merge(broker_service, on="broker_id", how="left", validate="many_to_one")
    x = x.merge(broker_supply_bal, on="broker_id", how="left", validate="many_to_one")
    x = x.merge(broker_service_bal, on="broker_id", how="left", validate="many_to_one")
    x = x.merge(dyn_assign, on="inquiry_id", how="left", validate="one_to_one")
    x = x.merge(availability_features(iq, av), on="inquiry_id", how="left", validate="one_to_one")
    assert len(x) == len(iq)
    x["visit"] = x.broker_response.eq("scheduled_visit").astype(int)
    x["need_transition"] = x.need_profile.astype(str) + "->" + x.dynamic_need_profile.astype(str)

    required = [
        "persona_profile", "need_profile", "behavioral_profile", "source",
        "dynamic_need_profile", "physical_profile", "location_profile",
        "broker_profile", "broker_supply_profile", "broker_service_profile",
        "broker_supply_balanced_profile", "broker_service_balanced_profile"
    ]
    missing = x[required].isna().mean().rename("missing_rate").reset_index().rename(columns={"index": "feature"})
    missing.to_csv(OUT / "assignment_completeness.csv", index=False)
    if (missing.missing_rate > 0).any():
        raise RuntimeError("Profile assignment completeness failed:\n" + missing.to_string(index=False))

    train = x[(x.inquiry_at >= profile_cutoff) & (x.inquiry_at < test_cutoff)].copy()
    test = x[x.inquiry_at >= test_cutoff].copy()
    assert len(test) == 4516

    common = ["need_profile", "physical_profile", "location_profile", "broker_profile", "availability_state", "availability_lag_bucket"]
    cols = {
        "E006_parent_marginals": ["persona_profile"] + common,
        "E008_behavioral_persona": ["source", "behavioral_profile"] + common,
        "E009_dynamic_need_t1": [
            "source", "behavioral_profile", "need_profile", "dynamic_need_profile",
            "need_transition", "physical_profile", "location_profile", "broker_profile",
            "availability_state", "availability_lag_bucket"
        ],
        "E010_clean_broker_profiles": [
            "source", "behavioral_profile", "need_profile", "dynamic_need_profile",
            "need_transition", "physical_profile", "location_profile",
            "broker_supply_profile", "broker_service_profile",
            "availability_state", "availability_lag_bucket"
        ],
    }
    pred = {}
    for name, c in cols.items():
        pred[name] = fit_score(train, test, c)

    train_h, interaction_cols = add_interactions(train)
    test_h, _ = add_interactions(test)
    cols["E011_hierarchical_matching"] = cols["E010_clean_broker_profiles"] + interaction_cols
    pred["E011_hierarchical_matching"] = fit_score(
        train_h, test_h, cols["E011_hierarchical_matching"]
    )

    # Second branch: do not carry the E008 Persona regression into the strongest candidates.
    cols["E012_dynamic_need_strong_baseline"] = [
        "persona_profile", "need_profile", "dynamic_need_profile", "need_transition",
        "physical_profile", "location_profile", "broker_profile",
        "availability_state", "availability_lag_bucket"
    ]
    pred["E012_dynamic_need_strong_baseline"] = fit_score(
        train, test, cols["E012_dynamic_need_strong_baseline"]
    )

    # E013/E014 are only scientifically eligible if BOTH Broker families pass the pre-registered balance gate.
    broker_pair_valid = bool(supply_gate["passed"] and service_gate["passed"])
    cols["E013_balanced_broker_profiles"] = [
        "persona_profile", "need_profile", "dynamic_need_profile", "need_transition",
        "physical_profile", "location_profile",
        "broker_supply_balanced_profile", "broker_service_balanced_profile",
        "availability_state", "availability_lag_bucket"
    ]
    if broker_pair_valid:
        pred["E013_balanced_broker_profiles"] = fit_score(train, test, cols["E013_balanced_broker_profiles"])
        train_h2, interaction_cols_v2 = add_interactions_v2(train)
        test_h2, _ = add_interactions_v2(test)
        cols["E014_hierarchical_matching_v2"] = cols["E013_balanced_broker_profiles"] + interaction_cols_v2
        pred["E014_hierarchical_matching_v2"] = fit_score(train_h2, test_h2, cols["E014_hierarchical_matching_v2"])
    else:
        # Preserve metrics equal to parent only so harness can record the failed representation gate.
        pred["E013_balanced_broker_profiles"] = pred["E012_dynamic_need_strong_baseline"].copy()
        pred["E014_hierarchical_matching_v2"] = pred["E012_dynamic_need_strong_baseline"].copy()
        train_h2, interaction_cols_v2 = add_interactions_v2(train)
        test_h2, _ = add_interactions_v2(test)

    # E015: service-only branch remains eligible even when Supply is not clusterable.
    if not service_gate["passed"]:
        raise RuntimeError(
            f"broker_service_balanced failed balance gate: min={service_gate['min_cluster_share']:.3f}, "
            f"max={service_gate['max_cluster_share']:.3f}"
        )
    cols["E015_broker_service_profile"] = [
        "persona_profile", "need_profile", "dynamic_need_profile", "need_transition",
        "physical_profile", "location_profile", "broker_profile",
        "broker_service_balanced_profile", "availability_state", "availability_lag_bucket"
    ]
    pred["E015_broker_service_profile"] = fit_score(train, test, cols["E015_broker_service_profile"])

    train_s, service_interaction_cols = add_service_interactions(train)
    test_s, _ = add_service_interactions(test)
    cols["E016_dynamic_service_hierarchy"] = cols["E015_broker_service_profile"] + service_interaction_cols
    pred["E016_dynamic_service_hierarchy"] = fit_score(
        train_s, test_s, cols["E016_dynamic_service_hierarchy"]
    )

    # Reproduce the old E007 treatment as a same-test external benchmark.
    def old_interactions(df):
        z = df.copy()
        z["persona_x_need"] = z.persona_profile.astype(str) + "x" + z.need_profile.astype(str)
        z["need_x_physical"] = z.need_profile.astype(str) + "x" + z.physical_profile.astype(str)
        z["need_x_location"] = z.need_profile.astype(str) + "x" + z.location_profile.astype(str)
        z["need_x_broker"] = z.need_profile.astype(str) + "x" + z.broker_profile.astype(str)
        z["physical_x_broker"] = z.physical_profile.astype(str) + "x" + z.broker_profile.astype(str)
        z["need_x_physical_x_broker"] = (
            z.need_profile.astype(str) + "x" + z.physical_profile.astype(str) + "x" + z.broker_profile.astype(str)
        )
        return z
    old_train, old_test = old_interactions(train), old_interactions(test)
    old_cols = cols["E006_parent_marginals"] + [
        "persona_x_need", "need_x_physical", "need_x_location",
        "need_x_broker", "physical_x_broker", "need_x_physical_x_broker"
    ]
    pred["E007_old_compatibility"] = fit_score(old_train, old_test, old_cols)

    metric_rows = []
    for name, p in pred.items():
        lm, nlead, lrate = lead_metrics(test, p)
        metric_rows.append({
            "model": name, **metrics(test.visit, p),
            "lead_level_ap": lm["average_precision"], "lead_level_auc": lm["roc_auc"],
            "lead_level_lift_top_10pct": lm["lift_top_10pct"],
            "lead_level_n": nlead, "lead_level_visit_rate": lrate
        })
    metric_df = pd.DataFrame(metric_rows)
    metric_df.to_csv(OUT / "model_metrics.csv", index=False)

    comparisons = [
        ("E008_vs_E006", "E006_parent_marginals", "E008_behavioral_persona"),
        ("E009_vs_E008", "E008_behavioral_persona", "E009_dynamic_need_t1"),
        ("E010_vs_E009", "E009_dynamic_need_t1", "E010_clean_broker_profiles"),
        ("E011_vs_E010", "E010_clean_broker_profiles", "E011_hierarchical_matching"),
        ("E011_vs_E007_old", "E007_old_compatibility", "E011_hierarchical_matching"),
        ("E011_vs_E006_parent", "E006_parent_marginals", "E011_hierarchical_matching"),
        ("E012_vs_E006", "E006_parent_marginals", "E012_dynamic_need_strong_baseline"),
        ("E012_vs_E007_old", "E007_old_compatibility", "E012_dynamic_need_strong_baseline"),
        ("E013_vs_E012", "E012_dynamic_need_strong_baseline", "E013_balanced_broker_profiles"),
        ("E014_vs_E013", "E013_balanced_broker_profiles", "E014_hierarchical_matching_v2"),
        ("E014_vs_E007_old", "E007_old_compatibility", "E014_hierarchical_matching_v2"),
        ("E014_vs_E006_parent", "E006_parent_marginals", "E014_hierarchical_matching_v2"),
        ("E015_vs_E012", "E012_dynamic_need_strong_baseline", "E015_broker_service_profile"),
        ("E016_vs_E015", "E015_broker_service_profile", "E016_dynamic_service_hierarchy"),
        ("E016_vs_E007_old", "E007_old_compatibility", "E016_dynamic_service_hierarchy"),
        ("E016_vs_E006_parent", "E006_parent_marginals", "E016_dynamic_service_hierarchy"),
    ]
    boot_rows = []
    for label, a, b in comparisons:
        d = bootstrap_delta(test, pred[a], pred[b])
        boot_rows.append({"comparison": label, "control": a, "treatment": b, **d})
    boot = pd.DataFrame(boot_rows)
    boot.to_csv(OUT / "bootstrap_deltas.csv", index=False)

    global_rate = float(test.visit.mean())
    cells = compatibility_cells(test_h, global_rate)
    prior_best = 1.366344422133438
    cells["beats_prior_best_1_366x"] = cells.lift_vs_global > prior_best
    cells.to_csv(OUT / "top_compatibility_cells.csv", index=False)

    if broker_pair_valid:
        cells_v2 = compatibility_cells_v2(test_h2, global_rate)
    else:
        cells_v2 = pd.DataFrame(columns=["interaction","n","visit_rate","smoothed_rate","lift_vs_global"])
    cells_v2["beats_old_EV010_1_366x"] = cells_v2.get("lift_vs_global", pd.Series(dtype=float)) > 1.366344422133438
    cells_v2["beats_v4_first_pass_1_42685x"] = cells_v2.get("lift_vs_global", pd.Series(dtype=float)) > 1.42685
    cells_v2.to_csv(OUT / "top_compatibility_cells_v2.csv", index=False)

    service_cells = service_compatibility_cells(test_s, global_rate)
    service_cells["beats_old_EV010_1_366x"] = service_cells.lift_vs_global > 1.366344422133438
    service_cells["beats_v4_first_pass_1_42685x"] = service_cells.lift_vs_global > 1.42685
    service_cells.to_csv(OUT / "top_service_compatibility_cells.csv", index=False)

    # Profile transitions are useful product diagnostics independent of the model.
    trans = pd.crosstab(
        x.loc[x.inquiry_at >= test_cutoff, "need_profile"],
        x.loc[x.inquiry_at >= test_cutoff, "dynamic_need_profile"],
        normalize="index"
    )
    trans.to_csv(OUT / "need_t0_t1_transition_matrix.csv")

    # Status per governed experiment comes only from its parent comparison.
    parent_cmp = {
        "E008_behavioral_persona": "E008_vs_E006",
        "E009_dynamic_need_t1": "E009_vs_E008",
        "E010_clean_broker_profiles": "E010_vs_E009",
        "E011_hierarchical_matching": "E011_vs_E010",
        "E012_dynamic_need_strong_baseline": "E012_vs_E006",
        "E013_balanced_broker_profiles": "E013_vs_E012",
        "E014_hierarchical_matching_v2": "E014_vs_E013",
        "E015_broker_service_profile": "E015_vs_E012",
        "E016_dynamic_service_hierarchy": "E016_vs_E015",
    }
    next_map = {
        "E008_behavioral_persona": "E009_dynamic_need_t1",
        "E009_dynamic_need_t1": "E010_clean_broker_profiles",
        "E010_clean_broker_profiles": "E011_hierarchical_matching",
        "E011_hierarchical_matching": "E012_dynamic_need_strong_baseline",
        "E012_dynamic_need_strong_baseline": "E013_balanced_broker_profiles",
        "E013_balanced_broker_profiles": "E014_hierarchical_matching_v2",
        "E014_hierarchical_matching_v2": "E015_broker_service_profile because Broker Supply failed the balance gate",
        "E015_broker_service_profile": "E016_dynamic_service_hierarchy",
        "E016_dynamic_service_hierarchy": "Online randomized routing A/B if operationally available",
    }
    for eid, cmp_name in parent_cmp.items():
        row = boot.set_index("comparison").loc[cmp_name].to_dict()
        m = metric_df.set_index("model").loc[eid].to_dict()
        failed_broker_gate = eid in {"E013_balanced_broker_profiles","E014_hierarchical_matching_v2"} and not broker_pair_valid
        result = {
            "experiment_id": eid,
            "metrics": {k: float(v) for k, v in m.items() if isinstance(v, (int, float, np.number))},
            "conclusion": "NOT_SUPPORTED" if failed_broker_gate else conclusion(row),
            "comparison_to_parent": row,
            "caveats": [
                "Offline temporal backtest; not causal.",
                "scheduled_visit is a proxy for commercial progress, not hidden sale/conversion.",
                "Clusters are selected outcome-free; compatibility cells are exploratory and multiple comparisons are not family-wise adjusted."
            ] + ([
                f"Representation gate failed before model eligibility: Broker Supply min share={supply_gate['min_cluster_share']:.3f}, max share={supply_gate['max_cluster_share']:.3f}.",
                "Treatment predictions are intentionally copied from the valid parent only to satisfy the immutable harness record; no performance claim is made."
            ] if failed_broker_gate else []),
            "next_experiment": next_map[eid]
        }
        (OUT / f"{eid}_results.json").write_text(jdump(result), encoding="utf-8")

    selected = pd.concat([b1, b2, b3, b4, b5, b6], ignore_index=True).query("selected")
    best_cells = cells.head(15)
    best_cells_v2 = cells_v2.head(15)
    e011_vs_old = boot.set_index("comparison").loc["E011_vs_E007_old"]
    e011_vs_parent = boot.set_index("comparison").loc["E011_vs_E006_parent"]
    e012_vs_parent = boot.set_index("comparison").loc["E012_vs_E006"]
    e014_vs_old = boot.set_index("comparison").loc["E014_vs_E007_old"]
    e014_vs_parent = boot.set_index("comparison").loc["E014_vs_E006_parent"]
    e015_vs_parent = boot.set_index("comparison").loc["E015_vs_E012"]
    e016_vs_old = boot.set_index("comparison").loc["E016_vs_E007_old"]
    e016_vs_parent = boot.set_index("comparison").loc["E016_vs_E006_parent"]
    best_service_cells = service_cells.head(15)

    report = f"""# Matching profiles v4 — semantic profiles + dynamic need + clean broker + hierarchical matching

## Executive result

This suite keeps the same profile cutoff ({profile_cutoff}), predictive train window and untouched future test ({len(test):,} inquiries) as Matching A/B v3.

The ladder is intentionally incremental:

1. E008: replace lossy Persona with Acquisition Channel + Behavioral Maturity.
2. E009: add a semantic T1 Dynamic Need and the T0→T1 transition.
3. E010: replace legacy Broker with Supply + Historical Service profiles that never use broker_response_hours.
4. E011: add pre-specified hierarchical compatibility interactions.
5. E012: branch back to the strong E006 baseline and add Dynamic Need without carrying E008.
6. E013: replace legacy Broker with strictly balanced compact Supply + Service profiles.
7. E014: retry hierarchical matching only if both Broker profiles pass the balance gate.
8. E015: when Supply is not clusterable, add only the valid balanced Broker Service profile to E012.
9. E016: add Dynamic Need × Physical/Location × Broker Service interactions on that valid branch.

### Model metrics

{metric_df.to_markdown(index=False)}

### Paired lead-cluster bootstrap

{boot.to_markdown(index=False)}

**E011 vs old E007:** ΔAP {e011_vs_old.delta_ap:+.4f} (95% CI {e011_vs_old.delta_ap_low:+.4f}, {e011_vs_old.delta_ap_high:+.4f}); ΔLift@10 {e011_vs_old.delta_lift10:+.3f}.

**E011 vs E006 marginal parent:** ΔAP {e011_vs_parent.delta_ap:+.4f} (95% CI {e011_vs_parent.delta_ap_low:+.4f}, {e011_vs_parent.delta_ap_high:+.4f}).

**E012 Dynamic Need on strong baseline vs E006:** ΔAP {e012_vs_parent.delta_ap:+.4f} (95% CI {e012_vs_parent.delta_ap_low:+.4f}, {e012_vs_parent.delta_ap_high:+.4f}); ΔLift@10 {e012_vs_parent.delta_lift10:+.3f}.

**E014 v2 vs old E007:** ΔAP {e014_vs_old.delta_ap:+.4f} (95% CI {e014_vs_old.delta_ap_low:+.4f}, {e014_vs_old.delta_ap_high:+.4f}); ΔLift@10 {e014_vs_old.delta_lift10:+.3f}.

**E014 v2 vs E006:** ΔAP {e014_vs_parent.delta_ap:+.4f} (95% CI {e014_vs_parent.delta_ap_low:+.4f}, {e014_vs_parent.delta_ap_high:+.4f}). If Broker Supply failed the gate, E014 is NOT_SUPPORTED and these copied-parent metrics are not a treatment result.

**E015 Broker Service vs E012:** ΔAP {e015_vs_parent.delta_ap:+.4f} (95% CI {e015_vs_parent.delta_ap_low:+.4f}, {e015_vs_parent.delta_ap_high:+.4f}).

**E016 Service hierarchy vs old E007:** ΔAP {e016_vs_old.delta_ap:+.4f} (95% CI {e016_vs_old.delta_ap_low:+.4f}, {e016_vs_old.delta_ap_high:+.4f}); ΔLift@10 {e016_vs_old.delta_lift10:+.3f}.

**E016 Service hierarchy vs E006:** ΔAP {e016_vs_parent.delta_ap:+.4f} (95% CI {e016_vs_parent.delta_ap_low:+.4f}, {e016_vs_parent.delta_ap_high:+.4f}).

## Selected outcome-free clusterers

{selected.to_markdown(index=False)}

## Profile interpretability

{interp.to_markdown(index=False)}

## Top new future-test compatibility cells

Prior best from Matching A/B v3 was ~1.366x smoothed lift. The table below is exploratory and is not used to select the model.

{best_cells.to_markdown(index=False)}

## Top compatibility cells — balanced Broker / strong-baseline branch

{best_cells_v2.to_markdown(index=False) if len(best_cells_v2) else "_Not eligible: Broker Supply failed the strict balance gate._"}

## Top compatibility cells — Dynamic Need + balanced Broker Service

{best_service_cells.to_markdown(index=False)}

## Guardrails

- No weekday enters Dynamic Need.
- No broker_response_hours enters either Broker profile.
- Broker outcome history is frozen strictly before profile_cutoff.
- Availability remains backward-as-of.
- The future test is untouched by clustering selection.
- The same logistic model family/hyperparameters are used throughout the profile ladder.
- Local compatibility cells are hypothesis discovery, not causal routing rules.
"""
    (HERE / "README.md").write_text(report, encoding="utf-8")
    print(report)

if __name__ == "__main__":
    main()
