from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .contracts import Settings
from .data import load_all
from .features import add_clean_t2_history, add_t1_features
from .targets import add_t1_target, add_t2_target, build_t0_target, first_inquiries


def attach_availability_backward(rows: pd.DataFrame, availability: pd.DataFrame, *, row_key: str) -> pd.DataFrame:
    required = {row_key, "spot_id", "prediction_timestamp"}
    if not required.issubset(rows.columns):
        raise KeyError(f"Rows missing columns: {sorted(required - set(rows.columns))}")
    left = rows.copy()
    left["spot_id"] = pd.to_numeric(left["spot_id"], errors="raise").astype("int64")
    right = availability[["spot_id", "snapshot_id", "snapshot_date", "is_available", "days_until_available"]].copy()
    right["spot_id"] = pd.to_numeric(right["spot_id"], errors="raise").astype("int64")
    matched = pd.merge_asof(
        left.sort_values(["prediction_timestamp", "spot_id"], kind="mergesort"),
        right.sort_values(["snapshot_date", "spot_id"], kind="mergesort"),
        left_on="prediction_timestamp",
        right_on="snapshot_date",
        by="spot_id",
        direction="backward",
        allow_exact_matches=True,
    )
    if (matched["snapshot_date"] > matched["prediction_timestamp"]).fillna(False).any():
        raise AssertionError("Future availability snapshot detected")
    matched["availability_snapshot_age_days"] = (
        matched["prediction_timestamp"] - matched["snapshot_date"]
    ).dt.total_seconds() / 86400.0
    return matched.sort_values(row_key).reset_index(drop=True)


def build_t1_abt(settings: Settings, tables: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    tables = tables or load_all(settings)
    leads, inquiries, spots, attrs, availability = (
        tables["leads"], tables["inquiries"], tables["spots"], tables["spot_attributes"], tables["availability_snapshot"]
    )
    first = add_t1_target(first_inquiries(inquiries), settings).rename(columns={"inquiry_at": "prediction_timestamp"})
    lead_frame = leads.rename(columns={"created_at": "lead_created_at"})
    spot_static = spots.drop(columns=["days_on_market", "total_inquiries", "total_views", "is_active", "title", "description"])
    spot_static = spot_static.rename(columns={"created_at": "spot_created_at"})
    spot_static = spot_static.rename(columns={column: f"spot_{column}" for column in spot_static.columns if column not in {"spot_id", "spot_created_at"}})
    attr_static = attrs.rename(columns={column: f"spot_attr_{column}" for column in attrs.columns if column != "spot_id"})
    result = first.merge(lead_frame, on="lead_id", how="left", validate="one_to_one")
    result = result.merge(spot_static, on="spot_id", how="left", validate="many_to_one")
    result = result.merge(attr_static, on="spot_id", how="left", validate="many_to_one")
    if (result["spot_created_at"] > result["prediction_timestamp"]).fillna(False).any():
        raise AssertionError("Requested spot did not exist at T1")
    result = attach_availability_backward(result, availability, row_key="inquiry_id")
    result = add_t1_features(result)
    result["prediction_stage"] = "T1_first_inquiry"
    if len(result) != len(leads) or not result["lead_id"].is_unique:
        raise AssertionError("T1 ABT must contain exactly one row per lead")
    return result


def build_t0_abt(settings: Settings, tables: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    tables = tables or load_all(settings)
    leads, inquiries = tables["leads"], tables["inquiries"]
    target = build_t0_target(leads, inquiries, settings)
    result = leads.merge(target[["lead_id", "target_t0_30d", "target_mature"]], on="lead_id", validate="one_to_one")
    result = result.rename(columns={"created_at": "prediction_timestamp"})
    result["prediction_stage"] = "T0_lead_creation"
    return result


def build_t2_abt(settings: Settings, tables: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    tables = tables or load_all(settings)
    history = add_clean_t2_history(tables["inquiries"])
    target = add_t2_target(tables["inquiries"], settings)[["inquiry_id", "target_t2", "target_mature", "inquiry_number"]]
    result = history.merge(target, on="inquiry_id", how="inner", validate="one_to_one", suffixes=("", "_target"))
    result = result.merge(tables["leads"].rename(columns={"created_at": "lead_created_at"}), on="lead_id", how="left", validate="many_to_one")
    result = result.rename(columns={"inquiry_at": "prediction_timestamp"})
    result = add_t1_features(result)
    result["prediction_stage"] = "T2_rescore"
    return result


def assign_t1_split(frame: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    result = frame.copy()
    timestamp = result["prediction_timestamp"]
    split = settings.split
    conditions = [
        timestamp.ge(split.train_start) & timestamp.lt(split.train_end_exclusive),
        timestamp.ge(split.validation_start) & timestamp.lt(split.validation_end_exclusive),
        timestamp.ge(split.test_start) & timestamp.lt(split.test_end_exclusive),
    ]
    result["split"] = np.select(conditions, ["train", "validation", "test"], default="purge_or_censored")
    result.loc[result["target_t1"].isna(), "split"] = "censored"
    return result


def write_abts(settings: Settings) -> dict[str, Path]:
    output_dir = settings.codexway_root / "outputs" / "abt"
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = load_all(settings)
    frames = {
        "abt_t0_lead_creation": build_t0_abt(settings, tables),
        "abt_t1_first_inquiry": assign_t1_split(build_t1_abt(settings, tables), settings),
        "abt_t2_rescore": build_t2_abt(settings, tables),
    }
    paths = {}
    for name, frame in frames.items():
        path = output_dir / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        paths[name] = path
    return paths

