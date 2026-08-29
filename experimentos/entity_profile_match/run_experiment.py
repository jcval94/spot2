from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score, silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

SEED = 42
TRAIN_FRAC = 0.80
MIN_SHARE = 0.03
MIN_SUPPORT = 25
PRIOR = 30.0
BOOT = 300
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "candidate" / "csv"
HERE = Path(__file__).resolve().parent
OUT = HERE / "results"


def md_table(df, cols, n=15):
    x = df[list(cols)].head(n).copy()
    if x.empty:
        return "_Sin filas con soporte suficiente._"
    lines = ["| " + " | ".join(x.columns) + " |", "|" + "|".join(["---"] * len(x.columns)) + "|"]
    for row in x.itertuples(index=False, name=None):
        vals = []
        for v in row:
            if isinstance(v, float):
                vals.append("n/a" if pd.isna(v) else f"{v:.3f}")
            else:
                vals.append(str(v).replace("|", "/"))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def mode(s):
    x = s.dropna().astype(str)
    if x.empty:
        return "unknown"
    return x.value_counts().index[0]


def band(v, s, labels):
    q1, q2 = pd.to_numeric(s, errors="coerce").dropna().quantile([0.33, 0.67])
    if pd.isna(v):
        return "unknown"
    return labels[0] if v <= q1 else labels[2] if v >= q2 else labels[1]


def metrics(y, p):
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-8, 1 - 1e-8)
    top = max(1, int(math.ceil(len(y) * 0.10)))
    order = np.argsort(-p)[:top]
    return {
        "roc_auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "lift_top_10pct": float(y[order].mean() / y.mean()),
    }


def wilson(k, n, z=1.96):
    if not n:
        return np.nan, np.nan
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / d
    return max(0.0, c - m), min(1.0, c + m)


def preprocess(cat, num):
    return ColumnTransformer([
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")), ("oh", OneHotEncoder(handle_unknown="ignore"))]), cat),
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("scale", RobustScaler())]), num),
    ])


def cluster_entity(name, ref, all_df, cat, num, prefix):
    cols = cat + num
    prep = preprocess(cat, num)
   xr = prep.fit_transform(ref[cols])
    trials = []
    models = {}
    for k in range(3, 9):
        km = KMeans(n_clusters=k, n_init=20, random_state=SEED)
        lab = km.fit_predict(xr)
        share = np.bincount(lab, minlength=k).min() / len(lab)
        sil = silhouette_score(xr, lab, sample_size=min(2000, len(ref)), random_state=SEED)
        trials.append({"entity": name, "k": k, "silhouette": sil, "min_cluster_share": share, "valid": share >= MIN_SHARE})
        models[k] = km
    sel = pd.DataFrame(trials)
    pool = sel[sel.valid] if sel.valid.any() else sel
    best = int(pool.sort_values(["silhouette", "min_cluster_share"], ascending=False).iloc[0].k)
    sel["selected"] = sel.k.eq(best)
    km = models[best]
    raw_ref = km.predict(xr)
    raw_all = km.predict(prep.transform(all_df[cols]))
    order = pd.Series(raw_ref).value_counts().index.tolist()
    remap = {raw: i + 1 for i, raw in enumerate(order)}
    ref_ids = pd.Series([f"{prefix}{remap[x]}" for x in raw_ref], index=ref.index)
    all_ids = pd.Series([f"{prefix}{remap[x]}" for x in raw_all], index=all_df.index)
    return ref_ids, all_ids, sel


def broker_features(spots, train, cutoff):
    ids = pd.DataFrame({"broker_id": sorted(spots.broker_id.dropna().unique())})
    ps = spots[spots.created_at < cutoff].copy()
    base = ps.groupby("broker_id").agg(n_spots=("spot_id", "nunique"), median_area=("area_sqm", "median"), median_rent=("price_sqm_mxn_rent", "median"), median_sale=("price_sqm_mxn_sale", "median")).reset_index()
    for col, values in {"sector_name": ["Industrial", "Office", "Retail", "Land"], "modality": ["rent", "sale", "both"]}.items():
        tab = pd.crosstab(ps.broker_id, ps[col], normalize="index")
        for v in values:
            base = base.merge(tab.reindex(columns=[v], fill_value=0)[v].rename(f"share_{v.lower()}").reset_index(), on="broker_id", how="left")
    base = base.merge(ps.groupby("broker_id").sector_name.agg(lambda s: mode(s)).rename("top_sector").reset_index(), on="broker_id", how="left")
    base = base.merge(ps.groupby("broker_id").region.agg(lambda s: mode(s)).rename("top_region").reset_index(), on="broker_id", how="left")
    base = base.merge(ps.groupby("broker_id").modality.agg(lambda s: mode(s)).rename("top_modality").reset_index(), on="broker_id", how="left")

    h = train.merge(spots[["spot_id", "broker_id"]], on="spot_id", how="left")
    h["visit"] = h.broker_response.eq("scheduled_visit").astype(int)
    h["positive"] = h.broker_response.isin(["accepted", "scheduled_visit"]).astype(int)
    h["responded"] = h.broker_response.ne("no_response").astype(int)
    h["fast"] = np.where(h.broker_response_hours.notna(), (h.broker_response_hours <= 6).astype(float), np.nan)
    bh = h.groupby("broker_id").agg(n_inquiries=("inquiry_id", "size"), visit_n=("visit", "sum"), positive_n=("positive", "sum"), responded_n=("responded", "sum"), median_response_hours=("broker_response_hours", "median"), fast_rate=("fast", "mean")).reset_index()
    for success, out, global_rate in [
        ("visit_n", "visit_rate", h.visit.mean()),
        ("positive_n", "positive_rate", h.positive.mean()),
        ("responded_n", "response_rate", h.responded.mean()),
    ]:
        bh[out] = (bh[success] + 20 * global_rate) / (bh.n_inquiries + 20)

    x = ids.merge(base, on="broker_id", how="left").merge(bh, on="broker_id", how="left")
    x["n_spots"] = x.n_spots.fillna(0)
    x["n_inquiries"] = x.n_inquiries.fillna(0)
    x["log_spots"] = np.log1p(x.n_spots)
    x["log_inquiries"] = np.log1p(x.n_inquiries)
    for c in [c for c in x if c.startswith("share_")]:
        x[c] = x[c].fillna(0)
    for c in ["top_sector", "top_region", "top_modality"]:
        x[c] = x[c].fillna("unknown")
    defaults = {"median_response_hours": h.broker_response_hours.median(), "fast_rate": h.fast.mean(), "visit_rate": h.visit.mean(), "positive_rate": h.positive.mean(), "response_rate": h.responded.mean()}
    for c, v in defaults.items():
        x[c] = x[c].fillna(v)
    return x


def profile_tables(lead_ref, spot_ref, broker_ref):
    lr = []
    for pid, g in lead_ref.groupby("lead_profile"):
        area = g.target_area_sqm.median()
        lr.append({"profile_id": pid, "profile_name": f"{pid} · {mode(g.user_type)} | {mode(g.search_sector)} | {mode(g.search_modality)} | {band(area, lead_ref.target_area_sqm, ('compact','mid-size','large-area'))}", "n_reference": len(g), "share_reference": len(g)/len(lead_ref), "median_target_area_sqm": area, "median_prior_inquiries": g.prior_inquiries.median(), "prior_conversion_rate": g.has_converted_before.astype(bool).mean()})
    sr = []
    for pid, g in spot_ref.groupby("spot_profile"):
        area = g.area_sqm.median()
        sr.append({"profile_id": pid, "profile_name": f"{pid} · {mode(g.sector_name)} | {mode(g.modality)} | {mode(g.type_name)} | {band(area, spot_ref.area_sqm, ('compact','mid-size','large-area'))}", "n_reference": len(g), "share_reference": len(g)/len(spot_ref), "median_area_sqm": area, "median_rent_price_sqm": g.price_sqm_mxn_rent.median(), "median_sale_price_sqm": g.price_sqm_mxn_sale.median()})
    br = []
    for pid, g in broker_ref.groupby("broker_profile"):
        r = g.median_response_hours.median(); v = g.visit_rate.median(); s = g.n_spots.median()
        br.append({"profile_id": pid, "profile_name": f"{pid} · {mode(g.top_sector)} | {band(r, broker_ref.median_response_hours, ('faster','mid-speed','slower'))} | {band(v, broker_ref.visit_rate, ('lower-visit','mid-visit','higher-visit'))} | {band(s, broker_ref.n_spots, ('small-book','mid-book','large-book'))}", "n_reference": len(g), "share_reference": len(g)/len(broker_ref), "median_spots_pre": s, "median_inquiries_pre": g.n_inquiries.median(), "median_response_hours": r, "median_scheduled_visit_rate_pre": v})
    return pd.DataFrame(lr).sort_values("profile_id"), pd.DataFrame(sr).sort_values("profile_id"), pd.DataFrame(br).sort_values("profile_id")


def fit_model(train, test, interaction=False):
    cols = ["lead_profile", "spot_profile", "broker_profile"]
    a = train[cols].copy(); b = test[cols].copy()
    if interaction:
        for l, r, n in [("lead_profile","spot_profile","lead_spot"),("lead_profile","broker_profile","lead_broker"),("spot_profile","broker_profile","spot_broker")]:
            a[n] = a[l].astype(str) + "x" + a[r].astype(str); b[n] = b[l].astype(str) + "x" + b[r].astype(str)
        a["triple"] = a.lead_profile.astype(str) + "x" + a.spot_profile.astype(str) + "x" + a.broker_profile.astype(str)
        b["triple"] = b.lead_profile.astype(str) + "x" + b.spot_profile.astype(str) + "x" + b.broker_profile.astype(str)
    model = Pipeline([("oh", OneHotEncoder(handle_unknown="ignore", min_frequency=10)), ("lr", LogisticRegression(max_iter=3000, C=0.7, random_state=SEED))])
    model.fit(a, train.visit)
    return model.predict_proba(b)[:, 1]


def bootstrap(y, p0, p1):
    rng = np.random.default_rng(SEED); y = np.asarray(y, int); da = []; dp = []
    for _ in range(BOOT):
        idx = rng.integers(0, len(y), len(y)); ys = y[idx]
        if len(np.unique(ys)) < 2: continue
        da.append(roc_auc_score(ys, p1[idx]) - roc_auc_score(ys, p0[idx]))
        dp.append(average_precision_score(ys, p1[idx]) - average_precision_score(ys, p0[idx]))
    return {"delta_auc": roc_auc_score(y,p1)-roc_auc_score(y,p0), "delta_auc_low": np.quantile(da,.025), "delta_auc_high": np.quantile(da,.975), "delta_ap": average_precision_score(y,p1)-average_precision_score(y,p0), "delta_ap_low": np.quantile(dp,.025), "delta_ap_high": np.quantile(dp,.975)}


def group_perf(df, groups, baseline):
    rows = []
    for keys, g in df.groupby(groups):
        if not isinstance(keys, tuple): keys = (keys,)
        k = int(g.visit.sum()); n = len(g); raw = k/n; smooth = (k + PRIOR*baseline)/(n+PRIOR); lo,hi = wilson(k,n); exp = g.pred_marginal.mean()
        row = dict(zip(groups, keys)); row.update({"n":n,"scheduled_visit_rate":raw,"smoothed_visit_rate":smooth,"positive_response_rate":g.positive.mean(),"lift_vs_global":smooth/baseline,"expected_marginal_probability":exp,"synergy_vs_marginals":smooth-exp,"wilson_low":lo,"wilson_high":hi}); rows.append(row)
    return pd.DataFrame(rows)


def make_readme(cutoff, train, test, selection, lp, sp, bp, mm, boot, top, quality):
    m = mm.set_index("model"); m0=m.loc["profile_marginals"]; m1=m.loc["profile_interactions"]
    supported = boot["delta_auc_low"] > 0 or boot["delta_ap_low"] > 0
    conclusion = "Sí hay señal fuera de muestra de compatibilidad entre perfiles." if supported else "No hay evidencia robusta de química adicional entre perfiles fuera de muestra."
    ksel = selection[selection.selected][["entity","k","silhouette","min_cluster_share"]]
    return f"""# Experimento: perfiles Lead × Spot × Broker

## Resumen ejecutivo

**{conclusion}**

La hipótesis es que un lead no tiene una probabilidad fija de avanzar: parte de la oportunidad puede depender del tipo de inmueble y del tipo de broker con el que se conecta. Los perfiles se aprenden de forma no supervisada y la compatibilidad se evalúa en un periodo futuro.

> Importante: el dataset público del candidato no contiene cierre o venta real. El outcome primario aquí es scheduled_visit y el secundario es respuesta positiva (accepted o scheduled_visit). Una visita es un proxy de avance comercial, no una venta.

- Corte temporal: **{cutoff.isoformat()}**.
- Train: **{len(train):,} inquiries**; test futuro: **{len(test):,} inquiries**.
- Tasa de visita en test: **{test.visit.mean():.1%}**.
- Perfiles individuales: ROC AUC **{m0.roc_auc:.3f}**, AP **{m0.average_precision:.3f}**.
- Perfiles + interacciones: ROC AUC **{m1.roc_auc:.3f}**, AP **{m1.average_precision:.3f}**.
- Delta ROC AUC: **{boot['delta_auc']:+.3f}** (bootstrap 95% CI {boot['delta_auc_low']:+.3f} a {boot['delta_auc_high']:+.3f}).
- Delta AP: **{boot['delta_ap']:+.3f}** (bootstrap 95% CI {boot['delta_ap_low']:+.3f} a {boot['delta_ap_high']:+.3f}).

## Cómo se construyen los perfiles

K-Means sobre variables mixtas con imputación, one-hot encoding y escalado robusto. Se prueba K=3 a 8 y se elige por silhouette, evitando cuando es posible clusters menores a 3%.

### Selección de K

{md_table(ksel, ['entity','k','silhouette','min_cluster_share'])}

### Lead profiles

Usan quién busca, sector y modalidad deseados, tamaño, presupuesto, ubicación preferida, fuente e historia previa. Se excluye lead_score_internal.

{md_table(lp, ['profile_id','profile_name','n_reference','share_reference','median_target_area_sqm','median_prior_inquiries','prior_conversion_rate'])}

### Spot profiles

Usan sector, modalidad, tipo, ubicación, área, precio y atributos físicos. Se excluyen days_on_market, total_inquiries, total_views e is_active.

{md_table(sp, ['profile_id','profile_name','n_reference','share_reference','median_area_sqm','median_rent_price_sqm','median_sale_price_sqm'])}

### Broker profiles

No existe una tabla brokers. El perfil se reconstruye por broker_id usando sólo historia anterior al corte: composición del portafolio, volumen histórico, velocidad de respuesta y tasas históricas suavizadas de visita/respuesta.

{md_table(bp, ['profile_id','profile_name','n_reference','share_reference','median_spots_pre','median_inquiries_pre','median_response_hours','median_scheduled_visit_rate_pre'])}

## Prueba de compatibilidad

Se comparan: baseline global; modelo con lead_profile + spot_profile + broker_profile; y modelo que además agrega Lead×Spot, Lead×Broker, Spot×Broker y la combinación triple. Si el tercer modelo mejora fuera de muestra, hay evidencia de que importa la combinación y no sólo que un perfil individual sea fuerte.

{md_table(mm, ['model','roc_auc','average_precision','brier','log_loss','lift_top_10pct'])}

La métrica synergy_vs_marginals compara la tasa de visita suavizada de cada combinación contra la probabilidad esperada usando sólo los tres perfiles individuales. Sólo se muestran combinaciones con al menos {MIN_SUPPORT} interacciones futuras.

### Combinaciones con mayor sinergia

{md_table(top, ['lead_profile','spot_profile','broker_profile','n','scheduled_visit_rate','smoothed_visit_rate','lift_vs_global','expected_marginal_probability','synergy_vs_marginals','wilson_low','wilson_high'])}

## Protección contra leakage

- Corte temporal al 80% de inquiry_at.
- El comportamiento del broker se calcula sólo antes del corte.
- Lead y Spot se clusterizan con entidades existentes antes del corte y el transformador se aplica después a entidades nuevas.
- Se excluyen broker_response y broker_response_hours de los perfiles de Lead y Spot.
- Se excluyen acumulados actuales del Spot.
- has_converted_before se conserva porque representa historia previa declarada, no el resultado futuro de la inquiry actual.

## Calidad de joins

- Leads: {quality['n_leads']:,}; Spots: {quality['n_spots']:,}; Brokers: {quality['n_brokers']:,}; Inquiries: {quality['n_inquiries']:,}.
- Cobertura inquiry→lead: {quality['lead_join']:.1%}.
- Cobertura inquiry→spot: {quality['spot_join']:.1%}.
- Cobertura spot→attributes: {quality['attr_join']:.1%}.

## Outputs

Los CSV de perfiles, asignaciones, selección de K, métricas y compatibilidades quedan en la carpeta results junto con results.json.

## Ejecución

    python experimentos/entity_profile_match/run_experiment.py

GitHub Actions usa .github/workflows/entity-profile-match-experiment.yml. Es la única excepción fuera de experimentos porque GitHub sólo reconoce workflows dentro de .github/workflows.

## Uso recomendado

Si la señal de interacción se sostiene, usaría estos perfiles como una capa de compatibilidad, no como reemplazo del Lead Opportunity Score:

**Opportunity = Lead Quality × Inventory Availability × Compatibility(Lead type, Spot type, Broker type)**

La compatibilidad debe regularizarse y volver a efectos marginales cuando una combinación tenga poco soporte. Para afirmar causalidad sobre routing o asignación de brokers hace falta un experimento posterior.
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    leads = pd.read_csv(DATA/"leads.csv", parse_dates=["created_at"])
    spots = pd.read_csv(DATA/"spots.csv", parse_dates=["created_at"])
    attrs = pd.read_csv(DATA/"spot_attributes.csv")
    iq = pd.read_csv(DATA/"inquiries.csv", parse_dates=["inquiry_at"])
    assert leads.lead_id.is_unique and spots.spot_id.is_unique and attrs.spot_id.is_unique and iq.inquiry_id.is_unique
    quality = {"n_leads":len(leads),"n_spots":len(spots),"n_brokers":spots.broker_id.nunique(),"n_inquiries":len(iq),"lead_join":iq.lead_id.isin(leads.lead_id).mean(),"spot_join":iq.spot_id.isin(spots.spot_id).mean(),"attr_join":spots.spot_id.isin(attrs.spot_id).mean()}
    assert min(quality["lead_join"], quality["spot_join"], quality["attr_join"]) >= .995
    times = iq.inquiry_at.sort_values().reset_index(drop=True); cutoff = times.iloc[int(len(times)*TRAIN_FRAC)]
    train_iq = iq[iq.inquiry_at < cutoff].copy()

    lref = leads[leads.created_at < cutoff].copy()
    lcat = ["user_type","company_size","industry","search_sector","search_modality","preferred_state","preferred_municipality","preferred_corridor","source","has_converted_before"]
    lnum = ["target_area_sqm","min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly","min_budget_mxn_sale_total","max_budget_mxn_sale_total","prior_searches","prior_inquiries"]
    rid, aid, ls = cluster_entity("lead", lref, leads, lcat, lnum, "L"); lref["lead_profile"] = rid; leads["lead_profile"] = aid

    sx = spots.merge(attrs, on="spot_id", how="left", validate="one_to_one")
    sx["amenities_count"] = sx.amenities.fillna("[]").astype(str).str.count(",") + (~sx.amenities.fillna("[]").astype(str).eq("[]")).astype(int)
    sref = sx[sx.created_at < cutoff].copy()
    scat = ["sector_name","type_name","state","municipality","corridor","region","modality","natural_light","security_type","building_status","floor_material"]
    snum = ["area_sqm","price_sqm_mxn_rent","price_sqm_mxn_sale","price_total_mxn_rent","price_total_mxn_sale","maintenance_cost_mxn","luminaires","charging_ports","floor_level","elevators","vertical_height_m","parking_spaces","amenities_count"]
    rid, aid, ss = cluster_entity("spot", sref, sx, scat, snum, "S"); sref["spot_profile"] = rid; sx["spot_profile"] = aid

    bf = broker_features(spots, train_iq, cutoff)
    bref = bf[(bf.n_spots > 0) | (bf.n_inquiries > 0)].copy()
    bcat = ["top_sector","top_region","top_modality"]
    bnum = ["log_spots","log_inquiries","median_area","median_rent","median_sale","share_industrial","share_office","share_retail","share_land","share_rent","share_sale","share_both","median_response_hours","fast_rate","visit_rate","positive_rate","response_rate"]
    rid, aid, bs = cluster_entity("broker", bref, bref, bcat, bnum, "B"); bref["broker_profile"] = rid
    bf = bf.merge(bref[["broker_id","broker_profile"]], on="broker_id", how="left"); bf.broker_profile = bf.broker_profile.fillna("B0")
    lp, sp, bp = profile_tables(lref, sref, bref)
    selection = pd.concat([ls,ss,bs], ignore_index=True)

    x = iq.merge(leads[["lead_id","lead_profile"]], on="lead_id", how="left", validate="many_to_one")
    x = x.merge(sx[["spot_id","broker_id","spot_profile"]], on="spot_id", how="left", validate="many_to_one")
    x = x.merge(bf[["broker_id","broker_profile"]], on="broker_id", how="left", validate="many_to_one")
    assert not x[["lead_profile","spot_profile","broker_profile"]].isna().any().any()
    x["visit"] = x.broker_response.eq("scheduled_visit").astype(int); x["positive"] = x.broker_response.isin(["accepted","scheduled_visit"]).astype(int)
    train = x[x.inquiry_at < cutoff].copy(); test = x[x.inquiry_at >= cutoff].copy()
    pbase = np.repeat(train.visit.mean(), len(test)); pm = fit_model(train,test,False); pi = fit_model(train,test,True)
    test["pred_marginal"] = pm
    mm = pd.DataFrame([{"model":"global_baseline",**metrics(test.visit,pbase)},{"model":"profile_marginals",**metrics(test.visit,pm)},{"model":"profile_interactions",**metrics(test.visit,pi)}])
    boot = bootstrap(test.visit,pm,pi); baseline = test.visit.mean()
    combos = group_perf(test,["lead_profile","spot_profile","broker_profile"],baseline)
    top = combos[combos.n >= MIN_SUPPORT].sort_values(["synergy_vs_marginals","lift_vs_global","n"], ascending=False).reset_index(drop=True)

    lp.to_csv(OUT/"lead_profiles.csv",index=False); sp.to_csv(OUT/"spot_profiles.csv",index=False); bp.to_csv(OUT/"broker_profiles.csv",index=False)
    leads[["lead_id","lead_profile"]].to_csv(OUT/"lead_assignments.csv",index=False); sx[["spot_id","broker_id","spot_profile"]].to_csv(OUT/"spot_assignments.csv",index=False); bf.to_csv(OUT/"broker_assignments.csv",index=False)
    selection.to_csv(OUT/"cluster_selection.csv",index=False); mm.to_csv(OUT/"model_metrics.csv",index=False); combos.to_csv(OUT/"combination_performance_test.csv",index=False); top.to_csv(OUT/"top_combinations.csv",index=False)
    group_perf(test,["lead_profile","spot_profile"],baseline).to_csv(OUT/"lead_spot_performance_test.csv",index=False); group_perf(test,["lead_profile","broker_profile"],baseline).to_csv(OUT/"lead_broker_performance_test.csv",index=False); group_perf(test,["spot_profile","broker_profile"],baseline).to_csv(OUT/"spot_broker_performance_test.csv",index=False)
    result = {"seed":SEED,"cutoff":cutoff.isoformat(),"train_n":len(train),"test_n":len(test),"selected_k":selection[selection.selected].set_index("entity").k.astype(int).to_dict(),"metrics":mm.to_dict("records"),"bootstrap":{k:float(v) for k,v in boot.items()},"test_visit_rate":float(baseline),"supported_combinations":int((combos.n>=MIN_SUPPORT).sum()),"quality":{k:float(v) if isinstance(v,(float,np.floating)) else int(v) for k,v in quality.items()}}
    (OUT/"results.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    readme = make_readme(cutoff,train,test,selection,lp,sp,bp,mm,boot,top,quality); (HERE/"README.md").write_text(readme,encoding="utf-8"); print(readme)

if __name__ == "__main__":
    main()
