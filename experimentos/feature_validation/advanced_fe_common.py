from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from semantic_recovery_common import (
    TARGET,
    fit_predict,
    load_abt,
    metric_bundle,
    prepare_variant,
    stage_base_features,
)

SEED=42

FREQ_CAT_T0=[
    "source","industry","search_sector","search_modality",
    "preferred_state","preferred_municipality","preferred_corridor",
    "user_type","company_size",
]
FREQ_CAT_T1=FREQ_CAT_T0+[
    "channel","spot_sector_name","spot_type_name","spot_state",
    "spot_municipality","spot_corridor","spot_region","spot_modality",
]
BIN_NUM_T0=[
    "target_area_sqm","min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly",
    "min_budget_mxn_sale_total","max_budget_mxn_sale_total","prior_inquiries",
]
BIN_NUM_T1=BIN_NUM_T0+[
    "message_length","requested_area_sqm","requested_budget_mxn_rent_monthly",
    "requested_budget_mxn_sale_total","urgency_days","spot_area_sqm",
    "spot_price_sqm_mxn_rent","spot_price_sqm_mxn_sale",
    "spot_price_total_mxn_rent","spot_price_total_mxn_sale",
]

def missingness_features(df:pd.DataFrame,stage:str):
    z=df.copy(); nums=[]; cats=[]
    base=BIN_NUM_T0+FREQ_CAT_T0
    if stage=="T1_first_inquiry":
        base=BIN_NUM_T1+FREQ_CAT_T1
    base=[c for c in dict.fromkeys(base) if c in z]
    z["afe_missing_count"]=z[base].isna().sum(axis=1).astype(float)
    z["afe_missing_fraction"]=z[base].isna().mean(axis=1).astype(float)
    nums += ["afe_missing_count","afe_missing_fraction"]

    z["afe_budget_presence_pattern"]=(
        z["min_budget_mxn_rent_monthly"].notna().astype(int).astype(str)
        +z["max_budget_mxn_rent_monthly"].notna().astype(int).astype(str)
        +z["min_budget_mxn_sale_total"].notna().astype(int).astype(str)
        +z["max_budget_mxn_sale_total"].notna().astype(int).astype(str)
    )
    z["afe_geo_presence_pattern"]=(
        z["preferred_state"].notna().astype(int).astype(str)
        +z["preferred_municipality"].notna().astype(int).astype(str)
        +z["preferred_corridor"].notna().astype(int).astype(str)
    )
    cats += ["afe_budget_presence_pattern","afe_geo_presence_pattern"]
    if stage=="T1_first_inquiry":
        z["afe_request_presence_pattern"]=(
            z["requested_area_sqm"].notna().astype(int).astype(str)
            +z["requested_budget_mxn_rent_monthly"].notna().astype(int).astype(str)
            +z["requested_budget_mxn_sale_total"].notna().astype(int).astype(str)
            +z["urgency_days"].notna().astype(int).astype(str)
        )
        cats.append("afe_request_presence_pattern")
    return z,cats,nums

@dataclass
class FrequencyEncoder:
    columns:list[str]
    maps:dict[str,dict]|None=None

    def fit(self,df:pd.DataFrame):
        self.maps={}
        n=max(len(df),1)
        for c in self.columns:
            s=df[c].astype("string").fillna("__MISSING__")
            self.maps[c]=(s.value_counts(dropna=False)/n).to_dict()
        return self

    def transform(self,df:pd.DataFrame):
        assert self.maps is not None
        z=df.copy(); nums=[]
        for c,m in self.maps.items():
            out=f"afe_freq_{c}"
            s=z[c].astype("string").fillna("__MISSING__")
            z[out]=s.map(m).fillna(0.0).astype(float)
            nums.append(out)
        return z,[],nums

@dataclass
class QuantileBinner:
    columns:list[str]
    edges:dict[str,list[float]]|None=None

    def fit(self,df:pd.DataFrame):
        self.edges={}
        for c in self.columns:
            s=pd.to_numeric(df[c],errors="coerce").dropna()
            if len(s)<20: continue
            e=np.unique(np.quantile(s,[0,.2,.4,.6,.8,1.0]))
            if len(e)>=3:
                e=e.astype(float); e[0]=-np.inf; e[-1]=np.inf
                self.edges[c]=e.tolist()
        return self

    def transform(self,df:pd.DataFrame):
        assert self.edges is not None
        z=df.copy(); cats=[]
        for c,e in self.edges.items():
            out=f"afe_bin_{c}"
            z[out]=pd.cut(pd.to_numeric(z[c],errors="coerce"),bins=np.asarray(e,float),include_lowest=True).astype("string").fillna("missing")
            cats.append(out)
        return z,cats,[]

@dataclass
class InventoryReference:
    stage:str
    stats:pd.DataFrame|None=None
    global_stats:dict|None=None
    municipality_centroids:pd.DataFrame|None=None
    corridor_centroids:pd.DataFrame|None=None

    def fit(self,df:pd.DataFrame):
        if self.stage!="T1_first_inquiry":
            return self
        unique=df.dropna(subset=["spot_id"]).drop_duplicates("spot_id").copy()
        measures=[
            "spot_area_sqm","spot_price_sqm_mxn_rent","spot_price_sqm_mxn_sale",
            "spot_price_total_mxn_rent","spot_price_total_mxn_sale",
        ]
        self.global_stats={c:float(pd.to_numeric(unique[c],errors="coerce").median()) for c in measures}
        self.stats=unique.groupby(["spot_sector_name","spot_region","spot_modality"],dropna=False)[measures].median().reset_index()
        self.municipality_centroids=unique.groupby("spot_municipality")[["spot_lat","spot_lon"]].median().reset_index().rename(columns={"spot_lat":"pref_muni_lat","spot_lon":"pref_muni_lon"})
        self.corridor_centroids=unique.groupby("spot_corridor")[["spot_lat","spot_lon"]].median().reset_index().rename(columns={"spot_lat":"pref_corr_lat","spot_lon":"pref_corr_lon"})
        return self

    def transform(self,df:pd.DataFrame):
        z=df.copy(); nums=[]
        if self.stage!="T1_first_inquiry" or self.stats is None:
            return z,[],nums
        z=z.merge(self.stats,on=["spot_sector_name","spot_region","spot_modality"],how="left",suffixes=("","_ref"))
        for c,g in self.global_stats.items():
            ref=f"{c}_ref"
            z[ref]=pd.to_numeric(z[ref],errors="coerce").fillna(g)
            out=f"afe_rel_{c}"
            z[out]=np.log((pd.to_numeric(z[c],errors="coerce").clip(lower=0)+1)/(z[ref].clip(lower=0)+1))
            nums.append(out)
        z=z.merge(self.municipality_centroids,left_on="preferred_municipality",right_on="spot_municipality",how="left",suffixes=("","_pref_muni"))
        z=z.merge(self.corridor_centroids,left_on="preferred_corridor",right_on="spot_corridor",how="left",suffixes=("","_pref_corr"))

        def hav(lat1,lon1,lat2,lon2):
            a1=np.radians(pd.to_numeric(lat1,errors="coerce"))
            o1=np.radians(pd.to_numeric(lon1,errors="coerce"))
            a2=np.radians(pd.to_numeric(lat2,errors="coerce"))
            o2=np.radians(pd.to_numeric(lon2,errors="coerce"))
            da=a2-a1; do=o2-o1
            h=np.sin(da/2)**2+np.cos(a1)*np.cos(a2)*np.sin(do/2)**2
            return 6371*2*np.arcsin(np.sqrt(h.clip(0,1)))
        z["afe_distance_pref_municipality_km"]=hav(z["spot_lat"],z["spot_lon"],z["pref_muni_lat"],z["pref_muni_lon"])
        z["afe_distance_pref_corridor_km"]=hav(z["spot_lat"],z["spot_lon"],z["pref_corr_lat"],z["pref_corr_lon"])
        z["afe_distance_pref_best_km"]=pd.concat([
            z["afe_distance_pref_municipality_km"],z["afe_distance_pref_corridor_km"]
        ],axis=1).min(axis=1,skipna=True)
        nums += ["afe_distance_pref_municipality_km","afe_distance_pref_corridor_km","afe_distance_pref_best_km"]
        return z,[],nums

def apply_advanced(train:pd.DataFrame,other:pd.DataFrame,stage:str,variant:str):
    # Atomic baseline from governed E030.
    tr=train.copy(); ot=other.copy()
    cats,nums=stage_base_features(tr,stage)
    if variant=="atomic":
        return tr,ot,cats,nums

    tr,c1,n1=missingness_features(tr,stage); ot,_,_=missingness_features(ot,stage)
    cats+=c1; nums+=n1
    freq_cols=[c for c in (FREQ_CAT_T0 if stage=="T0_cold" else FREQ_CAT_T1) if c in tr]
    fe=FrequencyEncoder(freq_cols).fit(tr)
    tr,c2,n2=fe.transform(tr); ot,_,_=fe.transform(ot)
    cats+=c2; nums+=n2
    if variant=="missingness_frequency":
        return tr,ot,cats,nums

    bin_cols=[c for c in (BIN_NUM_T0 if stage=="T0_cold" else BIN_NUM_T1) if c in tr]
    qb=QuantileBinner(bin_cols).fit(tr)
    tr,c3,n3=qb.transform(tr); ot,_,_=qb.transform(ot)
    cats+=c3; nums+=n3
    if variant=="robust_bins":
        return tr,ot,cats,nums

    inv=InventoryReference(stage).fit(tr)
    tr,c4,n4=inv.transform(tr); ot,_,_=inv.transform(ot)
    cats+=c4; nums+=n4
    if variant=="geo_inventory_relative":
        return tr,ot,cats,nums

    # combined_v2 adds selected first-wave continuous semantic representation,
    # but deliberately does NOT add the soft clusters/interactions that failed.
    tr2,ot2,base_cats,base_nums=prepare_variant(train,other,stage,"semantic_need")
    # Merge only FE columns from semantic_need onto advanced frames by index.
    extra_c=[c for c in base_cats if c.startswith("fe_")]
    extra_n=[c for c in base_nums if c.startswith("fe_")]
    for c in extra_c+extra_n:
        tr[c]=tr2[c].values
        ot[c]=ot2[c].values
    cats+=extra_c; nums+=extra_n
    cats=list(dict.fromkeys(cats)); nums=list(dict.fromkeys(nums))
    return tr,ot,cats,nums

def rolling_folds(stage_df:pd.DataFrame):
    lead_dates=stage_df[["lead_id","created_at"]].drop_duplicates("lead_id").sort_values(["created_at","lead_id"]).reset_index(drop=True)
    n=len(lead_dates)
    cuts=[(.45,.60),(.60,.75),(.75,1.0)]
    for i,(a,b) in enumerate(cuts,1):
        ia=max(20,int(n*a)); ib=max(ia+20,min(n,int(n*b)))
        train_leads=set(lead_dates.iloc[:ia].lead_id)
        eval_leads=set(lead_dates.iloc[ia:ib].lead_id)
        tr=stage_df[stage_df.lead_id.isin(train_leads)].copy()
        ev=stage_df[stage_df.lead_id.isin(eval_leads)].copy()
        yield i,tr,ev

def eval_variant(stage_df:pd.DataFrame,stage:str,variant:str):
    rows=[]
    for fold,tr,ev in rolling_folds(stage_df):
        a,b,cats,nums=apply_advanced(tr,ev,stage,variant)
        p=fit_predict(a,b,cats,nums)
        rows.append({"fold":fold,"variant":variant,"stage":stage,"n_cat":len(cats),"n_num":len(nums),**metric_bundle(b[TARGET],p)})
    return rows
