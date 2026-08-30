from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from assessment_sol1.raw_audit import (
    FKS,
    PKS,
    TABLES,
    assert_csv_parquet_parity,
    exact_duplicate_rows,
    date_validity_audit,
    fk_orphan_count,
    pk_duplicate_rows,
    read_parquet_table,
    validate_temporal_registry,
    validate_source_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def frames() -> dict[str, pl.DataFrame]:
    return {t: read_parquet_table(REPO_ROOT, t) for t in TABLES}


@pytest.mark.parametrize("table", TABLES)
def test_csv_parquet_logical_parity(table: str) -> None:
    assert_csv_parquet_parity(REPO_ROOT, table)


@pytest.mark.parametrize("table", TABLES)
def test_primary_keys_unique_and_non_null(
    table: str, frames: dict[str, pl.DataFrame]
) -> None:
    df = frames[table]
    assert pk_duplicate_rows(df, PKS[table]) == 0
    for c in PKS[table]:
        assert df[c].null_count() == 0


@pytest.mark.parametrize("table", TABLES)
def test_no_exact_duplicate_rows(
    table: str, frames: dict[str, pl.DataFrame]
) -> None:
    assert exact_duplicate_rows(frames[table]) == 0


@pytest.mark.parametrize("child,child_col,parent,parent_col", FKS)
def test_foreign_keys(
    frames: dict[str, pl.DataFrame],
    child: str,
    child_col: str,
    parent: str,
    parent_col: str,
) -> None:
    assert fk_orphan_count(
        frames[child], child_col, frames[parent], parent_col
    ) == 0


def test_temporal_ordering_and_impossible_dates(
    frames: dict[str, pl.DataFrame]
) -> None:
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
    assert inquiries.filter(pl.col("inquiry_at") < pl.col("lead_created")).height == 0
    assert inquiries.filter(pl.col("inquiry_at") < pl.col("spot_created")).height == 0
    assert inquiries.filter(
        pl.col("inquiry_at") > pl.datetime(2026, 8, 30, 23, 59, 59)
    ).height == 0

    availability = frames["availability_snapshot"].select(
        "snapshot_id",
        "spot_id",
        pl.col("snapshot_date")
        .str.to_date(strict=True)
        .cast(pl.Datetime)
        .alias("snapshot_time"),
    ).join(spots, on="spot_id", how="left")
    assert availability.filter(
        pl.col("snapshot_time") < pl.col("spot_created")
    ).height == 0


def test_availability_spot_date_unique_and_state_consistent(
    frames: dict[str, pl.DataFrame]
) -> None:
    av = frames["availability_snapshot"]
    duplicate_spot_dates = (
        av.group_by("spot_id", "snapshot_date").len().filter(pl.col("len") > 1)
    )
    assert duplicate_spot_dates.height == 0
    conflicts = av.filter(
        (pl.col("is_available") & (pl.col("days_until_available") != 0))
        | (~pl.col("is_available") & (pl.col("days_until_available") <= 0))
    )
    assert conflicts.height == 0


def test_safe_dimension_joins_do_not_explode(
    frames: dict[str, pl.DataFrame]
) -> None:
    inquiries = frames["inquiries"]
    assert inquiries.join(
        frames["leads"].select("lead_id"), on="lead_id", how="left"
    ).height == inquiries.height
    assert inquiries.join(
        frames["spots"].select("spot_id"), on="spot_id", how="left"
    ).height == inquiries.height
    assert frames["spots"].join(
        frames["spot_attributes"].select("spot_id"), on="spot_id", how="left"
    ).height == frames["spots"].height


def test_naive_availability_join_is_detected_as_explosive(
    frames: dict[str, pl.DataFrame]
) -> None:
    inquiries = frames["inquiries"]
    naive = inquiries.select("inquiry_id", "spot_id").join(
        frames["availability_snapshot"].select("spot_id", "snapshot_id"),
        on="spot_id",
        how="left",
    )
    factor = naive.height / inquiries.height
    assert factor > 1.0
    assert factor == pytest.approx(10.017319277108435)


def test_backward_asof_never_uses_future_snapshot(
    frames: dict[str, pl.DataFrame]
) -> None:
    iq = frames["inquiries"].select(
        "inquiry_id",
        "spot_id",
        pl.col("inquiry_at").str.to_datetime(strict=True).alias("score_time"),
    ).sort("score_time")
    av = frames["availability_snapshot"].select(
        "spot_id",
        pl.col("snapshot_date")
        .str.to_date(strict=True)
        .cast(pl.Datetime)
        .alias("snapshot_time"),
    ).sort("snapshot_time")
    joined = iq.join_asof(
        av,
        left_on="score_time",
        right_on="snapshot_time",
        by="spot_id",
        strategy="backward",
    )
    assert joined.filter(pl.col("snapshot_time") > pl.col("score_time")).height == 0


def test_temporal_registry_covers_every_raw_column(
    frames: dict[str, pl.DataFrame]
) -> None:
    validate_temporal_registry(REPO_ROOT, frames)


def test_broker_response_hours_is_not_authorized_by_registry() -> None:
    registry = pl.read_csv(
        REPO_ROOT / "AssessmentSol1" / "evidence" / "temporal_column_registry.csv"
    )
    row = registry.filter(
        (pl.col("source") == "inquiries")
        & (pl.col("column") == "broker_response_hours")
    )
    assert row.height == 1
    assert row["leakage_risk"].item() == "CRITICAL"
    assert "AUDIT_ONLY" in row["notes"].item()


def test_market_context_is_eda_only() -> None:
    registry = pl.read_csv(
        REPO_ROOT / "AssessmentSol1" / "evidence" / "temporal_column_registry.csv"
    )
    market = registry.filter(pl.col("source") == "market_context")
    assert market.height == frames_width("market_context")
    assert market["known_at_T1"].unique().to_list() == ["BLOCKED_EDA_ONLY"]


def frames_width(table: str) -> int:
    return read_parquet_table(REPO_ROOT, table).width


def test_all_declared_dates_parse_and_are_plausible(
    frames: dict[str, pl.DataFrame]
) -> None:
    audit = date_validity_audit(frames)
    assert audit
    for result in audit.values():
        assert result["invalid_parse"] == 0
        assert result["before_2000"] == 0
        assert result["after_audit_date"] == 0


def test_response_timing_inconsistencies_are_explicit(
    frames: dict[str, pl.DataFrame]
) -> None:
    iq = frames["inquiries"]
    no_response_with_hours = iq.filter(
        (pl.col("broker_response") == "no_response")
        & pl.col("broker_response_hours").is_not_null()
    ).height
    realized_missing_hours = iq.filter(
        pl.col("broker_response").is_in(["accepted", "rejected", "scheduled_visit"])
        & pl.col("broker_response_hours").is_null()
    ).height
    scheduled_missing_hours = iq.filter(
        (pl.col("broker_response") == "scheduled_visit")
        & pl.col("broker_response_hours").is_null()
    ).height
    assert no_response_with_hours == 3786
    assert realized_missing_hours == 2701
    assert scheduled_missing_hours == 673


def test_spot_current_state_columns_are_forbidden() -> None:
    registry = pl.read_csv(
        REPO_ROOT / "AssessmentSol1" / "evidence" / "temporal_column_registry.csv"
    )
    blocked = registry.filter(
        (pl.col("source") == "spots")
        & pl.col("column").is_in(
            ["days_on_market", "total_inquiries", "total_views", "is_active"]
        )
    )
    assert blocked.height == 4
    assert set(blocked["known_at_T1"].to_list()) == {"BLOCKED"}
    assert set(blocked["point_in_time_reconstructable"].to_list()) == {"NO"}


def test_raw_fingerprints_match_frozen_manifest() -> None:
    observed = validate_source_manifest(REPO_ROOT)
    assert set(observed) == set(TABLES)
    for table in TABLES:
        assert observed[table]["csv_sha256"]
        assert observed[table]["parquet_sha256"]
        assert observed[table]["csv_git_blob_sha1"]
        assert observed[table]["parquet_git_blob_sha1"]


def test_spot_attributes_are_authorized_under_immutability_assumption() -> None:
    registry = pl.read_csv(
        REPO_ROOT / "AssessmentSol1" / "evidence" / "temporal_column_registry.csv"
    )
    attrs = registry.filter(pl.col("source") == "spot_attributes")
    assert attrs.height == frames_width("spot_attributes")
    assert set(attrs["known_at_T1"].to_list()) == {
        "YES_IF_SPOT_CREATED_LE_SCORE_TIME"
    }
    assert set(attrs["known_at_T2"].to_list()) == {
        "YES_IF_SPOT_CREATED_LE_SCORE_TIME"
    }
    assert set(attrs["point_in_time_reconstructable"].to_list()) == {
        "YES_UNDER_IMMUTABILITY_ASSUMPTION"
    }
    non_key = attrs.filter(pl.col("column") != "spot_id")
    assert set(non_key["mutable"].to_list()) == {"NO_ASSUMED_IMMUTABLE"}
