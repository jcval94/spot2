from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
FV = HERE.parent
E029_POLICY = FV / "E029_drift_sanitized_release_candidate" / "results" / "feature_policy.json"

FORBIDDEN = {
    "lead_score_internal",
    "broker_response",
    "broker_response_hours",
    "response_event_at",
    "first_conversion_at",
    "spot_days_on_market",
    "spot_total_inquiries",
    "spot_total_views",
    "spot_is_active",
}

BLOCKED_FROM_MODEL = {
    "score_weekday",
    "score_hour",
    "score_month",
    "days_from_lead_creation",
    "inquiry_number",
    "days_since_first_inquiry",
    "prior_searches",
    "availability_is_available",
    "availability_days_until_available",
    "availability_competing_inquiries_30d",
    "availability_snapshot_age_days",
    "has_availability_context",
    "availability_snapshot_age_log1p",
    "availability_staleness_bucket",
    "availability_stale_gt90",
    "availability_effective_known",
    "availability_effective_is_available",
}

VALID_SPLITS = {"train", "val", "test"}
BINARY_STATUSES = {"POSITIVE", "NEGATIVE"}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    audit = pd.read_csv(RESULTS / "abt_all_snapshots.csv.gz")
    ready = pd.read_csv(RESULTS / "abt_model_ready.csv.gz")
    roles = pd.read_csv(RESULTS / "column_roles.csv")
    schema = json.loads((RESULTS / "abt_schema.json").read_text(encoding="utf-8"))
    summary = json.loads((RESULTS / "abt_summary.json").read_text(encoding="utf-8"))
    policy = json.loads(E029_POLICY.read_text(encoding="utf-8"))

    checks: dict[str, object] = {}

    assert_true(len(audit) > 0, "Audit ABT is empty")
    assert_true(len(ready) > 0, "Model-ready ABT is empty")
    checks["non_empty"] = True

    assert_true(audit["prediction_key"].notna().all(), "Null prediction_key")
    assert_true(audit["prediction_key"].is_unique, "prediction_key is not unique")
    checks["prediction_key_unique"] = True

    assert_true(
        set(ready["target_status"].unique()) <= BINARY_STATUSES,
        f"Model-ready contains non-binary statuses: {sorted(set(ready['target_status']) - BINARY_STATUSES)}",
    )
    y = pd.to_numeric(ready["target_scheduled_visit_30d"], errors="coerce")
    assert_true(y.notna().all(), "Model-ready contains null target")
    assert_true(set(y.unique()) <= {0, 1}, "Model-ready target is not binary")
    checks["model_ready_target_binary_observed_only"] = True

    assert_true(
        audit["target_status"].eq("AMBIGUOUS_UNKNOWN_EVENT_TIME").any(),
        "Audit ABT unexpectedly has no ambiguous target rows",
    )
    assert_true(
        audit["target_status"].eq("RIGHT_CENSORED").any(),
        "Audit ABT unexpectedly has no right-censored rows",
    )
    checks["audit_preserves_ambiguous_and_censoring"] = True

    present_forbidden = sorted(FORBIDDEN & set(audit.columns))
    assert_true(not present_forbidden, f"Forbidden columns materialized: {present_forbidden}")
    checks["forbidden_columns_absent"] = True

    model_role = set(roles.loc[roles["role"].eq("model_feature"), "column"])
    expected_model = set(policy["categorical_features"] + policy["numeric_features"])
    assert_true(
        model_role == expected_model,
        f"Model feature role differs from E029 policy. Missing={sorted(expected_model-model_role)}, extra={sorted(model_role-expected_model)}",
    )
    assert_true(
        not (model_role & BLOCKED_FROM_MODEL),
        f"Blocked drift/guardrail features entered LeadQuality: {sorted(model_role & BLOCKED_FROM_MODEL)}",
    )
    checks["model_features_match_e029"] = True
    checks["blocked_features_not_model_features"] = True

    policy_role = set(roles.loc[roles["role"].eq("policy_guardrail"), "column"])
    assert_true(
        all(c.startswith("availability_") or c == "has_availability_context" for c in policy_role),
        f"Unexpected policy guardrails: {sorted(policy_role)}",
    )
    checks["availability_separated_as_policy_guardrail"] = True

    model_lead_splits = (
        ready.groupby("lead_id")["split"].nunique(dropna=False)
    )
    assert_true(
        int(model_lead_splits.max()) == 1,
        "At least one model-ready lead appears in multiple splits",
    )
    assert_true(set(ready["split"].unique()) == VALID_SPLITS, "Missing/extra model-ready splits")
    checks["lead_split_isolation"] = True

    lead_dates = (
        ready[["lead_id", "created_at", "split"]]
        .drop_duplicates("lead_id")
        .assign(created_at=lambda x: pd.to_datetime(x["created_at"], errors="raise", format="mixed"))
    )
    ranges = (
        lead_dates.groupby("split")["created_at"]
        .agg(["min", "max"])
        .to_dict("index")
    )
    assert_true(
        ranges["train"]["max"] <= ranges["val"]["min"],
        f"Train/val temporal overlap violates order: {ranges}",
    )
    assert_true(
        ranges["val"]["max"] <= ranges["test"]["min"],
        f"Val/test temporal overlap violates order: {ranges}",
    )
    checks["chronological_split_order"] = True

    score_time = pd.to_datetime(audit["score_time"], errors="raise", format="mixed")
    created_at = pd.to_datetime(audit["created_at"], errors="raise", format="mixed")
    t0 = audit["stage_id"].eq(0)
    assert_true(
        (score_time[t0] == created_at[t0]).all(),
        "T0 score_time must equal lead created_at",
    )
    inq_n = pd.to_numeric(audit["inquiry_number"], errors="coerce")
    t1 = audit["stage_id"].eq(1)
    t2 = audit["stage_id"].eq(2)
    assert_true(inq_n[t1].eq(1).all(), "T1 must be first inquiry")
    assert_true(inq_n[t2].ge(2).all(), "T2 must be second-or-later inquiry")
    checks["stage_semantics"] = True

    release_map = {
        0: "T0_neutral",
        1: "T1_neutral",
        2: "T2_candidate_pending_prospective_gate",
    }
    for sid, label in release_map.items():
        vals = set(audit.loc[audit["stage_id"].eq(sid), "release_stage_policy"].dropna())
        assert_true(vals == {label}, f"Stage {sid} release policy mismatch: {vals}")
    checks["release_stage_policy"] = True

    weights = pd.to_numeric(ready["sample_weight_stage_lead"], errors="coerce")
    assert_true(weights.notna().all(), "Missing model-ready sample weights")
    assert_true((weights > 0).all(), "Non-positive sample weights")
    checks["sample_weights_present"] = True

    assert_true(
        summary["audit_rows"] == len(audit),
        "Summary audit_rows mismatch",
    )
    assert_true(
        summary["model_ready_rows"] == len(ready),
        "Summary model_ready_rows mismatch",
    )
    checks["summary_reconciles"] = True

    validation = {
        "status": "PASS",
        "checks": checks,
        "audit_rows": int(len(audit)),
        "model_ready_rows": int(len(ready)),
        "model_ready_unique_leads": int(ready["lead_id"].nunique()),
        "model_feature_count": int(len(model_role)),
        "policy_guardrail_count": int(len(policy_role)),
        "split_created_at_ranges": {
            k: {"min": str(v["min"]), "max": str(v["max"])}
            for k, v in ranges.items()
        },
        "target_status_counts": {
            str(k): int(v)
            for k, v in audit["target_status"].value_counts(dropna=False).to_dict().items()
        },
    }
    (RESULTS / "validation.json").write_text(
        json.dumps(validation, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(validation, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
