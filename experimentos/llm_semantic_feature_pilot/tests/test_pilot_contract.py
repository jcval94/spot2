from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from run_pilot import SCHEMA, compact_record


ROOT = Path(__file__).resolve().parents[1]


def test_pilot_has_exactly_100_balanced_records():
    d = pd.read_csv(ROOT / "data" / "pilot_input_100.csv")
    assert len(d) == 100
    assert d["spot_id"].is_unique
    assert d["sample_stratum"].value_counts().to_dict() == {
        "rules_positive": 25,
        "land_semantic_residual": 25,
        "ambiguity_challenge": 25,
        "clean_control": 25,
    }


def test_original_text_is_preserved():
    d = pd.read_csv(ROOT / "data" / "pilot_input_100.csv")
    assert d["original_text"].notna().all()
    assert (d["original_text"].str.len() > 10).all()


def test_free_rule_columns_are_present():
    d = pd.read_csv(ROOT / "data" / "pilot_input_100.csv")
    expected = {
        "rule_claim_natural_light",
        "rule_claim_security",
        "rule_claim_parking",
        "rule_claim_readiness",
        "rule_direct_conflict_flag",
        "rule_land_building_copy_flag",
        "rule_ambiguity_candidate_flag",
    }
    assert expected.issubset(d.columns)


def test_payload_excludes_irrelevant_expensive_fields():
    d = pd.read_csv(ROOT / "data" / "pilot_input_100.csv")
    payload = compact_record(d.iloc[0])
    assert "price_total_mxn_sale" not in payload
    assert "lat" not in payload
    assert "lon" not in payload
    assert set(payload).issuperset(
        {"id", "txt", "sec", "typ", "rule_direct", "rule_land_copy"}
    )


def test_structured_output_is_closed_schema():
    assert SCHEMA["additionalProperties"] is False
    item = SCHEMA["properties"]["results"]["items"]
    assert item["additionalProperties"] is False
    assert set(item["required"]) == set(item["properties"])
