from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


LEAD_CATEGORICAL = [
    "user_type", "company_size", "industry", "search_sector", "search_modality",
    "preferred_state", "preferred_municipality", "preferred_corridor", "source",
]
LEAD_NUMERIC = [
    "target_area_sqm", "min_budget_mxn_rent_monthly", "max_budget_mxn_rent_monthly",
    "min_budget_mxn_sale_total", "max_budget_mxn_sale_total",
]
INQUIRY_CATEGORICAL = ["channel", "asked_visit"]
INQUIRY_NUMERIC = [
    "message_length", "requested_area_sqm", "requested_budget_mxn_rent_monthly",
    "requested_budget_mxn_sale_total", "urgency_days", "days_from_lead_creation",
    "area_request_to_target_ratio", "rent_request_to_lead_budget_ratio",
    "sale_request_to_lead_budget_ratio",
]
CLEAN_T1_FEATURES = LEAD_CATEGORICAL + LEAD_NUMERIC + INQUIRY_CATEGORICAL + INQUIRY_NUMERIC
STABLE_SEGMENT_FEATURES = ["industrial_small_or_paid_interaction"]

FORBIDDEN = {
    "lead_score_internal", "broker_response", "broker_response_hours", "days_on_market",
    "total_inquiries", "total_views", "is_active", "competing_inquiries_30d",
    "future_inquiry_count", "future_scheduled_visit",
}


def safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return pd.to_numeric(numerator, errors="coerce") / pd.to_numeric(denominator, errors="coerce").replace(0, np.nan)


def add_t1_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["days_from_lead_creation"] = (result["prediction_timestamp"] - result["lead_created_at"]).dt.total_seconds() / 86400.0
    result["area_request_to_target_ratio"] = safe_ratio(result["requested_area_sqm"], result["target_area_sqm"])
    result["rent_request_to_lead_budget_ratio"] = safe_ratio(
        result["requested_budget_mxn_rent_monthly"], result["max_budget_mxn_rent_monthly"]
    )
    result["sale_request_to_lead_budget_ratio"] = safe_ratio(
        result["requested_budget_mxn_sale_total"], result["max_budget_mxn_sale_total"]
    )
    # Low-cardinality, T0-safe interaction selected for temporal stability.  It
    # intentionally avoids mutable history and high-cardinality geography.
    result["industrial_small_or_paid_interaction"] = (
        result["search_sector"].eq("Industrial")
        & (result["company_size"].eq("small") | result["source"].eq("paid"))
    ).astype(int)
    return result


def add_clean_t2_history(inquiries: pd.DataFrame) -> pd.DataFrame:
    ordered = inquiries.sort_values(["lead_id", "inquiry_at", "inquiry_id"], kind="mergesort").copy()
    groups = ordered.groupby("lead_id", sort=False)
    ordered["hist_prior_inquiry_count"] = groups.cumcount()
    ordered["hist_days_since_first"] = (ordered["inquiry_at"] - groups["inquiry_at"].transform("first")).dt.total_seconds() / 86400.0
    ordered["hist_days_since_previous"] = groups["inquiry_at"].diff().dt.total_seconds() / 86400.0
    ordered["hist_prior_message_mean"] = groups["message_length"].transform(lambda s: s.shift(1).expanding().mean())
    ordered["hist_prior_urgency_mean"] = groups["urgency_days"].transform(lambda s: s.shift(1).expanding().mean())
    ordered["hist_prior_requested_area_mean"] = groups["requested_area_sqm"].transform(lambda s: s.shift(1).expanding().mean())
    ordered["hist_area_change_from_previous"] = safe_ratio(ordered["requested_area_sqm"], groups["requested_area_sqm"].shift(1))
    ordered["hist_same_spot_as_previous"] = ordered["spot_id"].eq(groups["spot_id"].shift(1)).astype(float)
    return ordered


def amenities_count(value: object) -> float:
    if pd.isna(value):
        return math.nan
    try:
        parsed = json.loads(str(value))
        return float(len(parsed)) if isinstance(parsed, list) else math.nan
    except (json.JSONDecodeError, TypeError, ValueError):
        return math.nan


def validate_clean_features(columns: list[str] | tuple[str, ...] | set[str], policy_path: Path | None = None) -> None:
    columns = set(columns)
    blocked = columns & FORBIDDEN
    if blocked:
        raise ValueError(f"Forbidden/leaky features in clean model: {sorted(blocked)}")
    if policy_path:
        policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))["clean_t1"]
        allow = set(policy["allow"])
        unexpected = columns - allow
        if unexpected:
            raise ValueError(f"Features absent from clean allowlist: {sorted(unexpected)}")
