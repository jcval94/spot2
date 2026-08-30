from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from advanced_fe_common import (
    FrequencyEncoder,
    FREQ_CAT_T1,
    InventoryReference,
    rolling_folds,
)
from semantic_recovery_common import (
    TARGET,
    fit_predict,
    load_abt,
    metric_bundle,
    stage_base_features,
)

HERE=Path(__file__).resolve().parent
E036=HERE/"E036_t1_geo_inventory_decomposition"/"results"
E037=HERE/"E037_temporal_smoothed_categorical_priors"/"results"
E036.mkdir(parents=True,exist_ok=True)
E037.mkdir(parents=True,exist_ok=True)

def write_json(path:Path,x:object):
    path.write_text(json.dumps(x,indent=2,ensure_ascii=False,default=str)+"\n",encoding="utf-8")

def summarize(rows:list[dict])->pd.DataFrame:
    df=pd.DataFrame(rows)
    out=[]
    for (stage,var),g in df.groupby(["stage","variant"]):
        out.append({
            "stage":stage,"variant":var,"folds":int(g.fold.nunique()),
            "mean_auc":g.roc_auc.mean(),"min_auc":g.roc_auc.min(),
            "mean_ap_over_prevalence":g.ap_over_prevalence.mean(),
            "min_ap_over_prevalence":g.ap_over_prevalence.min(),
            "mean_lift10":g.lift_top_10pct.mean(),"min_lift10":g.lift_top_10pct.min(),
            "folds_auc_gt_05":int((g.roc_auc>.5).sum()),
        })
    return pd.DataFrame(out)

def dev_status(r)->str:
    if r.mean_auc>=.52 and r.mean_ap_over_prevalence>=1.03 and r.min_lift10>=1.0 and r.folds_auc_gt_05>=2:
        return "ROBUST_DEV_SIGNAL"
    if r.mean_auc>.50 and r.mean_ap_over_prevalence>=1.01:
        return "WEAK_DEV_SIGNAL"
    return "NO_DEV_SIGNAL"

def e036_variant(tr:pd.DataFrame,ev:pd.DataFrame,variant:str):
    cats,nums=stage_base_features(tr,"T1_first_inquiry")
    if variant=="atomic":
        return tr.copy(),ev.copy(),cats,nums

    inv=InventoryReference("T1_first_inquiry").fit(tr)
    a,_,all_num=inv.transform(tr)
    b,_,_=inv.transform(ev)
    inv_cols=[c for c in all_num if c.startswith("afe_rel_")]
    geo_cols=[c for c in all_num if c.startswith("afe_distance_")]

    if variant=="inventory_relative":
        nums+=inv_cols
    elif variant=="geo_distance":
        nums+=geo_cols
    elif variant=="inventory_plus_geo":
        nums+=inv_cols+geo_cols
    elif variant=="inventory_geo_frequency":
        nums+=inv_cols+geo_cols
        freq=FrequencyEncoder([c for c in FREQ_CAT_T1 if c in a]).fit(a)
        a,_,fnum=freq.transform(a); b,_,_=freq.transform(b)
        nums+=fnum
    else:
        raise ValueError(variant)
    return a,b,cats,list(dict.fromkeys(nums))

def run_e036(dev:pd.DataFrame):
    stage="T1_first_inquiry"
    d=dev[dev.stage.eq(stage)].copy()
    variants=["atomic","inventory_relative","geo_distance","inventory_plus_geo","inventory_geo_frequency"]
    rows=[]
    for fold,tr,ev in rolling_folds(d):
        for variant in variants:
            a,b,cats,nums=e036_variant(tr,ev,variant)
            p=fit_predict(a,b,cats,nums)
            rows.append({"fold":fold,"stage":stage,"variant":variant,"n_cat":len(cats),"n_num":len(nums),**metric_bundle(b[TARGET],p)})
    raw=pd.DataFrame(rows); raw.to_csv(E036/"fold_metrics.csv",index=False)
    s=summarize(rows); s["status"]=s.apply(dev_status,axis=1); s.to_csv(E036/"summary.csv",index=False)
    best=s.sort_values(["mean_ap_over_prevalence","mean_lift10","mean_auc"],ascending=False).iloc[0].to_dict()
    write_json(E036/"selected.json",best)
    (E036/"REPORT.md").write_text(
        "# E036 — T1 geo/inventory decomposition\n\n**Development only.**\n\n"
        +s.to_markdown(index=False)
        +f"\n\nSelected exploratory component: **{best['variant']}** ({best['status']}).\n",
        encoding="utf-8"
    )
    return best

class TemporalTargetEncoder:
    def __init__(self,cols:list[str],alpha:float=50.0):
        self.cols=cols; self.alpha=alpha; self.global_rate=0.0; self.maps={}

    def fit(self,df:pd.DataFrame):
        y=df[TARGET].astype(float)
        self.global_rate=float(y.mean())
        self.maps={}
        for c in self.cols:
            key=df[c].astype("string").fillna("__MISSING__")
            g=pd.DataFrame({"k":key,"y":y}).groupby("k").y.agg(["sum","count"])
            rate=(g["sum"]+self.alpha*self.global_rate)/(g["count"]+self.alpha)
            self.maps[c]=pd.DataFrame({
                "centered":rate-self.global_rate,
                "support":g["count"],
            }).to_dict("index")
        return self

    def transform(self,df:pd.DataFrame):
        z=df.copy(); nums=[]
        for c,m in self.maps.items():
            key=z[c].astype("string").fillna("__MISSING__")
            enc=f"te_centered_{c}"; sup=f"te_log_support_{c}"
            z[enc]=key.map(lambda x:m.get(x,{"centered":0.0})["centered"]).astype(float)
            z[sup]=np.log1p(key.map(lambda x:m.get(x,{"support":0})["support"]).astype(float))
            nums += [enc,sup]
        return z,nums

def add_composites(df:pd.DataFrame,stage:str):
    z=df.copy()
    pairs={
        "tekey_source_sector":["source","search_sector"],
        "tekey_industry_modality":["industry","search_modality"],
        "tekey_prefmuni_sector":["preferred_municipality","search_sector"],
    }
    if stage=="T1_first_inquiry":
        pairs.update({
            "tekey_channel_visit":["channel","asked_visit"],
            "tekey_sector_match":["search_sector","spot_sector_name"],
            "tekey_modality_match":["search_modality","spot_modality"],
            "tekey_municipality_pair":["preferred_municipality","spot_municipality"],
        })
    for name,cols in pairs.items():
        z[name]=z[cols].astype("string").fillna("__MISSING__").agg("×".join,axis=1)
    return z,list(pairs)

def te_cols(stage:str):
    base=[
        "source","user_type","company_size","industry","search_sector","search_modality",
        "preferred_state","preferred_municipality","preferred_corridor",
    ]
    if stage=="T1_first_inquiry":
        base+=["channel","asked_visit","spot_sector_name","spot_type_name","spot_state",
               "spot_municipality","spot_corridor","spot_region","spot_modality"]
    return base

def e037_variant(tr:pd.DataFrame,ev:pd.DataFrame,stage:str,variant:str):
    a=tr.copy(); b=ev.copy(); cats,nums=stage_base_features(a,stage)
    if variant=="atomic":
        return a,b,cats,nums

    cols=[c for c in te_cols(stage) if c in a]
    if variant=="te_interactions":
        a,comp=add_composites(a,stage); b,_=add_composites(b,stage); cols+=comp
    enc=TemporalTargetEncoder(cols,alpha=50.0).fit(a)
    a,new=enc.transform(a); b,_=enc.transform(b)
    nums+=new
    return a,b,cats,list(dict.fromkeys(nums))

def run_e037(dev:pd.DataFrame):
    rows=[]
    for stage in ["T0_cold","T1_first_inquiry"]:
        d=dev[dev.stage.eq(stage)].copy()
        for fold,tr,ev in rolling_folds(d):
            for variant in ["atomic","te_marginals","te_interactions"]:
                a,b,cats,nums=e037_variant(tr,ev,stage,variant)
                p=fit_predict(a,b,cats,nums)
                rows.append({"fold":fold,"stage":stage,"variant":variant,"n_cat":len(cats),"n_num":len(nums),**metric_bundle(b[TARGET],p)})
    raw=pd.DataFrame(rows); raw.to_csv(E037/"fold_metrics.csv",index=False)
    s=summarize(rows); s["status"]=s.apply(dev_status,axis=1); s.to_csv(E037/"summary.csv",index=False)
    selected={}
    for stage,g in s.groupby("stage"):
        best=g.sort_values(["mean_ap_over_prevalence","mean_lift10","mean_auc"],ascending=False).iloc[0].to_dict()
        selected[stage]=best
    write_json(E037/"selected.json",selected)
    report="# E037 — Temporal smoothed categorical priors\n\n**Development only; target encoding is fit strictly on prior fold train.**\n\n"
    report+=s.to_markdown(index=False)
    for stage,x in selected.items():
        report+=f"\n- {stage}: **{x['variant']}** — {x['status']}.\n"
    (E037/"REPORT.md").write_text(report,encoding="utf-8")
    return selected

def main():
    abt=load_abt()
    dev=abt[abt.split.eq("train")].copy()
    e036=run_e036(dev)
    e037=run_e037(dev)
    print(json.dumps({"E036":e036,"E037":e037},indent=2,ensure_ascii=False,default=str))

if __name__=="__main__":
    main()
