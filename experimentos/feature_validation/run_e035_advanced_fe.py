from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from advanced_fe_common import eval_variant, load_abt

HERE=Path(__file__).resolve().parent
OUT=HERE/"E035_outcome_free_advanced_fe"/"results"
OUT.mkdir(parents=True,exist_ok=True)

VARIANTS=["atomic","missingness_frequency","robust_bins","geo_inventory_relative","combined_v2"]

def summarize(df:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for (stage,var),g in df.groupby(["stage","variant"]):
        rows.append({
            "stage":stage,"variant":var,"folds":int(g.fold.nunique()),
            "mean_auc":g.roc_auc.mean(),"min_auc":g.roc_auc.min(),
            "mean_ap":g.average_precision.mean(),
            "mean_ap_over_prevalence":g.ap_over_prevalence.mean(),
            "min_ap_over_prevalence":g.ap_over_prevalence.min(),
            "mean_lift10":g.lift_top_10pct.mean(),
            "min_lift10":g.lift_top_10pct.min(),
            "folds_auc_gt_05":int((g.roc_auc>.5).sum()),
        })
    return pd.DataFrame(rows)

def status(row)->str:
    if (
        row.mean_auc>=.52 and row.mean_ap_over_prevalence>=1.03
        and row.min_lift10>=1.0 and row.folds_auc_gt_05>=2
    ):
        return "ROBUST_DEV_SIGNAL"
    if row.mean_auc>.50 and row.mean_ap_over_prevalence>=1.01:
        return "WEAK_DEV_SIGNAL"
    return "NO_DEV_SIGNAL"

def main():
    abt=load_abt()
    # Test and validation remain untouched. E035 uses E030 train only.
    dev=abt[abt["split"].eq("train")].copy()
    rows=[]
    for stage in ["T0_cold","T1_first_inquiry"]:
        d=dev[dev.stage.eq(stage)].copy()
        for var in VARIANTS:
            rows.extend(eval_variant(d,stage,var))
    folds=pd.DataFrame(rows)
    folds.to_csv(OUT/"rolling_fold_metrics.csv",index=False)
    summary=summarize(folds)
    summary["status"]=summary.apply(status,axis=1)
    summary.to_csv(OUT/"variant_summary.csv",index=False)

    selected={}
    for stage,g in summary.groupby("stage"):
        q=g[g.status.eq("ROBUST_DEV_SIGNAL")]
        pool=q if len(q) else g
        best=pool.sort_values(
            ["mean_ap_over_prevalence","mean_lift10","mean_auc"],
            ascending=False
        ).iloc[0]
        selected[stage]=best.to_dict()
    (OUT/"selected_development_challengers.json").write_text(
        json.dumps(selected,indent=2,ensure_ascii=False,default=str)+"\n",encoding="utf-8"
    )

    report="# E035 — Outcome-free advanced Feature Engineering\n\n"
    report+="**Development only. E030 validation/test are not used.**\n\n"
    report+=summary.to_markdown(index=False)
    report+="\n\n## Selected development challengers\n\n"
    for stage,x in selected.items():
        report+=f"- {stage}: **{x['variant']}** — {x['status']}; mean AUC {x['mean_auc']:.3f}, AP/prevalence {x['mean_ap_over_prevalence']:.3f}x, min Lift@10 {x['min_lift10']:.3f}x.\n"
    (OUT/"REPORT.md").write_text(report,encoding="utf-8")
    print(json.dumps(selected,indent=2,ensure_ascii=False,default=str))

if __name__=="__main__":
    main()
