from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HORIZON_DAYS = 30
STAGES = {0: "T0_cold", 1: "T1_first_inquiry", 2: "T2_engaged"}

LEAD_CAT = [
    "user_type", "company_size", "industry", "search_sector", "search_modality",
    "preferred_state", "preferred_municipality", "preferred_corridor", "source",
]
LEAD_NUM = [
    "target_area_sqm", "min_budget_mxn_rent_monthly", "max_budget_mxn_rent_monthly",
    "min_budget_mxn_sale_total", "max_budget_mxn_sale_total", "prior_searches",
    "prior_inquiries", "has_converted_before",
]
INQUIRY_CAT = ["channel", "asked_visit", "score_weekday"]
INQUIRY_NUM = [
    "message_length", "requested_area_sqm", "requested_budget_mxn_rent_monthly",
    "requested_budget_mxn_sale_total", "urgency_days", "score_hour", "score_month",
    "days_from_lead_creation", "inquiry_number",
]
SPOT_CAT = [
    "spot_sector_name", "spot_type_name", "spot_state", "spot_municipality",
    "spot_settlement", "spot_corridor", "spot_region", "spot_modality",
    "spot_natural_light", "spot_security_type", "spot_building_status", "spot_floor_material",
]
SPOT_NUM = [
    "spot_lat", "spot_lon", "spot_area_sqm", "spot_price_sqm_mxn_rent",
    "spot_price_sqm_mxn_sale", "spot_price_total_mxn_rent", "spot_price_total_mxn_sale",
    "spot_maintenance_cost_mxn", "spot_luminaires", "spot_charging_ports",
    "spot_floor_level", "spot_elevators", "spot_vertical_height_m", "spot_parking_spaces",
    "spot_amenities_count",
]
MATCH_CAT = [
    "same_preferred_municipality", "same_preferred_corridor", "same_sector", "compatible_modality",
]
MATCH_NUM = [
    "requested_to_spot_area_ratio", "rent_budget_to_price_ratio", "sale_budget_to_price_ratio",
]
AVAIL_CAT = ["availability_is_available"]
AVAIL_NUM = [
    "availability_days_until_available", "availability_competing_inquiries_30d",
    "availability_snapshot_age_days",
]
HISTORY_NUM = [
    "hist_prior_inquiries", "hist_prior_unique_spots", "hist_prior_asked_visit_rate",
    "hist_prior_message_length_mean", "hist_prior_urgency_mean", "hist_prior_realized_responses",
    "hist_prior_accepted_responses", "hist_prior_accept_rate", "hist_prior_median_response_hours",
    "days_since_first_inquiry",
]
CONTEXT_NUM = ["has_inquiry_context", "has_spot_context", "has_availability_context"]

CAT_FEATURES = LEAD_CAT + INQUIRY_CAT + SPOT_CAT + MATCH_CAT + AVAIL_CAT
NUM_FEATURES = LEAD_NUM + INQUIRY_NUM + SPOT_NUM + MATCH_NUM + AVAIL_NUM + HISTORY_NUM + CONTEXT_NUM

FORBIDDEN_COLUMNS = {
    "lead_score_internal", "broker_response", "broker_response_hours", "spot_days_on_market",
    "spot_total_inquiries", "spot_total_views", "spot_is_active",
}


def safe_ratio(a: pd.Series, b: pd.Series) -> pd.Series:
    return pd.to_numeric(a, errors="coerce") / pd.to_numeric(b, errors="coerce").replace(0, np.nan)


def amenities_count(value: object) -> float:
    if pd.isna(value):
        return math.nan
    try:
        parsed = json.loads(str(value))
        return float(len(parsed)) if isinstance(parsed, list) else math.nan
    except (json.JSONDecodeError, TypeError, ValueError):
        return math.nan


def read_data(root: Path) -> tuple[pd.DataFrame, ...]:
    data = root / "data" / "candidate" / "csv"
    leads = pd.read_csv(data / "leads.csv", parse_dates=["created_at"])
    inquiries = pd.read_csv(data / "inquiries.csv", parse_dates=["inquiry_at"])
    spots = pd.read_csv(data / "spots.csv", parse_dates=["created_at"])
    attrs = pd.read_csv(data / "spot_attributes.csv")
    availability = pd.read_csv(data / "availability_snapshot.csv", parse_dates=["snapshot_date"])
    return leads, inquiries, spots, attrs, availability


def prepare_inquiries(inquiries: pd.DataFrame) -> pd.DataFrame:
    d = inquiries.sort_values(["lead_id", "inquiry_at", "inquiry_id"]).copy()
    d["inquiry_number"] = d.groupby("lead_id").cumcount() + 1
    hours = pd.to_numeric(d["broker_response_hours"], errors="coerce")
    d["response_event_at"] = d["inquiry_at"] + pd.to_timedelta(hours, unit="h")
    d.loc[hours.isna(), "response_event_at"] = pd.NaT
    return d


def add_history_features(inquiries: pd.DataFrame) -> pd.DataFrame:
    d = inquiries.copy()
    hist = {col: pd.Series(np.nan, index=d.index, dtype=float) for col in HISTORY_NUM}

    for _, g in d.groupby("lead_id", sort=False):
        g = g.sort_values(["inquiry_at", "inquiry_id"])
        seen_spots: set[object] = set()
        asked, messages, urgencies = [], [], []
        first_time = g["inquiry_at"].iloc[0]

        for idx, row in g.iterrows():
            t = row["inquiry_at"]
            known = g[(g["inquiry_at"] < t) & g["response_event_at"].notna() & (g["response_event_at"] <= t)]
            accepted = known["broker_response"].eq("accepted")
            hist["hist_prior_inquiries"].at[idx] = len(asked)
            hist["hist_prior_unique_spots"].at[idx] = len(seen_spots)
            hist["hist_prior_asked_visit_rate"].at[idx] = np.nanmean(asked) if asked else np.nan
            hist["hist_prior_message_length_mean"].at[idx] = np.nanmean(messages) if messages else np.nan
            hist["hist_prior_urgency_mean"].at[idx] = np.nanmean(urgencies) if urgencies else np.nan
            hist["hist_prior_realized_responses"].at[idx] = len(known)
            hist["hist_prior_accepted_responses"].at[idx] = accepted.sum()
            hist["hist_prior_accept_rate"].at[idx] = accepted.mean() if len(known) else np.nan
            hist["hist_prior_median_response_hours"].at[idx] = (
                pd.to_numeric(known["broker_response_hours"], errors="coerce").median() if len(known) else np.nan
            )
            hist["days_since_first_inquiry"].at[idx] = (t - first_time).total_seconds() / 86400.0

            seen_spots.add(row["spot_id"])
            av = row.get("asked_visit")
            if pd.isna(av):
                asked.append(np.nan)
            elif isinstance(av, str):
                asked.append(float(av.strip().lower() in {"true", "1", "yes"}))
            else:
                asked.append(float(bool(av)))
            messages.append(pd.to_numeric(pd.Series([row.get("message_length")]), errors="coerce").iloc[0])
            urgencies.append(pd.to_numeric(pd.Series([row.get("urgency_days")]), errors="coerce").iloc[0])

    for col, values in hist.items():
        d[col] = values
    return d


def attach_spots(rows: pd.DataFrame, spots: pd.DataFrame, attrs: pd.DataFrame) -> pd.DataFrame:
    spot_cols = [
        "spot_id", "sector_name", "type_name", "state", "municipality", "settlement", "corridor",
        "region", "lat", "lon", "area_sqm", "price_sqm_mxn_rent", "price_sqm_mxn_sale",
        "price_total_mxn_rent", "price_total_mxn_sale", "maintenance_cost_mxn", "modality",
    ]
    s = spots[spot_cols].rename(columns={c: f"spot_{c}" for c in spot_cols if c != "spot_id"})

    a = attrs.copy()
    a["amenities_count"] = a["amenities"].map(amenities_count)
    attr_cols = [
        "spot_id", "natural_light", "luminaires", "charging_ports", "security_type", "floor_level",
        "elevators", "vertical_height_m", "parking_spaces", "building_status", "floor_material",
        "amenities_count",
    ]
    a = a[attr_cols].rename(columns={c: f"spot_{c}" for c in attr_cols if c != "spot_id"})
    out = rows.merge(s, on="spot_id", how="left").merge(a, on="spot_id", how="left")
    out["has_spot_context"] = out["spot_id"].notna().astype(float)
    return out


def attach_availability(rows: pd.DataFrame, availability: pd.DataFrame) -> pd.DataFrame:
    out = rows.copy()
    for col in [
        "availability_is_available", "availability_days_until_available",
        "availability_competing_inquiries_30d", "availability_snapshot_age_days",
    ]:
        out[col] = np.nan

    mask = out["spot_id"].notna() & out["score_time"].notna()
    if mask.any():
        left = out.loc[mask, ["row_id", "spot_id", "score_time"]].copy()
        right = availability[[
            "spot_id", "snapshot_date", "is_available", "days_until_available", "competing_inquiries_30d"
        ]].copy()
        left["spot_id"] = pd.to_numeric(left["spot_id"], errors="coerce")
        right["spot_id"] = pd.to_numeric(right["spot_id"], errors="coerce")
        matched = pd.merge_asof(
            left.sort_values(["score_time", "spot_id"]),
            right.sort_values(["snapshot_date", "spot_id"]),
            left_on="score_time", right_on="snapshot_date", by="spot_id", direction="backward",
        ).set_index("row_id")
        matched["snapshot_age"] = (
            matched["score_time"] - matched["snapshot_date"]
        ).dt.total_seconds() / 86400.0
        mapper = out["row_id"]
        out["availability_is_available"] = mapper.map(matched["is_available"])
        out["availability_days_until_available"] = mapper.map(matched["days_until_available"])
        out["availability_competing_inquiries_30d"] = mapper.map(matched["competing_inquiries_30d"])
        out["availability_snapshot_age_days"] = mapper.map(matched["snapshot_age"])

    out["has_availability_context"] = out["availability_is_available"].notna().astype(float)
    return out


def add_match_features(d: pd.DataFrame) -> pd.DataFrame:
    out = d.copy()
    has_spot = out["spot_id"].notna()
    out["same_preferred_municipality"] = np.where(
        has_spot, out["preferred_municipality"].astype("string").eq(out["spot_municipality"].astype("string")), np.nan
    )
    out["same_preferred_corridor"] = np.where(
        has_spot, out["preferred_corridor"].astype("string").eq(out["spot_corridor"].astype("string")), np.nan
    )
    out["same_sector"] = np.where(
        has_spot, out["search_sector"].astype("string").eq(out["spot_sector_name"].astype("string")), np.nan
    )
    lead_mod, spot_mod = out["search_modality"].astype("string"), out["spot_modality"].astype("string")
    compatible = (
        (lead_mod.eq("rent") & spot_mod.isin(["rent", "both"]))
        | (lead_mod.eq("sale") & spot_mod.isin(["sale", "both"]))
        | lead_mod.eq("both")
    )
    out["compatible_modality"] = np.where(has_spot, compatible, np.nan)
    out["requested_to_spot_area_ratio"] = safe_ratio(out["requested_area_sqm"], out["spot_area_sqm"])
    out["rent_budget_to_price_ratio"] = safe_ratio(
        out["requested_budget_mxn_rent_monthly"], out["spot_price_total_mxn_rent"]
    )
    out["sale_budget_to_price_ratio"] = safe_ratio(
        out["requested_budget_mxn_sale_total"], out["spot_price_total_mxn_sale"]
    )
    return out


def add_targets(snapshots: pd.DataFrame, inquiries: pd.DataFrame) -> pd.DataFrame:
    scheduled = inquiries[
        inquiries["broker_response"].eq("scheduled_visit") & inquiries["response_event_at"].notna()
    ][["lead_id", "response_event_at"]]
    event_map = {
        lead: np.sort(g["response_event_at"].to_numpy(dtype="datetime64[ns]"))
        for lead, g in scheduled.groupby("lead_id")
    }
    observation_end = max(inquiries["inquiry_at"].max(), inquiries["response_event_at"].max())
    cutoff = observation_end - pd.Timedelta(days=HORIZON_DAYS)
    d = snapshots[snapshots["score_time"] <= cutoff].copy()
    targets = []
    for row in d.itertuples():
        events = event_map.get(row.lead_id)
        if events is None or len(events) == 0:
            targets.append(0)
            continue
        t = np.datetime64(pd.Timestamp(row.score_time).to_datetime64())
        end = np.datetime64((pd.Timestamp(row.score_time) + pd.Timedelta(days=HORIZON_DAYS)).to_datetime64())
        pos = np.searchsorted(events, t, side="right")
        targets.append(int(pos < len(events) and events[pos] <= end))
    d["target_30d"] = targets
    d["observation_end"] = observation_end
    d["censor_cutoff"] = cutoff
    return d


def build_snapshots(
    leads: pd.DataFrame, inquiries: pd.DataFrame, spots: pd.DataFrame,
    attrs: pd.DataFrame, availability: pd.DataFrame,
) -> pd.DataFrame:
    inquiries = add_history_features(inquiries)
    conversion = (
        inquiries[inquiries["broker_response"].eq("scheduled_visit") & inquiries["response_event_at"].notna()]
        .groupby("lead_id")["response_event_at"].min().rename("first_conversion_at")
    )

    t0 = leads.copy()
    t0["stage_id"], t0["stage"], t0["score_time"] = 0, STAGES[0], t0["created_at"]
    t0["spot_id"], t0["inquiry_id"], t0["inquiry_number"] = np.nan, np.nan, 0.0
    for col in [
        "channel", "asked_visit", "message_length", "requested_area_sqm",
        "requested_budget_mxn_rent_monthly", "requested_budget_mxn_sale_total", "urgency_days",
    ] + HISTORY_NUM:
        t0[col] = np.nan
    t0["has_inquiry_context"] = 0.0

    dyn = inquiries.merge(leads, on="lead_id", how="left", suffixes=("", "_lead")).merge(
        conversion, on="lead_id", how="left"
    )
    dyn = dyn[dyn["first_conversion_at"].isna() | (dyn["inquiry_at"] < dyn["first_conversion_at"])].copy()
    dyn["score_time"], dyn["has_inquiry_context"] = dyn["inquiry_at"], 1.0
    dyn["stage_id"] = np.where(dyn["inquiry_number"].eq(1), 1, 2)
    dyn["stage"] = dyn["stage_id"].map(STAGES)

    cols = sorted(set(t0.columns) | set(dyn.columns))
    snapshots = pd.concat([t0.reindex(columns=cols), dyn.reindex(columns=cols)], ignore_index=True)
    snapshots["row_id"] = np.arange(len(snapshots))
    snapshots = attach_spots(snapshots, spots, attrs)
    snapshots = attach_availability(snapshots, availability)
    snapshots = add_match_features(snapshots)
    snapshots["score_hour"] = snapshots["score_time"].dt.hour.astype(float)
    snapshots["score_month"] = snapshots["score_time"].dt.month.astype(float)
    snapshots["score_weekday"] = snapshots["score_time"].dt.day_name()
    snapshots["days_from_lead_creation"] = (
        snapshots["score_time"] - snapshots["created_at"]
    ).dt.total_seconds() / 86400.0

    for col in ["has_converted_before", "spot_natural_light", "availability_is_available"]:
        snapshots[col] = snapshots[col].map(
            lambda x: np.nan if pd.isna(x) else float(str(x).strip().lower() in {"true", "1", "yes"})
        )
    return add_targets(snapshots, inquiries)


def temporal_split(snapshots: pd.DataFrame) -> pd.DataFrame:
    leads = snapshots[["lead_id", "created_at"]].drop_duplicates("lead_id").sort_values(
        ["created_at", "lead_id"]
    ).reset_index(drop=True)
    n = len(leads)
    a, b = max(1, int(n * 0.70)), min(max(2, int(n * 0.85)), n - 1)
    labels = np.full(n, "test", dtype=object)
    labels[:a], labels[a:b] = "train", "val"
    leads["split"] = labels
    return snapshots.merge(leads[["lead_id", "split"]], on="lead_id", how="left")


def make_preprocessor() -> ColumnTransformer:
    cat = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=5, sparse_output=False, dtype=np.float32)),
    ])
    num = Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
    ])
    return ColumnTransformer(
        [("cat", cat, CAT_FEATURES), ("num", num, NUM_FEATURES)],
        remainder="drop", sparse_threshold=0.0,
    )


def stage_balanced_weights(df: pd.DataFrame) -> np.ndarray:
    per_lead_stage = df.groupby(["stage_id", "lead_id"])["row_id"].transform("count").astype(float)
    base = (1.0 / per_lead_stage).reset_index(drop=True)
    stage = df["stage_id"].reset_index(drop=True)
    stage_totals = base.groupby(stage).transform("sum")
    weights = base / stage_totals
    return (weights * (len(weights) / weights.sum())).to_numpy(dtype=np.float32)
