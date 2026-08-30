from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
FV = ROOT / "experimentos" / "feature_validation"
E030 = FV / "E030_definitive_abt"
POLICY = json.loads(
    (FV / "E029_drift_sanitized_release_candidate" / "results" / "feature_policy.json")
    .read_text(encoding="utf-8")
)
TARGET = "target_scheduled_visit_30d"
SEED = 42
BOOT = 500

BASE_CAT = list(POLICY["categorical_features"])
BASE_NUM = list(POLICY["numeric_features"])

T0_ALLOWED_PREFIX = {
    "user_type","company_size","industry","search_sector","search_modality",
    "preferred_state","preferred_municipality","preferred_corridor","source",
    "target_area_sqm","min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly",
    "min_budget_mxn_sale_total","max_budget_mxn_sale_total","prior_inquiries",
    "has_converted_before",
}

VARIANTS = [
    "atomic",
    "scale_specificity",
    "semantic_need",
    "soft_profiles",
    "semantic_interactions",
]


def load_abt() -> pd.DataFrame:
    p = E030 / "results" / "abt_model_ready.csv.gz"
    x = pd.read_csv(p)
    for c in ["score_time", "created_at"]:
        x[c] = pd.to_datetime(x[c], format="mixed", errors="raise")
    return x


def safe_log1p(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    return np.log1p(x.clip(lower=0))


def safe_log_ratio(a: pd.Series, b: pd.Series) -> pd.Series:
    x = pd.to_numeric(a, errors="coerce")
    y = pd.to_numeric(b, errors="coerce")
    return np.log((x.clip(lower=0) + 1.0) / (y.clip(lower=0) + 1.0))


def bool_num(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        return pd.to_numeric(s, errors="coerce")
    return s.astype(str).str.lower().isin(["true","1","yes"]).astype(float)


def add_scale_specificity(df: pd.DataFrame) -> tuple[pd.DataFrame,list[str],list[str]]:
    z = df.copy()
    nums: list[str] = []
    cats: list[str] = []

    for src, dst in [
        ("target_area_sqm","fe_log_target_area"),
        ("prior_inquiries","fe_log_prior_inquiries"),
        ("message_length","fe_log_message_length"),
        ("urgency_days","fe_log_urgency"),
        ("requested_area_sqm","fe_log_requested_area"),
        ("requested_budget_mxn_rent_monthly","fe_log_requested_rent_budget"),
        ("requested_budget_mxn_sale_total","fe_log_requested_sale_budget"),
        ("spot_area_sqm","fe_log_spot_area"),
        ("spot_price_total_mxn_rent","fe_log_spot_rent_total"),
        ("spot_price_total_mxn_sale","fe_log_spot_sale_total"),
    ]:
        if src in z:
            z[dst] = safe_log1p(z[src]); nums.append(dst)

    for pfx, lo, hi in [
        ("rent","min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly"),
        ("sale","min_budget_mxn_sale_total","max_budget_mxn_sale_total"),
    ]:
        a = pd.to_numeric(z[lo], errors="coerce")
        b = pd.to_numeric(z[hi], errors="coerce")
        mid = (a + b) / 2
        width = (b - a).clip(lower=0)
        z[f"fe_{pfx}_budget_mid"] = mid
        z[f"fe_{pfx}_budget_width"] = width
        z[f"fe_{pfx}_budget_width_rel"] = width / (mid.abs() + 1)
        z[f"fe_log_{pfx}_budget_mid"] = np.log1p(mid.clip(lower=0))
        nums += [
            f"fe_{pfx}_budget_mid",f"fe_{pfx}_budget_width",
            f"fe_{pfx}_budget_width_rel",f"fe_log_{pfx}_budget_mid"
        ]

    geo = ["preferred_state","preferred_municipality","preferred_corridor"]
    z["fe_geo_specificity"] = sum(z[c].notna().astype(float) for c in geo)
    z["fe_search_completeness"] = (
        z["target_area_sqm"].notna().astype(float)
        + z["search_sector"].notna().astype(float)
        + z["search_modality"].notna().astype(float)
        + z["min_budget_mxn_rent_monthly"].notna().astype(float)
        + z["max_budget_mxn_rent_monthly"].notna().astype(float)
        + z["min_budget_mxn_sale_total"].notna().astype(float)
        + z["max_budget_mxn_sale_total"].notna().astype(float)
        + z["preferred_state"].notna().astype(float)
        + z["preferred_municipality"].notna().astype(float)
        + z["preferred_corridor"].notna().astype(float)
    )
    z["fe_history_maturity"] = (
        safe_log1p(z["prior_inquiries"]).fillna(0)
        + 1.5 * bool_num(z["has_converted_before"]).fillna(0)
    )
    nums += ["fe_geo_specificity","fe_search_completeness","fe_history_maturity"]

    if "requested_area_sqm" in z:
        z["fe_area_shift_log"] = safe_log_ratio(z["requested_area_sqm"],z["target_area_sqm"])
        z["fe_area_shift_abs"] = z["fe_area_shift_log"].abs()
        z["fe_area_expanded"] = (z["fe_area_shift_log"] > 0).astype(float)
        nums += ["fe_area_shift_log","fe_area_shift_abs","fe_area_expanded"]

    rent_mid = z.get("fe_rent_budget_mid")
    sale_mid = z.get("fe_sale_budget_mid")
    if rent_mid is not None:
        z["fe_rent_shift_log"] = safe_log_ratio(z["requested_budget_mxn_rent_monthly"], rent_mid)
        z["fe_rent_shift_abs"] = z["fe_rent_shift_log"].abs()
        z["fe_rent_budget_raised"] = (z["fe_rent_shift_log"] > 0).astype(float)
        nums += ["fe_rent_shift_log","fe_rent_shift_abs","fe_rent_budget_raised"]
    if sale_mid is not None:
        z["fe_sale_shift_log"] = safe_log_ratio(z["requested_budget_mxn_sale_total"], sale_mid)
        z["fe_sale_shift_abs"] = z["fe_sale_shift_log"].abs()
        z["fe_sale_budget_raised"] = (z["fe_sale_shift_log"] > 0).astype(float)
        nums += ["fe_sale_shift_log","fe_sale_shift_abs","fe_sale_budget_raised"]

    if "requested_to_spot_area_ratio" in z:
        r = pd.to_numeric(z["requested_to_spot_area_ratio"],errors="coerce")
        z["fe_area_fit_log_abs"] = np.log(r.clip(lower=1e-6)).abs()
        z["fe_area_within_20pct"] = r.between(.8,1.2).astype(float)
        nums += ["fe_area_fit_log_abs","fe_area_within_20pct"]
    for src,name in [
        ("rent_budget_to_price_ratio","rent"),
        ("sale_budget_to_price_ratio","sale"),
    ]:
        r = pd.to_numeric(z[src],errors="coerce")
        z[f"fe_{name}_fit_log"] = np.log(r.clip(lower=1e-6))
        z[f"fe_{name}_fit_log_abs"] = z[f"fe_{name}_fit_log"].abs()
        z[f"fe_{name}_within_budget"] = r.ge(1).astype(float)
        nums += [f"fe_{name}_fit_log",f"fe_{name}_fit_log_abs",f"fe_{name}_within_budget"]

    match_cols = ["same_preferred_municipality","same_preferred_corridor","same_sector","compatible_modality"]
    z["fe_match_depth"] = sum(
        z[c].astype(str).str.lower().isin(["true","1","yes"]).astype(float)
        for c in match_cols
    )
    nums.append("fe_match_depth")
    return z,cats,nums


def add_semantic_need(df: pd.DataFrame) -> tuple[pd.DataFrame,list[str],list[str]]:
    z = df.copy()
    cats: list[str] = []
    nums: list[str] = []
    sm = z["search_modality"].astype("string").fillna("missing").str.lower()
    z["fe_search_need"] = np.select(
        [sm.eq("rent"), sm.eq("sale"), sm.isin(["both","flexible"])],
        ["N_RENT","N_SALE","N_FLEX"],
        default="N_OTHER",
    )
    cats.append("fe_search_need")

    rent = z["requested_budget_mxn_rent_monthly"].notna()
    sale = z["requested_budget_mxn_sale_total"].notna()
    z["fe_request_modality"] = np.select(
        [rent & sale, rent, sale],
        ["both","rent","sale"],
        default="unspecified",
    )
    cats.append("fe_request_modality")
    z["fe_need_transition"] = z["fe_search_need"].astype(str) + "->" + z["fe_request_modality"].astype(str)
    cats.append("fe_need_transition")

    z["fe_source_x_user_type"] = z["source"].astype(str) + "×" + z["user_type"].astype(str)
    z["fe_industry_x_sector"] = z["industry"].astype(str) + "×" + z["search_sector"].astype(str)
    z["fe_need_x_company_size"] = z["fe_search_need"].astype(str) + "×" + z["company_size"].astype(str)
    cats += ["fe_source_x_user_type","fe_industry_x_sector","fe_need_x_company_size"]
    return z,cats,nums


@dataclass
class SoftCluster:
    cat_cols: list[str]
    num_cols: list[str]
    k: int
    prefix: str
    prep: ColumnTransformer | None = None
    model: KMeans | None = None
    remap: dict[int,int] | None = None

    def fit(self, df: pd.DataFrame) -> "SoftCluster":
        cat = Pipeline([
            ("imp",SimpleImputer(strategy="most_frequent")),
            ("oh",OneHotEncoder(handle_unknown="ignore",min_frequency=5,sparse_output=False,dtype=np.float32)),
        ])
        num = Pipeline([
            ("imp",SimpleImputer(strategy="median")),
            ("sc",StandardScaler()),
        ])
        self.prep = ColumnTransformer(
            [("cat",cat,self.cat_cols),("num",num,self.num_cols)],
            sparse_threshold=0.0,
        )
        X = np.asarray(self.prep.fit_transform(df[self.cat_cols+self.num_cols]),dtype=np.float32)
        self.model = KMeans(n_clusters=self.k,random_state=SEED,n_init=20)
        lab = self.model.fit_predict(X)
        order = pd.Series(lab).value_counts().index.tolist()
        self.remap = {int(raw):i+1 for i,raw in enumerate(order)}
        return self

    def transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame,list[str],list[str]]:
        assert self.prep is not None and self.model is not None and self.remap is not None
        X = np.asarray(self.prep.transform(df[self.cat_cols+self.num_cols]),dtype=np.float32)
        raw = self.model.predict(X)
        dist = self.model.transform(X)
        z = df.copy()
        z[f"{self.prefix}_profile"] = [f"{self.prefix}{self.remap[int(x)]}" for x in raw]
        num_cols=[]
        for raw_id,new_id in sorted(self.remap.items(),key=lambda kv:kv[1]):
            c=f"{self.prefix}_dist_{new_id}"
            z[c]=dist[:,raw_id]
            num_cols.append(c)
        ordered=np.sort(dist,axis=1)
        z[f"{self.prefix}_nearest_distance"]=ordered[:,0]
        z[f"{self.prefix}_distance_margin"]=ordered[:,1]-ordered[:,0] if self.k>1 else 0.0
        num_cols += [f"{self.prefix}_nearest_distance",f"{self.prefix}_distance_margin"]
        return z,[f"{self.prefix}_profile"],num_cols


def cluster_specs(stage: str) -> list[SoftCluster]:
    if stage=="T0_cold":
        return [
            SoftCluster(
                ["search_modality","search_sector"],
                ["fe_log_target_area","fe_log_rent_budget_mid","fe_log_sale_budget_mid",
                 "fe_rent_budget_width_rel","fe_sale_budget_width_rel","fe_geo_specificity"],
                3,"SN",
            )
        ]
    return [
        SoftCluster(
            ["fe_request_modality","channel","asked_visit"],
            ["fe_log_requested_area","fe_log_requested_rent_budget","fe_log_requested_sale_budget",
             "fe_log_urgency","fe_log_message_length","fe_area_shift_log",
             "fe_rent_shift_log","fe_sale_shift_log"],
            5,"DN",
        ),
        SoftCluster(
            ["spot_sector_name","spot_type_name","spot_modality","spot_natural_light",
             "spot_security_type","spot_building_status","spot_floor_material"],
            ["fe_log_spot_area","spot_luminaires","spot_charging_ports","spot_floor_level",
             "spot_elevators","spot_vertical_height_m","spot_parking_spaces","spot_amenities_count"],
            4,"PH",
        ),
        SoftCluster(
            ["spot_state","spot_municipality","spot_settlement","spot_corridor","spot_region"],
            ["spot_lat","spot_lon"],
            7,"LOC",
        ),
    ]


def add_interactions(df: pd.DataFrame, stage: str) -> tuple[pd.DataFrame,list[str],list[str]]:
    z=df.copy(); cats=[]; nums=[]
    if stage=="T0_cold":
        pairs={
            "fe_searchneed_x_source":["fe_search_need","source"],
            "fe_searchneed_x_sector":["fe_search_need","search_sector"],
            "fe_searchneed_x_user_type":["fe_search_need","user_type"],
            "fe_sn_x_industry":["SN_profile","industry"],
        }
    else:
        pairs={
            "fe_needtransition_x_physical":["fe_need_transition","PH_profile"],
            "fe_dynamicneed_x_physical":["DN_profile","PH_profile"],
            "fe_dynamicneed_x_location":["DN_profile","LOC_profile"],
            "fe_searchneed_x_dynamicneed":["fe_search_need","DN_profile"],
            "fe_dynamicneed_x_modalityfit":["DN_profile","compatible_modality"],
            "fe_dynamicneed_x_sectorfit":["DN_profile","same_sector"],
        }
    for name,cols in pairs.items():
        if all(c in z for c in cols):
            z[name]=z[cols].astype(str).agg("×".join,axis=1); cats.append(name)
    return z,cats,nums


def stage_base_features(df: pd.DataFrame, stage: str) -> tuple[list[str],list[str]]:
    if stage=="T0_cold":
        cats=[c for c in BASE_CAT if c in T0_ALLOWED_PREFIX]
        nums=[c for c in BASE_NUM if c in T0_ALLOWED_PREFIX]
    else:
        cats=list(BASE_CAT); nums=list(BASE_NUM)
    cats=[c for c in cats if c in df and df[c].notna().any()]
    nums=[c for c in nums if c in df and pd.to_numeric(df[c],errors="coerce").notna().any()]
    return cats,nums


def prepare_variant(
    train: pd.DataFrame,
    other: pd.DataFrame,
    stage: str,
    variant: str,
) -> tuple[pd.DataFrame,pd.DataFrame,list[str],list[str]]:
    tr=train.copy(); ot=other.copy()
    cats,nums=stage_base_features(tr,stage)
    if variant=="atomic":
        return tr,ot,cats,nums

    tr,c1,n1=add_scale_specificity(tr); ot,_,_=add_scale_specificity(ot)
    cats+=c1; nums+=n1
    if variant=="scale_specificity":
        return tr,ot,cats,nums

    tr,c2,n2=add_semantic_need(tr); ot,_,_=add_semantic_need(ot)
    cats+=c2; nums+=n2
    if variant=="semantic_need":
        return tr,ot,cats,nums

    fitted=[]
    for spec in cluster_specs(stage):
        # Fit spot profiles on unique spots so repeated inquiries do not weight a Spot.
        fit_df=tr
        if spec.prefix in {"PH","LOC"}:
            fit_df=tr.dropna(subset=["spot_id"]).drop_duplicates("spot_id")
        spec.fit(fit_df)
        tr,cc,nn=spec.transform(tr)
        ot,_,_=spec.transform(ot)
        cats+=cc; nums+=nn; fitted.append(spec)
    if variant=="soft_profiles":
        return tr,ot,cats,nums

    tr,c3,n3=add_interactions(tr,stage); ot,_,_=add_interactions(ot,stage)
    cats+=c3; nums+=n3
    return tr,ot,cats,nums


def make_model(cat_cols:list[str],num_cols:list[str]) -> Pipeline:
    cat=Pipeline([
        ("imp",SimpleImputer(strategy="most_frequent")),
        ("oh",OneHotEncoder(handle_unknown="ignore",min_frequency=5,sparse_output=False,dtype=np.float32)),
    ])
    num=Pipeline([
        ("imp",SimpleImputer(strategy="median",add_indicator=True)),
        ("sc",StandardScaler()),
    ])
    prep=ColumnTransformer([("cat",cat,cat_cols),("num",num,num_cols)],sparse_threshold=0.0)
    rf=RandomForestClassifier(
        n_estimators=400,min_samples_leaf=10,max_features="sqrt",
        class_weight="balanced_subsample",random_state=SEED,n_jobs=-1,
    )
    return Pipeline([("prep",prep),("model",rf)])


def metric_bundle(y: Iterable[int],p: Iterable[float]) -> dict[str,float]:
    y=np.asarray(y,dtype=int); p=np.asarray(p,dtype=float)
    p=np.clip(p,1e-8,1-1e-8)
    n=len(y); top=max(1,int(math.ceil(n*.10))); top20=max(1,int(math.ceil(n*.20)))
    idx=np.argsort(-p)
    prev=float(y.mean())
    ap=float(average_precision_score(y,p))
    return {
        "n":int(n),"positive_rate":prev,
        "roc_auc":float(roc_auc_score(y,p)) if len(np.unique(y))>1 else np.nan,
        "average_precision":ap,
        "ap_over_prevalence":ap/prev if prev>0 else np.nan,
        "brier":float(brier_score_loss(y,p)),
        "log_loss":float(log_loss(y,p,labels=[0,1])),
        "lift_top_10pct":float(y[idx[:top]].mean()/prev) if prev>0 else np.nan,
        "recall_top_20pct":float(y[idx[:top20]].sum()/y.sum()) if y.sum()>0 else np.nan,
    }


def fit_predict(train:pd.DataFrame,test:pd.DataFrame,cat:list[str],num:list[str]) -> np.ndarray:
    model=make_model(cat,num)
    model.fit(train[cat+num],train[TARGET].astype(int))
    return model.predict_proba(test[cat+num])[:,1]


def bootstrap_metrics(frame:pd.DataFrame,pred:np.ndarray,n_boot:int=BOOT) -> dict[str,dict[str,float]]:
    rng=np.random.default_rng(SEED)
    leads=frame["lead_id"].astype(str).to_numpy()
    unique=pd.unique(leads)
    vals={k:[] for k in ["roc_auc","average_precision","ap_over_prevalence","lift_top_10pct"]}
    for _ in range(n_boot):
        sampled=rng.choice(unique,size=len(unique),replace=True)
        idx=np.concatenate([np.flatnonzero(leads==lead) for lead in sampled])
        y=frame[TARGET].to_numpy(dtype=int)[idx]
        if len(np.unique(y))<2: continue
        m=metric_bundle(y,pred[idx])
        for k in vals: vals[k].append(m[k])
    out={}
    for k,v in vals.items():
        a=np.asarray(v,float)
        out[k]={
            "point":metric_bundle(frame[TARGET],pred)[k],
            "ci95_low":float(np.quantile(a,.025)),
            "ci95_high":float(np.quantile(a,.975)),
        }
    return out


def bootstrap_delta(frame:pd.DataFrame,cand:np.ndarray,base:np.ndarray,n_boot:int=BOOT) -> dict[str,dict[str,float]]:
    rng=np.random.default_rng(SEED)
    leads=frame["lead_id"].astype(str).to_numpy(); unique=pd.unique(leads)
    keys=["roc_auc","average_precision","lift_top_10pct"]; vals={k:[] for k in keys}
    for _ in range(n_boot):
        sampled=rng.choice(unique,size=len(unique),replace=True)
        idx=np.concatenate([np.flatnonzero(leads==lead) for lead in sampled])
        y=frame[TARGET].to_numpy(dtype=int)[idx]
        if len(np.unique(y))<2: continue
        a=metric_bundle(y,cand[idx]); b=metric_bundle(y,base[idx])
        for k in keys: vals[k].append(a[k]-b[k])
    out={}
    full_a=metric_bundle(frame[TARGET],cand); full_b=metric_bundle(frame[TARGET],base)
    for k,v in vals.items():
        arr=np.asarray(v,float)
        out[k]={
            "point_delta":float(full_a[k]-full_b[k]),
            "ci95_low":float(np.quantile(arr,.025)),
            "ci95_high":float(np.quantile(arr,.975)),
            "probability_gt_0":float((arr>0).mean()),
        }
    return out


def select_variant(validation_rows:list[dict]) -> dict:
    # Pre-registered: qualify on absolute signal, then maximize AP/prevalence.
    qualifying=[
        r for r in validation_rows
        if r["roc_auc"]>=.52 and r["ap_over_prevalence"]>=1.03 and r["lift_top_10pct"]>=1.05
    ]
    pool=qualifying or validation_rows
    chosen=sorted(
        pool,
        key=lambda r:(r["ap_over_prevalence"],r["lift_top_10pct"],r["roc_auc"]),
        reverse=True,
    )[0]
    return {**chosen,"qualified_on_validation":bool(qualifying)}


def development_ladder(stage:str,abt:pd.DataFrame) -> tuple[pd.DataFrame,dict]:
    tr=abt[(abt["stage"].eq(stage)) & abt["split"].eq("train")].copy()
    va=abt[(abt["stage"].eq(stage)) & abt["split"].eq("val")].copy()
    rows=[]
    for variant in VARIANTS:
        a,b,cats,nums=prepare_variant(tr,va,stage,variant)
        p=fit_predict(a,b,cats,nums)
        m=metric_bundle(b[TARGET],p)
        rows.append({"stage":stage,"variant":variant,"n_cat":len(cats),"n_num":len(nums),**m})
    choice=select_variant(rows)
    return pd.DataFrame(rows),choice


def final_test(stage:str,variant:str,abt:pd.DataFrame) -> dict:
    fit=abt[(abt["stage"].eq(stage)) & abt["split"].isin(["train","val"])].copy()
    test=abt[(abt["stage"].eq(stage)) & abt["split"].eq("test")].copy()

    a,b,cats,nums=prepare_variant(fit,test,stage,variant)
    pred=fit_predict(a,b,cats,nums)

    ba,bb,bcats,bnums=prepare_variant(fit,test,stage,"atomic")
    base_pred=fit_predict(ba,bb,bcats,bnums)

    candidate=metric_bundle(b[TARGET],pred)
    baseline=metric_bundle(bb[TARGET],base_pred)
    ci=bootstrap_metrics(b,pred)
    delta=bootstrap_delta(b,pred,base_pred)

    recovered=(
        ci["roc_auc"]["ci95_low"]>0.50
        and candidate["ap_over_prevalence"]>=1.05
        and candidate["lift_top_10pct"]>=1.10
        and candidate["average_precision"]>baseline["average_precision"]
    )
    promising=(
        candidate["roc_auc"]>.50
        and candidate["ap_over_prevalence"]>=1.03
        and candidate["lift_top_10pct"]>=1.05
    )
    status="RECOVERED" if recovered else ("PROMISING_NOT_CONFIRMED" if promising else "NOT_RECOVERED")
    return {
        "stage":stage,"selected_variant":variant,"status":status,
        "candidate_metrics":candidate,"atomic_baseline_metrics":baseline,
        "candidate_bootstrap":ci,"delta_vs_atomic":delta,
        "n_cat":len(cats),"n_num":len(nums),
    }
