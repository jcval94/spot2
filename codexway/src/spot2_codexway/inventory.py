from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .contracts import Settings


def _as_bool(value: object) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _modality_ok(search: str, spot: str) -> bool:
    return search == "both" or spot == "both" or search == spot


def _fit_ratio(candidate: float, desired: float) -> float:
    if not np.isfinite(candidate) or not np.isfinite(desired) or candidate <= 0 or desired <= 0:
        return 0.0
    return float(math.exp(-abs(math.log(candidate / desired))))


def _geometric_fit(components: list[float]) -> float:
    return float(np.prod(components) ** (1 / len(components))) if components and all(value > 0 for value in components) else 0.0


def _price_fit(row: pd.Series, spot: pd.Series) -> float:
    values = []
    if row["search_modality"] in {"rent", "both"}:
        budget = row.get("requested_budget_mxn_rent_monthly")
        budget = budget if pd.notna(budget) and budget > 0 else row.get("max_budget_mxn_rent_monthly")
        price = spot.get("price_total_mxn_rent")
        if pd.notna(budget) and pd.notna(price) and budget > 0 and price > 0:
            values.append(1.0 if price <= budget else _fit_ratio(price, budget))
    if row["search_modality"] in {"sale", "both"}:
        budget = row.get("requested_budget_mxn_sale_total")
        budget = budget if pd.notna(budget) and budget > 0 else row.get("max_budget_mxn_sale_total")
        price = spot.get("price_total_mxn_sale")
        if pd.notna(budget) and pd.notna(price) and budget > 0 and price > 0:
            values.append(1.0 if price <= budget else _fit_ratio(price, budget))
    return max(values, default=0.0)


def _latest_snapshot(snapshot_groups: dict[int, pd.DataFrame], spot_id: int, timestamp: pd.Timestamp) -> pd.Series | None:
    history = snapshot_groups.get(int(spot_id))
    if history is None or history.empty:
        return None
    times = history["snapshot_date"].to_numpy(dtype="datetime64[ns]")
    position = int(np.searchsorted(times, np.datetime64(timestamp.tz_convert(None)), side="right") - 1)
    return None if position < 0 else history.iloc[position]


def build_inventory_candidates(t1: pd.DataFrame, spots: pd.DataFrame, availability: pd.DataFrame, settings: Settings) -> tuple[pd.DataFrame, pd.DataFrame]:
    snapshot_groups = {
        int(spot_id): group.sort_values("snapshot_date").reset_index(drop=True)
        for spot_id, group in availability.groupby("spot_id", sort=False)
    }
    spots_by_sector_state = {
        key: group.copy() for key, group in spots.groupby(["sector_name", "state"], sort=False)
    }
    candidate_rows: list[dict] = []
    score_rows: list[dict] = []
    freshness = settings.availability_freshness_days

    for lead in t1.itertuples(index=False):
        spot_state = getattr(lead, "spot_state", None)
        spot_municipality = getattr(lead, "spot_municipality", None)
        spot_corridor = getattr(lead, "spot_corridor", None)
        desired_state = spot_state if pd.notna(spot_state) else lead.preferred_state
        desired_municipality = spot_municipality if pd.notna(spot_municipality) else lead.preferred_municipality
        desired_corridor = spot_corridor if pd.notna(spot_corridor) else lead.preferred_corridor
        pool = spots_by_sector_state.get((lead.search_sector, desired_state), spots.iloc[0:0])
        exact = spots[spots["spot_id"].eq(lead.spot_id)]
        pool = pd.concat([pool, exact], ignore_index=True).drop_duplicates("spot_id")
        pool = pool[(pool["created_at"] <= lead.prediction_timestamp) & pool.apply(lambda row: _modality_ok(lead.search_modality, row["modality"]), axis=1)]

        scored = []
        observed_fresh = 0
        for _, spot in pool.iterrows():
            snapshot = _latest_snapshot(snapshot_groups, int(spot["spot_id"]), lead.prediction_timestamp)
            snapshot_date = pd.NaT if snapshot is None else snapshot["snapshot_date"]
            age = np.nan if snapshot is None else (lead.prediction_timestamp - snapshot_date).total_seconds() / 86400.0
            fresh = snapshot is not None and age >= 0 and age <= freshness
            observed_fresh += int(fresh)
            urgency = float(lead.urgency_days) if pd.notna(lead.urgency_days) and lead.urgency_days > 0 else 30.0
            if not fresh:
                availability_fit_lower = 0.0
                availability_fit_upper = 1.0
                availability_state = "unknown_missing_or_stale"
            elif _as_bool(snapshot["is_available"]):
                availability_fit_lower = availability_fit_upper = 1.0
                availability_state = "fresh_available_now"
            else:
                days = float(snapshot["days_until_available"]) if pd.notna(snapshot["days_until_available"]) else float("inf")
                availability_fit_lower = max(0.0, 1.0 - days / max(1.0, urgency)) if days <= urgency else 0.0
                availability_fit_upper = availability_fit_lower
                availability_state = "fresh_available_within_urgency" if availability_fit_lower > 0 else "fresh_not_attendable"
            if spot["corridor"] == desired_corridor:
                geo_fit, tier = 1.0, "same_corridor"
            elif spot["municipality"] == desired_municipality:
                geo_fit, tier = 0.85, "same_municipality"
            else:
                geo_fit, tier = 0.65, "same_state"
            desired_area = lead.requested_area_sqm if pd.notna(lead.requested_area_sqm) else lead.target_area_sqm
            area_fit = _fit_ratio(float(spot["area_sqm"]), float(desired_area))
            price_fit = _price_fit(pd.Series(lead._asdict()), spot)
            compatibility_fit = _geometric_fit([area_fit, price_fit, geo_fit])
            candidate_match_lower = _geometric_fit([area_fit, price_fit, geo_fit, availability_fit_lower])
            candidate_match_upper = _geometric_fit([area_fit, price_fit, geo_fit, availability_fit_upper])
            reason_codes = [tier, availability_state]
            record = {
                "lead_id": lead.lead_id,
                "score_id": lead.inquiry_id,
                "prediction_timestamp": lead.prediction_timestamp,
                "candidate_spot_id": int(spot["spot_id"]),
                "is_exact_spot": bool(spot["spot_id"] == lead.spot_id),
                "snapshot_date": snapshot_date,
                "snapshot_age_days": age,
                "snapshot_fresh": fresh,
                "availability_state": availability_state,
                "area_fit": area_fit,
                "price_fit": price_fit,
                "geo_fit": geo_fit,
                "compatibility_fit": compatibility_fit,
                "availability_fit": availability_fit_lower,
                "availability_fit_lower": availability_fit_lower,
                "availability_fit_upper": availability_fit_upper,
                "candidate_match": candidate_match_lower,
                "candidate_match_lower": candidate_match_lower,
                "candidate_match_upper": candidate_match_upper,
                "candidate_uncertainty_width": candidate_match_upper - candidate_match_lower,
                "relaxation_tier": tier,
                "listing_state_temporal_status": "CONDITIONAL_UNVERSIONED_ASSUMED_STATIC_SINCE_CREATION",
                "reason_codes": json.dumps(reason_codes),
            }
            candidate_rows.append(record)
            scored.append(record)

        ranked = sorted(scored, key=lambda item: (-item["candidate_match_lower"], -item["candidate_match_upper"], item["candidate_spot_id"]))
        exact_lower = max((item["candidate_match_lower"] for item in ranked if item["is_exact_spot"]), default=0.0)
        exact_upper = max((item["candidate_match_upper"] for item in ranked if item["is_exact_spot"]), default=0.0)
        exact_availability_lower = max((item["availability_fit_lower"] for item in ranked if item["is_exact_spot"]), default=0.0)
        exact_availability_upper = max((item["availability_fit_upper"] for item in ranked if item["is_exact_spot"]), default=0.0)
        alternatives_lower = [item for item in ranked if not item["is_exact_spot"] and item["candidate_match_lower"] > 0]
        alternatives_upper = [item for item in ranked if not item["is_exact_spot"] and item["candidate_match_upper"] > 0]
        top_lower = alternatives_lower[:3]
        top_upper = sorted(alternatives_upper, key=lambda item: (-item["candidate_match_upper"], item["candidate_spot_id"]))[:3]
        fallback_lower = (
            float(np.mean([item["candidate_match_lower"] for item in top_lower])) * (1 - math.exp(-len(alternatives_lower) / 3))
            if top_lower else 0.0
        )
        fallback_upper = (
            float(np.mean([item["candidate_match_upper"] for item in top_upper])) * (1 - math.exp(-len(alternatives_upper) / 3))
            if top_upper else 0.0
        )
        serviceability_lower = max(exact_lower, fallback_lower)
        serviceability_upper = max(exact_upper, fallback_upper)
        confidence = observed_fresh / max(1, len(pool))
        recommendations = alternatives_lower[: settings.max_fallback_recommendations]
        if len(recommendations) < settings.max_fallback_recommendations:
            known_ids = {item["candidate_spot_id"] for item in recommendations}
            recommendations.extend([
                item for item in top_upper if item["candidate_spot_id"] not in known_ids
            ][: settings.max_fallback_recommendations - len(recommendations)])
        score_rows.append({
            "lead_id": lead.lead_id,
            "score_id": lead.inquiry_id,
            "inventory_serviceability": serviceability_lower,
            "inventory_serviceability_lower": serviceability_lower,
            "inventory_serviceability_upper": serviceability_upper,
            "inventory_uncertainty_width": serviceability_upper - serviceability_lower,
            "inventory_confidence": confidence,
            "exact_component_lower": exact_lower,
            "exact_component_upper": exact_upper,
            "fallback_component_lower": fallback_lower,
            "fallback_component_upper": fallback_upper,
            "exact_availability_lower": exact_availability_lower,
            "exact_availability_upper": exact_availability_upper,
            "exact_spot_attendable": exact_availability_lower > 0,
            "exact_spot_availability_unknown": exact_availability_lower == 0 and exact_availability_upper > 0,
            "exact_spot_available": exact_availability_lower > 0,
            "eligible_candidate_count": len(pool),
            "attendable_alternative_count": len(alternatives_lower),
            "potential_alternative_count": len(alternatives_upper),
            "listing_state_temporal_status": "CONDITIONAL_UNVERSIONED_ASSUMED_STATIC_SINCE_CREATION",
            "availability_temporal_status": "POINT_IN_TIME_BACKWARD_ASOF",
            "fallback_spot_ids": json.dumps([item["candidate_spot_id"] for item in recommendations]),
            "fallback_reason_codes": json.dumps([json.loads(item["reason_codes"]) for item in recommendations]),
        })
    candidates = pd.DataFrame(candidate_rows)
    scores = pd.DataFrame(score_rows)
    if (candidates["snapshot_date"] > candidates["prediction_timestamp"]).fillna(False).any():
        raise AssertionError("Inventory candidates contain future snapshots")
    candidates["fallback_rank"] = candidates.groupby("lead_id")["candidate_match"].rank(method="first", ascending=False)
    return candidates, scores


def combine_opportunity(t1: pd.DataFrame, quality_probabilities: np.ndarray, inventory_scores: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    result = t1[["lead_id", "inquiry_id", "prediction_timestamp", "prediction_stage", "split"]].copy()
    result["p_lead_quality"] = quality_probabilities
    result = result.merge(inventory_scores, left_on=["lead_id", "inquiry_id"], right_on=["lead_id", "score_id"], how="left", validate="one_to_one")
    # Keep the combiner usable with older/materialized inventory artifacts while
    # making uncertainty explicit for newly-built ones.  A missing interval is
    # interpreted as a point estimate, never as extra historical evidence.
    if "inventory_serviceability_lower" not in result:
        result["inventory_serviceability_lower"] = result["inventory_serviceability"]
    if "inventory_serviceability_upper" not in result:
        result["inventory_serviceability_upper"] = result["inventory_serviceability"]
    if "inventory_uncertainty_width" not in result:
        result["inventory_uncertainty_width"] = (
            result["inventory_serviceability_upper"] - result["inventory_serviceability_lower"]
        )
    result["lead_quality_score_0_100"] = 100 * result["p_lead_quality"]
    result["opportunity_probability"] = result["p_lead_quality"] * result["inventory_serviceability_lower"].fillna(0)
    result["opportunity_probability_lower"] = result["opportunity_probability"]
    result["opportunity_probability_upper"] = result["p_lead_quality"] * result["inventory_serviceability_upper"].fillna(0)
    result["opportunity_score_0_100"] = 100 * result["opportunity_probability"]
    result["opportunity_score_upper_0_100"] = 100 * result["opportunity_probability_upper"]
    validation = result[result["split"].eq("validation")]["opportunity_probability"]
    q30, q70, q90 = validation.quantile([0.30, 0.70, 0.90]).tolist()
    result["priority_band"] = pd.cut(
        result["opportunity_probability"], bins=[-np.inf, q30, q70, q90, np.inf],
        labels=["Low", "Medium", "High", "Priority"], include_lowest=True,
    ).astype(str)
    quality_validation = result[result["split"].eq("validation")]["p_lead_quality"]
    quality_q70, quality_q90 = quality_validation.quantile([0.70, 0.90]).tolist()
    result["quality_band"] = pd.cut(
        result["p_lead_quality"], bins=[-np.inf, quality_q70, quality_q90, np.inf],
        labels=["Standard", "High", "Priority"], include_lowest=True,
    ).astype(str)
    result["serviceability_band"] = np.select(
        [
            result["inventory_confidence"].lt(0.50) | result["inventory_uncertainty_width"].gt(0.20),
            result["inventory_serviceability_lower"].ge(0.75),
            result["inventory_serviceability_upper"].ge(0.50),
        ],
        ["Uncertain", "Serviceable", "Potential fallback"],
        default="Low serviceability",
    )
    result["diagnostic_action"] = np.select(
        [
            result["quality_band"].isin(["High", "Priority"]) & result["serviceability_band"].eq("Serviceable"),
            result["quality_band"].isin(["High", "Priority"]) & result["serviceability_band"].eq("Uncertain"),
            result["quality_band"].isin(["High", "Priority"]),
        ],
        ["work_if_model_gate_passes", "verify_inventory_first", "source_or_offer_fallback"],
        default="standard_workflow",
    )
    result["deployment_status"] = "DIAGNOSTIC_ONLY_PENDING_SYSTEM_GATE"
    result["model_version"] = "codexway-0.1.0"
    return result
