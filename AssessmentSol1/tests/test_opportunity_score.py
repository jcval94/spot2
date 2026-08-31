from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
OPP = ROOT / "opportunity_score"
if str(OPP) not in sys.path:
    sys.path.insert(0, str(OPP))

from build_score import OUTPUT_COLUMNS, _band_expr, load_score_config  # noqa: E402
from evaluate_score import _evaluate_ranked  # noqa: E402


def test_frozen_formula_and_double_counting_gate() -> None:
    cfg = load_score_config()
    assert cfg["formula"]["internal_0_1"] == "lead_quality_probability * inventory_serviceability"
    assert cfg["formula"]["grid_search"] is False
    assert cfg["formula"]["exponent_search"] is False
    assert cfg["formula"]["stacking"] is False
    assert cfg["double_counting_check"]["status"] == "PASS"
    assert cfg["lead_quality"]["feature_set"] == "BASE_RATE_NO_FEATURES"
    assert cfg["double_counting_check"]["selected_spot_challenger_used_in_opportunity_score"] is False


def test_priority_thresholds_are_frozen_and_ordered() -> None:
    cfg = load_score_config()
    b = cfg["priority_bands"]
    assert b["PRIORITY"]["min_score_0_100"] > b["HIGH"]["min_score_0_100"]
    assert b["HIGH"]["min_score_0_100"] > b["MEDIUM"]["min_score_0_100"]
    df = pl.DataFrame({"opportunity_score_0_100": [
        b["PRIORITY"]["min_score_0_100"] + 0.01,
        b["HIGH"]["min_score_0_100"] + 0.001,
        b["MEDIUM"]["min_score_0_100"] + 0.001,
        0.0,
    ]}).with_columns(_band_expr(cfg))
    assert df["priority_band"].to_list() == ["PRIORITY", "HIGH", "MEDIUM", "LOW"]


def test_product_output_excludes_targets_and_outcomes() -> None:
    forbidden = {"target_value", "target_status", "broker_response", "broker_response_hours", "lead_score_internal"}
    assert not forbidden.intersection(OUTPUT_COLUMNS)


def test_constant_lead_quality_has_undefined_capacity_ranking() -> None:
    df = pl.DataFrame({
        "lead_id": list(range(1, 21)),
        "target_value": [1, 0] * 10,
        "lead_quality_probability": [0.2] * 20,
        "inventory_confidence": [1.0] * 20,
    })
    rows = _evaluate_ranked(df, "lead_quality_probability", "LEAD_QUALITY_ONLY", "TEST")
    assert len(rows) == 3
    assert all(r["status"] == "UNDEFINED_CONSTANT_SCORE" for r in rows)
    assert all(r["lift_at_x"] is None for r in rows)


def test_inventory_and_opportunity_rank_identity_for_constant_positive_lq() -> None:
    p = 0.20375457875457875
    df = pl.DataFrame({
        "lead_id": [1, 2, 3, 4],
        "inventory_serviceability": [0.3, 0.9, 0.1, 0.6],
        "inventory_confidence": [1.0, 0.8, 1.0, 0.5],
    }).with_columns((100 * p * pl.col("inventory_serviceability")).alias("opportunity_score_0_100"))
    a = df.sort(["inventory_serviceability", "inventory_confidence", "lead_id"], descending=[True, True, False])["lead_id"].to_list()
    b = df.sort(["opportunity_score_0_100", "inventory_confidence", "lead_id"], descending=[True, True, False])["lead_id"].to_list()
    assert a == b
