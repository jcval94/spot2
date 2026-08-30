from __future__ import annotations

import json
from typing import Iterable

import numpy as np
import pandas as pd

HORIZON_DAYS = 30
UNKNOWN = "__UNKNOWN__"
UNSPECIFIED = "__UNSPECIFIED__"
STAGES = {0: "T0_cold", 1: "T1_first_inquiry", 2: "T2_engaged"}
RESPONSE_STATUSES = {"accepted", "rejected", "scheduled_visit"}
AMENITY_VOCAB = (
    "meeting_rooms", "cafeteria", "kitchen", "rooftop", "conference_room",
    "storage", "lounge", "security_booth", "reception", "loading_dock",
    "parking", "gym",
)

BLOCKED_RAW_FEATURES = {
    "lead_id", "spot_id", "inquiry_id", "snapshot_id", "broker_id",
    "lead_score_internal", "broker_response", "broker_response_hours",
    "days_on_market", "total_inquiries", "total_views", "is_active",
    "title", "description", "amenities", "month",
}

LEAD_CATS = [
    "user_type", "company_size_fe", "industry_fe", "search_sector", "search_modality",
    "preferred_state", "preferred_municipality", "preferred_corridor_fe", "source",
]
LEAD_NUMS = [
    "target_area_sqm", "log_target_area_sqm",
    "rent_budget_applicable", "rent_min_missing_when_applicable", "rent_budget_min_effective",
    "rent_budget_max", "rent_budget_mid", "rent_budget_width", "log_rent_budget_max",
    "sale_budget_applicable", "sale_min_missing_when_applicable", "sale_budget_min_effective",
    "sale_budget_max", "sale_budget_mid", "sale_budget_width", "log_sale_budget_max",
    "prior_searches", "log_prior_searches", "prior_searches_zero",
    "prior_inquiries", "log_prior_inquiries", "prior_inquiries_zero",
    "has_converted_before", "geographic_specificity", "lead_month", "lead_weekday_num",
]
INQUIRY_CATS = ["channel", "urgency_bucket", "inquiry_weekday"]
INQUIRY_NUMS = [
    "message_length", "log_message_length", "requested_area_sqm", "log_requested_area_sqm",
    "requested_rent_budget", "log_requested_rent_budget", "requested_sale_budget",
    "log_requested_sale_budget", "urgency_days", "urgency_missing", "asked_visit",
    "inquiry_hour", "inquiry_number", "days_from_lead_creation",
    "requested_to_target_area_ratio", "log_requested_to_target_area_ratio",
    "requested_rent_vs_initial_mid", "requested_sale_vs_initial_mid",
    "requested_rent_inside_initial_range", "requested_sale_inside_initial_range",
]
SPOT_CATS = [
    "spot_sector_name", "spot_type_name", "spot_state", "spot_municipality", "spot_settlement",
    "spot_corridor", "spot_region", "spot_modality", "spot_security_type",
    "spot_building_status", "spot_floor_material", "spot_floor_level_bucket",
]
SPOT_NUMS = [
    "spot_lat", "spot_lon", "spot_area_sqm", "log_spot_area_sqm",
    "spot_price_sqm_mxn_rent", "log_spot_price_sqm_mxn_rent",
    "spot_price_sqm_mxn_sale", "log_spot_price_sqm_mxn_sale",
    "spot_price_total_mxn_rent", "log_spot_price_total_mxn_rent",
    "spot_price_total_mxn_sale", "log_spot_price_total_mxn_sale",
    "spot_maintenance_cost_mxn", "log_spot_maintenance_cost_mxn",
    "spot_effective_monthly_cost", "log_spot_effective_monthly_cost",
    "spot_age_at_score_days", "spot_built_environment_applicable",
    "spot_natural_light", "spot_luminaires", "log_spot_luminaires",
    "spot_luminaires_per_100_sqm", "spot_charging_ports", "spot_charging_ports_missing",
    "spot_charging_ports_per_100_sqm", "spot_floor_level", "spot_elevators",
    "log_spot_elevators", "spot_elevators_per_1000_sqm", "spot_vertical_height_m",
    "spot_vertical_height_missing", "spot_parking_spaces", "log_spot_parking_spaces",
    "spot_parking_per_1000_sqm", "spot_amenities_count",
] + [f"spot_amenity_{a}" for a in AMENITY_VOCAB]
MATCH_CATS = ["same_state", "same_municipality", "same_corridor", "same_sector", "compatible_modality"]
MATCH_NUMS = [
    "requested_to_spot_area_ratio", "log_requested_to_spot_area_ratio",
    "rent_budget_to_price_ratio", "sale_budget_to_price_ratio",
    "rent_headroom_ratio", "sale_headroom_ratio",
]
AVAIL_CATS = ["availability_is_available", "availability_window", "availability_freshness"]
AVAIL_NUMS = [
    "availability_days_until_available", "log_availability_days_until_available",
    "availability_competing_inquiries_30d", "log_availability_competing_inquiries_30d",
    "availability_snapshot_age_days", "has_availability_context",
]
SUPPLY_HISTORY_NUMS = [
    "spot_hist_prior_inquiries", "spot_hist_prior_unique_leads", "spot_hist_prior_scheduled_visits",
    "spot_hist_schedule_rate", "broker_hist_prior_inquiries", "broker_hist_prior_unique_leads",
    "broker_hist_realized_responses", "broker_hist_accepted_responses", "broker_hist_scheduled_visits",
    "broker_hist_accept_rate", "broker_hist_schedule_rate", "broker_hist_median_response_hours",
]
HISTORY_NUMS = [
    "hist_prior_inquiries", "hist_prior_unique_spots", "hist_prior_asked_visit_rate",
    "hist_prior_message_length_mean", "hist_prior_urgency_mean", "hist_prior_realized_responses",
    "hist_prior_accepted_responses", "hist_prior_scheduled_visits", "hist_prior_accept_rate",
    "hist_prior_median_response_hours", "days_since_first_inquiry",
]

BASE_FEATURES_T0 = LEAD_CATS + LEAD_NUMS
BASE_FEATURES_T1 = BASE_FEATURES_T0 + INQUIRY_CATS + INQUIRY_NUMS + SPOT_CATS + SPOT_NUMS + MATCH_CATS + MATCH_NUMS + AVAIL_CATS + AVAIL_NUMS + SUPPLY_HISTORY_NUMS
BASE_FEATURES_T2 = BASE_FEATURES_T1 + HISTORY_NUMS


def safe_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def safe_log1p(s: pd.Series) -> pd.Series:
    x = safe_num(s)
    return np.log1p(x.where(x >= 0))


def safe_ratio(a: pd.Series, b: pd.Series) -> pd.Series:
    return safe_num(a) / safe_num(b).replace(0, np.nan)


def parse_bool(s: pd.Series) -> pd.Series:
    def one(x: object) -> float:
        if pd.isna(x):
            return np.nan
        if isinstance(x, (bool, np.bool_)):
            return float(x)
        return float(str(x).strip().lower() in {"true", "1", "yes", "y"})
    return s.map(one).astype(float)


def parse_amenities(value: object) -> list[str]:
    if pd.isna(value):
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    try:
        parsed = json.loads(str(value))
        return [str(v) for v in parsed] if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


def validate_raw_tables(
    leads: pd.DataFrame,
    spots: pd.DataFrame,
    attrs: pd.DataFrame,
    inquiries: pd.DataFrame,
    availability: pd.DataFrame,
) -> None:
    for df, key in [
        (leads, "lead_id"), (spots, "spot_id"), (attrs, "spot_id"),
        (inquiries, "inquiry_id"), (availability, "snapshot_id"),
    ]:
        if df[key].isna().any() or df[key].duplicated().any():
            raise ValueError(f"Primary-key violation in {key}")
    if not set(inquiries["lead_id"]).issubset(set(leads["lead_id"])):
        raise ValueError("inquiries.lead_id contains orphan keys")
    if not set(inquiries["spot_id"]).issubset(set(spots["spot_id"])):
        raise ValueError("inquiries.spot_id contains orphan keys")
    if set(attrs["spot_id"]) != set(spots["spot_id"]):
        raise ValueError("spot_attributes must be 1:1 with spots")
    if not set(availability["spot_id"]).issubset(set(spots["spot_id"])):
        raise ValueError("availability_snapshot contains orphan spot_id")

    for modality, required, forbidden in [
        ("rent", ["price_sqm_mxn_rent", "price_total_mxn_rent", "maintenance_cost_mxn"], ["price_sqm_mxn_sale", "price_total_mxn_sale"]),
        ("sale", ["price_sqm_mxn_sale", "price_total_mxn_sale"], ["price_sqm_mxn_rent", "price_total_mxn_rent", "maintenance_cost_mxn"]),
        ("both", ["price_sqm_mxn_rent", "price_total_mxn_rent", "maintenance_cost_mxn", "price_sqm_mxn_sale", "price_total_mxn_sale"], []),
    ]:
        part = spots[spots["modality"].eq(modality)]
        for col in required:
            if part[col].isna().any():
                raise ValueError(f"{col} missing where spots.modality={modality}")
        for col in forbidden:
            if part[col].notna().any():
                raise ValueError(f"{col} unexpectedly populated where spots.modality={modality}")


def engineer_leads(leads: pd.DataFrame) -> pd.DataFrame:
    d = leads.copy()
    d["created_at"] = pd.to_datetime(d["created_at"], errors="raise")
    d["company_size_fe"] = d["company_size"].astype("string").fillna(UNKNOWN)
    d["industry_fe"] = d["industry"].astype("string").fillna(UNKNOWN)
    d["preferred_corridor_fe"] = d["preferred_corridor"].astype("string").fillna(UNSPECIFIED)
    d["geographic_specificity"] = d["preferred_corridor"].notna().astype(float) + 2.0
    d["has_converted_before"] = parse_bool(d["has_converted_before"])
    d["log_target_area_sqm"] = safe_log1p(d["target_area_sqm"])
    for c in ["prior_searches", "prior_inquiries"]:
        d[f"log_{c}"] = safe_log1p(d[c])
        d[f"{c}_zero"] = safe_num(d[c]).eq(0).astype(float)

    modality = d["search_modality"].astype("string")
    rent_app, sale_app = modality.isin(["rent", "both"]), modality.isin(["sale", "both"])
    d["rent_budget_applicable"], d["sale_budget_applicable"] = rent_app.astype(float), sale_app.astype(float)
    rent_min = safe_num(d["min_budget_mxn_rent_monthly"])
    rent_max = safe_num(d["max_budget_mxn_rent_monthly"])
    sale_min = safe_num(d["min_budget_mxn_sale_total"])
    sale_max = safe_num(d["max_budget_mxn_sale_total"])
    d["rent_min_missing_when_applicable"] = (rent_app & rent_min.isna()).astype(float)
    d["sale_min_missing_when_applicable"] = (sale_app & sale_min.isna()).astype(float)
    d["rent_budget_min_effective"] = np.where(rent_app, rent_min.fillna(0), np.nan)
    d["sale_budget_min_effective"] = np.where(sale_app, sale_min.fillna(0), np.nan)
    d["rent_budget_max"] = np.where(rent_app, rent_max, np.nan)
    d["sale_budget_max"] = np.where(sale_app, sale_max, np.nan)
    d["rent_budget_mid"] = np.where(rent_app, (d["rent_budget_min_effective"] + rent_max) / 2.0, np.nan)
    d["sale_budget_mid"] = np.where(sale_app, (d["sale_budget_min_effective"] + sale_max) / 2.0, np.nan)
    d["rent_budget_width"] = np.where(rent_app, rent_max - d["rent_budget_min_effective"], np.nan)
    d["sale_budget_width"] = np.where(sale_app, sale_max - d["sale_budget_min_effective"], np.nan)
    d["log_rent_budget_max"] = safe_log1p(d["rent_budget_max"])
    d["log_sale_budget_max"] = safe_log1p(d["sale_budget_max"])
    d["lead_month"] = d["created_at"].dt.month.astype(float)
    d["lead_weekday_num"] = d["created_at"].dt.weekday.astype(float)
    return d


def prepare_inquiries(inquiries: pd.DataFrame) -> pd.DataFrame:
    d = inquiries.copy()
    d["inquiry_at"] = pd.to_datetime(d["inquiry_at"], errors="raise")
    d = d.sort_values(["lead_id", "inquiry_at", "inquiry_id"]).copy()
    d["inquiry_number"] = d.groupby("lead_id").cumcount() + 1
    hours = safe_num(d["broker_response_hours"])
    realized = d["broker_response"].isin(RESPONSE_STATUSES) & hours.notna()
    d["response_event_at"] = pd.NaT
    d.loc[realized, "response_event_at"] = d.loc[realized, "inquiry_at"] + pd.to_timedelta(hours[realized], unit="h")
    d["response_time_ambiguous"] = (
        d["broker_response"].eq("scheduled_visit") & hours.isna()
    ).astype(float)
    d["response_semantic_inconsistency"] = (
        (d["broker_response"].eq("no_response") & hours.notna())
        | (d["broker_response"].isin(RESPONSE_STATUSES) & hours.isna())
    ).astype(float)
    return d


def add_history_features(inquiries: pd.DataFrame) -> pd.DataFrame:
    d = inquiries.copy()
    for col in HISTORY_NUMS:
        d[col] = np.nan
    for _, g in d.groupby("lead_id", sort=False):
        g = g.sort_values(["inquiry_at", "inquiry_id"])
        first_time, previous_indices = g["inquiry_at"].iloc[0], []
        for idx, row in g.iterrows():
            t = row["inquiry_at"]
            prev = g.loc[previous_indices] if previous_indices else g.iloc[0:0]
            realized = prev[prev["response_event_at"].notna() & (prev["response_event_at"] <= t)]
            d.at[idx, "hist_prior_inquiries"] = len(prev)
            d.at[idx, "hist_prior_unique_spots"] = prev["spot_id"].nunique()
            d.at[idx, "hist_prior_asked_visit_rate"] = parse_bool(prev["asked_visit"]).mean() if len(prev) else np.nan
            d.at[idx, "hist_prior_message_length_mean"] = safe_num(prev["message_length"]).mean() if len(prev) else np.nan
            d.at[idx, "hist_prior_urgency_mean"] = safe_num(prev["urgency_days"]).mean() if len(prev) else np.nan
            d.at[idx, "hist_prior_realized_responses"] = len(realized)
            d.at[idx, "hist_prior_accepted_responses"] = realized["broker_response"].eq("accepted").sum()
            d.at[idx, "hist_prior_scheduled_visits"] = realized["broker_response"].eq("scheduled_visit").sum()
            d.at[idx, "hist_prior_accept_rate"] = realized["broker_response"].eq("accepted").mean() if len(realized) else np.nan
            d.at[idx, "hist_prior_median_response_hours"] = safe_num(realized["broker_response_hours"]).median() if len(realized) else np.nan
            d.at[idx, "days_since_first_inquiry"] = (t - first_time).total_seconds() / 86400.0
            previous_indices.append(idx)
    return d


def add_supply_history_features(inquiries: pd.DataFrame, spots: pd.DataFrame) -> pd.DataFrame:
    d = inquiries.merge(spots[["spot_id", "broker_id"]], on="spot_id", how="left", validate="many_to_one").copy()
    for col in SUPPLY_HISTORY_NUMS:
        d[col] = np.nan

    for _, g in d.groupby("spot_id", sort=False):
        g = g.sort_values(["inquiry_at", "inquiry_id"])
        prior_indices = []
        for idx, row in g.iterrows():
            t = row["inquiry_at"]
            prev = g.loc[prior_indices] if prior_indices else g.iloc[0:0]
            realized = prev[prev["response_event_at"].notna() & (prev["response_event_at"] <= t)]
            scheduled = realized["broker_response"].eq("scheduled_visit")
            d.at[idx, "spot_hist_prior_inquiries"] = len(prev)
            d.at[idx, "spot_hist_prior_unique_leads"] = prev["lead_id"].nunique()
            d.at[idx, "spot_hist_prior_scheduled_visits"] = scheduled.sum()
            d.at[idx, "spot_hist_schedule_rate"] = scheduled.mean() if len(realized) else np.nan
            prior_indices.append(idx)

    for _, g in d.groupby("broker_id", sort=False):
        g = g.sort_values(["inquiry_at", "inquiry_id"])
        prior_indices = []
        for idx, row in g.iterrows():
            t = row["inquiry_at"]
            prev = g.loc[prior_indices] if prior_indices else g.iloc[0:0]
            realized = prev[prev["response_event_at"].notna() & (prev["response_event_at"] <= t)]
            accepted = realized["broker_response"].eq("accepted")
            scheduled = realized["broker_response"].eq("scheduled_visit")
            d.at[idx, "broker_hist_prior_inquiries"] = len(prev)
            d.at[idx, "broker_hist_prior_unique_leads"] = prev["lead_id"].nunique()
            d.at[idx, "broker_hist_realized_responses"] = len(realized)
            d.at[idx, "broker_hist_accepted_responses"] = accepted.sum()
            d.at[idx, "broker_hist_scheduled_visits"] = scheduled.sum()
            d.at[idx, "broker_hist_accept_rate"] = accepted.mean() if len(realized) else np.nan
            d.at[idx, "broker_hist_schedule_rate"] = scheduled.mean() if len(realized) else np.nan
            d.at[idx, "broker_hist_median_response_hours"] = safe_num(realized["broker_response_hours"]).median() if len(realized) else np.nan
            prior_indices.append(idx)
    return d


def engineer_inquiry_rows(rows: pd.DataFrame) -> pd.DataFrame:
    d = rows.copy()
    d["asked_visit"] = parse_bool(d["asked_visit"])
    d["log_message_length"] = safe_log1p(d["message_length"])
    d["log_requested_area_sqm"] = safe_log1p(d["requested_area_sqm"])
    d["requested_rent_budget"] = safe_num(d["requested_budget_mxn_rent_monthly"])
    d["requested_sale_budget"] = safe_num(d["requested_budget_mxn_sale_total"])
    d["log_requested_rent_budget"] = safe_log1p(d["requested_rent_budget"])
    d["log_requested_sale_budget"] = safe_log1p(d["requested_sale_budget"])
    d["urgency_days"] = safe_num(d["urgency_days"])
    d["urgency_missing"] = d["urgency_days"].isna().astype(float)
    d["urgency_bucket"] = pd.cut(
        d["urgency_days"], [-np.inf, 7, 30, 90, 180, np.inf],
        labels=["<=7", "8-30", "31-90", "91-180", ">180"],
    ).astype("string").fillna(UNKNOWN)
    d["inquiry_hour"] = d["inquiry_at"].dt.hour.astype(float)
    d["inquiry_weekday"] = d["inquiry_at"].dt.day_name()
    d["days_from_lead_creation"] = (d["inquiry_at"] - d["created_at"]).dt.total_seconds() / 86400.0
    d["requested_to_target_area_ratio"] = safe_ratio(d["requested_area_sqm"], d["target_area_sqm"])
    d["log_requested_to_target_area_ratio"] = np.log(d["requested_to_target_area_ratio"].where(d["requested_to_target_area_ratio"] > 0))
    d["requested_rent_vs_initial_mid"] = safe_ratio(d["requested_rent_budget"], d["rent_budget_mid"])
    d["requested_sale_vs_initial_mid"] = safe_ratio(d["requested_sale_budget"], d["sale_budget_mid"])
    d["requested_rent_inside_initial_range"] = np.where(
        d["rent_budget_applicable"].eq(1) & d["requested_rent_budget"].notna(),
        (d["requested_rent_budget"] >= d["rent_budget_min_effective"]) & (d["requested_rent_budget"] <= d["rent_budget_max"]), np.nan,
    )
    d["requested_sale_inside_initial_range"] = np.where(
        d["sale_budget_applicable"].eq(1) & d["requested_sale_budget"].notna(),
        (d["requested_sale_budget"] >= d["sale_budget_min_effective"]) & (d["requested_sale_budget"] <= d["sale_budget_max"]), np.nan,
    )
    return d


def engineer_spots(spots: pd.DataFrame, attrs: pd.DataFrame) -> pd.DataFrame:
    s = spots.merge(attrs, on="spot_id", how="left", validate="one_to_one").copy()
    s["created_at"] = pd.to_datetime(s["created_at"], errors="raise")
    s["built_environment_applicable"] = ~s["sector_name"].eq("Land")
    parsed = s["amenities"].map(parse_amenities)
    s["amenities_count"] = parsed.map(len).astype(float)
    for amenity in AMENITY_VOCAB:
        s[f"amenity_{amenity}"] = parsed.map(lambda xs, a=amenity: float(a in xs))
    for c in ["luminaires", "charging_ports", "floor_level", "elevators", "vertical_height_m",
              "natural_light", "security_type", "building_status", "floor_material"]:
        s[f"model_{c}"] = s[c].where(s["built_environment_applicable"], np.nan)
    return s


def attach_spot_features(rows: pd.DataFrame, spot_features: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "spot_id", "broker_id", "sector_name", "type_name", "state", "municipality", "settlement", "corridor",
        "region", "lat", "lon", "area_sqm", "price_sqm_mxn_rent", "price_sqm_mxn_sale",
        "price_total_mxn_rent", "price_total_mxn_sale", "maintenance_cost_mxn", "modality", "created_at",
        "built_environment_applicable", "model_natural_light", "model_luminaires", "model_charging_ports",
        "model_security_type", "model_floor_level", "model_elevators", "model_vertical_height_m",
        "parking_spaces", "model_building_status", "model_floor_material", "amenities_count",
    ] + [f"amenity_{a}" for a in AMENITY_VOCAB]
    sf = spot_features[keep].rename(columns={c: f"spot_{c}" for c in keep if c != "spot_id"})
    d = rows.merge(sf, on="spot_id", how="left", validate="many_to_one").rename(columns={
        "spot_model_natural_light": "spot_natural_light", "spot_model_luminaires": "spot_luminaires",
        "spot_model_charging_ports": "spot_charging_ports", "spot_model_security_type": "spot_security_type",
        "spot_model_floor_level": "spot_floor_level", "spot_model_elevators": "spot_elevators",
        "spot_model_vertical_height_m": "spot_vertical_height_m", "spot_model_building_status": "spot_building_status",
        "spot_model_floor_material": "spot_floor_material",
    })
    d["spot_natural_light"] = parse_bool(d["spot_natural_light"])
    d["spot_built_environment_applicable"] = parse_bool(d["spot_built_environment_applicable"])
    d["spot_charging_ports_missing"] = d["spot_charging_ports"].isna().astype(float)
    d["spot_vertical_height_missing"] = d["spot_vertical_height_m"].isna().astype(float)
    d["log_spot_area_sqm"] = safe_log1p(d["spot_area_sqm"])
    for c in ["price_sqm_mxn_rent", "price_sqm_mxn_sale", "price_total_mxn_rent", "price_total_mxn_sale", "maintenance_cost_mxn"]:
        d[f"log_spot_{c}"] = safe_log1p(d[f"spot_{c}"])
    d["spot_effective_monthly_cost"] = safe_num(d["spot_price_total_mxn_rent"]) + safe_num(d["spot_maintenance_cost_mxn"])
    d["log_spot_effective_monthly_cost"] = safe_log1p(d["spot_effective_monthly_cost"])
    d["spot_age_at_score_days"] = (d["score_time"] - d["spot_created_at"]).dt.total_seconds() / 86400.0
    d["log_spot_luminaires"] = safe_log1p(d["spot_luminaires"])
    d["spot_luminaires_per_100_sqm"] = safe_ratio(d["spot_luminaires"], d["spot_area_sqm"]) * 100
    d["spot_charging_ports_per_100_sqm"] = safe_ratio(d["spot_charging_ports"], d["spot_area_sqm"]) * 100
    d["log_spot_elevators"] = safe_log1p(d["spot_elevators"])
    d["spot_elevators_per_1000_sqm"] = safe_ratio(d["spot_elevators"], d["spot_area_sqm"]) * 1000
    d["log_spot_parking_spaces"] = safe_log1p(d["spot_parking_spaces"])
    d["spot_parking_per_1000_sqm"] = safe_ratio(d["spot_parking_spaces"], d["spot_area_sqm"]) * 1000
    d["spot_floor_level_bucket"] = pd.cut(
        safe_num(d["spot_floor_level"]), [-np.inf, 0, 3, 10, np.inf], labels=["ground", "low", "mid", "high"]
    ).astype("string").fillna(UNKNOWN)
    return d


def attach_availability(rows: pd.DataFrame, availability: pd.DataFrame) -> pd.DataFrame:
    d, a = rows.copy(), availability.copy()
    a["snapshot_date"] = pd.to_datetime(a["snapshot_date"], errors="raise")
    left = d[["row_id", "spot_id", "score_time"]].dropna(subset=["spot_id", "score_time"]).copy()
    if left.empty:
        for c in ["availability_is_available", "availability_days_until_available", "availability_competing_inquiries_30d", "availability_snapshot_age_days"]:
            d[c] = np.nan
    else:
        left["spot_id"] = safe_num(left["spot_id"]).astype("int64")
        a["spot_id"] = safe_num(a["spot_id"]).astype("int64")
        matched = pd.merge_asof(
            left.sort_values(["score_time", "spot_id"]),
            a[["spot_id", "snapshot_date", "is_available", "days_until_available", "competing_inquiries_30d"]]
             .sort_values(["snapshot_date", "spot_id"]),
            left_on="score_time", right_on="snapshot_date", by="spot_id", direction="backward",
        )
        if (matched["snapshot_date"] > matched["score_time"]).fillna(False).any():
            raise AssertionError("Future availability snapshot used")
        matched["availability_snapshot_age_days"] = (matched["score_time"] - matched["snapshot_date"]).dt.total_seconds() / 86400.0
        matched = matched.set_index("row_id")
        mapper = d["row_id"]
        d["availability_is_available"] = mapper.map(parse_bool(matched["is_available"]))
        d["availability_days_until_available"] = mapper.map(safe_num(matched["days_until_available"]))
        d["availability_competing_inquiries_30d"] = mapper.map(safe_num(matched["competing_inquiries_30d"]))
        d["availability_snapshot_age_days"] = mapper.map(matched["availability_snapshot_age_days"])
    d["has_availability_context"] = d["availability_is_available"].notna().astype(float)
    d["log_availability_days_until_available"] = safe_log1p(d["availability_days_until_available"])
    d["log_availability_competing_inquiries_30d"] = safe_log1p(d["availability_competing_inquiries_30d"])
    d["availability_window"] = pd.cut(
        safe_num(d["availability_days_until_available"]), [-np.inf, 0, 30, 60, 90, np.inf],
        labels=["now", "1-30", "31-60", "61-90", ">90"],
    ).astype("string").fillna(UNKNOWN)
    d["availability_freshness"] = pd.cut(
        safe_num(d["availability_snapshot_age_days"]), [-np.inf, 30, 90, np.inf],
        labels=["fresh_30d", "stale_31_90d", "very_stale_gt90d"],
    ).astype("string").fillna(UNKNOWN)
    return d


def add_match_features(rows: pd.DataFrame) -> pd.DataFrame:
    d = rows.copy()
    has_spot = d["spot_id"].notna()
    def eq(a: str, b: str) -> pd.Series:
        return np.where(has_spot, d[a].astype("string").eq(d[b].astype("string")), np.nan)
    d["same_state"] = eq("preferred_state", "spot_state")
    d["same_municipality"] = eq("preferred_municipality", "spot_municipality")
    d["same_corridor"] = eq("preferred_corridor_fe", "spot_corridor")
    d["same_sector"] = eq("search_sector", "spot_sector_name")
    lm, sm = d["search_modality"].astype("string"), d["spot_modality"].astype("string")
    compatible = (lm.eq("rent") & sm.isin(["rent", "both"])) | (lm.eq("sale") & sm.isin(["sale", "both"])) | lm.eq("both")
    d["compatible_modality"] = np.where(has_spot, compatible, np.nan)
    d["requested_to_spot_area_ratio"] = safe_ratio(d["requested_area_sqm"], d["spot_area_sqm"])
    d["log_requested_to_spot_area_ratio"] = np.log(d["requested_to_spot_area_ratio"].where(d["requested_to_spot_area_ratio"] > 0))
    d["rent_budget_to_price_ratio"] = safe_ratio(d["requested_rent_budget"], d["spot_effective_monthly_cost"])
    d["sale_budget_to_price_ratio"] = safe_ratio(d["requested_sale_budget"], d["spot_price_total_mxn_sale"])
    d["rent_headroom_ratio"] = safe_ratio(d["requested_rent_budget"] - d["spot_effective_monthly_cost"], d["requested_rent_budget"])
    d["sale_headroom_ratio"] = safe_ratio(d["requested_sale_budget"] - d["spot_price_total_mxn_sale"], d["requested_sale_budget"])
    return d


def add_target(rows: pd.DataFrame, inquiries: pd.DataFrame, horizon_days: int = HORIZON_DAYS) -> pd.DataFrame:
    d = rows.copy()
    scheduled = inquiries[
        inquiries["broker_response"].eq("scheduled_visit") & inquiries["response_event_at"].notna()
    ][["lead_id", "response_event_at"]]
    ambiguous = inquiries[
        inquiries["broker_response"].eq("scheduled_visit") & inquiries["response_event_at"].isna()
    ][["lead_id", "inquiry_at"]]
    event_map = {
        k: np.sort(g["response_event_at"].to_numpy(dtype="datetime64[ns]"))
        for k, g in scheduled.groupby("lead_id")
    }
    ambiguous_map = {
        k: np.sort(g["inquiry_at"].to_numpy(dtype="datetime64[ns]"))
        for k, g in ambiguous.groupby("lead_id")
    }
    observation_end = max(inquiries["inquiry_at"].max(), inquiries["response_event_at"].max())
    cutoff = observation_end - pd.Timedelta(days=horizon_days)
    d["is_right_censored"] = (d["score_time"] > cutoff).astype(float)

    ys, ambiguous_flags = [], []
    for row in d.itertuples():
        t = np.datetime64(pd.Timestamp(row.score_time).to_datetime64())
        end = np.datetime64((pd.Timestamp(row.score_time) + pd.Timedelta(days=horizon_days)).to_datetime64())

        events = event_map.get(row.lead_id)
        positive = 0
        if events is not None and len(events):
            pos = np.searchsorted(events, t, side="right")
            positive = int(pos < len(events) and events[pos] <= end)
        ys.append(positive)

        ambiguous_times = ambiguous_map.get(row.lead_id)
        is_ambiguous = 0
        if positive == 0 and ambiguous_times is not None and len(ambiguous_times):
            pos = np.searchsorted(ambiguous_times, t, side="left")
            is_ambiguous = int(pos < len(ambiguous_times) and ambiguous_times[pos] <= end)
        ambiguous_flags.append(is_ambiguous)

    d["target_scheduled_visit_30d"] = ys
    d["label_time_ambiguous"] = ambiguous_flags
    d["observation_end"] = observation_end
    d["censor_cutoff"] = cutoff
    return d


def feature_columns_for_stage(stage_id: int) -> list[str]:
    if stage_id == 0:
        return BASE_FEATURES_T0
    if stage_id == 1:
        return BASE_FEATURES_T1
    if stage_id == 2:
        return BASE_FEATURES_T2
    raise ValueError(stage_id)


def assert_no_blocked_features(columns: Iterable[str]) -> None:
    bad = set(columns) & BLOCKED_RAW_FEATURES
    if bad:
        raise AssertionError(f"Blocked raw features in model feature set: {sorted(bad)}")
