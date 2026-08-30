from __future__ import annotations

import shutil
import sys
from pathlib import Path

import polars as pl
import pytest

ABT_DIR = Path(__file__).resolve().parents[1] / "abt"
if str(ABT_DIR) not in sys.path:
    sys.path.insert(0, str(ABT_DIR))

from build_t0 import build_t0
from build_t1 import build_t1
from build_t2 import build_t2
from build_inventory_candidates import build_inventory_candidates
from validate_abts import validate_all


def _write_raw(repo: Path) -> None:
    raw = repo / "data" / "candidate" / "csv"
    raw.mkdir(parents=True, exist_ok=True)

    leads = pl.DataFrame(
        {
            "lead_id": [1, 2],
            "user_type": ["company", "broker"],
            "company_size": ["small", "medium"],
            "industry": ["tech", "services"],
            "search_sector": ["office", "office"],
            "search_modality": ["rent", "rent"],
            "target_area_sqm": [100.0, 150.0],
            "min_budget_mxn_rent_monthly": [10000.0, 15000.0],
            "max_budget_mxn_rent_monthly": [20000.0, 25000.0],
            "min_budget_mxn_sale_total": [None, None],
            "max_budget_mxn_sale_total": [None, None],
            "preferred_state": ["CDMX", "CDMX"],
            "preferred_municipality": ["M1", "M1"],
            "preferred_corridor": ["C1", "C1"],
            "source": ["web", "organic"],
            "prior_searches": [5, 7],
            "prior_inquiries": [2, 3],
            "has_converted_before": [False, False],
            "lead_score_internal": [0.99, 0.01],
            "created_at": ["2026-01-01T10:00:00Z", "2026-01-02T10:00:00Z"],
        }
    )
    leads.write_csv(raw / "leads.csv")

    inquiries = pl.DataFrame(
        {
            "inquiry_id": [101, 102, 103, 201, 202],
            "lead_id": [1, 1, 1, 2, 2],
            "spot_id": [10, 11, 10, 10, 12],
            "inquiry_at": [
                "2026-01-05T10:00:00Z",
                "2026-01-06T10:00:00Z",
                "2026-01-06T10:00:00Z",
                "2026-01-10T10:00:00Z",
                "2026-03-01T10:00:00Z",
            ],
            "channel": ["web", "web", "phone", "web", "phone"],
            "message_length": [10, 20, 30, 40, 50],
            "requested_area_sqm": [100.0, 110.0, 120.0, 150.0, 155.0],
            "requested_budget_mxn_rent_monthly": [18000.0, 19000.0, 20000.0, 24000.0, 24500.0],
            "requested_budget_mxn_sale_total": [None, None, None, None, None],
            "urgency_days": [30, 20, 10, None, 5],
            "asked_visit": [True, False, True, False, True],
            "broker_response": ["scheduled_visit", "rejected", "scheduled_visit", None, "rejected"],
            "broker_response_hours": [2.0, 3.0, 4.0, None, 1.0],
        }
    )
    inquiries.write_csv(raw / "inquiries.csv")

    spots = pl.DataFrame(
        {
            "spot_id": [10, 11, 12],
            "broker_id": [1, 2, 3],
            "sector_name": ["office", "office", "office"],
            "type_name": ["building", "building", "building"],
            "state": ["CDMX", "CDMX", "CDMX"],
            "municipality": ["M1", "M1", "M1"],
            "settlement": ["S1", "S2", "S3"],
            "corridor": ["C1", "C1", "C1"],
            "region": ["R1", "R1", "R1"],
            "lat": [19.0, 19.1, 19.2],
            "lon": [-99.0, -99.1, -99.2],
            "title": ["future mutable", "future mutable", "future mutable"],
            "description": ["d", "d", "d"],
            "area_sqm": [100.0, 130.0, 160.0],
            "price_sqm_mxn_rent": [100.0, 100.0, 100.0],
            "price_sqm_mxn_sale": [None, None, None],
            "price_total_mxn_rent": [10000.0, 13000.0, 16000.0],
            "price_total_mxn_sale": [None, None, None],
            "maintenance_cost_mxn": [1000.0, 1000.0, 1000.0],
            "modality": ["rent", "rent", "rent"],
            "days_on_market": [999, 999, 999],
            "total_inquiries": [999, 999, 999],
            "total_views": [999, 999, 999],
            "is_active": [True, True, True],
            "created_at": [
                "2025-12-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
                "2026-02-01T00:00:00Z",
            ],
        }
    )
    spots.write_csv(raw / "spots.csv")

    attrs = pl.DataFrame(
        {
            "spot_id": [10, 11, 12],
            "natural_light": [True, False, True],
            "luminaires": [10, 20, 30],
            "charging_ports": [1, 2, 3],
            "security_type": ["24h", "24h", "none"],
            "floor_level": [1, 2, 3],
            "elevators": [1, 2, 3],
            "vertical_height_m": [3.0, 3.2, 4.0],
            "parking_spaces": [2, 3, 4],
            "building_status": ["ready", "ready", "ready"],
            "floor_material": ["tile", "tile", "concrete"],
            "amenities": ["[]", "[]", "[]"],
        }
    )
    attrs.write_csv(raw / "spot_attributes.csv")

    availability = pl.DataFrame(
        {
            "snapshot_id": [1, 2, 3],
            "spot_id": [10, 10, 11],
            "snapshot_date": ["2026-01-01", "2026-01-04", "2026-01-07"],
            "is_available": [True, False, True],
            "days_until_available": [0, 10, 0],
            "competing_inquiries_30d": [999, 999, 999],
        }
    )
    availability.write_csv(raw / "availability_snapshot.csv")

    # Deliberately tempting future-looking context: builders must never read it.
    pl.DataFrame(
        {
            "state": ["CDMX"],
            "municipality": ["M1"],
            "corridor": ["C1"],
            "sector": ["office"],
            "month": ["2030-01-01"],
            "similar_available_spots": [9999],
            "avg_price_sqm_mxn": [9999.0],
            "recent_occupancy_rate": [1.0],
            "absorption_velocity_days": [1.0],
            "recent_inquiry_volume": [9999],
        }
    ).write_csv(raw / "market_context.csv")


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    _write_raw(repo)
    abt = repo / "AssessmentSol1" / "abt"
    abt.mkdir(parents=True, exist_ok=True)
    shutil.copy(ABT_DIR / "COLUMN_LINEAGE.csv", abt / "COLUMN_LINEAGE.csv")
    return repo


def test_t0_t1_t2_grains_and_primary_separation(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    t0_a, t0_m = build_t0(repo)
    t1_a, t1_m = build_t1(repo)
    t2_a, t2_m = build_t2(repo)

    assert t0_a.height == 2
    assert t0_a["lead_id"].n_unique() == 2
    assert t1_a.height == 2
    assert t1_a["lead_id"].n_unique() == 2
    assert t1_a["first_inquiry_id"].to_list() == [101, 201]
    assert t2_a.height == 3
    assert t2_a["inquiry_id"].n_unique() == 3

    for df in (t0_m, t1_m, t2_m):
        assert "matching_current_spot_id" not in df.columns
        assert not any(c.startswith("inventory_") for c in df.columns)
        assert "broker_response" not in df.columns
        assert "broker_response_hours" not in df.columns
        assert "lead_score_internal" not in df.columns
    assert "channel" not in t0_m.columns
    assert "channel" in t1_m.columns
    assert "hist_prior_inquiry_count" in t2_m.columns


def test_t2_history_is_strictly_earlier_not_id_tiebroken_history(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    t2_a, _ = build_t2(repo)
    row_103 = t2_a.filter(pl.col("inquiry_id") == 103).row(0, named=True)
    # inquiry 102 has the same timestamp as 103 and therefore is not historical.
    assert row_103["hist_prior_inquiry_count"] == 1
    assert row_103["hist_max_inquiry_time"] < row_103["score_time"]
    assert row_103["audit_response_history_feature_used"] is False


def test_inventory_candidates_use_backward_asof_and_preserve_unknown(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    audit, model = build_inventory_candidates(repo)

    assert audit.group_by("score_id", "candidate_spot_id").len().filter(pl.col("len") > 1).height == 0
    assert audit.filter(pl.col("spot_created_at") > pl.col("score_time")).height == 0
    assert audit.filter(
        pl.col("snapshot_date_asof").is_not_null()
        & (pl.col("snapshot_date_asof") > pl.col("score_time").dt.date())
    ).height == 0

    # At lead-1 Jan-5 score, spot 11's only snapshot is Jan-7: must be UNKNOWN, not future-joined.
    unknown = audit.filter(
        (pl.col("score_id") == "L1:T1:I101") & (pl.col("candidate_spot_id") == 11)
    ).row(0, named=True)
    assert unknown["availability_known"] is False
    assert unknown["availability_state"] == "UNKNOWN"
    assert unknown["is_available_asof"] is None
    assert unknown["days_until_available_asof"] is None
    assert unknown["freshness_bucket"] == "UNKNOWN"

    # Future-created spot 12 cannot enter Jan scores.
    assert audit.filter(
        (pl.col("score_time") < pl.datetime(2026, 2, 1, time_zone="UTC"))
        & (pl.col("candidate_spot_id") == 12)
    ).height == 0

    assert "competing_inquiries_30d" not in audit.columns
    assert "competing_inquiries_30d" not in model.columns
    assert "price_total_mxn_rent" not in model.columns
    assert not any(c.startswith("market_") for c in model.columns)


def test_validator_materializes_p4_and_keeps_censored_ambiguous_in_audit(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    qa = validate_all(repo, materialize=True)
    assert qa["status"] == "PASS"
    assert qa["raw_inputs_only"] is True
    assert qa["future_inquiry_history_rows"] == 0
    assert qa["future_spot_rows"] == 0
    assert qa["future_availability_rows"] == 0
    assert qa["competing_inquiries_30d_used"] is False
    assert qa["t2_response_history_feature_used"] is False
    assert (repo / "AssessmentSol1" / "abt" / "artifacts" / "abt_t1_audit_all_rows.parquet").exists()
    assert (repo / "AssessmentSol1" / "abt" / "artifacts" / "inventory_candidates_model_ready.parquet").exists()

    t1_a = pl.read_parquet(repo / "AssessmentSol1" / "abt" / "artifacts" / "abt_t1_audit_all_rows.parquet")
    t1_m = pl.read_parquet(repo / "AssessmentSol1" / "abt" / "artifacts" / "abt_t1_model_ready.parquet")
    assert "AMBIGUOUS" in set(t1_a["target_status"].to_list())
    assert "AMBIGUOUS" not in set(t1_m["target_status"].to_list())


def test_split_integrity_fails_if_lead_crosses_partitions(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    split_dir = repo / "AssessmentSol1" / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"lead_id": [1, 1, 2], "split": ["train", "test", "train"]}).write_csv(
        split_dir / "split_assignments.csv"
    )
    with pytest.raises(AssertionError, match="same lead appears in multiple"):
        validate_all(repo, materialize=False)
