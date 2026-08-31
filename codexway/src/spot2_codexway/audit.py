from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .contracts import Settings
from .data import TABLES, canonical_csv_frame, dataframe_fingerprint, load_all
from .targets import add_t1_target, first_inquiries


PRIMARY_KEYS = {
    "leads": ["lead_id"],
    "inquiries": ["inquiry_id"],
    "spots": ["spot_id"],
    "spot_attributes": ["spot_id"],
    "availability_snapshot": ["snapshot_id"],
    "market_context": ["state", "municipality", "corridor", "sector", "month"],
}


def _json_value(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if np.isnan(value) else float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def run_audit(settings: Settings) -> dict[str, Any]:
    tables = load_all(settings)
    table_profiles: dict[str, Any] = {}
    duplicate_formats: dict[str, bool] = {}
    for name in TABLES:
        frame = tables[name]
        key = PRIMARY_KEYS[name]
        duplicate_formats[name] = dataframe_fingerprint(frame) == dataframe_fingerprint(canonical_csv_frame(settings, name))
        profile = {
            "rows": len(frame),
            "columns": len(frame.columns),
            "primary_key": key,
            "primary_key_unique": not frame.duplicated(key).any(),
            "missing_fraction": {column: float(frame[column].isna().mean()) for column in frame.columns},
        }
        for column in frame.select_dtypes(include=["datetime", "datetimetz"]).columns:
            profile[f"{column}_min"] = frame[column].min()
            profile[f"{column}_max"] = frame[column].max()
        table_profiles[name] = profile

    leads, inquiries, spots, attrs, availability = (
        tables["leads"], tables["inquiries"], tables["spots"], tables["spot_attributes"], tables["availability_snapshot"]
    )
    first = add_t1_target(first_inquiries(inquiries), settings)
    mature = first[first["target_t1"].notna()]
    inquiry_lead = inquiries.merge(leads[["lead_id", "created_at"]], on="lead_id", how="left", validate="many_to_one")
    inquiry_spot = inquiries.merge(spots[["spot_id", "created_at"]], on="spot_id", how="left", validate="many_to_one")
    t0_spot_future = inquiry_lead.merge(spots[["spot_id", "created_at"]], on="spot_id", suffixes=("_lead", "_spot"), validate="many_to_one")

    response_hours = inquiries["broker_response_hours"].notna()
    relationship_checks = {
        "inquiries_lead_fk_missing": int((~inquiries["lead_id"].isin(leads["lead_id"])).sum()),
        "inquiries_spot_fk_missing": int((~inquiries["spot_id"].isin(spots["spot_id"])).sum()),
        "attributes_spot_fk_missing": int((~attrs["spot_id"].isin(spots["spot_id"])).sum()),
        "availability_spot_fk_missing": int((~availability["spot_id"].isin(spots["spot_id"])).sum()),
        "inquiries_before_lead_creation": int((inquiry_lead["inquiry_at"] < inquiry_lead["created_at"]).sum()),
        "spots_created_after_inquiry": int((inquiry_spot["created_at"] > inquiry_spot["inquiry_at"]).sum()),
        "inquiry_spot_not_available_at_lead_creation": int((t0_spot_future["created_at_spot"] > t0_spot_future["created_at_lead"]).sum()),
        "no_response_with_hours": int((inquiries["broker_response"].eq("no_response") & response_hours).sum()),
        "response_without_hours": int((~inquiries["broker_response"].eq("no_response") & ~response_hours).sum()),
    }
    report = {
        "canonical_format": "parquet",
        "duplicate_formats_equal": duplicate_formats,
        "tables": table_profiles,
        "relationships": relationship_checks,
        "t1_contract": {
            "rows_all": len(first),
            "rows_mature": len(mature),
            "positives": int(mature["target_t1"].sum()),
            "positive_rate": float(mature["target_t1"].mean()),
            "right_censored": int(first["target_t1"].isna().sum()),
        },
    }
    return json.loads(json.dumps(report, default=_json_value))


def write_audit(settings: Settings, output: Path | None = None) -> Path:
    output = output or settings.codexway_root / "outputs" / "tables" / "data_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(run_audit(settings), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output

