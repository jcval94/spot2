from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pytest

ASSESSMENT_ROOT = Path(__file__).resolve().parents[1]
FEATURE_DIR = ASSESSMENT_ROOT / "features"
if str(FEATURE_DIR) not in sys.path:
    sys.path.insert(0, str(FEATURE_DIR))

from build_features import add_t1_deterministic_features, build_t2_trajectory
from transformers import FeatureRegistryGate, FoldAwareKMeans, GuardedPreprocessor


def _registry() -> Path:
    return ASSESSMENT_ROOT / "features" / "FEATURE_REGISTRY.csv"


def test_every_frozen_ablation_feature_exists_in_registry() -> None:
    registry = pd.read_csv(_registry())
    names = set(registry["feature_name"])
    groups = json.loads(
        (ASSESSMENT_ROOT / "features" / "feature_groups.json").read_text()
    )
    plan = json.loads(
        (ASSESSMENT_ROOT / "features" / "ablation_plan.json").read_text()
    )

    all_group_features: set[str] = set()
    for group in groups["t1"].values():
        all_group_features.update(group)
    for variant in plan["variants"]:
        for feature in variant.get("remove_features", []):
            assert feature in names
    assert all_group_features <= names


def test_registry_gate_rejects_unknown_forbidden_and_inventory_for_core() -> None:
    gate = FeatureRegistryGate(_registry())
    gate.assert_allowed(
        ["user_type", "search_sector", "target_area_sqm"],
        stage="T1",
        model_roles=("LEAD_QUALITY",),
    )

    with pytest.raises(ValueError, match="missing from FEATURE_REGISTRY"):
        gate.assert_allowed(["invented_feature"], stage="T1")

    with pytest.raises(ValueError, match="model_role=FORBIDDEN"):
        gate.assert_allowed(
            ["llm_*"],
            stage="T1",
            model_roles=("LEAD_QUALITY", "FORBIDDEN"),
            statuses=("REQUIRED", "SUPPORTED", "REJECTED"),
        )

    with pytest.raises(ValueError, match="model_role=INVENTORY"):
        gate.assert_allowed(["availability_known"], stage="T1")


def test_leadquality_groups_do_not_silently_include_matching_inventory() -> None:
    registry = pd.read_csv(_registry()).set_index("feature_name")
    groups = json.loads(
        (ASSESSMENT_ROOT / "features" / "feature_groups.json").read_text()
    )
    core = (
        groups["t1"]["A_LEAD_INTAKE"]
        + groups["t1"]["B_CURRENT_INQUIRY"]
        + groups["t1"]["C_REFINEMENT"]
    )
    assert set(registry.loc[core, "model_role"]) == {"LEAD_QUALITY"}
    assert not any(f.startswith("selected_spot_") for f in core)
    assert "inventory_candidate_count" not in core
    assert "availability_known" not in core


def test_structural_budget_missingness_is_not_labeled_unknown() -> None:
    frame = pd.DataFrame(
        {
            "score_id": ["a", "b"],
            "score_time": ["2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"],
            "search_modality": ["sale", "rent"],
            "user_type": ["investor", "tenant_direct"],
            "company_size": ["small", "small"],
            "industry": ["retail", "retail"],
            "search_sector": ["Office", "Office"],
            "target_area_sqm": [100.0, 100.0],
            "min_budget_mxn_rent_monthly": [np.nan, np.nan],
            "max_budget_mxn_rent_monthly": [np.nan, np.nan],
            "min_budget_mxn_sale_total": [1_000_000.0, np.nan],
            "max_budget_mxn_sale_total": [2_000_000.0, np.nan],
            "preferred_state": ["CDMX", "CDMX"],
            "preferred_municipality": ["M", "M"],
            "preferred_corridor": [None, None],
            "source": ["organic", "organic"],
            "channel": ["web", "web"],
            "message_length": [100, 100],
            "requested_area_sqm": [110.0, 110.0],
            "requested_budget_mxn_rent_monthly": [np.nan, np.nan],
            "requested_budget_mxn_sale_total": [1_500_000.0, np.nan],
            "urgency_days": [30.0, np.nan],
            "asked_visit": [False, False],
        }
    )
    out = add_t1_deterministic_features(frame)

    assert out.loc[0, "rent_budget_applicable"] == False
    assert out.loc[0, "intake_rent_budget_state"] == "NOT_APPLICABLE"
    assert out.loc[0, "inquiry_rent_budget_state"] == "NOT_APPLICABLE"

    assert out.loc[1, "rent_budget_applicable"] == True
    assert out.loc[1, "intake_rent_budget_state"] == "UNKNOWN"
    assert out.loc[1, "inquiry_rent_budget_state"] == "UNKNOWN"
    assert out.loc[1, "urgency_not_stated"] == True

    # The raw numeric value stays missing. The semantic state is carried separately.
    assert pd.isna(out.loc[0, "min_budget_mxn_rent_monthly"])
    assert pd.isna(out.loc[1, "min_budget_mxn_rent_monthly"])


def test_learned_preprocessor_refuses_validation_fit() -> None:
    X = pd.DataFrame(
        {
            "x": [1.0, np.nan, 3.0],
            "cat": ["a", None, "b"],
        }
    )
    y = pd.Series([0, 1, 0])
    prep = GuardedPreprocessor(["x"], ["cat"])

    with pytest.raises(ValueError, match="non-TRAIN"):
        prep.fit(X, y, fit_roles=["TRAIN", "VALIDATION", "TRAIN"])

    prep.fit(X, y, fit_roles=["TRAIN", "TRAIN", "TRAIN"])
    transformed = prep.transform(X)
    assert transformed.shape[0] == len(X)


def test_predictive_clusterer_refuses_non_train_fit() -> None:
    X = np.asarray([[0.0], [1.0], [2.0], [3.0]])
    cluster = FoldAwareKMeans(n_clusters=2, random_state=7)
    with pytest.raises(ValueError, match="non-TRAIN"):
        cluster.fit(X, fit_roles=["TRAIN", "TRAIN", "VALIDATION", "TRAIN"])

    cluster.fit(X, fit_roles=["TRAIN"] * 4)
    assert len(cluster.predict(X)) == 4


def _write_t2_sources(repo: Path) -> None:
    raw = repo / "data" / "candidate" / "csv"
    raw.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "lead_id": [1],
            "search_modality": ["rent"],
        }
    ).write_csv(raw / "leads.csv")
    pl.DataFrame(
        {
            "inquiry_id": [10, 11, 12, 13],
            "lead_id": [1, 1, 1, 1],
            "spot_id": [100, 101, 102, 100],
            "inquiry_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T10:00:00Z",
                "2026-01-02T10:00:00Z",
                "2026-01-03T10:00:00Z",
            ],
            "channel": ["web", "app", "phone", "web"],
            "message_length": [10, 20, 30, 40],
            "requested_area_sqm": [100.0, 110.0, 130.0, 120.0],
            "requested_budget_mxn_rent_monthly": [10_000.0, 11_000.0, 13_000.0, 12_000.0],
            "requested_budget_mxn_sale_total": [None, None, None, None],
            "urgency_days": [30, 20, 10, 15],
            "asked_visit": [False, False, True, True],
            # Deliberate forbidden outcome bait: build_t2_trajectory must not select it.
            "broker_response": [
                "scheduled_visit",
                "accepted",
                "rejected",
                "scheduled_visit",
            ],
            "broker_response_hours": [1.0, 2.0, 3.0, 4.0],
        }
    ).write_csv(raw / "inquiries.csv")


def test_t2_trajectory_uses_strict_past_and_same_time_batch_shift(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write_t2_sources(repo)
    traj = build_t2_trajectory(repo)

    row_11 = traj.loc[traj["inquiry_id"] == 11].iloc[0]
    row_12 = traj.loc[traj["inquiry_id"] == 12].iloc[0]
    row_13 = traj.loc[traj["inquiry_id"] == 13].iloc[0]

    # Inquiries 11 and 12 share a timestamp; neither can see the other.
    assert row_11["t2_prior_inquiry_count"] == 1
    assert row_12["t2_prior_inquiry_count"] == 1
    assert row_11["t2_hist_area_mean"] == 100.0
    assert row_12["t2_hist_area_mean"] == 100.0

    # The later inquiry can see all three truly prior rows, including both same-time events.
    assert row_13["t2_prior_inquiry_count"] == 3
    assert row_13["t2_prior_unique_spots"] == 3
    assert row_13["t2_current_spot_prior_count"] == 1
    assert bool(row_13["t2_current_spot_revisit_flag"])

    assert "_strict_prior_max_time" in traj.columns
    assert (
        pd.to_datetime(traj["_strict_prior_max_time"].dropna(), utc=True)
        < pd.to_datetime(
            [
                "2026-01-02T10:00:00Z",
                "2026-01-02T10:00:00Z",
                "2026-01-03T10:00:00Z",
            ],
            utc=True,
        )
    ).all()


def test_semantic_rules_are_qa_only_and_not_an_ablation() -> None:
    registry = pd.read_csv(_registry())
    semantic = registry.loc[
        registry["feature_family"].eq("SEMANTIC_RULES_QA")
    ]
    assert not semantic.empty
    assert set(semantic["model_role"]) == {"AUDIT_ONLY"}

    plan = json.loads(
        (ASSESSMENT_ROOT / "features" / "ablation_plan.json").read_text()
    )
    assert plan["semantic_rules"]["status"] == "QA_ONLY_NOT_ABLATED"
    assert all(
        "SEMANTIC" not in str(v).upper()
        for v in plan["variants"]
    )
