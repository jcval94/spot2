import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from feature_engineering import (
    AMENITY_VOCAB,
    BASE_FEATURES_T0,
    BASE_FEATURES_T1,
    BASE_FEATURES_T2,
    add_history_features,
    assert_no_blocked_features,
    attach_availability,
    engineer_leads,
    engineer_spots,
    parse_amenities,
    prepare_inquiries,
)


def test_blocked_columns_never_in_feature_contract():
    assert_no_blocked_features(BASE_FEATURES_T0)
    assert_no_blocked_features(BASE_FEATURES_T1)
    assert_no_blocked_features(BASE_FEATURES_T2)


def test_structural_budget_missing_is_not_median_imputed():
    leads = pd.DataFrame(
        {
            "lead_id": [1, 2],
            "created_at": pd.to_datetime(["2026-01-01", "2026-01-01"]),
            "company_size": [None, "small"],
            "industry": [None, "retail"],
            "preferred_corridor": [None, "x"],
            "search_modality": ["sale", "rent"],
            "has_converted_before": [False, False],
            "target_area_sqm": [100, 200],
            "prior_searches": [0, 1],
            "prior_inquiries": [0, 2],
            "min_budget_mxn_rent_monthly": [np.nan, np.nan],
            "max_budget_mxn_rent_monthly": [np.nan, 10000],
            "min_budget_mxn_sale_total": [np.nan, np.nan],
            "max_budget_mxn_sale_total": [2000000, np.nan],
            "user_type": ["investor", "tenant_direct"],
            "search_sector": ["Office", "Retail"],
            "preferred_state": ["CDMX", "CDMX"],
            "preferred_municipality": ["X", "X"],
            "source": ["organic", "paid"],
        }
    )
    x = engineer_leads(leads)
    assert np.isnan(x.loc[0, "rent_budget_max"])
    assert x.loc[0, "rent_budget_applicable"] == 0
    assert x.loc[0, "sale_budget_min_effective"] == 0
    assert x.loc[0, "sale_min_missing_when_applicable"] == 1


def test_no_response_hours_is_not_treated_as_realized_response():
    q = pd.DataFrame(
        {
            "inquiry_id": [1, 2],
            "lead_id": [1, 1],
            "spot_id": [1, 2],
            "inquiry_at": pd.to_datetime(
                ["2026-01-01 10:00", "2026-01-02 10:00"]
            ),
            "broker_response": ["no_response", "accepted"],
            "broker_response_hours": [2.0, 3.0],
            "asked_visit": [False, False],
            "message_length": [100, 100],
            "urgency_days": [10, 10],
        }
    )
    x = add_history_features(prepare_inquiries(q))
    assert pd.isna(
        x.loc[x.inquiry_id.eq(1), "response_event_at"]
    ).all()
    assert (
        x.loc[
            x.inquiry_id.eq(2), "hist_prior_realized_responses"
        ].iloc[0]
        == 0
    )


def test_availability_is_strictly_backward_asof():
    rows = pd.DataFrame(
        {
            "row_id": [1],
            "spot_id": [7],
            "score_time": pd.to_datetime(["2026-01-10"]),
        }
    )
    avail = pd.DataFrame(
        {
            "snapshot_id": [1, 2],
            "spot_id": [7, 7],
            "snapshot_date": pd.to_datetime(
                ["2026-01-05", "2026-01-20"]
            ),
            "is_available": [True, False],
            "days_until_available": [0, 12],
            "competing_inquiries_30d": [3, 9],
        }
    )
    x = attach_availability(rows, avail)
    assert x.loc[0, "availability_is_available"] == 1
    assert x.loc[0, "availability_competing_inquiries_30d"] == 3
    assert x.loc[0, "availability_snapshot_age_days"] == 5


def test_land_building_attributes_are_gated_not_learned_as_real():
    spots = pd.DataFrame(
        {
            "spot_id": [1],
            "sector_name": ["Land"],
            "type_name": ["Single"],
            "state": ["X"],
            "municipality": ["Y"],
            "settlement": ["Z"],
            "corridor": ["C"],
            "region": ["R"],
            "lat": [20.0],
            "lon": [-99.0],
            "area_sqm": [1000],
            "price_sqm_mxn_rent": [10.0],
            "price_sqm_mxn_sale": [1000.0],
            "price_total_mxn_rent": [10000.0],
            "price_total_mxn_sale": [1000000.0],
            "maintenance_cost_mxn": [100.0],
            "modality": ["both"],
            "created_at": pd.to_datetime(["2025-01-01"]),
            "broker_id": [1],
        }
    )
    attrs = pd.DataFrame(
        {
            "spot_id": [1],
            "natural_light": [True],
            "luminaires": [30],
            "charging_ports": [10],
            "security_type": ["full"],
            "floor_level": [9],
            "elevators": [88],
            "vertical_height_m": [0],
            "parking_spaces": [2],
            "building_status": ["new"],
            "floor_material": ["wood"],
            "amenities": ['["gym", "parking"]'],
        }
    )
    x = engineer_spots(spots, attrs)
    assert x.loc[0, "built_environment_applicable"] == False
    assert pd.isna(x.loc[0, "model_elevators"])
    assert pd.isna(x.loc[0, "model_floor_material"])
    assert x.loc[0, "amenity_parking"] == 1


def test_amenity_parser_has_fixed_vocab():
    vals = parse_amenities('["gym", "parking"]')
    assert vals == ["gym", "parking"]
    assert "gym" in AMENITY_VOCAB


def test_supply_history_replaces_current_totals_and_broker_id():
    from feature_engineering import add_supply_history_features

    q = pd.DataFrame(
        {
            "inquiry_id": [1, 2, 3],
            "lead_id": [10, 11, 12],
            "spot_id": [7, 7, 8],
            "inquiry_at": pd.to_datetime(
                [
                    "2026-01-01 10:00",
                    "2026-01-02 10:00",
                    "2026-01-03 10:00",
                ]
            ),
            "broker_response": ["accepted", "scheduled_visit", "rejected"],
            "broker_response_hours": [2.0, 2.0, 2.0],
            "asked_visit": [False, True, False],
            "message_length": [100, 120, 80],
            "urgency_days": [10, 5, 20],
        }
    )
    q = prepare_inquiries(q)
    spots = pd.DataFrame(
        {"spot_id": [7, 8], "broker_id": [99, 99]}
    )
    x = add_supply_history_features(q, spots)
    second = x.loc[x.inquiry_id.eq(2)].iloc[0]
    third = x.loc[x.inquiry_id.eq(3)].iloc[0]
    assert second["spot_hist_prior_inquiries"] == 1
    assert second["broker_hist_prior_inquiries"] == 1
    assert second["broker_hist_realized_responses"] == 1
    assert third["broker_hist_prior_inquiries"] == 2
    assert third["broker_hist_scheduled_visits"] == 1
