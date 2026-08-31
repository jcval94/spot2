from __future__ import annotations

import argparse, json, math, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl

HERE = Path(__file__).resolve().parent
ABT = HERE.parent / "abt"
if str(ABT) not in sys.path:
    sys.path.insert(0, str(ABT))
from _common import load_inquiries, load_leads, load_spots, parse_date, read_raw  # noqa:E402

FORBIDDEN = {"broker_response", "broker_response_hours", "target_status", "target_value",
             "lead_score_internal", "competing_inquiries_30d"}
PRICE = {"price_sqm_mxn_rent", "price_sqm_mxn_sale", "price_total_mxn_rent",
         "price_total_mxn_sale", "maintenance_cost_mxn"}
STRUCTURAL = ["sector_name", "type_name", "state", "municipality", "settlement",
              "corridor", "region", "lat", "lon", "area_sqm", "modality"]


def load_config() -> dict[str, Any]:
    return json.loads((HERE / "frozen_inventory_config.json").read_text())


def norm(x: Any) -> str | None:
    if x is None: return None
    x = str(x).strip()
    return x.casefold() if x else None


def compatible_modalities(lead: str | None, spot: str | None) -> bool:
    lead, spot = norm(lead), norm(spot)
    return bool(lead and spot and (lead == "both" or spot == "both" or lead == spot))


def search_modes(spot: str | None) -> tuple[str, ...]:
    spot = norm(spot)
    return ("rent", "sale", "both") if spot == "both" else ((spot, "both") if spot in {"rent", "sale"} else ())


def compute_area_fits(candidate: float | None, requested: float | None):
    if candidate is None or requested is None or candidate <= 0 or requested <= 0:
        return None, None, None
    gap = abs(float(candidate) - float(requested)) / float(requested)
    return max(0.0, 1.0-gap), math.exp(-abs(math.log(float(candidate)/float(requested)))), gap


def compute_budget_fit(*, transaction_mode: str, candidate_price: float | None,
                       min_budget: float | None, max_budget: float | None,
                       requested_budget: float | None):
    """Unit-safe pure rule for a future versioned price source; canonical builder never feeds current Spot price."""
    if norm(transaction_mode) not in {"rent", "sale"}: return None, None, "UNKNOWN_TRANSACTION_MODE"
    if candidate_price is None: return None, None, "UNKNOWN_PRICE_NOT_PIT"
    p = float(candidate_price)
    if p <= 0 or not math.isfinite(p): return None, None, "INVALID_CANDIDATE_PRICE"
    lo = None if min_budget is None else float(min_budget)
    hi = None if max_budget is None else float(max_budget)
    req = None if requested_budget is None else float(requested_budget)
    if req and req > 0:
        return (1.0, 0.0, "WITHIN_REQUESTED_BUDGET") if p <= req else (req/p, p-req, "ABOVE_REQUESTED_BUDGET")
    if lo is None and hi is None: return None, None, "MISSING_BUDGET"
    if lo is not None and hi is not None:
        if lo <= p <= hi: return 1.0, 0.0, "WITHIN_BUDGET_INTERVAL"
        return (p/lo, lo-p, "BELOW_BUDGET_INTERVAL") if p < lo else (hi/p, p-hi, "ABOVE_BUDGET_INTERVAL")
    if hi is not None: return (1.0, 0.0, "WITHIN_MAX_BUDGET") if p <= hi else (hi/p, p-hi, "ABOVE_MAX_BUDGET")
    return (1.0, 0.0, "ABOVE_MIN_BUDGET") if p >= lo else (p/lo, lo-p, "BELOW_MIN_BUDGET")


def build_score_frame(repo: Path, cutoff: datetime | None = None) -> pl.DataFrame:
    leads = load_leads(repo).select("lead_id", "search_sector", "search_modality", "target_area_sqm",
        "min_budget_mxn_rent_monthly", "max_budget_mxn_rent_monthly", "min_budget_mxn_sale_total",
        "max_budget_mxn_sale_total", "preferred_state", "preferred_municipality", "preferred_corridor")
    iq = load_inquiries(repo).filter(pl.col("inquiry_number") == 1).select("lead_id", "inquiry_id",
        pl.col("_inquiry_time").alias("score_time"), "requested_area_sqm",
        "requested_budget_mxn_rent_monthly", "requested_budget_mxn_sale_total", "urgency_days")
    out = iq.join(leads, on="lead_id", how="left", validate="m:1").with_columns(
        pl.format("L{}:T1:I{}", "lead_id", "inquiry_id").alias("score_id"),
        pl.lit("T1").alias("stage"),
        pl.coalesce(["requested_area_sqm", "target_area_sqm"]).alias("matching_area_reference_sqm"))
    return out.filter(pl.col("score_time") < pl.lit(cutoff)) if cutoff else out


def _record(score: dict[str, Any], spot: dict[str, Any], tier: int, geo: str) -> dict[str, Any]:
    af, lf, rg = compute_area_fits(spot.get("area_sqm"), score.get("matching_area_reference_sqm"))
    ref, ca = score.get("matching_area_reference_sqm"), spot.get("area_sqm")
    return {"score_id": score["score_id"], "lead_id": int(score["lead_id"]), "stage": "T1",
        "score_time": score["score_time"], "candidate_spot_id": int(spot["spot_id"]),
        "spot_created_at": spot["spot_created_at"], "relaxation_tier": "TIER_3_EXPERIMENTAL" if tier == 3 else f"TIER_{tier}",
        "relaxation_tier_index": tier, "modality_match": True, "sector_match": tier < 3,
        "geographic_match": geo, "candidate_area_sqm": ca, "matching_area_reference_sqm": ref,
        "area_gap_sqm": abs(float(ca)-float(ref)) if ca is not None and ref is not None else None,
        "area_gap_relative": rg, "area_fit_relative": af, "area_fit_log": lf, "urgency_days": score.get("urgency_days"),
        "requested_budget_mxn_rent_monthly": score.get("requested_budget_mxn_rent_monthly"),
        "requested_budget_mxn_sale_total": score.get("requested_budget_mxn_sale_total"),
        "min_budget_mxn_rent_monthly": score.get("min_budget_mxn_rent_monthly"),
        "max_budget_mxn_rent_monthly": score.get("max_budget_mxn_rent_monthly"),
        "min_budget_mxn_sale_total": score.get("min_budget_mxn_sale_total"), "max_budget_mxn_sale_total": score.get("max_budget_mxn_sale_total")}


def candidate_universe(repo: Path, scores: pl.DataFrame) -> pl.DataFrame:
    spots = load_spots(repo).select("spot_id", "spot_created_at", *STRUCTURAL).to_dicts()
    same, anysec = defaultdict(list), defaultdict(list)
    for s in spots:
        sec = norm(s["sector_name"])
        for mode in search_modes(s["modality"]):
            for geo, val in (("CORRIDOR", s["corridor"]), ("MUNICIPALITY", s["municipality"]), ("STATE", s["state"])):
                if norm(val): same[(mode, sec, geo, norm(val))].append(s); anysec[(mode, geo, norm(val))].append(s)
    rows = []
    for q in scores.to_dicts():
        mode, sec, seen = norm(q["search_modality"]), norm(q["search_sector"]), set()
        levels = [(0,"CORRIDOR",q["preferred_corridor"]),(1,"MUNICIPALITY",q["preferred_municipality"]),(2,"STATE",q["preferred_state"])]
        for tier, geo, val in levels:
            for s in same.get((mode, sec, geo, norm(val)), []):
                sid = int(s["spot_id"])
                if sid not in seen and s["spot_created_at"] <= q["score_time"]: seen.add(sid); rows.append(_record(q,s,tier,geo))
        for _, geo, val in levels:
            for s in anysec.get((mode, geo, norm(val)), []):
                sid = int(s["spot_id"])
                if sid not in seen and norm(s["sector_name"]) != sec and s["spot_created_at"] <= q["score_time"]:
                    seen.add(sid); rows.append(_record(q,s,3,geo))
    if not rows:
        return pl.DataFrame(schema={
            "score_id": pl.String, "lead_id": pl.Int64, "stage": pl.String,
            "score_time": pl.Datetime, "candidate_spot_id": pl.Int64,
            "spot_created_at": pl.Datetime, "relaxation_tier": pl.String,
            "relaxation_tier_index": pl.Int64,
        })
    out = pl.DataFrame(rows)
    if out.filter(pl.col("spot_created_at") > pl.col("score_time")).height: raise AssertionError("FORBIDDEN_FUTURE_SPOT")
    if out.group_by("score_id","candidate_spot_id").len().filter(pl.col("len")>1).height: raise AssertionError("duplicate candidate")
    return out


def attach_availability(repo: Path, x: pl.DataFrame, cfg: dict[str, Any]) -> pl.DataFrame:
    av = parse_date(read_raw(repo,"availability_snapshot"),"snapshot_date").drop("competing_inquiries_30d", strict=False)
    av = av.sort(["spot_id","snapshot_date","snapshot_id"]).unique(["spot_id","snapshot_date"],keep="last").select(
        pl.col("spot_id").cast(pl.Int64).alias("candidate_spot_id"), "snapshot_id",
        pl.col("snapshot_date").alias("snapshot_date_asof"), "is_available", "days_until_available").sort(["candidate_spot_id","snapshot_date_asof"])
    x = x.with_columns(pl.col("score_time").dt.date().alias("_date")).sort(["candidate_spot_id","_date"])
    x = x.join_asof(av,left_on="_date",right_on="snapshot_date_asof",by="candidate_spot_id",strategy="backward")
    if x.filter(pl.col("snapshot_date_asof").is_not_null() & (pl.col("snapshot_date_asof") > pl.col("_date"))).height: raise AssertionError("future snapshot")
    c, f = cfg["freshness"]["confidence_by_age"], cfg["availability_fit"]
    x = x.with_columns(pl.col("snapshot_id").is_not_null().alias("availability_known"),
        (pl.col("_date")-pl.col("snapshot_date_asof")).dt.total_days().alias("snapshot_age_days"))
    x = x.with_columns(
        pl.when(pl.col("availability_known")).then(pl.col("is_available")).otherwise(None).alias("is_available_asof"),
        pl.when(pl.col("availability_known")).then(pl.col("days_until_available")).otherwise(None).alias("days_until_available_asof"),
        pl.when(~pl.col("availability_known")).then(pl.lit("UNKNOWN")).when(pl.col("is_available")).then(pl.lit("AVAILABLE_NOW"))
          .when(pl.col("urgency_days").is_not_null() & pl.col("days_until_available").is_not_null() & (pl.col("days_until_available")<=pl.col("urgency_days"))).then(pl.lit("AVAILABLE_WITHIN_URGENCY")).otherwise(pl.lit("UNAVAILABLE")).alias("availability_state"),
        pl.when(~pl.col("availability_known")).then(pl.lit("UNKNOWN")).when(pl.col("snapshot_age_days")<=7).then(pl.lit("1_7D")).when(pl.col("snapshot_age_days")<=30).then(pl.lit("8_30D")).when(pl.col("snapshot_age_days")<=90).then(pl.lit("31_90D")).otherwise(pl.lit("GT_90D")).alias("freshness_bucket"),
        pl.when(~pl.col("availability_known")).then(pl.lit(c["unknown"])).when(pl.col("snapshot_age_days")<=7).then(pl.lit(c["le_7d"])).when(pl.col("snapshot_age_days")<=30).then(pl.lit(c["le_30d"])).when(pl.col("snapshot_age_days")<=90).then(pl.lit(c["le_90d"])).otherwise(pl.lit(c["gt_90d"])).cast(pl.Float64).alias("inventory_confidence"))
    return x.with_columns(pl.col("availability_state").replace_strict({"AVAILABLE_NOW":f["available_now"],"AVAILABLE_WITHIN_URGENCY":f["available_within_urgency"],"UNKNOWN":f["unknown"],"UNAVAILABLE":f["unavailable"]},return_dtype=pl.Float64).alias("availability_fit")).drop("_date","is_available","days_until_available")


def build_inventory(repo: Path, *, max_score_time_exclusive: datetime | None = None, config: dict[str, Any] | None = None) -> pl.DataFrame:
    cfg = config or load_config()
    x = candidate_universe(repo, build_score_frame(repo, max_score_time_exclusive))
    if x.is_empty():
        return x
    x = attach_availability(repo, x, cfg)
    loc, sec, caps = cfg["location_fit"], cfg["sector_fit"], cfg["serviceability_score"]["tier_caps"]
    budget_missing = pl.all_horizontal([pl.col(c).is_null() for c in ["requested_budget_mxn_rent_monthly","requested_budget_mxn_sale_total","min_budget_mxn_rent_monthly","max_budget_mxn_rent_monthly","min_budget_mxn_sale_total","max_budget_mxn_sale_total"]])
    x = x.with_columns(
        pl.when(pl.col("relaxation_tier")=="TIER_0").then(pl.lit(loc["TIER_0"])).when(pl.col("relaxation_tier")=="TIER_1").then(pl.lit(loc["TIER_1"])).when(pl.col("relaxation_tier")=="TIER_2").then(pl.lit(loc["TIER_2"])).when(pl.col("geographic_match")=="CORRIDOR").then(pl.lit(loc["TIER_3_EXPERIMENTAL"]["CORRIDOR"])).when(pl.col("geographic_match")=="MUNICIPALITY").then(pl.lit(loc["TIER_3_EXPERIMENTAL"]["MUNICIPALITY"])).otherwise(pl.lit(loc["TIER_3_EXPERIMENTAL"]["STATE"])).cast(pl.Float64).alias("location_fit"),
        pl.when(pl.col("sector_match")).then(pl.lit(sec["same_sector"])).otherwise(pl.lit(sec["tier3_sector_relaxation"])).cast(pl.Float64).alias("sector_fit"),
        pl.lit(None,dtype=pl.Float64).alias("physical_fit"), pl.lit(None,dtype=pl.Float64).alias("budget_fit"), pl.lit(None,dtype=pl.Float64).alias("budget_gap"),
        pl.when(budget_missing).then(pl.lit("MISSING_BUDGET")).otherwise(pl.lit("UNKNOWN_PRICE_NOT_PIT")).alias("budget_status"))
    x = x.with_columns((pl.col("area_fit_relative")>=cfg["viability"]["min_area_fit_relative"]).alias("is_viable"),
        pl.mean_horizontal([pl.col("area_fit_relative"),pl.col("availability_fit"),pl.col("budget_fit")]).alias("_quality"),
        pl.col("relaxation_tier").replace_strict(caps,return_dtype=pl.Float64).alias("_cap"))
    x = x.with_columns((pl.col("_quality")*pl.col("_cap")).clip(0,1).alias("candidate_serviceability_score"), pl.lit(False).alias("budget_verified"), pl.lit("PARTIAL_PIT_NO_VERSIONED_PRICE").alias("serviceability_completeness")).drop("_quality","_cap")
    if (FORBIDDEN|PRICE).intersection(x.columns): raise AssertionError("forbidden outcome/price dependency")
    return x.sort(["score_id","relaxation_tier_index","candidate_spot_id"])


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--development-only",action="store_true"); p.add_argument("--output",type=Path); a=p.parse_args()
    repo=Path(__file__).resolve().parents[2]; cutoff=datetime(2026,5,1) if a.development_only else None
    x=build_inventory(repo,max_score_time_exclusive=cutoff); out=a.output or HERE/"outputs"/"inventory_candidates.parquet"; out.parent.mkdir(parents=True,exist_ok=True); x.write_parquet(out)
    print(json.dumps({"rows":x.height,"scores":x["score_id"].n_unique(),"output":str(out)},indent=2))

if __name__ == "__main__": main()
