from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

INVENTORY_DIR = Path(__file__).resolve().parents[1] / "inventory"
ABT_DIR = Path(__file__).resolve().parents[1] / "abt"
for p in (INVENTORY_DIR, ABT_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from build_inventory import build_inventory, compute_budget_fit, load_config  # noqa: E402
from rank_fallbacks import rank_score_rows  # noqa: E402


def _write_raw(repo: Path, *, response: str = "scheduled_visit") -> None:
    raw = repo / "data" / "candidate" / "csv"
    raw.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({
        "lead_id": [1], "user_type": ["company"], "company_size": ["small"], "industry": ["tech"],
        "search_sector": ["Office"], "search_modality": ["rent"], "target_area_sqm": [100.0],
        "min_budget_mxn_rent_monthly": [10000.0], "max_budget_mxn_rent_monthly": [20000.0],
        "min_budget_mxn_sale_total": [None], "max_budget_mxn_sale_total": [None],
        "preferred_state": ["CDMX"], "preferred_municipality": ["M1"], "preferred_corridor": ["C1"],
        "source": ["web"], "prior_searches": [999], "prior_inquiries": [999],
        "has_converted_before": [True], "lead_score_internal": [0.99],
        "created_at": ["2026-01-01T10:00:00Z"],
    }).write_csv(raw / "leads.csv")
    pl.DataFrame({
        "inquiry_id": [101], "lead_id": [1], "spot_id": [10],
        "inquiry_at": ["2026-01-05T10:00:00Z"], "channel": ["web"], "message_length": [20],
        "requested_area_sqm": [100.0], "requested_budget_mxn_rent_monthly": [18000.0],
        "requested_budget_mxn_sale_total": [None], "urgency_days": [30], "asked_visit": [True],
        "broker_response": [response], "broker_response_hours": [2.0],
    }).write_csv(raw / "inquiries.csv")
    pl.DataFrame({
        "spot_id": [10, 11, 12, 13], "broker_id": [1,2,3,4],
        "sector_name": ["Office","Office","Office","Retail"], "type_name": ["building"]*4,
        "state": ["CDMX"]*4, "municipality": ["M1"]*4, "settlement": ["S1"]*4,
        "corridor": ["C1"]*4, "region": ["R1"]*4, "lat": [19.0,19.1,19.2,19.3],
        "lon": [-99.0,-99.1,-99.2,-99.3], "title": ["mutable"]*4, "description": ["d"]*4,
        "area_sqm": [100.0,110.0,90.0,100.0], "price_sqm_mxn_rent": [100.0]*4,
        "price_sqm_mxn_sale": [None]*4, "price_total_mxn_rent": [10000.0,11000.0,9000.0,10000.0],
        "price_total_mxn_sale": [None]*4, "maintenance_cost_mxn": [1000.0]*4,
        "modality": ["rent","sale","rent","rent"], "days_on_market": [999]*4,
        "total_inquiries": [999]*4, "total_views": [999]*4, "is_active": [True]*4,
        "created_at": ["2025-12-01T00:00:00Z","2025-12-01T00:00:00Z",
                       "2026-02-01T00:00:00Z","2025-12-01T00:00:00Z"],
    }).write_csv(raw / "spots.csv")
    pl.DataFrame({
        "snapshot_id": [1,2,3], "spot_id": [10,10,13],
        "snapshot_date": ["2025-09-01","2026-01-10","2026-01-04"],
        "is_available": [True,False,True], "days_until_available": [0,40,0],
        "competing_inquiries_30d": [999,999,999],
    }).write_csv(raw / "availability_snapshot.csv")


def _repo(tmp_path: Path, *, response: str = "scheduled_visit") -> Path:
    repo = tmp_path / response
    _write_raw(repo, response=response)
    return repo


def test_future_spot_future_snapshot_and_modality(tmp_path: Path) -> None:
    inv = build_inventory(_repo(tmp_path))
    assert 12 not in inv["candidate_spot_id"].to_list()
    assert 11 not in inv["candidate_spot_id"].to_list()
    spot10 = inv.filter(pl.col("candidate_spot_id") == 10).row(0, named=True)
    assert spot10["snapshot_date_asof"].isoformat() == "2025-09-01"
    assert spot10["availability_known"] is True
    assert spot10["availability_state"] == "AVAILABLE_NOW"
    assert spot10["freshness_bucket"] == "GT_90D"
    spot13 = inv.filter(pl.col("candidate_spot_id") == 13).row(0, named=True)
    assert spot13["relaxation_tier"] == "TIER_3_EXPERIMENTAL"


def test_missing_snapshot_remains_unknown(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    p = repo / "data" / "candidate" / "csv" / "availability_snapshot.csv"
    pl.read_csv(p).filter(pl.col("spot_id") != 13).write_csv(p)
    row = build_inventory(repo).filter(pl.col("candidate_spot_id") == 13).row(0, named=True)
    assert row["availability_known"] is False
    assert row["availability_state"] == "UNKNOWN"
    assert row["inventory_confidence"] == 0.0


def test_budget_fit_unit_consistency_and_monotonicity() -> None:
    rent = compute_budget_fit(transaction_mode="rent", candidate_price=15000, min_budget=10000,
                              max_budget=20000, requested_budget=None)
    sale = compute_budget_fit(transaction_mode="sale", candidate_price=3_000_000, min_budget=2_000_000,
                              max_budget=2_500_000, requested_budget=None)
    assert rent[0] == 1.0
    assert abs(sale[0] - 2_500_000/3_000_000) < 1e-12
    assert sale[1] == 500_000
    assert compute_budget_fit(transaction_mode="rent", candidate_price=None, min_budget=10000,
                              max_budget=20000, requested_budget=18000) == (None, None, "UNKNOWN_PRICE_NOT_PIT")


def _rank_row(i: int) -> dict:
    return {
        "score_id":"S1", "lead_id":1, "score_time":"2026-01-05T10:00:00Z",
        "candidate_spot_id":i, "relaxation_tier":"TIER_0", "relaxation_tier_index":0,
        "modality_match":True, "sector_match":True, "geographic_match":"CORRIDOR",
        "area_gap_relative":i/100.0, "area_gap_sqm":float(i), "area_fit_relative":1-i/100.0,
        "budget_fit":None, "budget_gap":None, "budget_status":"UNKNOWN_PRICE_NOT_PIT",
        "inventory_confidence":1.0, "availability_state":"AVAILABLE_NOW",
        "freshness_bucket":"1_7D", "is_viable":True, "candidate_serviceability_score":0.9,
    }


def test_max_five_unique_rank_deterministic_and_no_inventory() -> None:
    cfg = load_config()
    rows = [_rank_row(i) for i in range(1,9)]
    rec1, summary1 = rank_score_rows(rows, cfg)
    rec2, summary2 = rank_score_rows(list(reversed(rows)), cfg)
    assert rec1 == rec2 and summary1 == summary2
    assert len(rec1) == 5
    assert [x["rank"] for x in rec1] == [1,2,3,4,5]
    assert len({x["rank"] for x in rec1}) == 5
    rec0, summary0 = rank_score_rows([], cfg)
    assert rec0 == [] and summary0["no_result_reason"] == "NO_INVENTORY"


def test_reproducibility_and_no_outcome_dependence(tmp_path: Path) -> None:
    repo_a = _repo(tmp_path/"a", response="scheduled_visit")
    repo_b = _repo(tmp_path/"b", response="rejected")
    a = build_inventory(repo_a).sort(["score_id","candidate_spot_id"])
    b = build_inventory(repo_b).sort(["score_id","candidate_spot_id"])
    assert a.equals(build_inventory(repo_a).sort(["score_id","candidate_spot_id"]))
    assert a.equals(b)
    forbidden = {"broker_response","broker_response_hours","target_status","target_value","competing_inquiries_30d"}
    assert not forbidden.intersection(a.columns)
    assert "price_total_mxn_rent" not in a.columns
