from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "AssessmentSol1" / "target" / "build_targets.py"
SPEC = importlib.util.spec_from_file_location("assessment_sol1_build_targets", MODULE_PATH)
assert SPEC and SPEC.loader
targets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(targets)

UTC = timezone.utc


def inquiry(
    inquiry_id: int,
    lead_id: int,
    at: datetime,
    response: str | None,
    hours: float | None,
) -> dict:
    return {
        "inquiry_id": inquiry_id,
        "lead_id": lead_id,
        "spot_id": 1,
        "inquiry_at": at.isoformat(),
        "broker_response": response,
        "broker_response_hours": hours,
    }


def test_first_inquiry_is_deterministic_on_timestamp_tie() -> None:
    t = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        inquiry(20, 1, t, "accepted", 2.0),
        inquiry(10, 1, t, "scheduled_visit", 2.0),
        inquiry(30, 1, t + timedelta(seconds=1), "rejected", 2.0),
    ]
    first = targets.first_inquiry(rows)
    assert first["inquiry_id"] == 10


def test_target_a_score_time_is_first_inquiry_and_hours_do_not_define_label() -> None:
    t = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        inquiry(1, 7, t, "accepted", None),
        inquiry(2, 7, t + timedelta(days=1), "scheduled_visit", 1.0),
    ]
    first = targets.first_inquiry(rows)
    status, label = targets.target_a(first)
    assert targets._parse_dt(first["inquiry_at"]) == t
    assert status == "LABELED"
    assert label == 0


def test_target_b_boundary_excludes_score_time_and_includes_exact_30d() -> None:
    t = datetime(2026, 1, 1, tzinfo=UTC)
    horizon = t + timedelta(days=60)

    at_score = [inquiry(1, 1, t, "scheduled_visit", 0.0)]
    result_at_score = targets.target_b(at_score, t, horizon)
    assert result_at_score["label"] == 0

    exact_30d = [
        inquiry(1, 1, t, "accepted", 1.0),
        inquiry(2, 1, t + timedelta(days=29), "scheduled_visit", 24.0),
    ]
    result_30 = targets.target_b(exact_30d, t, horizon)
    assert result_30["label"] == 1

    after_30d = [
        inquiry(1, 1, t, "accepted", 1.0),
        inquiry(2, 1, t + timedelta(days=29), "scheduled_visit", 24.1),
    ]
    result_after = targets.target_b(after_30d, t, horizon)
    assert result_after["label"] == 0


def test_target_b_right_censors_when_30d_window_not_observable() -> None:
    t = datetime(2026, 1, 1, tzinfo=UTC)
    result = targets.target_b(
        [inquiry(1, 1, t, "accepted", 1.0)],
        t,
        t + timedelta(days=29, hours=23),
    )
    assert result["status"] == "CENSORED"
    assert result["label"] is None


def test_maturity_latest_observation_boundary() -> None:
    horizon = datetime(2026, 7, 13, tzinfo=UTC)
    assert targets.is_mature(horizon - timedelta(days=14), horizon, 14)
    assert not targets.is_mature(
        horizon - timedelta(days=14) + timedelta(seconds=1),
        horizon,
        14,
    )


def test_multiple_inquiries_distinguish_A_from_C() -> None:
    t = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        inquiry(1, 1, t, "accepted", 1.0),
        inquiry(2, 1, t + timedelta(days=10), "scheduled_visit", None),
    ]
    a_status, a_label = targets.target_a(targets.first_inquiry(rows))
    c = targets.target_c(
        rows,
        t,
        t + timedelta(days=100),
        maturity_buffer_days=14,
    )
    assert a_status == "LABELED"
    assert a_label == 0
    assert c["status"] == "LABELED"
    assert c["label"] == 1


def test_missing_response_fields_are_not_silently_negative() -> None:
    t = datetime(2026, 1, 1, tzinfo=UTC)

    a_status, a_label = targets.target_a(inquiry(1, 1, t, None, None))
    assert a_status.startswith("AMBIGUOUS")
    assert a_label is None

    b = targets.target_b(
        [inquiry(1, 1, t, "scheduled_visit", None)],
        t,
        t + timedelta(days=60),
    )
    assert b["status"] == "AMBIGUOUS"
    assert b["label"] is None

    c = targets.target_c(
        [inquiry(1, 1, t, None, None)],
        t,
        t + timedelta(days=60),
        maturity_buffer_days=14,
    )
    assert c["status"] == "AMBIGUOUS"
    assert c["label"] is None


def test_target_c_does_not_claim_visit_scheduled_inside_horizon() -> None:
    t = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        inquiry(1, 1, t, "accepted", 1.0),
        inquiry(2, 1, t + timedelta(days=20), "scheduled_visit", None),
    ]
    result = targets.target_c(
        rows,
        t,
        t + timedelta(days=100),
        maturity_buffer_days=14,
        inquiry_horizon_days=30,
    )
    assert result["label"] == 1
    assert result["positive_inquiry_at"] == t + timedelta(days=20)


def test_outcome_fields_are_label_only_and_blocked_as_features() -> None:
    targets.assert_outcome_fields_not_features(["channel", "asked_visit"])
    with pytest.raises(AssertionError):
        targets.assert_outcome_fields_not_features(
            ["channel", "broker_response"]
        )
    with pytest.raises(AssertionError):
        targets.assert_outcome_fields_not_features(
            ["broker_response_hours"]
        )


def test_frozen_contract_forbids_reselection_by_model_performance() -> None:
    contract = json.loads(
        (REPO_ROOT / "AssessmentSol1" / "target" / "target_contract.json").read_text()
    )
    assert contract["primary_target"]["id"] == targets.PRIMARY_TARGET_ID
    assert contract["primary_target"]["maturity_buffer_days"] == 14
    assert contract["freeze_policy"]["model_performance_can_change_target"] is False
    assert set(contract["outcome_fields"]["blocked_as_features"]) == {
        "broker_response",
        "broker_response_hours",
    }
