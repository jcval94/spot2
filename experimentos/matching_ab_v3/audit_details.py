from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/"data"/"candidate"/"csv"
OUT=Path(__file__).resolve().parent/"results"

leads=pd.read_csv(DATA/"leads.csv",parse_dates=["created_at"])
spots=pd.read_csv(DATA/"spots.csv",parse_dates=["created_at"])
iq=pd.read_csv(DATA/"inquiries.csv",parse_dates=["inquiry_at"])
av=pd.read_csv(DATA/"availability_snapshot.csv",parse_dates=["snapshot_date"])
market=pd.read_csv(DATA/"market_context.csv",parse_dates=["month"])

# 1) Diagnose response-hours semantics instead of treating nullness as a flat missingness issue.
resp=iq.groupby("broker_response",dropna=False).agg(
    n=("inquiry_id","size"),
    response_hours_non_null=("broker_response_hours","count"),
    median_response_hours=("broker_response_hours","median"),
    min_response_hours=("broker_response_hours","min"),
    max_response_hours=("broker_response_hours","max"),
).reset_index()
resp["response_hours_missing"]=resp["n"]-resp["response_hours_non_null"]
resp["non_null_rate"]=resp["response_hours_non_null"]/resp["n"]
resp.to_csv(OUT/"response_hours_by_response.csv",index=False)

# 2) Cross Lead -> Inquiry -> Spot rather than profiling each table alone.
x=iq.merge(
    leads[["lead_id","search_sector","search_modality","target_area_sqm",
           "min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly",
           "min_budget_mxn_sale_total","max_budget_mxn_sale_total",
           "preferred_municipality","preferred_corridor"]],
    on="lead_id",how="left",validate="many_to_one"
).merge(
    spots[["spot_id","sector_name","modality","area_sqm","municipality","corridor",
           "price_sqm_mxn_rent","price_total_mxn_rent","price_sqm_mxn_sale","price_total_mxn_sale",
           "total_inquiries"]],
    on="spot_id",how="left",validate="many_to_one",suffixes=("","_spot")
)

pd.crosstab(x.search_sector,x.sector_name,margins=True).to_csv(OUT/"lead_spot_sector_cross.csv")
pd.crosstab(x.search_modality,x.modality,margins=True).to_csv(OUT/"lead_spot_modality_cross.csv")

geo=x.groupby("search_sector").apply(
    lambda g: pd.Series({
        "n":len(g),
        "same_sector_rate":g.search_sector.eq(g.sector_name).mean(),
        "same_municipality_rate":g.preferred_municipality.eq(g.municipality).mean(),
        "declared_corridor_n":int(g.preferred_corridor.notna().sum()),
        "same_corridor_rate_when_declared":g.loc[g.preferred_corridor.notna(),"preferred_corridor"].eq(
            g.loc[g.preferred_corridor.notna(),"corridor"]).mean()
    }),include_groups=False
).reset_index()
geo.to_csv(OUT/"lead_spot_match_by_search_sector.csv",index=False)

# 3) Lead-declared need vs inquiry refinement.
rows=[]
rent=x.requested_budget_mxn_rent_monthly.notna() & x.min_budget_mxn_rent_monthly.notna() & x.max_budget_mxn_rent_monthly.notna()
sale=x.requested_budget_mxn_sale_total.notna() & x.min_budget_mxn_sale_total.notna() & x.max_budget_mxn_sale_total.notna()
area=x.requested_area_sqm.notna() & x.target_area_sqm.notna()
for name,mask,val,lo,hi in [
    ("rent_requested_within_lead_budget",rent,"requested_budget_mxn_rent_monthly","min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly"),
    ("sale_requested_within_lead_budget",sale,"requested_budget_mxn_sale_total","min_budget_mxn_sale_total","max_budget_mxn_sale_total")
]:
    rows.append({"check":name,"n_comparable":int(mask.sum()),
                 "rate":float(x.loc[mask,val].between(x.loc[mask,lo],x.loc[mask,hi]).mean()) if mask.any() else np.nan})
ratio=x.loc[area,"requested_area_sqm"]/x.loc[area,"target_area_sqm"]
rows += [
    {"check":"requested_area_vs_lead_target_median_ratio","n_comparable":int(area.sum()),"rate":float(ratio.median())},
    {"check":"requested_area_within_0.5x_2x_lead_target","n_comparable":int(area.sum()),"rate":float(ratio.between(.5,2).mean())},
]
pd.DataFrame(rows).to_csv(OUT/"lead_inquiry_need_consistency.csv",index=False)

# 4) Listing arithmetic consistency.
price_rows=[]
for mode,psqm,total in [
    ("rent","price_sqm_mxn_rent","price_total_mxn_rent"),
    ("sale","price_sqm_mxn_sale","price_total_mxn_sale")
]:
    mask=spots[psqm].notna()&spots[total].notna()&spots.area_sqm.notna()&(spots.area_sqm>0)
    expected=spots.loc[mask,psqm]*spots.loc[mask,"area_sqm"]
    rel=(spots.loc[mask,total]-expected).abs()/expected.replace(0,np.nan)
    price_rows.append({"mode":mode,"n_comparable":int(mask.sum()),"median_relative_error":float(rel.median()),
                       "p95_relative_error":float(rel.quantile(.95)),"within_1pct":float(rel.le(.01).mean())})
pd.DataFrame(price_rows).to_csv(OUT/"spot_price_arithmetic_consistency.csv",index=False)

# 5) Spot aggregate inquiries vs actual inquiry table, diagnostic only.
actual=iq.groupby("spot_id").size().rename("actual_inquiries_in_candidate").reset_index()
agg=spots[["spot_id","total_inquiries"]].merge(actual,on="spot_id",how="left").fillna({"actual_inquiries_in_candidate":0})
agg["difference_total_minus_candidate"]=agg.total_inquiries-agg.actual_inquiries_in_candidate
summary=pd.DataFrame([{
    "spots":len(agg),"exact_match_rate":float(agg.total_inquiries.eq(agg.actual_inquiries_in_candidate).mean()),
    "total_ge_candidate_rate":float(agg.total_inquiries.ge(agg.actual_inquiries_in_candidate).mean()),
    "correlation":float(agg[["total_inquiries","actual_inquiries_in_candidate"]].corr().iloc[0,1]),
    "median_difference":float(agg.difference_total_minus_candidate.median())
}])
summary.to_csv(OUT/"spot_total_inquiries_vs_event_table_summary.csv",index=False)

# 6) Availability coverage by calendar month and availability-state consistency.
left=iq[["inquiry_id","spot_id","inquiry_at"]].sort_values(["inquiry_at","spot_id"])
right=av[["spot_id","snapshot_date","is_available","days_until_available"]].sort_values(["snapshot_date","spot_id"])
a=pd.merge_asof(left,right,left_on="inquiry_at",right_on="snapshot_date",by="spot_id",direction="backward")
a["lag_days"]=(a.inquiry_at-a.snapshot_date).dt.total_seconds()/86400
a["month"]=a.inquiry_at.dt.to_period("M").astype(str)
cov=a.groupby("month").agg(n=("inquiry_id","size"),coverage=("snapshot_date",lambda s:s.notna().mean()),
                           median_lag_days=("lag_days","median"),p90_lag_days=("lag_days",lambda s:s.quantile(.9))).reset_index()
cov.to_csv(OUT/"availability_coverage_by_month.csv",index=False)
avail_flag=a.is_available.astype(str).str.lower().isin(["true","1","yes"])
avail_cons=pd.DataFrame([{
    "available_rows":int((avail_flag&a.snapshot_date.notna()).sum()),
    "available_with_days_until_zero_rate":float(a.loc[avail_flag&a.snapshot_date.notna(),"days_until_available"].fillna(0).eq(0).mean()),
    "not_available_rows":int((~avail_flag&a.snapshot_date.notna()).sum()),
    "not_available_positive_days_until_rate":float(a.loc[(~avail_flag)&a.snapshot_date.notna(),"days_until_available"].fillna(0).gt(0).mean())
}])
avail_cons.to_csv(OUT/"availability_state_consistency.csv",index=False)

# 7) Market context exact coverage by sector/month; descriptive because effective/publication time is unknown.
sm=spots[["spot_id","state","municipality","corridor","sector_name"]]
mi=iq[["inquiry_id","spot_id","inquiry_at"]].merge(sm,on="spot_id",how="left")
mi["month"]=mi.inquiry_at.dt.to_period("M").dt.to_timestamp()
mm=market.rename(columns={"sector":"sector_name"})
keys=["state","municipality","corridor","sector_name","month"]
mj=mi.merge(mm[keys].drop_duplicates().assign(context_match=1),on=keys,how="left")
mj["covered"]=mj.context_match.eq(1)
msector=mj.groupby("sector_name").agg(n=("inquiry_id","size"),exact_coverage=("covered","mean")).reset_index()
mmonth=mj.assign(month_label=mj["month"].dt.to_period("M").astype(str)).groupby("month_label").agg(
    n=("inquiry_id","size"),exact_coverage=("covered","mean")).reset_index()
msector.to_csv(OUT/"market_context_coverage_by_sector.csv",index=False)
mmonth.to_csv(OUT/"market_context_coverage_by_month.csv",index=False)

print("Cross-table audit detail outputs written.")
