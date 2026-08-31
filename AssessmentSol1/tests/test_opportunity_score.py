from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
OPP = ROOT / "opportunity_score"
if str(OPP) not in sys.path:
    sys.path.insert(0, str(OPP))

from build_score import OUTPUT_COLUMNS, _assign_priority_bands, load_score_config  # noqa: E402
from evaluate_score import _evaluate_ranked  # noqa: E402


def test_post_recovery_formula_and_double_counting_gate() -> None:
    cfg = load_score_config()
    assert cfg["formula"]["internal_0_1"] == "lead_quality_probability * inventory_actionability_gate"
    assert cfg["formula"]["grid_search"] is False
    assert cfg["formula"]["exponent_search"] is False
    assert cfg["formula"]["stacking"] is False
    assert cfg["double_counting_check"]["status"] == "PASS_AFTER_DEDUPLICATION"
    assert cfg["lead_quality"]["version"] == "LQ_RECOVERY_R4_STATIC_MATCH_V1"
    assert cfg["lead_quality"]["availability_used"] is False
    assert cfg["double_counting_check"]["continuous_inventory_serviceability_multiplied"] is False


def test_priority_bands_are_exact_rank_based_even_with_score_ties() -> None:
    cfg = load_score_config()
    df = pl.DataFrame({
        "lead_id": list(range(1, 21)),
        "opportunity_score_0_100": [20.0] * 20,
    })
    out = _assign_priority_bands(df, cfg)
    counts = dict(zip(*out.group_by("priority_band").len().select("priority_band", "len").to_dict(as_series=False).values()))
    assert counts["PRIORITY"] == 1
    assert counts["HIGH"] == 1
    assert counts["MEDIUM"] == 2
    assert counts["LOW"] == 16
    assert out.sort(["opportunity_score_0_100", "lead_id"], descending=[True, False])["lead_id"].head(4).to_list() == [1, 2, 3, 4]


def test_product_output_excludes_targets_and_outcomes() -> None:
    forbidden = {"target_value", "target_status", "broker_response", "broker_response_hours", "lead_score_internal"}
    assert not forbidden.intersection(OUTPUT_COLUMNS)


def test_recovered_capacity_has_four_required_slices() -> None:
    df = pl.DataFrame({
        "lead_id": list(range(1, 21)),
        "target_value": [1, 0] * 10,
        "lead_quality_probability": [float(21-i) for i in range(20)],
    })
    rows = _evaluate_ranked(df, "lead_quality_probability", "LEAD_QUALITY_RECOVERED", "TEST")
    assert [r["capacity_pct"] for r in rows] == [5, 10, 15, 20]
    assert all(r["status"] == "DEFINED" for r in rows)


def test_inventory_continuous_score_is_not_in_v2_formula() -> None:
    cfg = load_score_config()
    formula = cfg["formula"]["internal_0_1"]
    assert "inventory_serviceability" not in formula
    assert "inventory_actionability_gate" in formula


def test_internal_reference_is_prohibited_from_v2() -> None:
    cfg = load_score_config()
    assert cfg["external_reference"]["lead_score_internal"] == "PROHIBITED_FROM_V2"
    assert cfg["external_reference"]["allowed_as_predictor"] is False
    assert cfg["external_reference"]["allowed_for_policy_selection"] is False
