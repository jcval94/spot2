
from __future__ import annotations

import json
import math
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, BisectingKMeans, Birch
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    adjusted_rand_score,
    average_precision_score,
    brier_score_loss,
    calinski_harabasz_score,
    davies_bouldin_score,
    log_loss,
    roc_auc_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler

SEED = 42
PROFILE_FRAC = 0.30
TEST_FRAC = 0.20
MIN_CLUSTER_SHARE = 0.05
MAX_CLUSTER_SHARE = 0.70
MIN_SUPPORT = 30
PRIOR = 40.0
BOOT = 300
K_VALUES = range(3, 8)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "candidate" / "csv"
HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
SPECS = HERE / "specs"

CORE_METRICS = [
    "roc_auc",
    "average_precision",
    "brier",
    "log_loss",
    "lift_top_10pct",
    "recall_top_20pct",
]


def safe_mode(s: pd.Series) -> str:
    x = s.dropna().astype(str)
    return "unknown" if x.empty else x.value_counts().index[0]


def md_table(df: pd.DataFrame, cols, n=20) -> str:
    x = df[list(cols)].head(n).copy()
    if x.empty:
        return "_Sin filas con soporte suficiente._"
    lines = [
        "| " + " | ".join(x.columns) + " |",
        "|" + "|".join(["---"] * len(x.columns)) + "|",
    ]
    for row in x.itertuples(index=False, name=None):
        vals = []
        for v in row:
            if isinstance(v, (float, np.floating)):
                vals.append("n/a" if pd.isna(v) else f"{float(v):.3f}")
            else:
                vals.append(str(v).replace("|", "/"))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def metric_bundle(y, p):
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-8, 1 - 1e-8)
    if len(np.unique(y)) < 2:
        raise ValueError("Target requires both classes.")
    if np.allclose(p, p[0]):
        lift10 = 1.0
        recall20 = 0.20
    else:
        order = np.argsort(-p, kind="stable")
        n10 = max(1, int(math.ceil(len(y) * 0.10)))
        n20 = max(1, int(math.ceil(len(y) * 0.20)))
        lift10 = y[order[:n10]].mean() / y.mean()
        recall20 = y[order[:n20]].sum() / max(1, y.sum())
    return {
        "roc_auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "lift_top_10pct": float(lift10),
        "recall_top_20pct": float(recall20),
    }


def wilson(k, n, z=1.96):
    if not n:
        return np.nan, np.nan
    p = k / n
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return max(0.0, ctr - margin), min(1.0, ctr + margin)


def temporal_cutoffs(iq):
    t = iq["inquiry_at"].sort_values().reset_index(drop=True)
    profile_cut = t.iloc[int(len(t) * PROFILE_FRAC)]
    test_cut = t.iloc[int(len(t) * (1 - TEST_FRAC))]
    return profile_cut, test_cut


def common_embedding(ref, all_df, cat, num):
    cat_pipe = Pipeline([
        ("imp", SimpleImputer(strategy="most_frequent")),
        ("oh", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=0.01)),
    ])
    num_pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("scale", RobustScaler()),
    ])
    prep = ColumnTransformer(
        [("cat", cat_pipe, cat), ("num", num_pipe, num)],
        sparse_threshold=0.3,
    )
    cols = cat + num
    xr = prep.fit_transform(ref[cols])
    xa = prep.transform(all_df[cols])
    max_components = min(24, xr.shape[0] - 1, xr.shape[1] - 1)
    if max_components >= 2:
        svd = TruncatedSVD(n_components=max_components, random_state=SEED)
        zr = svd.fit_transform(xr)
        za = svd.transform(xa)
    else:
        zr = xr.toarray() if hasattr(xr, "toarray") else np.asarray(xr)
        za = xa.toarray() if hasattr(xa, "toarray") else np.asarray(xa)
    scaler = StandardScaler()
    zr = scaler.fit_transform(zr)
    za = scaler.transform(za)
    return zr, za


def fit_cluster(method, k, z, seed):
    if method == "kmeans":
        model = KMeans(n_clusters=k, n_init=30, random_state=seed)
        labels = model.fit_predict(z)
    elif method == "bisecting":
        model = BisectingKMeans(n_clusters=k, n_init=10, random_state=seed)
        labels = model.fit_predict(z)
    elif method == "birch":
        model = Birch(n_clusters=k, threshold=0.6)
        labels = model.fit_predict(z)
    elif method == "gmm":
        model = GaussianMixture(
            n_components=k,
            covariance_type="diag",
            reg_covar=1e-5,
            n_init=3,
            random_state=seed,
        )
        model.fit(z)
        labels = model.predict(z)
    else:
        raise ValueError(method)
    return model, labels


def cluster_predict(model, method, z):
    if method in {"kmeans", "bisecting", "birch", "gmm"}:
        return model.predict(z)
    raise ValueError(method)


def cluster_quality(z, labels, k):
    counts = np.bincount(labels, minlength=k)
    shares = counts / counts.sum()
    min_share = float(shares.min())
    max_share = float(shares.max())
    entropy = float(-(shares * np.log(shares + 1e-12)).sum() / np.log(k))
    sample = min(1000, len(z))
    sil = float(silhouette_score(z, labels, sample_size=sample, random_state=SEED))
    db = float(davies_bouldin_score(z, labels))
    ch = float(calinski_harabasz_score(z, labels))
    return min_share, max_share, entropy, sil, db, ch


def benchmark_profiles(name, ref, all_df, cat, num, prefix):
    zr, za = common_embedding(ref, all_df, cat, num)
    rows, fitted = [], {}
    methods = ["kmeans", "bisecting", "birch", "gmm"]

    for method in methods:
        for k in K_VALUES:
            model, labels = fit_cluster(method, k, zr, SEED)
            min_share, max_share, entropy, sil, db, ch = cluster_quality(zr, labels, k)
            if method == "birch":
                stability = 1.0
            else:
                _, labels2 = fit_cluster(method, k, zr, SEED + 19)
                stability = float(adjusted_rand_score(labels, labels2))
            balance_ok = min_share >= MIN_CLUSTER_SHARE and max_share <= MAX_CLUSTER_SHARE
            penalty = 0.90 * max(0.0, max_share - 0.65) + 0.60 * max(0.0, 0.05 - min_share)
            selection_score = sil + 0.22 * entropy + 0.12 * stability - penalty
            rows.append({
                "profile_family": name,
                "method": method,
                "k": k,
                "silhouette": sil,
                "davies_bouldin": db,
                "calinski_harabasz": ch,
                "min_cluster_share": min_share,
                "max_cluster_share": max_share,
                "normalized_entropy": entropy,
                "stability_ari": stability,
                "balance_ok": balance_ok,
                "selection_score": selection_score,
            })
            fitted[(method, k)] = (model, labels)

    bench = pd.DataFrame(rows)
    eligible = bench[bench["balance_ok"]]
    pool = eligible if not eligible.empty else bench
    best = pool.sort_values(
        ["selection_score", "silhouette", "normalized_entropy", "stability_ari"],
        ascending=False,
    ).iloc[0]
    method, k = str(best["method"]), int(best["k"])
    model, ref_labels = fitted[(method, k)]
    all_labels = cluster_predict(model, method, za)

    order = pd.Series(ref_labels).value_counts().index.tolist()
    remap = {raw: i + 1 for i, raw in enumerate(order)}
    ref_ids = pd.Series([f"{prefix}{remap[x]}" for x in ref_labels], index=ref.index)
    all_ids = pd.Series(
        [f"{prefix}{remap.get(x, len(remap) + 1)}" for x in all_labels],
        index=all_df.index,
    )
    bench["selected"] = (bench["method"].eq(method) & bench["k"].eq(k))
    return ref_ids, all_ids, bench


def robust_numeric_signal(cluster, full, col):
    a = pd.to_numeric(cluster[col], errors="coerce").dropna()
    b = pd.to_numeric(full[col], errors="coerce").dropna()
    if a.empty or b.empty:
        return None
    cm, gm = a.median(), b.median()
    q25, q75 = b.quantile([0.25, 0.75])
    iqr = float(q75 - q25)
    if not np.isfinite(iqr) or iqr <= 1e-12:
        return None
    effect = float((cm - gm) / iqr)
    if abs(effect) < 0.18:
        return None
    direction = "alto" if effect > 0 else "bajo"
    return abs(effect), f"{col} {direction} ({cm:.2f}; {effect:+.2f} IQR)"


def categorical_signal(cluster, full, col):
    cv = cluster[col].fillna("<missing>").astype(str)
    fv = full[col].fillna("<missing>").astype(str)
    cp = cv.value_counts(normalize=True)
    gp = fv.value_counts(normalize=True)
    best = None
    for val, share in cp.items():
        delta = float(share - gp.get(val, 0.0))
        if share < 0.15 or delta < 0.08:
            continue
        cand = (delta, f"{col}={val} ({share:.0%}; {delta:+.0%}pp)")
        if best is None or cand[0] > best[0]:
            best = cand
    return best


def interpret_profiles(ref, profile_col, cat, num):
    rows = []
    for pid, g in ref.groupby(profile_col):
        cats = [x for x in (categorical_signal(g, ref, c) for c in cat) if x]
        nums = [x for x in (robust_numeric_signal(g, ref, c) for c in num) if x]
        cats = sorted(cats, reverse=True)[:3]
        nums = sorted(nums, reverse=True)[:3]
        signals = [x[1] for x in cats] + [x[1] for x in nums]
        rows.append({
            "profile_id": pid,
            "n_reference": int(len(g)),
            "share_reference": float(len(g) / len(ref)),
            "top_signals": " | ".join(signals[:5]) if signals else "Sin señal dominante; cluster multivariado.",
        })
    return pd.DataFrame(rows).sort_values("profile_id")


def broker_feature_frame(spots, calibration_iq, profile_cut):
    broker_ids = pd.DataFrame({"broker_id": sorted(spots["broker_id"].dropna().unique())})
    ps = spots[spots["created_at"] <= profile_cut].copy()
    base = ps.groupby("broker_id").agg(
        n_spots=("spot_id", "nunique"),
        median_area=("area_sqm", "median"),
        median_rent=("price_sqm_mxn_rent", "median"),
        median_sale=("price_sqm_mxn_sale", "median"),
    ).reset_index()

    for col, vals in {
        "sector_name": ["Industrial", "Office", "Retail", "Land"],
        "modality": ["rent", "sale", "both"],
        "region": sorted(ps["region"].dropna().unique().tolist()),
    }.items():
        tab = pd.crosstab(ps["broker_id"], ps[col], normalize="index")
        for val in vals:
            cname = f"share_{col}_{str(val).lower().replace(' ', '_')}"
            series = tab[val] if val in tab else pd.Series(0.0, index=tab.index)
            base = base.merge(series.rename(cname).reset_index(), on="broker_id", how="left")

    h = calibration_iq.merge(spots[["spot_id", "broker_id"]], on="spot_id", how="left", validate="many_to_one")
    h["visit"] = h["broker_response"].eq("scheduled_visit").astype(int)
    h["positive"] = h["broker_response"].isin(["accepted", "scheduled_visit"]).astype(int)
    h["responded"] = h["broker_response"].ne("no_response").astype(int)
    h["fast"] = np.where(
        h["broker_response_hours"].notna(),
        (h["broker_response_hours"] <= 6).astype(float),
        np.nan,
    )
    hist = h.groupby("broker_id").agg(
        n_inquiries=("inquiry_id", "size"),
        visit_n=("visit", "sum"),
        positive_n=("positive", "sum"),
        responded_n=("responded", "sum"),
        median_response_hours=("broker_response_hours", "median"),
        fast_rate=("fast", "mean"),
    ).reset_index()

    for succ, out, global_rate in [
        ("visit_n", "visit_rate", h["visit"].mean()),
        ("positive_n", "positive_rate", h["positive"].mean()),
        ("responded_n", "response_rate", h["responded"].mean()),
    ]:
        hist[out] = (hist[succ] + 25 * global_rate) / (hist["n_inquiries"] + 25)

    x = broker_ids.merge(base, on="broker_id", how="left").merge(hist, on="broker_id", how="left")
    x["n_spots"] = x["n_spots"].fillna(0)
    x["n_inquiries"] = x["n_inquiries"].fillna(0)
    x["log_spots"] = np.log1p(x["n_spots"])
    x["log_inquiries"] = np.log1p(x["n_inquiries"])
    share_cols = [c for c in x.columns if c.startswith("share_")]
    x[share_cols] = x[share_cols].fillna(0)

    defaults = {
        "median_area": ps["area_sqm"].median(),
        "median_rent": ps["price_sqm_mxn_rent"].median(),
        "median_sale": ps["price_sqm_mxn_sale"].median(),
        "median_response_hours": h["broker_response_hours"].median(),
        "fast_rate": h["fast"].mean(),
        "visit_rate": h["visit"].mean(),
        "positive_rate": h["positive"].mean(),
        "response_rate": h["responded"].mean(),
    }
    for c, val in defaults.items():
        x[c] = x[c].fillna(val)
    return x, share_cols


def add_inquiry_time_features(df):
    x = df.copy()
    x["inquiry_weekday"] = x["inquiry_at"].dt.day_name()
    x["inquiry_hour"] = x["inquiry_at"].dt.hour.astype(float)
    x["inquiry_hour_band"] = pd.cut(
        x["inquiry_hour"],
        bins=[-1, 8, 12, 17, 21, 24],
        labels=["early", "morning", "afternoon", "evening", "late"],
    ).astype("string")
    return x


def make_interactions(df, features, interaction_pairs, full_name=None):
    x = df[features].astype(str).copy()
    for a, b in interaction_pairs:
        x[f"{a}__x__{b}"] = x[a] + "×" + x[b]
    if full_name:
        x[full_name] = x[features].agg("×".join, axis=1)
    return x


def fit_profile_model(train, test, features, interaction_pairs=(), full_name=None):
    a = make_interactions(train, features, interaction_pairs, full_name)
    b = make_interactions(test, features, interaction_pairs, full_name)
    model = Pipeline([
        ("oh", OneHotEncoder(handle_unknown="ignore", min_frequency=15)),
        ("lr", LogisticRegression(max_iter=3000, C=0.5, random_state=SEED)),
    ])
    model.fit(a, train["visit"])
    return model.predict_proba(b)[:, 1]


def bootstrap_delta(y, p0, p1, n_boot=BOOT):
    rng = np.random.default_rng(SEED)
    y = np.asarray(y, dtype=int)
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    auc, ap, lift = [], [], []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        ys = y[idx]
        if len(np.unique(ys)) < 2:
            continue
        m0, m1 = metric_bundle(ys, p0[idx]), metric_bundle(ys, p1[idx])
        auc.append(m1["roc_auc"] - m0["roc_auc"])
        ap.append(m1["average_precision"] - m0["average_precision"])
        lift.append(m1["lift_top_10pct"] - m0["lift_top_10pct"])
    def pack(vals, name):
        return {
            f"delta_{name}": float(np.mean(vals)),
            f"delta_{name}_low": float(np.quantile(vals, 0.025)),
            f"delta_{name}_high": float(np.quantile(vals, 0.975)),
        }
    return {**pack(auc, "auc"), **pack(ap, "ap"), **pack(lift, "lift10")}


def group_performance(df, groups, pred_col):
    baseline = float(df["visit"].mean())
    rows = []
    for keys, g in df.groupby(groups, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        n = len(g)
        k = int(g["visit"].sum())
        smoothed = (k + PRIOR * baseline) / (n + PRIOR)
        lo, hi = wilson(k, n)
        row = dict(zip(groups, keys))
        row.update({
            "n": n,
            "scheduled_visit_rate": k / n,
            "smoothed_visit_rate": smoothed,
            "positive_response_rate": float(g["positive"].mean()),
            "lift_vs_global": smoothed / baseline,
            "expected_model_probability": float(g[pred_col].mean()),
            "residual_synergy": smoothed - float(g[pred_col].mean()),
            "wilson_low": lo,
            "wilson_high": hi,
        })
        rows.append(row)
    return pd.DataFrame(rows)


def segment_metrics(df, pred_col):
    rows = []
    for segment in ["search_sector", "search_modality", "user_type"]:
        for value, g in df.groupby(segment):
            if len(g) < 100 or g["visit"].nunique() < 2:
                continue
            m = metric_bundle(g["visit"], g[pred_col])
            rows.append({"segment": segment, "value": value, "n": len(g), **m})
    return rows


def conclusion_for(metrics_new, metrics_parent=None, balance_ok=None, require_gain=False):
    if balance_ok is False:
        return "NOT_SUPPORTED"
    if metrics_parent is None:
        return "SUPPORTED" if metrics_new["lift_top_10pct"] >= 1.05 else "INCONCLUSIVE"
    gain = (
        metrics_new["average_precision"] > metrics_parent["average_precision"]
        and metrics_new["lift_top_10pct"] > metrics_parent["lift_top_10pct"]
    )
    if gain:
        return "SUPPORTED"
    if require_gain:
        return "NOT_SUPPORTED"
    return "INCONCLUSIVE"


def write_experiment_result(exp_id, metrics, segment_rows, conclusion, caveats, next_exp):
    payload = {
        "experiment_id": exp_id,
        "metrics": {k: float(metrics[k]) for k in CORE_METRICS},
        "segment_metrics": segment_rows,
        "conclusion": conclusion,
        "caveats": caveats,
        "next_experiment": next_exp,
    }
    path = OUT / f"{exp_id}_results.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    leads = pd.read_csv(DATA / "leads.csv", parse_dates=["created_at"])
    spots = pd.read_csv(DATA / "spots.csv", parse_dates=["created_at"])
    attrs = pd.read_csv(DATA / "spot_attributes.csv")
    iq = pd.read_csv(DATA / "inquiries.csv", parse_dates=["inquiry_at"])
    assert leads["lead_id"].is_unique
    assert spots["spot_id"].is_unique
    assert attrs["spot_id"].is_unique
    assert iq["inquiry_id"].is_unique

    quality = {
        "n_leads": int(len(leads)),
        "n_spots": int(len(spots)),
        "n_brokers": int(spots["broker_id"].nunique()),
        "n_inquiries": int(len(iq)),
        "inquiry_to_lead": float(iq["lead_id"].isin(leads["lead_id"]).mean()),
        "inquiry_to_spot": float(iq["spot_id"].isin(spots["spot_id"]).mean()),
        "spot_to_attributes": float(spots["spot_id"].isin(attrs["spot_id"]).mean()),
    }
    assert min(quality["inquiry_to_lead"], quality["inquiry_to_spot"], quality["spot_to_attributes"]) >= 0.995

    profile_cut, test_cut = temporal_cutoffs(iq)
    calibration_iq = iq[iq["inquiry_at"] < profile_cut].copy()
    model_train_iq = iq[(iq["inquiry_at"] >= profile_cut) & (iq["inquiry_at"] < test_cut)].copy()
    test_iq = iq[iq["inquiry_at"] >= test_cut].copy()

    sx = spots.merge(attrs, on="spot_id", how="left", validate="one_to_one")
    sx["amenities_count"] = sx["amenities"].fillna("[]").astype(str).str.count(",") + (~sx["amenities"].fillna("[]").astype(str).eq("[]")).astype(int)

    benchmarks = []
    interpretations = []

    lead_cat = [
        "user_type", "company_size", "industry", "search_sector", "search_modality",
        "preferred_state", "preferred_municipality", "preferred_corridor", "source",
        "has_converted_before",
    ]
    lead_num = [
        "target_area_sqm", "min_budget_mxn_rent_monthly", "max_budget_mxn_rent_monthly",
        "min_budget_mxn_sale_total", "max_budget_mxn_sale_total", "prior_searches", "prior_inquiries",
    ]
    lead_ref = leads[leads["created_at"] <= profile_cut].copy()
    r, a, bench = benchmark_profiles("lead", lead_ref, leads, lead_cat, lead_num, "L")
    lead_ref["lead_profile"] = r
    leads["lead_profile"] = a
    benchmarks.append(bench)
    p = interpret_profiles(lead_ref, "lead_profile", lead_cat, lead_num)
    p["profile_family"] = "lead"
    interpretations.append(p)

    persona_cat = ["user_type", "company_size", "industry", "source", "has_converted_before"]
    persona_num = ["prior_searches", "prior_inquiries"]
    r, a, bench = benchmark_profiles("lead_persona", lead_ref, leads, persona_cat, persona_num, "P")
    lead_ref["persona_profile"] = r
    leads["persona_profile"] = a
    benchmarks.append(bench)
    p = interpret_profiles(lead_ref, "persona_profile", persona_cat, persona_num)
    p["profile_family"] = "lead_persona"
    interpretations.append(p)

    need_cat = ["search_sector", "search_modality", "preferred_state", "preferred_municipality", "preferred_corridor"]
    need_num = [
        "target_area_sqm", "min_budget_mxn_rent_monthly", "max_budget_mxn_rent_monthly",
        "min_budget_mxn_sale_total", "max_budget_mxn_sale_total",
    ]
    r, a, bench = benchmark_profiles("search_need", lead_ref, leads, need_cat, need_num, "N")
    lead_ref["need_profile"] = r
    leads["need_profile"] = a
    benchmarks.append(bench)
    p = interpret_profiles(lead_ref, "need_profile", need_cat, need_num)
    p["profile_family"] = "search_need"
    interpretations.append(p)

    spot_cat = [
        "sector_name", "type_name", "state", "municipality", "corridor", "region", "modality",
        "natural_light", "security_type", "building_status", "floor_material",
    ]
    spot_num = [
        "area_sqm", "price_sqm_mxn_rent", "price_sqm_mxn_sale",
        "price_total_mxn_rent", "price_total_mxn_sale", "maintenance_cost_mxn",
        "luminaires", "charging_ports", "floor_level", "elevators",
        "vertical_height_m", "parking_spaces", "amenities_count",
    ]
    spot_ref = sx[sx["created_at"] <= profile_cut].copy()
    r, a, bench = benchmark_profiles("spot", spot_ref, sx, spot_cat, spot_num, "S")
    spot_ref["spot_profile"] = r
    sx["spot_profile"] = a
    benchmarks.append(bench)
    p = interpret_profiles(spot_ref, "spot_profile", spot_cat, spot_num)
    p["profile_family"] = "spot"
    interpretations.append(p)

    broker_df, broker_share_cols = broker_feature_frame(spots, calibration_iq, profile_cut)
    broker_cat = []
    broker_num = [
        "log_spots", "log_inquiries", "median_area", "median_rent", "median_sale",
        "median_response_hours", "fast_rate", "visit_rate", "positive_rate", "response_rate",
        *broker_share_cols,
    ]
    r, a, bench = benchmark_profiles("broker", broker_df, broker_df, broker_cat, broker_num, "B")
    broker_df["broker_profile"] = a
    benchmarks.append(bench)
    p = interpret_profiles(broker_df, "broker_profile", broker_cat, broker_num)
    p["profile_family"] = "broker"
    interpretations.append(p)

    iq_time = add_inquiry_time_features(iq)
    cal_intent = iq_time[iq_time["inquiry_at"] < profile_cut].copy()
    intent_cat = ["channel", "asked_visit", "inquiry_weekday", "inquiry_hour_band"]
    intent_num = [
        "message_length", "requested_area_sqm", "requested_budget_mxn_rent_monthly",
        "requested_budget_mxn_sale_total", "urgency_days", "inquiry_hour",
    ]
    r, a, bench = benchmark_profiles("inquiry_intent", cal_intent, iq_time, intent_cat, intent_num, "I")
    cal_intent["intent_profile"] = r
    iq_time["intent_profile"] = a
    benchmarks.append(bench)
    p = interpret_profiles(cal_intent, "intent_profile", intent_cat, intent_num)
    p["profile_family"] = "inquiry_intent"
    interpretations.append(p)

    benchmark_df = pd.concat(benchmarks, ignore_index=True)
    interp_df = pd.concat(interpretations, ignore_index=True)
    benchmark_df.to_csv(OUT / "clustering_benchmark.csv", index=False)
    interp_df.to_csv(OUT / "profile_interpretability.csv", index=False)

    selected = benchmark_df[benchmark_df["selected"]].copy()
    selected.to_csv(OUT / "selected_clusterers.csv", index=False)

    x = iq_time.merge(
        leads[["lead_id", "user_type", "search_sector", "search_modality", "lead_profile", "persona_profile", "need_profile"]],
        on="lead_id", how="left", validate="many_to_one",
    )
    x = x.merge(
        sx[["spot_id", "broker_id", "spot_profile"]],
        on="spot_id", how="left", validate="many_to_one",
    )
    x = x.merge(
        broker_df[["broker_id", "broker_profile"]],
        on="broker_id", how="left", validate="many_to_one",
    )
    assert not x[["lead_profile", "persona_profile", "need_profile", "spot_profile", "broker_profile", "intent_profile"]].isna().any().any()

    x["visit"] = x["broker_response"].eq("scheduled_visit").astype(int)
    x["positive"] = x["broker_response"].isin(["accepted", "scheduled_visit"]).astype(int)
    train = x[(x["inquiry_at"] >= profile_cut) & (x["inquiry_at"] < test_cut)].copy()
    test = x[x["inquiry_at"] >= test_cut].copy()

    constant = np.repeat(train["visit"].mean(), len(test))
    p_e001 = fit_profile_model(
        train, test,
        ["lead_profile", "spot_profile", "broker_profile"],
        interaction_pairs=[
            ("lead_profile", "spot_profile"),
            ("lead_profile", "broker_profile"),
            ("spot_profile", "broker_profile"),
        ],
        full_name="triple_profile",
    )
    p_e002 = fit_profile_model(
        train, test,
        ["persona_profile", "need_profile", "spot_profile", "broker_profile"],
        interaction_pairs=[
            ("persona_profile", "need_profile"),
            ("need_profile", "spot_profile"),
            ("persona_profile", "broker_profile"),
            ("spot_profile", "broker_profile"),
        ],
        full_name="facet_profile",
    )
    p_e003 = fit_profile_model(
        train, test,
        ["persona_profile", "need_profile", "spot_profile", "broker_profile", "intent_profile"],
        interaction_pairs=[
            ("persona_profile", "intent_profile"),
            ("need_profile", "intent_profile"),
            ("spot_profile", "intent_profile"),
            ("broker_profile", "intent_profile"),
            ("need_profile", "spot_profile"),
            ("spot_profile", "broker_profile"),
        ],
        full_name=None,
    )

    test["pred_global"] = constant
    test["pred_e001"] = p_e001
    test["pred_e002"] = p_e002
    test["pred_e003"] = p_e003

    metric_rows = []
    for model, col in [
        ("global_baseline", "pred_global"),
        ("E001_balanced_profiles", "pred_e001"),
        ("E002_lead_facets", "pred_e002"),
        ("E003_inquiry_intent", "pred_e003"),
    ]:
        metric_rows.append({"model": model, **metric_bundle(test["visit"], test[col])})
    metrics_df = pd.DataFrame(metric_rows)
    metrics_df.to_csv(OUT / "model_metrics.csv", index=False)

    m0 = metric_rows[0]
    m1 = metric_rows[1]
    m2 = metric_rows[2]
    m3 = metric_rows[3]
    boot12 = bootstrap_delta(test["visit"], p_e001, p_e002)
    boot23 = bootstrap_delta(test["visit"], p_e002, p_e003)
    pd.DataFrame([
        {"comparison": "E002_vs_E001", **boot12},
        {"comparison": "E003_vs_E002", **boot23},
    ]).to_csv(OUT / "bootstrap_deltas.csv", index=False)

    e001_balance = bool(
        selected[selected["profile_family"].isin(["lead", "spot", "broker"])]["balance_ok"].all()
    )
    e002_balance = bool(
        selected[selected["profile_family"].isin(["lead_persona", "search_need", "spot", "broker"])]["balance_ok"].all()
    )
    e003_balance = bool(
        selected[selected["profile_family"].isin(["lead_persona", "search_need", "spot", "broker", "inquiry_intent"])]["balance_ok"].all()
    )

    seg1 = segment_metrics(test, "pred_e001")
    seg2 = segment_metrics(test, "pred_e002")
    seg3 = segment_metrics(test, "pred_e003")

    e001 = write_experiment_result(
        "E001_balanced_profiles",
        m1,
        seg1,
        conclusion_for(m1, None, e001_balance),
        [
            "scheduled_visit is a proxy for commercial progress, not a true sale.",
            "Profile discovery is frozen before predictive training; no future test outcomes are used.",
            "Broker archetypes use only the early calibration window and are frozen afterwards.",
        ],
        "E002_lead_facets separates who the lead is from what the lead needs.",
    )
    e002 = write_experiment_result(
        "E002_lead_facets",
        m2,
        seg2,
        conclusion_for(m2, m1, e002_balance, require_gain=True),
        [
            "Lead Persona and Search Need are latent facets derived from the same lead row, not new physical entities.",
            "The comparison is temporal and directly comparable with E001.",
        ],
        "E003_inquiry_intent adds a T1 intent profile from the inquiry itself.",
    )
    e003 = write_experiment_result(
        "E003_inquiry_intent",
        m3,
        seg3,
        conclusion_for(m3, m2, e003_balance, require_gain=True),
        [
            "Inquiry Intent is an event-state profile available at T1, not a persistent customer entity.",
            "scheduled_visit remains a proxy outcome.",
        ],
        "If supported, validate routing impact with an online or quasi-randomized experiment.",
    )

    combo3 = group_performance(test, ["lead_profile", "spot_profile", "broker_profile"], "pred_e001")
    combo3 = combo3[combo3["n"] >= MIN_SUPPORT].sort_values(
        ["residual_synergy", "lift_vs_global", "n"], ascending=False
    )
    combo3.to_csv(OUT / "top_3entity_combinations.csv", index=False)

    facet_pairs = {}
    for name, groups in {
        "need_spot": ["need_profile", "spot_profile"],
        "persona_broker": ["persona_profile", "broker_profile"],
        "spot_broker": ["spot_profile", "broker_profile"],
        "intent_need": ["intent_profile", "need_profile"],
        "intent_spot": ["intent_profile", "spot_profile"],
        "intent_broker": ["intent_profile", "broker_profile"],
    }.items():
        pred_col = "pred_e003" if name.startswith("intent_") else "pred_e002"
        perf = group_performance(test, groups, pred_col)
        perf = perf[perf["n"] >= MIN_SUPPORT].sort_values(
            ["residual_synergy", "lift_vs_global", "n"], ascending=False
        )
        perf.to_csv(OUT / f"{name}_performance.csv", index=False)
        facet_pairs[name] = perf

    profile_assign = {
        "lead": leads[["lead_id", "lead_profile", "persona_profile", "need_profile"]],
        "spot": sx[["spot_id", "broker_id", "spot_profile"]],
        "broker": broker_df[["broker_id", "broker_profile"]],
        "inquiry": iq_time[["inquiry_id", "intent_profile"]],
    }
    for name, df in profile_assign.items():
        df.to_csv(OUT / f"{name}_assignments.csv", index=False)

    entity_review = pd.DataFrame([
        {
            "candidate": "Lead Persona",
            "status": "PROFILE",
            "why": "Separates actor characteristics from the commercial requirement; stable at T1.",
            "tested": True,
        },
        {
            "candidate": "Search Need",
            "status": "PROFILE",
            "why": "Represents sector/modality/area/budget/geography requested; directly relevant to matching.",
            "tested": True,
        },
        {
            "candidate": "Inquiry Intent",
            "status": "PROFILE_AT_T1",
            "why": "Captures channel, visit intent, urgency and requested parameters; only exists after inquiry.",
            "tested": True,
        },
        {
            "candidate": "Market Context",
            "status": "CONTEXT_NOT_ENTITY",
            "why": "Potentially useful regime, but monthly timestamp does not prove publication availability; excluded from governed predictive test.",
            "tested": False,
        },
        {
            "candidate": "Availability Snapshot",
            "status": "DIRECT_STATE",
            "why": "Use latest non-future availability directly; clustering would hide operational meaning.",
            "tested": False,
        },
        {
            "candidate": "Spot Attributes",
            "status": "MERGED_INTO_SPOT",
            "why": "1:1 extension of Spot, already included in Spot archetype.",
            "tested": True,
        },
        {
            "candidate": "Geography",
            "status": "DIMENSION",
            "why": "Useful for matching/context, but not a standalone behavioral entity.",
            "tested": False,
        },
    ])
    entity_review.to_csv(OUT / "entity_profile_review.csv", index=False)

    legacy = None
    legacy_path = ROOT / "experimentos" / "entity_profile_match" / "results" / "results.json"
    if legacy_path.exists():
        try:
            legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
        except Exception:
            legacy = None

    selected_view = selected[
        ["profile_family", "method", "k", "silhouette", "min_cluster_share", "max_cluster_share",
         "normalized_entropy", "stability_ari", "balance_ok", "selection_score"]
    ].sort_values("profile_family")

    best_model = metrics_df.sort_values(["average_precision", "lift_top_10pct"], ascending=False).iloc[0]
    best_name = best_model["model"]

    readme = f"""# Clustering benchmark v2 — perfiles interpretables y compatibilidad

## Resumen ejecutivo

Se repitió el experimento con una metodología más estricta y con cuatro familias de clustering: **K-Means, Bisecting K-Means, BIRCH y Gaussian Mixture**, evaluadas entre K=3 y K=7.

La selección de clusters **no usa el outcome**. Combina separación, balance y estabilidad. Además, la línea temporal se divide en tres ventanas:

1. **Profile calibration**: primeros {PROFILE_FRAC:.0%} de inquiries; descubre y congela los perfiles.
2. **Predictive train**: tramo intermedio hasta el 80%.
3. **Future test**: 20% final, completamente fuera de muestra.

Esto corrige el look-ahead del experimento anterior en los perfiles históricos del broker.

- Profile cutoff: **{profile_cut.isoformat()}**
- Test cutoff: **{test_cut.isoformat()}**
- Calibration inquiries: **{len(calibration_iq):,}**
- Predictive train inquiries: **{len(train):,}**
- Future test inquiries: **{len(test):,}**
- Future scheduled-visit rate: **{test["visit"].mean():.1%}**

> `scheduled_visit` sigue siendo un proxy de avance comercial. El dataset público no contiene la venta/cierre real.

## 1. ¿Se resolvió el problema del cluster de ~90%?

### Clusterers seleccionados

{md_table(selected_view, selected_view.columns, 20)}

El criterio `balance_ok` exige simultáneamente **cluster mínimo >= {MIN_CLUSTER_SHARE:.0%}** y **cluster máximo <= {MAX_CLUSTER_SHARE:.0%}**. Si una familia no consigue una solución así, se conserva la mejor alternativa pero se marca explícitamente.

### Interpretabilidad de perfiles

{md_table(interp_df, ["profile_family", "profile_id", "n_reference", "share_reference", "top_signals"], 40)}

Los nombres no se asignan con el target. `top_signals` compara cada cluster contra su población de calibración y muestra las características que más lo distinguen.

## 2. ¿Alguna representación aumenta el lift?

{md_table(metrics_df, ["model", *CORE_METRICS], 10)}

- **E001**: Lead + Spot + Broker con clustering multi-método balanceado.
- **E002**: separa Lead en **Lead Persona + Search Need**, manteniendo Spot + Broker.
- **E003**: agrega **Inquiry Intent** en T1.

### Incertidumbre de los cambios

{md_table(pd.DataFrame([{"comparison": "E002_vs_E001", **boot12}, {"comparison": "E003_vs_E002", **boot23}]), ["comparison", "delta_auc", "delta_auc_low", "delta_auc_high", "delta_ap", "delta_ap_low", "delta_ap_high", "delta_lift10", "delta_lift10_low", "delta_lift10_high"], 10)}

**Mejor modelo por Average Precision: {best_name}**.

## 3. Compatibilidad de perfiles

### Lead × Spot × Broker

{md_table(combo3, ["lead_profile", "spot_profile", "broker_profile", "n", "scheduled_visit_rate", "smoothed_visit_rate", "lift_vs_global", "expected_model_probability", "residual_synergy", "wilson_low", "wilson_high"], 12)}

### Search Need × Spot

{md_table(facet_pairs["need_spot"], ["need_profile", "spot_profile", "n", "scheduled_visit_rate", "smoothed_visit_rate", "lift_vs_global", "expected_model_probability", "residual_synergy"], 12)}

### Inquiry Intent × Search Need

{md_table(facet_pairs["intent_need"], ["intent_profile", "need_profile", "n", "scheduled_visit_rate", "smoothed_visit_rate", "lift_vs_global", "expected_model_probability", "residual_synergy"], 12)}

### Inquiry Intent × Broker

{md_table(facet_pairs["intent_broker"], ["intent_profile", "broker_profile", "n", "scheduled_visit_rate", "smoothed_visit_rate", "lift_vs_global", "expected_model_probability", "residual_synergy"], 12)}

`residual_synergy` compara la tasa suavizada observada del grupo contra la probabilidad que ya esperaba el modelo correspondiente. Es una señal exploratoria; no implica causalidad.

## 4. ¿Qué otras entidades/facetas vale la pena perfilar?

{md_table(entity_review, ["candidate", "status", "tested", "why"], 20)}

La recomendación conceptual es:

- **Sí** perfilar `Lead Persona`, `Search Need`, `Spot` y `Broker`.
- **Sí, pero sólo en T1**, perfilar `Inquiry Intent`.
- **No** separar `Spot Attributes`: son una extensión 1:1 de Spot.
- **No** clusterizar `Availability Snapshot`: conviene usar disponibilidad como estado temporal directo.
- **Market Context** puede convertirse en un `Market Regime`, pero no se usa aquí porque la fecha mensual no demuestra cuándo estaba publicado. Incluirlo sin esa semántica rompería el contrato de leakage.

## 5. Leakage y trazabilidad

- Los clusterers se aprenden sólo en la ventana temprana de calibración.
- Los perfiles del broker usan únicamente spots e inquiries anteriores al `profile_cutoff`.
- Esos perfiles se congelan antes del entrenamiento predictivo.
- `lead_score_internal`, `days_on_market`, `total_inquiries`, `total_views` e `is_active` no entran en los perfiles.
- `broker_response` sólo define el target; `broker_response_hours` sólo se usa en la ventana histórica de calibración del broker.
- Inquiry Intent usa únicamente información disponible en `inquiry_at`.
- Los experimentos E001→E002→E003 usan el harness del repo y tienen contratos comparables.

## 6. Calidad de joins

- Leads: **{quality["n_leads"]:,}**
- Spots: **{quality["n_spots"]:,}**
- Brokers observados: **{quality["n_brokers"]:,}**
- Inquiries: **{quality["n_inquiries"]:,}**
- inquiry→lead: **{quality["inquiry_to_lead"]:.1%}**
- inquiry→spot: **{quality["inquiry_to_spot"]:.1%}**
- spot→attributes: **{quality["spot_to_attributes"]:.1%}**

## 7. Archivos

- `results/clustering_benchmark.csv`: todos los métodos/K probados.
- `results/selected_clusterers.csv`: clusterer seleccionado por familia.
- `results/profile_interpretability.csv`: explicación de cada cluster.
- `results/model_metrics.csv`: comparación E001/E002/E003.
- `results/bootstrap_deltas.csv`: incertidumbre de cambios.
- `results/*_performance.csv`: compatibilidades con soporte.
- `results/*_assignments.csv`: asignación de perfiles.
- `results/E00*_results.json`: contratos de resultados para el harness.

## Conclusión

La decisión no debe ser “tener clusters balanceados a cualquier costo”. Un perfil útil necesita **separación + tamaño suficiente + estabilidad + significado de negocio + señal futura**. Esta versión evalúa esas cinco condiciones por separado.

Si E003 mejora fuera de muestra, `Inquiry Intent` merece convertirse en una capa dinámica del journey. Si E002 mejora sin E003, la ganancia viene de separar **quién es el lead** de **qué necesita**. Si ninguna mejora, los perfiles siguen siendo útiles descriptivamente, pero no deben multiplicar el Opportunity Score.
"""
    (HERE / "README.md").write_text(readme, encoding="utf-8")

    summary = {
        "profile_cutoff": profile_cut.isoformat(),
        "test_cutoff": test_cut.isoformat(),
        "calibration_n": int(len(calibration_iq)),
        "train_n": int(len(train)),
        "test_n": int(len(test)),
        "test_visit_rate": float(test["visit"].mean()),
        "selected_clusterers": selected_view.to_dict("records"),
        "metrics": metrics_df.to_dict("records"),
        "bootstrap": {"E002_vs_E001": boot12, "E003_vs_E002": boot23},
        "quality": quality,
        "best_model_by_ap": best_name,
        "legacy_reference": legacy,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(readme)


if __name__ == "__main__":
    main()
