from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist

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

SEED = 42
BOOT = 300
MIN_CELL = 50
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA = ROOT / "data" / "candidate" / "csv"
PARENT = ROOT / "experimentos" / "profile_clustering_v2" / "results"
OUT = HERE / "results"

def jdump(obj):
    def clean(x):
        if isinstance(x, (np.integer,)): return int(x)
        if isinstance(x, (np.floating,)): return None if np.isnan(x) else float(x)
        if isinstance(x, pd.Timestamp): return x.isoformat()
        if isinstance(x, np.bool_): return bool(x)
        raise TypeError(type(x).__name__)
    return json.dumps(obj, indent=2, ensure_ascii=False, default=clean)

def safe_bool(s):
    if pd.api.types.is_bool_dtype(s): return s.astype(bool)
    return s.astype(str).str.lower().isin(["true", "1", "yes"])

def load():
    leads = pd.read_csv(DATA/"leads.csv", parse_dates=["created_at"])
    spots = pd.read_csv(DATA/"spots.csv", parse_dates=["created_at"])
    attrs = pd.read_csv(DATA/"spot_attributes.csv")
    iq = pd.read_csv(DATA/"inquiries.csv", parse_dates=["inquiry_at"])
    av = pd.read_csv(DATA/"availability_snapshot.csv", parse_dates=["snapshot_date"])
    market = pd.read_csv(DATA/"market_context.csv", parse_dates=["month"])
    return leads, spots, attrs, iq, av, market

def add_check(rows, group, check, value, expected, ok, severity="HIGH", note=""):
    rows.append({
        "group": group, "check": check, "value": value, "expected": expected,
        "status": "PASS" if bool(ok) else "FAIL", "severity": severity, "note": note
    })

def audit_data(leads, spots, attrs, iq, av, market):
    OUT.mkdir(parents=True, exist_ok=True)
    tables = {
        "leads": (leads, "lead_id"),
        "spots": (spots, "spot_id"),
        "spot_attributes": (attrs, "spot_id"),
        "inquiries": (iq, "inquiry_id"),
        "availability_snapshot": (av, "snapshot_id"),
    }
    table_rows, rel, content = [], [], []
    for name, (df, pk) in tables.items():
        table_rows.append({
            "table": name, "rows": len(df), "columns": len(df.columns),
            "exact_duplicate_rows": int(df.duplicated().sum()),
            "pk": pk, "pk_nulls": int(df[pk].isna().sum()),
            "pk_duplicates": int(df[pk].duplicated().sum()),
            "pk_distinct": int(df[pk].nunique(dropna=True)),
        })
        add_check(rel, "primary_key", f"{name}.{pk} unique/non-null",
                  int(df[pk].duplicated().sum()+df[pk].isna().sum()), "0",
                  df[pk].isna().sum()==0 and df[pk].duplicated().sum()==0, "CRITICAL")
    table_rows.append({
        "table":"market_context","rows":len(market),"columns":len(market.columns),
        "exact_duplicate_rows":int(market.duplicated().sum()),"pk":"state+municipality+corridor+sector+month",
        "pk_nulls":int(market[["state","municipality","corridor","sector","month"]].isna().any(axis=1).sum()),
        "pk_duplicates":int(market.duplicated(["state","municipality","corridor","sector","month"]).sum()),
        "pk_distinct":int(market[["state","municipality","corridor","sector","month"]].drop_duplicates().shape[0]),
    })
    add_check(rel, "primary_key", "market_context composite key unique",
              int(market.duplicated(["state","municipality","corridor","sector","month"]).sum()), "0",
              market.duplicated(["state","municipality","corridor","sector","month"]).sum()==0, "CRITICAL")
    add_check(rel, "grain", "availability spot_id+snapshot_date unique",
              int(av.duplicated(["spot_id","snapshot_date"]).sum()), "0",
              av.duplicated(["spot_id","snapshot_date"]).sum()==0, "CRITICAL")

    fk_specs = [
        ("inquiries.lead_id -> leads", iq.lead_id, leads.lead_id),
        ("inquiries.spot_id -> spots", iq.spot_id, spots.spot_id),
        ("spot_attributes.spot_id -> spots", attrs.spot_id, spots.spot_id),
        ("spots.spot_id -> spot_attributes", spots.spot_id, attrs.spot_id),
        ("availability.spot_id -> spots", av.spot_id, spots.spot_id),
    ]
    for name, child, parent in fk_specs:
        orphan = int((~child.isin(parent)).sum())
        add_check(rel, "referential_integrity", name, orphan, "0", orphan==0, "CRITICAL")

    base_n = len(iq)
    joined = iq.merge(leads[["lead_id"]], on="lead_id", how="left", validate="many_to_one", indicator=True)
    add_check(rel, "join_preservation", "inquiry LEFT lead preserves rows", len(joined), str(base_n), len(joined)==base_n, "CRITICAL")
    joined = iq.merge(spots[["spot_id"]], on="spot_id", how="left", validate="many_to_one", indicator=True)
    add_check(rel, "join_preservation", "inquiry LEFT spot preserves rows", len(joined), str(base_n), len(joined)==base_n, "CRITICAL")
    joined = spots.merge(attrs, on="spot_id", how="left", validate="one_to_one", indicator=True)
    add_check(rel, "join_preservation", "spot LEFT attributes is 1:1", len(joined), str(len(spots)), len(joined)==len(spots), "CRITICAL")

    raw_av_n = len(iq.merge(av[["spot_id","snapshot_id"]], on="spot_id", how="left"))
    add_check(rel, "join_risk", "raw inquiry x availability join expansion factor",
              raw_av_n/max(1,len(iq)), "must be >1 and never used directly", raw_av_n>len(iq), "LOW",
              "Expected one-to-many expansion; production feature join must use backward as-of.")

    iq_sorted = iq[["inquiry_id","spot_id","inquiry_at"]].sort_values(["inquiry_at","spot_id"]).copy()
    av2 = av[["spot_id","snapshot_date","is_available","days_until_available","competing_inquiries_30d"]].sort_values(["snapshot_date","spot_id"]).copy()
    asof = pd.merge_asof(iq_sorted, av2, left_on="inquiry_at", right_on="snapshot_date",
                         by="spot_id", direction="backward", allow_exact_matches=True)
    asof["lag_days"] = (asof.inquiry_at-asof.snapshot_date).dt.total_seconds()/86400
    coverage = float(asof.snapshot_date.notna().mean())
    lag90 = float((asof.lag_days.le(90) & asof.snapshot_date.notna()).mean())
    future = int((asof.snapshot_date>asof.inquiry_at).fillna(False).sum())
    add_check(rel, "point_in_time", "availability backward-asof coverage", coverage, ">=0.90", coverage>=.90, "HIGH")
    add_check(rel, "point_in_time", "availability coverage with lag <=90d", lag90, ">=0.80", lag90>=.80, "MEDIUM")
    add_check(rel, "point_in_time", "future availability snapshots used", future, "0", future==0, "CRITICAL")

    li = iq.merge(leads[["lead_id","created_at"]], on="lead_id", how="left")
    si = iq.merge(spots[["spot_id","created_at"]], on="spot_id", how="left")
    lead_future = int((li.created_at>li.inquiry_at).sum())
    spot_future = int((si.created_at>si.inquiry_at).sum())
    add_check(content, "temporal", "lead created after inquiry", lead_future, "0", lead_future==0, "CRITICAL")
    add_check(content, "temporal", "spot created after inquiry", spot_future, "0", spot_future==0, "CRITICAL")

    ix = iq.merge(leads, on="lead_id", how="left", suffixes=("","_lead")).merge(
        spots[["spot_id","sector_name","modality","state","municipality","corridor"]], on="spot_id", how="left", suffixes=("","_spot"))
    def modality_ok(r):
        a, b = str(r.search_modality), str(r.modality)
        return a=="both" or b=="both" or a==b
    mod_ok = float(ix.apply(modality_ok,axis=1).mean())
    sec_ok = float(ix.search_sector.eq(ix.sector_name).mean())
    muni_ok = float(ix.preferred_municipality.eq(ix.municipality).mean())
    cor_mask = ix.preferred_corridor.notna()
    cor_ok = float(ix.loc[cor_mask,"preferred_corridor"].eq(ix.loc[cor_mask,"corridor"]).mean()) if cor_mask.any() else np.nan
    add_check(content, "cross_table_semantics", "inquiry lead/spot modality compatible", mod_ok, "descriptive >=0.50", mod_ok>=.50, "MEDIUM")
    add_check(content, "cross_table_semantics", "inquiry lead/spot sector exact match", sec_ok, "descriptive", True, "LOW")
    add_check(content, "cross_table_semantics", "inquiry preferred municipality exact match", muni_ok, "descriptive", True, "LOW")
    add_check(content, "cross_table_semantics", "inquiry preferred corridor exact match when declared", cor_ok, "descriptive", True, "LOW")

    for low, high in [
        ("min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly"),
        ("min_budget_mxn_sale_total","max_budget_mxn_sale_total"),
    ]:
        both = leads[low].notna() & leads[high].notna()
        bad = int((leads.loc[both,low]>leads.loc[both,high]).sum())
        add_check(content, "business_rule", f"{low} <= {high}", bad, "0", bad==0, "HIGH")

    budget_rules = [
        ("rent","min_budget_mxn_rent_monthly"),("rent","max_budget_mxn_rent_monthly"),
        ("sale","min_budget_mxn_sale_total"),("sale","max_budget_mxn_sale_total")
    ]
    for mode, col in budget_rules:
        mask = leads.search_modality.isin([mode,"both"])
        miss = int(leads.loc[mask,col].isna().sum())
        rate = miss/max(1,int(mask.sum()))
        add_check(content, "conditional_completeness", f"lead {col} populated for {mode}/both", 1-rate, ">=0.95", rate<.05, "HIGH")

    price_rules = [
        ("rent","price_sqm_mxn_rent"),("rent","price_total_mxn_rent"),
        ("sale","price_sqm_mxn_sale"),("sale","price_total_mxn_sale")
    ]
    for mode, col in price_rules:
        mask=spots.modality.isin([mode,"both"])
        miss=int(spots.loc[mask,col].isna().sum())
        rate=miss/max(1,int(mask.sum()))
        add_check(content,"conditional_completeness",f"spot {col} populated for {mode}/both",1-rate,">=0.95",rate<.05,"HIGH")

    noresp=iq.broker_response.eq("no_response")
    contradiction=int((noresp & iq.broker_response_hours.notna()).sum())
    responded_missing=int((~noresp & iq.broker_response_hours.isna()).sum())
    add_check(content,"response_consistency","no_response with response_hours",contradiction,"0",contradiction==0,"HIGH")
    add_check(content,"response_consistency","response outcome missing response_hours",responded_missing,"0 preferred",responded_missing==0,"MEDIUM")

    add_check(content,"range","negative requested/target area",
              int((pd.to_numeric(iq.requested_area_sqm,errors="coerce")<0).sum()+(pd.to_numeric(leads.target_area_sqm,errors="coerce")<0).sum()),
              "0", ((pd.to_numeric(iq.requested_area_sqm,errors="coerce")<0).sum()+(pd.to_numeric(leads.target_area_sqm,errors="coerce")<0).sum())==0,"HIGH")
    lat_ok=spots.lat.between(14,33, inclusive="both")
    lon_ok=spots.lon.between(-119,-86, inclusive="both")
    add_check(content,"range","spot coordinates plausible Mexico bounding box",
              float((lat_ok&lon_ok).mean()),">=0.99",float((lat_ok&lon_ok).mean())>=.99,"MEDIUM")

    # Exact same-month market-context coverage is descriptive only: publication timing is unknown.
    sm=spots[["spot_id","state","municipality","corridor","sector_name"]].copy()
    mi=iq[["inquiry_id","spot_id","inquiry_at"]].merge(sm,on="spot_id",how="left")
    mi["month"]=mi.inquiry_at.dt.to_period("M").dt.to_timestamp()
    mm=market.rename(columns={"sector":"sector_name"})
    mj=mi.merge(mm[["state","municipality","corridor","sector_name","month"]].drop_duplicates(),
                on=["state","municipality","corridor","sector_name","month"],how="left",indicator=True)
    mcov=float(mj._merge.eq("both").mean())
    add_check(content,"market_context","spot geography+sector+same-month exact coverage",mcov,"descriptive only",True,"LOW",
              "Not used as a historical feature because publication semantics are unknown.")

    complete=[]
    for name,df in [("leads",leads),("spots",spots),("spot_attributes",attrs),("inquiries",iq),("availability_snapshot",av),("market_context",market)]:
        for c in df.columns:
            complete.append({"table":name,"column":c,"non_null_rate":float(df[c].notna().mean()),
                             "null_count":int(df[c].isna().sum()),"distinct":int(df[c].nunique(dropna=True))})
    pd.DataFrame(table_rows).to_csv(OUT/"table_profile.csv",index=False)
    pd.DataFrame(rel).to_csv(OUT/"relationship_checks.csv",index=False)
    pd.DataFrame(content).to_csv(OUT/"content_consistency_checks.csv",index=False)
    pd.DataFrame(complete).to_csv(OUT/"column_completeness.csv",index=False)
    all_checks=pd.concat([pd.DataFrame(rel),pd.DataFrame(content)],ignore_index=True)
    summary=all_checks.groupby(["severity","status"]).size().rename("n").reset_index()
    summary.to_csv(OUT/"data_quality_summary.csv",index=False)
    critical=int(((all_checks.severity=="CRITICAL")&(all_checks.status=="FAIL")).sum())
    return {"critical_failures":critical,"availability_coverage":coverage,"availability_lag90":lag90,
            "market_exact_coverage":mcov,"modality_match":mod_ok,"sector_match":sec_ok,
            "municipality_match":muni_ok,"corridor_match":cor_ok}, asof

def preprocessor(cat,num):
    return ColumnTransformer([
        ("cat",Pipeline([("imp",SimpleImputer(strategy="most_frequent")),("oh",OneHotEncoder(handle_unknown="ignore"))]),cat),
        ("num",Pipeline([("imp",SimpleImputer(strategy="median")),("sc",RobustScaler())]),num),
    ])

def entropy(labels):
    p=pd.Series(labels).value_counts(normalize=True).values
    return float(-(p*np.log(p)).sum()/np.log(len(p))) if len(p)>1 else 0.0

def select_clusterer(ref, all_df, cat, num, prefix):
    cols=cat+num
    prep=preprocessor(cat,num)
    xr=prep.fit_transform(ref[cols])
    xa=prep.transform(all_df[cols])
    if hasattr(xr,"toarray") and xr.shape[1]<200: xr_eval=xr.toarray(); xa_eval=xa.toarray()
    else: xr_eval=xr; xa_eval=xa
    rows=[]; models={}
    for method in ["kmeans","bisecting","gmm"]:
        for k in range(3,8):
            if method=="kmeans":
                m=KMeans(n_clusters=k,n_init=20,random_state=SEED); lab=m.fit_predict(xr_eval); all_lab=m.predict(xa_eval)
                m2=KMeans(n_clusters=k,n_init=20,random_state=SEED+17); lab2=m2.fit_predict(xr_eval)
            elif method=="bisecting":
                m=BisectingKMeans(n_clusters=k,random_state=SEED); lab=m.fit_predict(xr_eval); all_lab=m.predict(xa_eval)
                m2=BisectingKMeans(n_clusters=k,random_state=SEED+17); lab2=m2.fit_predict(xr_eval)
            else:
                m=GaussianMixture(n_components=k,covariance_type="diag",reg_covar=1e-5,random_state=SEED)
                lab=m.fit_predict(np.asarray(xr_eval)); all_lab=m.predict(np.asarray(xa_eval))
                m2=GaussianMixture(n_components=k,covariance_type="diag",reg_covar=1e-5,random_state=SEED+17)
                lab2=m2.fit_predict(np.asarray(xr_eval))
            shares=pd.Series(lab).value_counts(normalize=True)
            sil=float(silhouette_score(xr_eval,lab,sample_size=min(2000,len(ref)),random_state=SEED))
            ari=float(adjusted_rand_score(lab,lab2))
            ent=entropy(lab); mn=float(shares.min()); mx=float(shares.max()); bal=mn>=.05 and mx<=.70
            score=sil+0.20*ent+0.15*ari+(0.10 if bal else -0.20)
            rows.append({"profile_family":prefix,"method":method,"k":k,"silhouette":sil,
                         "min_cluster_share":mn,"max_cluster_share":mx,"normalized_entropy":ent,
                         "stability_ari":ari,"balance_ok":bal,"selection_score":score})
            models[(method,k)]=(m,lab,all_lab)
    bench=pd.DataFrame(rows)
    pool=bench[bench.balance_ok] if bench.balance_ok.any() else bench
    best=pool.sort_values("selection_score",ascending=False).iloc[0]
    method,k=str(best.method),int(best.k)
    m,lab,all_lab=models[(method,k)]
    # stable IDs by descending reference size
    order=pd.Series(lab).value_counts().index.tolist()
    remap={raw:i+1 for i,raw in enumerate(order)}
    ref_ids=pd.Series([f"{prefix}{remap[x]}" for x in lab],index=ref.index)
    all_ids=pd.Series([f"{prefix}{remap[x]}" for x in all_lab],index=all_df.index)
    bench["selected"]=(bench.method.eq(method)&bench.k.eq(k))
    return ref_ids, all_ids, bench

def profile_notes(df, profile_col, cat, num):
    out=[]
    for pid,g in df.groupby(profile_col):
        bits=[]
        for c in cat[:5]:
            if c in g:
                mode=g[c].dropna().astype(str).mode()
                if len(mode): bits.append(f"{c}={mode.iloc[0]} ({(g[c].astype(str)==mode.iloc[0]).mean():.0%})")
        for c in num[:4]:
            med=pd.to_numeric(g[c],errors="coerce").median()
            if pd.notna(med): bits.append(f"{c} median={med:.2f}")
        out.append({"profile_id":pid,"n":len(g),"share":len(g)/len(df),"interpretation":" | ".join(bits)})
    return pd.DataFrame(out)

def metrics(y,p):
    y=np.asarray(y,int); p=np.clip(np.asarray(p,float),1e-8,1-1e-8)
    top=max(1,int(math.ceil(len(y)*.10)))
    idx=np.argsort(-p)[:top]
    top20=max(1,int(math.ceil(len(y)*.20))); idx20=np.argsort(-p)[:top20]
    return {
        "roc_auc":float(roc_auc_score(y,p)) if len(np.unique(y))>1 else np.nan,
        "average_precision":float(average_precision_score(y,p)),
        "brier":float(brier_score_loss(y,p)),
        "log_loss":float(log_loss(y,p,labels=[0,1])),
        "lift_top_10pct":float(y[idx].mean()/y.mean()) if y.mean()>0 else np.nan,
        "recall_top_20pct":float(y[idx20].sum()/y.sum()) if y.sum()>0 else np.nan,
    }

def fit_score(train,test,cols):
    a=train[cols].astype(str).fillna("missing")
    b=test[cols].astype(str).fillna("missing")
    model=Pipeline([
        ("oh",OneHotEncoder(handle_unknown="ignore",min_frequency=10)),
        ("lr",LogisticRegression(C=.5,max_iter=3000,random_state=SEED))
    ])
    model.fit(a,train.visit.astype(int))
    return model.predict_proba(b)[:,1]

def cluster_bootstrap(test,p_a,p_b,n=BOOT):
    rng=np.random.default_rng(SEED)
    leads=test.lead_id.drop_duplicates().to_numpy()
    out=[]
    for _ in range(n):
        sampled=rng.choice(leads,size=len(leads),replace=True)
        idx=np.concatenate([np.flatnonzero(test.lead_id.to_numpy()==x) for x in sampled])
        y=test.visit.to_numpy()[idx]
        if len(np.unique(y))<2: continue
        ma,mb=metrics(y,p_a[idx]),metrics(y,p_b[idx])
        out.append([mb["roc_auc"]-ma["roc_auc"],mb["average_precision"]-ma["average_precision"],mb["lift_top_10pct"]-ma["lift_top_10pct"]])
    arr=np.asarray(out)
    names=["delta_auc","delta_ap","delta_lift10"]
    res={}
    for i,nm in enumerate(names):
        res[nm]=float(np.mean(arr[:,i]))
        res[nm+"_low"]=float(np.quantile(arr[:,i],.025))
        res[nm+"_high"]=float(np.quantile(arr[:,i],.975))
    return res

def lead_metrics(test,p):
    z=pd.DataFrame({"lead_id":test.lead_id.values,"y":test.visit.values,"p":p})
    g=z.groupby("lead_id").agg(y=("y","max"),p=("p","max"))
    return metrics(g.y,g.p), int(len(g)), float(g.y.mean())

def conclusion(delta, key="delta_ap"):
    if delta[key+"_low"]>0: return "SUPPORTED"
    if delta[key+"_high"]<0: return "NOT_SUPPORTED"
    return "INCONCLUSIVE"

def segment_metrics(test,p,model_name):
    rows=[]
    for col in ["search_sector","search_modality","user_type"]:
        for val,g in test.assign(_p=p).groupby(col):
            if len(g)<100 or g.visit.nunique()<2: continue
            m=metrics(g.visit,g._p)
            rows.append({"model":model_name,"segment":col,"value":val,"n":len(g),**m})
    return rows

def power_rows(p0):
    nd=NormalDist(); z1=nd.inv_cdf(.975); z2=nd.inv_cdf(.80)
    rows=[]
    for mde in [.01,.015,.02,.025,.03]:
        p1=min(.999,p0+mde); pbar=(p0+p1)/2
        n=((z1*math.sqrt(2*pbar*(1-pbar))+z2*math.sqrt(p0*(1-p0)+p1*(1-p1)))**2)/(mde**2)
        rows.append({"baseline_rate":p0,"absolute_mde":mde,"relative_lift":p1/p0-1,
                     "n_per_arm":int(math.ceil(n)),"total_n":int(math.ceil(2*n))})
    return pd.DataFrame(rows)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    leads,spots,attrs,iq,av,market=load()
    quality,asof=audit_data(leads,spots,attrs,iq,av,market)
    if quality["critical_failures"]>0:
        (OUT/"FAILED_DATA_QUALITY_GATE.txt").write_text(jdump(quality),encoding="utf-8")
        raise RuntimeError(f"Critical data-quality failures: {quality['critical_failures']}")

    parent=json.loads((PARENT/"summary.json").read_text())
    profile_cutoff=pd.Timestamp(parent["profile_cutoff"])
    test_cutoff=pd.Timestamp(parent["test_cutoff"])
    la=pd.read_csv(PARENT/"lead_assignments.csv")
    sa=pd.read_csv(PARENT/"spot_assignments.csv")
    ba=pd.read_csv(PARENT/"broker_assignments.csv")

    sx=spots.merge(attrs,on="spot_id",how="left",validate="one_to_one")
    sx["amenities_count"]=sx.amenities.fillna("[]").astype(str).str.count(",")+(~sx.amenities.fillna("[]").astype(str).eq("[]")).astype(int)
    ref=sx[sx.created_at<profile_cutoff].copy()
    physical_cat=["sector_name","type_name","modality","natural_light","security_type","building_status","floor_material"]
    physical_num=["area_sqm","luminaires","charging_ports","floor_level","elevators","vertical_height_m","parking_spaces","amenities_count"]
    location_cat=["state","municipality","settlement","corridor","region"]
    location_num=["lat","lon"]

    rid,aid,pbench=select_clusterer(ref,sx,physical_cat,physical_num,"PH")
    ref["physical_profile"]=rid; sx["physical_profile"]=aid
    rid,aid,lbench=select_clusterer(ref,sx,location_cat,location_num,"LOC")
    ref["location_profile"]=rid; sx["location_profile"]=aid
    bench=pd.concat([pbench,lbench],ignore_index=True)
    bench.to_csv(OUT/"spot_decomposition_clustering_benchmark.csv",index=False)
    selected=bench[bench.selected].copy()
    selected.to_csv(OUT/"spot_decomposition_selected.csv",index=False)
    notes=pd.concat([
        profile_notes(ref,"physical_profile",physical_cat,physical_num).assign(profile_family="physical"),
        profile_notes(ref,"location_profile",location_cat,location_num).assign(profile_family="location")
    ],ignore_index=True)
    notes.to_csv(OUT/"spot_decomposition_interpretability.csv",index=False)
    sx[["spot_id","broker_id","physical_profile","location_profile"]].to_csv(OUT/"spot_decomposed_assignments.csv",index=False)

    x=iq.merge(la,on="lead_id",how="left",validate="many_to_one")
    x=x.merge(leads[["lead_id","user_type","search_sector","search_modality"]],on="lead_id",how="left",validate="many_to_one")
    x=x.merge(sa,on="spot_id",how="left",validate="many_to_one")
    x=x.merge(sx[["spot_id","physical_profile","location_profile"]],on="spot_id",how="left",validate="many_to_one")
    x=x.merge(ba,on="broker_id",how="left",validate="many_to_one")
    avf=asof[["inquiry_id","snapshot_date","is_available","lag_days"]].copy()
    avf["available_flag"]=safe_bool(avf.is_available)
    avf["availability_state"]=np.where(avf.snapshot_date.isna(),"missing",np.where(avf.available_flag,"available","not_available"))
    avf["availability_lag_bucket"]=pd.cut(avf.lag_days,[-np.inf,7,30,90,np.inf],labels=["0-7d","8-30d","31-90d",">90d"]).astype(str)
    x=x.merge(avf[["inquiry_id","availability_state","availability_lag_bucket"]],on="inquiry_id",how="left",validate="one_to_one")
    x["visit"]=x.broker_response.eq("scheduled_visit").astype(int)
    assert not x[["persona_profile","need_profile","spot_profile","broker_profile","physical_profile","location_profile"]].isna().any().any()

    train=x[(x.inquiry_at>=profile_cutoff)&(x.inquiry_at<test_cutoff)].copy()
    test=x[x.inquiry_at>=test_cutoff].copy()
    common=["persona_profile","need_profile","broker_profile","availability_state","availability_lag_bucket"]
    e6a=common+["spot_profile"]
    e6b=common+["physical_profile","location_profile"]
    p6a=fit_score(train,test,e6a); p6b=fit_score(train,test,e6b)

    e7a=e6b
    def add_interactions(df):
        z=df.copy()
        z["persona_x_need"]=z.persona_profile.astype(str)+"x"+z.need_profile.astype(str)
        z["need_x_physical"]=z.need_profile.astype(str)+"x"+z.physical_profile.astype(str)
        z["need_x_location"]=z.need_profile.astype(str)+"x"+z.location_profile.astype(str)
        z["need_x_broker"]=z.need_profile.astype(str)+"x"+z.broker_profile.astype(str)
        z["physical_x_broker"]=z.physical_profile.astype(str)+"x"+z.broker_profile.astype(str)
        z["need_x_physical_x_broker"]=z.need_profile.astype(str)+"x"+z.physical_profile.astype(str)+"x"+z.broker_profile.astype(str)
        return z
    train_i=add_interactions(train); test_i=add_interactions(test)
    interaction_cols=["persona_x_need","need_x_physical","need_x_location","need_x_broker","physical_x_broker","need_x_physical_x_broker"]
    p7a=fit_score(train_i,test_i,e7a); p7b=fit_score(train_i,test_i,e7a+interaction_cols)

    model_rows=[]
    for name,p in [("E006_A_unified_spot",p6a),("E006_B_physical_plus_location",p6b),
                   ("E007_A_marginals",p7a),("E007_B_compatibility_interactions",p7b)]:
        lm,nlead,lrate=lead_metrics(test,p)
        model_rows.append({"model":name,**metrics(test.visit,p),
                           "lead_level_ap":lm["average_precision"],"lead_level_auc":lm["roc_auc"],
                           "lead_level_n":nlead,"lead_level_visit_rate":lrate})
    model_df=pd.DataFrame(model_rows); model_df.to_csv(OUT/"model_metrics.csv",index=False)
    d6=cluster_bootstrap(test,p6a,p6b); d7=cluster_bootstrap(test,p7a,p7b)
    boot=pd.DataFrame([{"comparison":"E006_B_vs_A",**d6},{"comparison":"E007_B_vs_A",**d7}])
    boot.to_csv(OUT/"bootstrap_deltas.csv",index=False)
    seg=pd.DataFrame(segment_metrics(test,p6a,"E006_A")+segment_metrics(test,p6b,"E006_B")+
                     segment_metrics(test,p7a,"E007_A")+segment_metrics(test,p7b,"E007_B"))
    seg.to_csv(OUT/"segment_metrics.csv",index=False)

    # Supported cells are estimated ONLY on untouched future test and shrunk toward global rate.
    global_rate=float(test.visit.mean()); cells=[]
    for cols,label in [
        (["need_profile","physical_profile"],"need_x_physical"),
        (["need_profile","location_profile"],"need_x_location"),
        (["need_profile","broker_profile"],"need_x_broker"),
        (["physical_profile","broker_profile"],"physical_x_broker"),
        (["need_profile","physical_profile","broker_profile"],"need_x_physical_x_broker"),
    ]:
        for keys,g in test.groupby(cols):
            if len(g)<MIN_CELL: continue
            if not isinstance(keys,tuple): keys=(keys,)
            k=int(g.visit.sum()); n=len(g); smooth=(k+30*global_rate)/(n+30)
            row={"interaction":label,"n":n,"visit_rate":k/n,"smoothed_rate":smooth,"lift_vs_global":smooth/global_rate}
            row.update(dict(zip(cols,keys))); cells.append(row)
    cell_df=pd.DataFrame(cells).sort_values(["lift_vs_global","n"],ascending=[False,False]) if cells else pd.DataFrame()
    cell_df.to_csv(OUT/"compatibility_cells_future_test.csv",index=False)

    _,nlead,lead_rate=lead_metrics(test,p6a)
    power=power_rows(lead_rate); power.to_csv(OUT/"power_analysis.csv",index=False)
    protocols={
        "E006_online_ab":{
            "status":"PRE_REGISTERED_NOT_RUN","randomization_unit":"lead_id","allocation":"50/50 sticky",
            "stratification":["search_sector","search_modality","user_type"],
            "control":"Current routing/ranking using unified Spot profile plus identical common features.",
            "treatment":"Replace unified Spot profile with Physical Space Archetype + Location Profile.",
            "exposure":"First eligible ranking/routing served after assignment; lead remains in arm for 30 days.",
            "primary_outcome":"lead-level any scheduled_visit within 30 days of first exposure",
            "secondary_outcomes":["lead-level any accepted_or_scheduled response","time_to_first_positive_response","fallback_use_rate if instrumented"],
            "guardrails":["sample_ratio_mismatch","eligibility_violations","availability_asof_coverage","availability_snapshot_lag","unavailable_spot_recommendation_rate","broker_workload_concentration","no_result_rate"],
            "analysis":"Intention-to-treat at lead level; fixed 30-day horizon; two-sided alpha=0.05; 95% CI; no peeking/optional stopping.",
            "power_reference":power.to_dict("records")
        },
        "E007_online_ab":{
            "status":"PRE_REGISTERED_NOT_RUN","randomization_unit":"lead_id","allocation":"50/50 sticky",
            "stratification":["search_sector","search_modality","user_type"],
            "control":"E006 treatment representation used only as marginal effects.",
            "treatment":"Same marginal profiles plus pre-specified regularized compatibility interactions.",
            "exposure":"First eligible routing decision after assignment; lead remains in arm for 30 days.",
            "primary_outcome":"lead-level any scheduled_visit within 30 days of first exposure",
            "secondary_outcomes":["positive_response_rate","time_to_first_positive_response","fallback_use_rate if instrumented"],
            "guardrails":["sample_ratio_mismatch","eligibility_violations","availability_asof_coverage","unavailable_spot_recommendation_rate","broker_workload_concentration","no_result_rate"],
            "analysis":"Intention-to-treat at lead level; fixed horizon; alpha=0.05; 95% CI; multiplicity only for secondary metrics; no causal claim from offline backtest.",
            "power_reference":power.to_dict("records")
        }
    }
    (OUT/"online_ab_protocols.json").write_text(jdump(protocols),encoding="utf-8")

    m6=model_df.set_index("model"); c6=conclusion(d6); c7=conclusion(d7)
    r6={
        "experiment_id":"E006_physical_location_spot",
        "metrics":{k:float(v) for k,v in m6.loc["E006_B_physical_plus_location"].items() if isinstance(v,(int,float,np.number))},
        "segment_metrics":seg[seg.model.eq("E006_B")].to_dict("records"),
        "conclusion":c6,
        "caveats":["Offline A/B is a temporal backtest, not randomized causal evidence.","scheduled_visit is a proxy, not a true sale.","Market context is audited but excluded because publication timing is unknown."],
        "next_experiment":"E007_compatibility_routing"
    }
    r7={
        "experiment_id":"E007_compatibility_routing",
        "metrics":{k:float(v) for k,v in m6.loc["E007_B_compatibility_interactions"].items() if isinstance(v,(int,float,np.number))},
        "segment_metrics":seg[seg.model.eq("E007_B")].to_dict("records"),
        "conclusion":c7,
        "caveats":["Offline interaction lift is associative, not causal.","Cells are shrunk and require minimum support, but multiple exploratory cells are still hypothesis-generating.","Online randomized routing is required before production causal claims."],
        "next_experiment":"Run the pre-registered online A/B if operational instrumentation is available."
    }
    (OUT/"E006_physical_location_spot_results.json").write_text(jdump(r6),encoding="utf-8")
    (OUT/"E007_compatibility_routing_results.json").write_text(jdump(r7),encoding="utf-8")

    report=f"""# Matching A/B v3 — relational audit + two governed experiments

## Executive result

Data-quality gate: **PASS** with {quality['critical_failures']} critical failures.
The suite audited all six candidate tables before fitting any model and used cross-table joins, temporal checks, business rules and point-in-time availability.

- E006 conclusion: **{c6}**. Delta AP B−A {d6['delta_ap']:+.4f} (95% cluster-bootstrap CI {d6['delta_ap_low']:+.4f} to {d6['delta_ap_high']:+.4f}).
- E007 conclusion: **{c7}**. Delta AP B−A {d7['delta_ap']:+.4f} (95% cluster-bootstrap CI {d7['delta_ap_low']:+.4f} to {d7['delta_ap_high']:+.4f}).

The offline comparisons are **pre-experiment evidence only**. A causal A/B requires the randomized lead-level protocols saved in results/online_ab_protocols.json.

## Relational/data audit

- Leads: {len(leads):,}; Spots: {len(spots):,}; Spot attributes: {len(attrs):,}; Inquiries: {len(iq):,}; Availability snapshots: {len(av):,}; Market-context rows: {len(market):,}.
- Availability backward-as-of coverage: {quality['availability_coverage']:.1%}; coverage with lag <=90d: {quality['availability_lag90']:.1%}.
- Exact same-month market-context coverage at Spot geography/sector grain: {quality['market_exact_coverage']:.1%}. It is **not used** as a historical feature because publication semantics are unknown.
- Actual inquiry lead↔spot modality compatibility: {quality['modality_match']:.1%}; sector exact match: {quality['sector_match']:.1%}; preferred municipality exact match: {quality['municipality_match']:.1%}; declared corridor exact match: {quality['corridor_match']:.1%}.

See relationship_checks.csv, content_consistency_checks.csv and column_completeness.csv for the full evidence rather than relying on a dry single-table profile.

## Spot decomposition

{selected.to_markdown(index=False)}

### Interpretable profiles

{notes.to_markdown(index=False)}

## Offline A/B metrics

{model_df.to_markdown(index=False)}

## Paired uncertainty

Bootstrap resamples **lead_id clusters**, not individual inquiries, preserving within-lead dependence.

{boot.to_markdown(index=False)}

## Compatibility cells

{cell_df.head(15).to_markdown(index=False) if len(cell_df) else "_No future-test cells passed minimum support._"}

## Complete online A/B design

Both experiments are pre-registered as 50/50 sticky lead-level randomized tests, stratified by sector, modality and lead type. Primary analysis is ITT after a fixed 30-day maturation window.

### Power

Baseline future lead-level rate: {lead_rate:.1%}; unique future-test leads: {nlead:,}.

{power.to_markdown(index=False)}

## Interpretation rules

1. No offline result is called causal.
2. E006 changes only the Spot representation between A and B; common availability features are identical.
3. E007 changes only the interaction terms between A and B.
4. Availability is joined with the latest snapshot_date <= inquiry_at.
5. Market Context is audited but excluded until publication/effective-time semantics are defensible.
6. scheduled_visit is commercial-progress proxy, not hidden true conversion/sale.
"""
    (HERE/"README.md").write_text(report,encoding="utf-8")
    print(report)

if __name__=="__main__":
    main()
