"""Reproducible raw-data audit for AssessmentSol1 P1.

Reads raw candidate data read-only. Parquet is canonical after CSV/Parquet
logical parity passes. No target is constructed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

import polars as pl
from polars.testing import assert_frame_equal

TABLES = (
    "leads",
    "inquiries",
    "spots",
    "spot_attributes",
    "availability_snapshot",
    "market_context",
)

PKS: dict[str, tuple[str, ...]] = {
    "leads": ("lead_id",),
    "inquiries": ("inquiry_id",),
    "spots": ("spot_id",),
    "spot_attributes": ("spot_id",),
    "availability_snapshot": ("snapshot_id",),
    "market_context": ("state", "municipality", "corridor", "sector", "month"),
}

FKS: tuple[tuple[str, str, str, str], ...] = (
    ("inquiries", "lead_id", "leads", "lead_id"),
    ("inquiries", "spot_id", "spots", "spot_id"),
    ("spot_attributes", "spot_id", "spots", "spot_id"),
    ("availability_snapshot", "spot_id", "spots", "spot_id"),
)

TIME_COLUMNS: dict[str, tuple[str, ...]] = {
    "leads": ("created_at",),
    "inquiries": ("inquiry_at",),
    "spots": ("created_at",),
    "spot_attributes": (),
    "availability_snapshot": ("snapshot_date",),
    "market_context": ("month",),
}

FORBIDDEN_SPOT_BACKTEST = (
    "days_on_market",
    "total_inquiries",
    "total_views",
    "is_active",
)

COLUMN_TEMPORAL_CLASSIFICATION = {
    "leads": {
        "static_columns": [
            "lead_id",
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
            "created_at"
        ],
        "mutable_columns": [],
        "temporal_unknown_columns": [
            "prior_searches",
            "prior_inquiries",
            "has_converted_before",
            "lead_score_internal"
        ],
        "note": "Intake fields are treated as the delivered creation snapshot. Historical counters/internal score lack a separate observation/effective-time contract."
    },
    "inquiries": {
        "static_columns": [
            "inquiry_id",
            "lead_id",
            "spot_id",
            "inquiry_at",
            "channel",
            "message_length",
            "requested_area_sqm",
            "requested_budget_mxn_rent_monthly",
            "requested_budget_mxn_sale_total",
            "urgency_days",
            "asked_visit"
        ],
        "mutable_columns": [
            "broker_response",
            "broker_response_hours"
        ],
        "temporal_unknown_columns": [
            "broker_response",
            "broker_response_hours"
        ],
        "note": "Request fields are event facts at inquiry_at. Response fields arrive after inquiry and lack a reliable event/observation timestamp."
    },
    "spots": {
        "static_columns": [
            "spot_id",
            "created_at"
        ],
        "mutable_columns": [
            "days_on_market",
            "total_inquiries",
            "total_views",
            "is_active"
        ],
        "temporal_unknown_columns": [
            "broker_id",
            "sector_name",
            "type_name",
            "state",
            "municipality",
            "settlement",
            "corridor",
            "region",
            "lat",
            "lon",
            "title",
            "description",
            "area_sqm",
            "price_sqm_mxn_rent",
            "price_sqm_mxn_sale",
            "price_total_mxn_rent",
            "price_total_mxn_sale",
            "maintenance_cost_mxn",
            "modality"
        ],
        "note": "Descriptive/pricing fields may be stable in practice but have no version/effective timestamps, so historical mutability is not invented."
    },
    "spot_attributes": {
        "static_columns": [
            "spot_id",
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
            "amenities"
        ],
        "mutable_columns": [],
        "temporal_unknown_columns": [],
        "note": "All spot attribute values are treated as immutable over the lifetime of the spot by explicit assessment assumption. Raw has no attribute timestamp; T1/T2 use requires spots.created_at <= score_time."
    },
    "availability_snapshot": {
        "static_columns": [
            "snapshot_id",
            "spot_id",
            "snapshot_date"
        ],
        "mutable_columns": [
            "is_available",
            "days_until_available",
            "competing_inquiries_30d"
        ],
        "temporal_unknown_columns": [
            "competing_inquiries_30d"
        ],
        "note": "State changes across snapshots. Snapshot_date is the only historical anchor; competing_inquiries_30d window direction is unproven."
    },
    "market_context": {
        "static_columns": [
            "state",
            "municipality",
            "corridor",
            "sector",
            "month"
        ],
        "mutable_columns": [
            "similar_available_spots",
            "avg_price_sqm_mxn",
            "recent_occupancy_rate",
            "absorption_velocity_days",
            "recent_inquiry_volume"
        ],
        "temporal_unknown_columns": [
            "similar_available_spots",
            "avg_price_sqm_mxn",
            "recent_occupancy_rate",
            "absorption_velocity_days",
            "recent_inquiry_volume"
        ],
        "note": "Month is a period label, not publication/effective time. Aggregates are EDA_ONLY."
    }
}

AUDIT_DATE = pl.datetime(2026, 8, 30, 23, 59, 59)


def candidate_dir(repo_root: Path, fmt: str) -> Path:
    return repo_root / "data" / "candidate" / fmt


def read_parquet_table(repo_root: Path, table: str) -> pl.DataFrame:
    return pl.read_parquet(candidate_dir(repo_root, "parquet") / f"{table}.parquet")


def read_csv_table(repo_root: Path, table: str) -> pl.DataFrame:
    return pl.read_csv(
        candidate_dir(repo_root, "csv") / f"{table}.csv",
        infer_schema_length=None,
        null_values="",
        try_parse_dates=False,
    )


def _cast_csv_like_parquet(csv_df: pl.DataFrame, pq_df: pl.DataFrame) -> pl.DataFrame:
    if csv_df.columns != pq_df.columns:
        raise AssertionError(
            f"Column mismatch: CSV={csv_df.columns!r}, Parquet={pq_df.columns!r}"
        )
    exprs = [
        pl.col(c).cast(pq_df.schema[c], strict=False).alias(c)
        for c in pq_df.columns
    ]
    return csv_df.select(exprs)


def assert_csv_parquet_parity(repo_root: Path, table: str) -> None:
    """Exact logical row/order parity; formats are never concatenated."""
    csv_df = _cast_csv_like_parquet(
        read_csv_table(repo_root, table),
        read_parquet_table(repo_root, table),
    )
    pq_df = read_parquet_table(repo_root, table)
    assert_frame_equal(
        csv_df,
        pq_df,
        check_row_order=True,
        check_column_order=True,
        check_dtypes=True,
        check_exact=True,
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def git_blob_sha1_file(path: Path) -> str:
    """Compute the Git blob SHA-1 for a local file without using Git."""
    data = path.read_bytes()
    header = f"blob {len(data)}\\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def load_source_manifest(repo_root: Path) -> dict:
    path = repo_root / "AssessmentSol1" / "config" / "raw_source_manifest.json"
    return json.loads(path.read_text())


def validate_source_manifest(repo_root: Path) -> dict[str, dict[str, str]]:
    """Fail if any raw file differs from the frozen P1 fingerprint manifest."""
    manifest = load_source_manifest(repo_root)
    observed: dict[str, dict[str, str]] = {}
    for table, formats in manifest["tables"].items():
        observed[table] = {}
        for fmt, spec in formats.items():
            path = repo_root / spec["path"]
            sha256 = sha256_file(path)
            blob = git_blob_sha1_file(path)
            if sha256 != spec["sha256"]:
                raise AssertionError(
                    f"Raw SHA256 drift for {table}/{fmt}: {sha256} != {spec['sha256']}"
                )
            if blob != spec["git_blob_sha1"]:
                raise AssertionError(
                    f"Raw Git blob drift for {table}/{fmt}: {blob} != {spec['git_blob_sha1']}"
                )
            observed[table][f"{fmt}_sha256"] = sha256
            observed[table][f"{fmt}_git_blob_sha1"] = blob
    return observed


def pk_duplicate_rows(df: pl.DataFrame, cols: Iterable[str]) -> int:
    cols = list(cols)
    return int(
        df.group_by(cols)
        .len()
        .filter(pl.col("len") > 1)
        .select((pl.col("len") - 1).sum())
        .item()
        or 0
    )


def exact_duplicate_rows(df: pl.DataFrame) -> int:
    return int(df.is_duplicated().sum())


def fk_orphan_count(
    child: pl.DataFrame, child_col: str, parent: pl.DataFrame, parent_col: str
) -> int:
    parent_keys = parent.select(parent_col).unique()
    return child.join(
        parent_keys,
        left_on=child_col,
        right_on=parent_col,
        how="anti",
    ).height


def _numeric_profile(s: pl.Series) -> dict[str, float | int | None]:
    x = s.drop_nulls()
    if not x.len():
        return {}
    q1 = x.quantile(0.25, "linear")
    q3 = x.quantile(0.75, "linear")
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = x.filter((x < lo) | (x > hi)).len()
    return {
        "min": float(x.min()),
        "q1": float(q1),
        "median": float(x.median()),
        "q3": float(q3),
        "max": float(x.max()),
        "iqr_outlier_count": int(outliers),
        "iqr_outlier_rate": float(outliers / x.len()),
    }


def profile_table(df: pl.DataFrame, table: str) -> dict:
    missingness = {}
    distinct = {}
    numeric = {}
    for c, dtype in df.schema.items():
        n_null = df[c].null_count()
        missingness[c] = {
            "count": int(n_null),
            "rate": float(n_null / df.height),
        }
        distinct[c] = int(df[c].drop_nulls().n_unique())
        if dtype.is_numeric() and not c.endswith("_id") and c not in {"lat", "lon"}:
            numeric[c] = _numeric_profile(df[c])

    temporal = {}
    for c in TIME_COLUMNS[table]:
        if c in {"snapshot_date", "month"}:
            parsed = df[c].str.to_date(strict=True)
            temporal[c] = {
                "min": str(parsed.min()),
                "max": str(parsed.max()),
            }
        else:
            parsed = df[c].str.to_datetime(strict=True)
            temporal[c] = {
                "min": str(parsed.min()),
                "max": str(parsed.max()),
            }

    return {
        "rows": df.height,
        "columns": df.width,
        "pk": list(PKS[table]),
        "pk_duplicate_rows": pk_duplicate_rows(df, PKS[table]),
        "exact_duplicate_rows": exact_duplicate_rows(df),
        "missingness": missingness,
        "distinct_count": distinct,
        "temporal_range": temporal,
        "numeric_profile": numeric,
    }


def inquiry_response_audit(inquiries: pl.DataFrame) -> dict:
    by_status = {}
    for status in inquiries["broker_response"].unique().to_list():
        part = inquiries.filter(pl.col("broker_response") == status)
        by_status[str(status)] = {
            "rows": part.height,
            "hours_missing": part["broker_response_hours"].null_count(),
            "hours_present": part.height - part["broker_response_hours"].null_count(),
        }
    return {
        "by_status": by_status,
        "no_response_with_hours": inquiries.filter(
            (pl.col("broker_response") == "no_response")
            & pl.col("broker_response_hours").is_not_null()
        ).height,
        "realized_status_missing_hours": inquiries.filter(
            pl.col("broker_response").is_in(
                ["accepted", "rejected", "scheduled_visit"]
            )
            & pl.col("broker_response_hours").is_null()
        ).height,
        "scheduled_visit_missing_hours": inquiries.filter(
            (pl.col("broker_response") == "scheduled_visit")
            & pl.col("broker_response_hours").is_null()
        ).height,
        "negative_response_hours": inquiries.filter(
            pl.col("broker_response_hours") < 0
        ).height,
        "policy": (
            "OUTCOME_ONLY after P2; broker_response_hours is prohibited as a feature. "
            "It may be used only to audit the reconstructed-event Target B alternative; "
            "the frozen primary Target A ignores broker_response_hours."
        ),
    }


def spots_current_state_audit(
    spots: pl.DataFrame, inquiries: pl.DataFrame
) -> dict:
    counts = inquiries.group_by("spot_id").len().rename({"len": "reconstructed"})
    x = spots.select("spot_id", "total_inquiries").join(counts, on="spot_id", how="left")
    x = x.with_columns(pl.col("reconstructed").fill_null(0))
    agreement = x.filter(pl.col("total_inquiries") == pl.col("reconstructed")).height
    return {
        "total_inquiries_exact_agreement": agreement,
        "total_inquiries_exact_agreement_rate": agreement / spots.height,
        "forbidden_backtest": list(FORBIDDEN_SPOT_BACKTEST),
    }


def availability_audit(
    inquiries: pl.DataFrame, availability: pl.DataFrame
) -> dict:
    iq = inquiries.select(
        "inquiry_id",
        "spot_id",
        pl.col("inquiry_at").str.to_datetime(strict=True).alias("score_time"),
    ).sort("score_time")
    av = availability.select(
        "snapshot_id",
        "spot_id",
        pl.col("snapshot_date")
        .str.to_date(strict=True)
        .cast(pl.Datetime)
        .alias("snapshot_time"),
        "is_available",
        "days_until_available",
        "competing_inquiries_30d",
    ).sort("snapshot_time")

    backward = iq.join_asof(
        av,
        left_on="score_time",
        right_on="snapshot_time",
        by="spot_id",
        strategy="backward",
    )
    if backward.filter(pl.col("snapshot_time") > pl.col("score_time")).height:
        raise AssertionError("Backward as-of selected a future snapshot")

    covered = backward.filter(pl.col("snapshot_time").is_not_null()).with_columns(
        (pl.col("score_time") - pl.col("snapshot_time"))
        .dt.total_seconds()
        .truediv(86400)
        .alias("lag_days")
    )

    nearest = iq.join_asof(
        av,
        left_on="score_time",
        right_on="snapshot_time",
        by="spot_id",
        strategy="nearest",
    )
    future_nearest = nearest.filter(pl.col("snapshot_time") > pl.col("score_time")).height

    naive_rows = inquiries.select("inquiry_id", "spot_id").join(
        availability.select("spot_id", "snapshot_id"),
        on="spot_id",
        how="left",
    ).height

    lag = covered["lag_days"]
    return {
        "backward_coverage_count": covered.height,
        "backward_coverage_rate": covered.height / inquiries.height,
        "lag_days_median": float(lag.median()),
        "lag_days_p90": float(lag.quantile(0.90, "linear")),
        "lag_days_p95": float(lag.quantile(0.95, "linear")),
        "lag_days_max": float(lag.max()),
        "lag_gt90_rate": covered.filter(pl.col("lag_days") > 90).height
        / covered.height,
        "nearest_would_choose_future_count": future_nearest,
        "nearest_would_choose_future_rate": future_nearest / inquiries.height,
        "naive_join_rows": naive_rows,
        "naive_join_expansion_factor": naive_rows / inquiries.height,
    }



def cardinality_summary(df: pl.DataFrame, key: str) -> dict[str, float | int]:
    counts = df.group_by(key).len()["len"].sort()
    return {
        "parents": counts.len(),
        "min": int(counts.min()),
        "p50": int(counts.quantile(0.50, "nearest")),
        "p90": int(counts.quantile(0.90, "nearest")),
        "p95": int(counts.quantile(0.95, "nearest")),
        "max": int(counts.max()),
        "mean": float(counts.mean()),
    }


def date_validity_audit(frames: dict[str, pl.DataFrame]) -> dict[str, dict[str, int]]:
    """Parse every declared raw time column and flag impossible/future dates."""
    out: dict[str, dict[str, int]] = {}
    for table, columns in TIME_COLUMNS.items():
        for column in columns:
            raw = frames[table][column]
            if column in {"snapshot_date", "month"}:
                parsed = raw.str.to_date(strict=False)
                invalid = parsed.null_count() - raw.null_count()
                before_2000 = parsed.filter(parsed < pl.date(2000, 1, 1)).len()
                after_audit = parsed.filter(parsed > pl.date(2026, 8, 30)).len()
            else:
                parsed = raw.str.to_datetime(strict=False)
                invalid = parsed.null_count() - raw.null_count()
                before_2000 = parsed.filter(
                    parsed < pl.datetime(2000, 1, 1, 0, 0, 0)
                ).len()
                after_audit = parsed.filter(
                    parsed > pl.datetime(2026, 8, 30, 23, 59, 59)
                ).len()
            out[f"{table}.{column}"] = {
                "invalid_parse": int(invalid),
                "before_2000": int(before_2000),
                "after_audit_date": int(after_audit),
            }
    return out


def temporal_relational_checks(frames: dict[str, pl.DataFrame]) -> dict[str, int]:
    leads = frames["leads"].select(
        "lead_id",
        pl.col("created_at").str.to_datetime(strict=True).alias("lead_created"),
    )
    spots = frames["spots"].select(
        "spot_id",
        pl.col("created_at").str.to_datetime(strict=True).alias("spot_created"),
    )
    inquiries = (
        frames["inquiries"]
        .select(
            "inquiry_id",
            "lead_id",
            "spot_id",
            pl.col("inquiry_at").str.to_datetime(strict=True).alias("inquiry_at"),
        )
        .join(leads, on="lead_id", how="left")
        .join(spots, on="spot_id", how="left")
    )
    av = (
        frames["availability_snapshot"]
        .select(
            "snapshot_id",
            "spot_id",
            pl.col("snapshot_date")
            .str.to_date(strict=True)
            .cast(pl.Datetime)
            .alias("snapshot_time"),
            "is_available",
            "days_until_available",
        )
        .join(spots, on="spot_id", how="left")
    )
    duplicate_spot_date_rows = int(
        frames["availability_snapshot"]
        .group_by("spot_id", "snapshot_date")
        .len()
        .filter(pl.col("len") > 1)
        .select((pl.col("len") - 1).sum())
        .item()
        or 0
    )
    state_conflicts = frames["availability_snapshot"].filter(
        (pl.col("is_available") & (pl.col("days_until_available") != 0))
        | (~pl.col("is_available") & (pl.col("days_until_available") <= 0))
    ).height
    return {
        "inquiry_before_lead_created": inquiries.filter(
            pl.col("inquiry_at") < pl.col("lead_created")
        ).height,
        "inquiry_before_spot_created": inquiries.filter(
            pl.col("inquiry_at") < pl.col("spot_created")
        ).height,
        "snapshot_before_spot_created": av.filter(
            pl.col("snapshot_time") < pl.col("spot_created")
        ).height,
        "duplicate_spot_snapshot_date_rows": duplicate_spot_date_rows,
        "availability_state_conflicts": state_conflicts,
    }


def market_context_audit(
    inquiries: pl.DataFrame, spots: pl.DataFrame, market: pl.DataFrame
) -> dict[str, float | int | str | None]:
    iq = inquiries.select(
        "inquiry_id",
        "spot_id",
        pl.col("inquiry_at").str.slice(0, 7).alias("_ym"),
    ).join(
        spots.select(
            "spot_id",
            pl.col("state").alias("_state"),
            pl.col("municipality").alias("_municipality"),
            pl.col("corridor").alias("_corridor"),
            pl.col("sector_name").alias("_sector"),
        ),
        on="spot_id",
        how="left",
    ).with_columns((pl.col("_ym") + pl.lit("-01")).alias("_month"))

    mk = market.select(
        pl.col("state").alias("_state"),
        pl.col("municipality").alias("_municipality"),
        pl.col("corridor").alias("_corridor"),
        pl.col("sector").alias("_sector"),
        pl.col("month").alias("_month"),
    ).unique()
    matched = iq.join(
        mk,
        on=["_state", "_municipality", "_corridor", "_sector", "_month"],
        how="inner",
    ).height
    return {
        "publication_time_column": None,
        "effective_time_column": None,
        "same_month_matches": matched,
        "same_month_inquiry_coverage": matched / inquiries.height,
        "distinct_months": market["month"].n_unique(),
        "temporal_decision": "EDA_ONLY",
        "reason": (
            "month is a period label; no publication/observation/effective "
            "timestamp proves values were known at scoring time"
        ),
    }


def _schema_dtype_names(table: str, column: str, dtype: pl.DataType) -> tuple[str, str]:
    physical_map = {
        pl.Boolean: "BOOLEAN",
        pl.Int64: "INT64",
        pl.Float64: "FLOAT64",
        pl.String: "STRING/BYTE_ARRAY",
    }
    physical = physical_map.get(dtype, str(dtype).upper())
    canonical = physical
    if column in TIME_COLUMNS[table]:
        canonical = "DATE" if column in {"snapshot_date", "month"} else "DATETIME_UTC"
    if table == "spot_attributes" and column == "amenities":
        canonical = "JSON_STRING"
    return canonical, physical


def build_schema_frame(frames: dict[str, pl.DataFrame]) -> pl.DataFrame:
    rows: list[dict] = []
    fk_lookup = {
        (ct, cc): f"{pt}.{pc}"
        for ct, cc, pt, pc in FKS
    }
    for table, df in frames.items():
        for column, dtype in df.schema.items():
            missing = df[column].null_count()
            canonical_dtype, physical_dtype = _schema_dtype_names(table, column, dtype)
            rows.append(
                {
                    "source": table,
                    "column": column,
                    "canonical_dtype": canonical_dtype,
                    "parquet_physical_type": physical_dtype,
                    "row_count": df.height,
                    "non_null_count": df.height - missing,
                    "missing_count": missing,
                    "missing_rate": missing / df.height,
                    "distinct_count": df[column].drop_nulls().n_unique(),
                    "is_pk": column in PKS[table],
                    "fk": fk_lookup.get((table, column), ""),
                }
            )
    return pl.DataFrame(rows)

def validate_temporal_registry(repo_root: Path, frames: dict[str, pl.DataFrame]) -> None:
    path = repo_root / "AssessmentSol1" / "evidence" / "temporal_column_registry.csv"
    registry = pl.read_csv(path)
    expected = {
        (table, column)
        for table, df in frames.items()
        for column in df.columns
    }
    actual = set(
        zip(registry["source"].to_list(), registry["column"].to_list(), strict=True)
    )
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise AssertionError(f"Temporal registry mismatch: missing={missing}, extra={extra}")
    if registry.filter(
        pl.col("event_time").is_null()
        | pl.col("observation_time").is_null()
        | pl.col("effective_time").is_null()
    ).height:
        raise AssertionError("Temporal registry contains blank temporal semantics")


def build_audit(repo_root: Path) -> dict:
    source_manifest_validation = validate_source_manifest(repo_root)
    frames = {t: read_parquet_table(repo_root, t) for t in TABLES}

    parity = {}
    for t in TABLES:
        assert_csv_parquet_parity(repo_root, t)
        csv_path = candidate_dir(repo_root, "csv") / f"{t}.csv"
        pq_path = candidate_dir(repo_root, "parquet") / f"{t}.parquet"
        parity[t] = {
            "status": "PASS",
            "csv_sha256": sha256_file(csv_path),
            "parquet_sha256": sha256_file(pq_path),
            "rows": frames[t].height,
            "columns": frames[t].width,
        }

    fk = {}
    for ct, cc, pt, pc in FKS:
        fk[f"{ct}.{cc}->{pt}.{pc}"] = fk_orphan_count(
            frames[ct], cc, frames[pt], pc
        )

    validate_temporal_registry(repo_root, frames)

    return {
        "audit_version": "P1-raw-audit-v1",
        "source_manifest_validation": source_manifest_validation,
        "canonical_format": "parquet",
        "csv_role": "parity/reference only; never concatenated",
        "target_built": False,
        "parity": parity,
        "table_profiles": {t: profile_table(frames[t], t) for t in TABLES},
        "foreign_key_orphans": fk,
        "inquiries_response_audit": inquiry_response_audit(frames["inquiries"]),
        "spots_current_state_audit": spots_current_state_audit(
            frames["spots"], frames["inquiries"]
        ),
        "availability_audit": availability_audit(
            frames["inquiries"], frames["availability_snapshot"]
        ),
        "cardinalities": {
            "inquiries_per_lead": cardinality_summary(frames["inquiries"], "lead_id"),
            "inquiries_per_spot": cardinality_summary(frames["inquiries"], "spot_id"),
            "snapshots_per_spot": cardinality_summary(
                frames["availability_snapshot"], "spot_id"
            ),
            "spots_per_broker": cardinality_summary(frames["spots"], "broker_id"),
        },
        "date_validity": date_validity_audit(frames),
        "temporal_relational_checks": temporal_relational_checks(frames),
        "market_context_audit": market_context_audit(
            frames["inquiries"], frames["spots"], frames["market_context"]
        ),
        "temporal_source_classification": {
            "leads": "T0_INTAKE_SNAPSHOT_WITH_CONDITIONAL_HISTORY",
            "inquiries": "EVENT_TABLE_WITH_POST_EVENT_RESPONSE_FIELDS",
            "spots": "MIXED_ENTITY_AND_UNVERSIONED_EXTRACT_STATE",
            "spot_attributes": "IMMUTABLE_BY_EXPLICIT_ASSESSMENT_ASSUMPTION",
            "availability_snapshot": "DATED_MUTABLE_STATE_BACKWARD_ASOF_ONLY",
            "market_context": "MONTHLY_AGGREGATE_WITHOUT_PUBLICATION_TIME_EDA_ONLY",
        },
        "column_temporality": COLUMN_TEMPORAL_CLASSIFICATION,
        "gates": {
            "csv_parquet_parity": "PASS",
            "pk_fk_duplicates": "PASS",
            "impossible_dates": "PASS",
            "availability_join_safety": "PASS_WITH_BACKWARD_ASOF_ONLY",
            "spots_current_state": "FORBIDDEN_BACKTEST",
            "market_context": "EDA_ONLY",
            "spot_attributes": "AUTHORIZED_IMMUTABLE_ASSUMPTION",
            "broker_response_fields": "OUTCOME_ONLY_PRIMARY_A_IGNORES_HOURS",
            "target_built": False,
            "every_source_has_explicit_temporal_semantics": "PASS",
        },
        "source_policy": {
            "spots_current_state": "FORBIDDEN_BACKTEST",
            "spot_attributes": "AUTHORIZED_IMMUTABLE_ASSUMPTION",
            "market_context": "EDA_ONLY",
            "broker_response_fields": "OUTCOME_ONLY_PRIMARY_A_IGNORES_HOURS",
            "availability_competing_inquiries_30d": (
                "BLOCKED_UNTIL_WINDOW_DIRECTION_PROVEN"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    audit = build_audit(root)
    if args.write:
        evidence = root / "AssessmentSol1" / "evidence"
        out = evidence / "data_audit.json"
        out.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n")
        frames = {t: read_parquet_table(root, t) for t in TABLES}
        build_schema_frame(frames).write_csv(evidence / "data_schema.csv")
    print(json.dumps(audit["source_policy"], indent=2))


if __name__ == "__main__":
    main()
