from __future__ import annotations

from pathlib import Path
from typing import Iterable
import polars as pl

MATURITY_DAYS = 14
T0_HORIZON_DAYS = 30

LEAD_QUALITY_FEATURES = [
    "user_type",
    "company_size",
    "industry",
    "search_sector",
    "search_modality",
    "target_area_sqm",
    "min_budget_mxn_rent_monthly",
    "max_budget_mxn_rent_monthly",
    "min_budget_mxn_sale_total",
    "max_budget_mxn_sale_total",
    "preferred_state",
    "preferred_municipality",
    "preferred_corridor",
    "source",
]

LEAD_AUDIT_ONLY = ["prior_searches", "prior_inquiries", "has_converted_before"]

CURRENT_INQUIRY_FEATURES = [
    "channel",
    "message_length",
    "requested_area_sqm",
    "requested_budget_mxn_rent_monthly",
    "requested_budget_mxn_sale_total",
    "urgency_days",
    "asked_visit",
]

HISTORY_FEATURES = [
    "hist_prior_inquiry_count",
    "hist_prior_unique_spots",
    "hist_prior_asked_visit_count",
    "hist_prior_asked_visit_rate",
    "hist_prior_message_length_mean",
    "hist_prior_urgency_known_count",
    "hist_prior_urgency_days_mean",
]

FORBIDDEN_RAW_FEATURES = {
    "lead_score_internal",
    "broker_response",
    "broker_response_hours",
    "days_on_market",
    "total_views",
    "total_inquiries",
    "is_active",
    "competing_inquiries_30d",
    "similar_available_spots",
    "avg_price_sqm_mxn",
    "recent_occupancy_rate",
    "absorption_velocity_days",
    "recent_inquiry_volume",
}

UNVERSIONED_SPOT_FIELDS = {
    "broker_id",
    "title",
    "description",
    "price_sqm_mxn_rent",
    "price_sqm_mxn_sale",
    "price_total_mxn_rent",
    "price_total_mxn_sale",
    "maintenance_cost_mxn",
}

SPOT_STRUCTURAL_FIELDS = [
    "sector_name",
    "type_name",
    "state",
    "municipality",
    "settlement",
    "corridor",
    "region",
    "lat",
    "lon",
    "area_sqm",
    "modality",
]

SPOT_ATTRIBUTE_FIELDS = [
    "natural_light",
    "luminaires",
    "charging_ports",
    "security_type",
    "floor_level",
    "elevators",
    "vertical_height_m",
    "parking_spaces",
    "building_status",
    "floor_material",
    "amenities",
]


def raw_root(repo_root: Path) -> Path:
    return repo_root / "data" / "candidate"


def read_raw(repo_root: Path, name: str) -> pl.DataFrame:
    root = raw_root(repo_root)
    parquet = root / "parquet" / f"{name}.parquet"
    csv = root / "csv" / f"{name}.csv"
    if parquet.exists():
        return pl.read_parquet(parquet)
    if csv.exists():
        return pl.read_csv(csv, infer_schema_length=10_000)
    raise FileNotFoundError(f"Raw source not found for {name}: {parquet} or {csv}")


def parse_datetime(df: pl.DataFrame, column: str, alias: str | None = None) -> pl.DataFrame:
    alias = alias or column
    dtype = df.schema[column]
    if dtype == pl.String:
        return df.with_columns(pl.col(column).str.to_datetime(strict=True).alias(alias))
    if dtype == pl.Date:
        return df.with_columns(pl.col(column).cast(pl.Datetime).alias(alias))
    return df.with_columns(pl.col(column).cast(pl.Datetime).alias(alias))


def parse_date(df: pl.DataFrame, column: str, alias: str | None = None) -> pl.DataFrame:
    alias = alias or column
    dtype = df.schema[column]
    if dtype == pl.String:
        return df.with_columns(pl.col(column).str.to_date(strict=True).alias(alias))
    return df.with_columns(pl.col(column).cast(pl.Date).alias(alias))


def load_leads(repo_root: Path) -> pl.DataFrame:
    return parse_datetime(read_raw(repo_root, "leads"), "created_at", "lead_created_at")


def load_inquiries(repo_root: Path) -> pl.DataFrame:
    iq = parse_datetime(read_raw(repo_root, "inquiries"), "inquiry_at", "_inquiry_time")
    return (
        iq.sort(["lead_id", "_inquiry_time", "inquiry_id"])
        .with_columns(pl.int_range(1, pl.len() + 1).over("lead_id").alias("inquiry_number"))
    )


def load_spots(repo_root: Path) -> pl.DataFrame:
    return parse_datetime(read_raw(repo_root, "spots"), "created_at", "spot_created_at")


def activity_horizon(inquiries: pl.DataFrame):
    return inquiries["_inquiry_time"].max()


def target_status_expr(response_column: str, score_time_column: str, horizon) -> pl.Expr:
    mature = (
        pl.col(score_time_column) + pl.duration(days=MATURITY_DAYS) <= pl.lit(horizon)
    )
    return (
        pl.when(~mature)
        .then(pl.lit("CENSORED"))
        .when(pl.col(response_column).is_null())
        .then(pl.lit("AMBIGUOUS"))
        .when(pl.col(response_column) == "scheduled_visit")
        .then(pl.lit("POSITIVE"))
        .otherwise(pl.lit("NEGATIVE"))
    )


def add_binary_target(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.when(pl.col("target_status") == "POSITIVE")
        .then(pl.lit(1))
        .when(pl.col("target_status") == "NEGATIVE")
        .then(pl.lit(0))
        .otherwise(pl.lit(None))
        .cast(pl.Int8)
        .alias("target_value")
    )


def model_ready_filter(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter(pl.col("target_status").is_in(["POSITIVE", "NEGATIVE"]))


def assert_columns_absent(df: pl.DataFrame, forbidden: Iterable[str], context: str) -> None:
    overlap = sorted(set(df.columns).intersection(forbidden))
    if overlap:
        raise AssertionError(f"{context}: forbidden columns present: {overlap}")


def ensure_output_dir(repo_root: Path) -> Path:
    out = repo_root / "AssessmentSol1" / "abt" / "artifacts"
    out.mkdir(parents=True, exist_ok=True)
    return out
