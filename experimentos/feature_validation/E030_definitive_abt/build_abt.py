from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FV = HERE.parent
ROOT = HERE.parents[2]
MODEL3 = ROOT / "experimentos" / "modelo_3"
E028 = FV / "E028_definitive_opportunity_score_abt"
E029 = FV / "E029_drift_sanitized_release_candidate"
for p in [MODEL3, E028]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from data_pipeline import (  # noqa: E402
    HISTORY_NUM,
    STAGES,
    add_history_features,
    add_match_features,
    attach_availability,
    attach_spots,
    prepare_inquiries,
    read_data,
    stage_balanced_weights,
)
from target_contract import TARGET_NAME, label_scoring_snapshots  # noqa: E402

RESULTS = HERE / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

MODEL_TARGET_STATUSES = {"POSITIVE", "NEGATIVE"}
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

IDENTIFIERS = [
    "prediction_key",
    "row_id",
    "lead_id",
    "inquiry_id",
    "spot_id",
    "stage_id",
    "stage",
    "score_time",
    "created_at",
    "split",
    "release_stage_policy",
    "sample_weight_stage_lead",
]

TARGET_COLUMNS = [
    TARGET_NAME,
    "target_status",
    "target_observation_end",
    "target_maturity_cutoff",
]

POLICY_GUARDRAILS = [
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
]

AUDIT_ONLY = [
    "score_weekday",
    "score_hour",
    "score_month",
    "days_from_lead_creation",
    "inquiry_number",
    "days_since_first_inquiry",
    "prior_searches",
]


def write_json(name: str, payload: object) -> None:
    (RESULTS / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


def raw_scoring_snapshots() -> tuple[pd.DataFrame, pd.DataFrame]:
    leads, inquiries_raw, spots, attrs, availability = read_data(ROOT)
    inquiries = add_history_features(prepare_inquiries(inquiries_raw))

    known_conversion = (
        inquiries[
            inquiries["broker_response"].eq("scheduled_visit")
            & inquiries["response_event_at"].notna()
        ]
        .groupby("lead_id")["response_event_at"]
        .min()
        .rename("first_conversion_at")
    )

    t0 = leads.copy()
    t0["stage_id"] = 0
    t0["stage"] = STAGES[0]
    t0["score_time"] = t0["created_at"]
    t0["spot_id"] = np.nan
    t0["inquiry_id"] = np.nan
    t0["inquiry_number"] = 0.0
    for col in [
        "channel",
        "asked_visit",
        "message_length",
        "requested_area_sqm",
        "requested_budget_mxn_rent_monthly",
        "requested_budget_mxn_sale_total",
        "urgency_days",
    ] + HISTORY_NUM:
        t0[col] = np.nan
    t0["has_inquiry_context"] = 0.0

    dyn = (
        inquiries.merge(leads, on="lead_id", how="left", suffixes=("", "_lead"))
        .merge(known_conversion, on="lead_id", how="left")
    )
    # A known visit already realized before a later inquiry makes the later
    # inquiry ineligible for re-scoring. Unknown-time visits are handled by
    # the canonical target as AMBIGUOUS rather than guessed here.
    dyn = dyn[
        dyn["first_conversion_at"].isna()
        | (dyn["inquiry_at"] < dyn["first_conversion_at"])
    ].copy()
    dyn["score_time"] = dyn["inquiry_at"]
    dyn["has_inquiry_context"] = 1.0
    dyn["stage_id"] = np.where(dyn["inquiry_number"].eq(1), 1, 2)
    dyn["stage"] = dyn["stage_id"].map(STAGES)

    cols = sorted(set(t0.columns) | set(dyn.columns))
    snapshots = pd.concat(
        [t0.reindex(columns=cols), dyn.reindex(columns=cols)],
        ignore_index=True,
    )
    snapshots["row_id"] = np.arange(len(snapshots), dtype=np.int64)
    snapshots = attach_spots(snapshots, spots, attrs)
    snapshots = attach_availability(snapshots, availability)
    snapshots = add_match_features(snapshots)

    snapshots["score_hour"] = snapshots["score_time"].dt.hour.astype(float)
    snapshots["score_month"] = snapshots["score_time"].dt.month.astype(float)
    snapshots["score_weekday"] = snapshots["score_time"].dt.day_name()
    snapshots["days_from_lead_creation"] = (
        snapshots["score_time"] - snapshots["created_at"]
    ).dt.total_seconds() / 86400.0

    for col in ["has_converted_before", "spot_natural_light", "availability_is_available"]:
        if col in snapshots:
            snapshots[col] = snapshots[col].map(
                lambda x: (
                    np.nan
                    if pd.isna(x)
                    else float(str(x).strip().lower() in {"true", "1", "yes"})
                )
            )

    labeled = label_scoring_snapshots(
        snapshots,
        inquiries_raw,
        observation_end=None,
    )
    return labeled, leads


def add_policy_guardrails(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    age = pd.to_numeric(out["availability_snapshot_age_days"], errors="coerce")
    out["availability_snapshot_age_log1p"] = np.log1p(age.clip(lower=0))
    out["availability_stale_gt90"] = age.gt(90).astype(float)
    out["availability_staleness_bucket"] = (
        pd.cut(
            age,
            bins=[-np.inf, 7, 30, 90, np.inf],
            labels=["0-7d", "8-30d", "31-90d", ">90d"],
            right=True,
        )
        .astype("string")
        .fillna("missing")
        .astype(object)
    )
    has_context = pd.to_numeric(out["has_availability_context"], errors="coerce").fillna(0)
    fresh = age.le(90) & age.notna() & has_context.eq(1)
    out["availability_effective_known"] = fresh.astype(float)
    raw = pd.to_numeric(out["availability_is_available"], errors="coerce")
    out["availability_effective_is_available"] = raw.where(fresh, np.nan)
    return out


def assign_temporal_split(df: pd.DataFrame, leads: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    model_ready_leads = set(
        out.loc[out["target_status"].isin(MODEL_TARGET_STATUSES), "lead_id"].dropna()
    )
    lead_frame = (
        leads.loc[leads["lead_id"].isin(model_ready_leads), ["lead_id", "created_at"]]
        .drop_duplicates("lead_id")
        .sort_values(["created_at", "lead_id"])
        .reset_index(drop=True)
    )
    n = len(lead_frame)
    if n < 3:
        raise RuntimeError("At least three model-ready leads are required for temporal split")
    a = max(1, int(n * 0.70))
    b = min(max(a + 1, int(n * 0.85)), n - 1)
    labels = np.full(n, "test", dtype=object)
    labels[:a] = "train"
    labels[a:b] = "val"
    lead_frame["split"] = labels
    split_map = lead_frame.set_index("lead_id")["split"]
    out["split"] = out["lead_id"].map(split_map).fillna("unlabeled_future")
    return out


def add_sample_weights(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["sample_weight_stage_lead"] = np.nan
    ready = out["target_status"].isin(MODEL_TARGET_STATUSES)
    for split_name in ["train", "val", "test"]:
        mask = ready & out["split"].eq(split_name)
        if not mask.any():
            continue
        part = out.loc[mask].copy()
        weights = stage_balanced_weights(part)
        out.loc[part.index, "sample_weight_stage_lead"] = weights
    return out


def prediction_key(df: pd.DataFrame) -> pd.Series:
    inquiry = df["inquiry_id"].astype("string").fillna("T0")
    score = pd.to_datetime(df["score_time"]).dt.strftime("%Y-%m-%dT%H:%M:%S.%f")
    return (
        df["lead_id"].astype("string")
        + "|"
        + df["stage"].astype("string")
        + "|"
        + score.astype("string")
        + "|"
        + inquiry
    )


def build_roles(
    model_cats: list[str],
    model_nums: list[str],
    final_columns: list[str],
) -> pd.DataFrame:
    model = set(model_cats + model_nums)
    policy = set(POLICY_GUARDRAILS)
    audit = set(AUDIT_ONLY)
    identifiers = set(IDENTIFIERS)
    targets = set(TARGET_COLUMNS)

    overlaps = {
        "model_policy": model & policy,
        "model_audit": model & audit,
        "model_identifier": model & identifiers,
        "model_target": model & targets,
    }
    bad = {k: sorted(v) for k, v in overlaps.items() if v}
    if bad:
        raise RuntimeError(f"ABT role overlap: {bad}")

    rows = []
    for col in final_columns:
        if col in model:
            role = "model_feature"
            subtype = "categorical" if col in model_cats else "numeric"
        elif col in policy:
            role, subtype = "policy_guardrail", "policy"
        elif col in audit:
            role, subtype = "audit_only", "diagnostic"
        elif col in identifiers:
            role, subtype = "identifier", "metadata"
        elif col in targets:
            role, subtype = "target", "label"
        else:
            role, subtype = "unclassified", "review"
        rows.append({"column": col, "role": role, "subtype": subtype})
    roles = pd.DataFrame(rows)
    unknown = roles.loc[roles["role"].eq("unclassified"), "column"].tolist()
    if unknown:
        raise RuntimeError(f"Unclassified ABT columns: {unknown}")
    return roles


def main() -> None:
    policy = json.loads(
        (E029 / "results" / "feature_policy.json").read_text(encoding="utf-8")
    )
    model_cats = list(policy["categorical_features"])
    model_nums = list(policy["numeric_features"])
    model_features = model_cats + model_nums

    labeled, leads = raw_scoring_snapshots()
    labeled = add_policy_guardrails(labeled)
    labeled = assign_temporal_split(labeled, leads)
    labeled = add_sample_weights(labeled)
    labeled["prediction_key"] = prediction_key(labeled)
    labeled["release_stage_policy"] = labeled["stage_id"].map(
        {
            0: "T0_neutral",
            1: "T1_neutral",
            2: "T2_candidate_pending_prospective_gate",
        }
    )

    absent = [c for c in model_features + POLICY_GUARDRAILS + AUDIT_ONLY if c not in labeled]
    if absent:
        raise RuntimeError(f"Required ABT columns missing: {absent}")

    leaked = sorted(FORBIDDEN & set(labeled.columns))
    # The raw intermediate may contain response fields, but they are explicitly
    # excluded from materialized ABT. We only fail if final selection contains them.
    ordered = []
    for group in [
        IDENTIFIERS,
        TARGET_COLUMNS,
        model_cats,
        model_nums,
        POLICY_GUARDRAILS,
        AUDIT_ONLY,
    ]:
        for col in group:
            if col in labeled and col not in ordered:
                ordered.append(col)

    final_forbidden = sorted(FORBIDDEN & set(ordered))
    if final_forbidden:
        raise RuntimeError(f"Forbidden columns selected into ABT: {final_forbidden}")

    audit = labeled[ordered].copy()
    model_ready = audit[
        audit["target_status"].isin(MODEL_TARGET_STATUSES)
        & audit["split"].isin(["train", "val", "test"])
    ].copy()
    model_ready[TARGET_NAME] = pd.to_numeric(
        model_ready[TARGET_NAME], errors="raise"
    ).astype(int)

    roles = build_roles(model_cats, model_nums, ordered)

    audit.to_csv(RESULTS / "abt_all_snapshots.csv.gz", index=False, compression="gzip")
    model_ready.to_csv(
        RESULTS / "abt_model_ready.csv.gz", index=False, compression="gzip"
    )
    roles.to_csv(RESULTS / "column_roles.csv", index=False)

    status = (
        audit.groupby(["stage", "target_status"], dropna=False)
        .agg(n=("prediction_key", "size"), unique_leads=("lead_id", "nunique"))
        .reset_index()
    )
    status["share_within_stage"] = status["n"] / status.groupby("stage")["n"].transform("sum")
    status.to_csv(RESULTS / "status_summary.csv", index=False)

    stage_target = (
        model_ready.groupby(["stage", "split"], dropna=False)
        .agg(
            n=("prediction_key", "size"),
            unique_leads=("lead_id", "nunique"),
            positive_rate=(TARGET_NAME, "mean"),
        )
        .reset_index()
    )
    stage_target.to_csv(RESULTS / "stage_target_summary.csv", index=False)

    split_summary = (
        model_ready.groupby("split")
        .agg(
            rows=("prediction_key", "size"),
            unique_leads=("lead_id", "nunique"),
            positive_rate=(TARGET_NAME, "mean"),
            min_lead_created_at=("created_at", "min"),
            max_lead_created_at=("created_at", "max"),
            min_score_time=("score_time", "min"),
            max_score_time=("score_time", "max"),
        )
        .reset_index()
    )
    split_summary.to_csv(RESULTS / "split_summary.csv", index=False)

    schema = {
        "schema_version": "v1",
        "grain": "lead_id × stage × score_time",
        "prediction_key": "lead_id|stage|score_time|inquiry_id-or-T0",
        "target": TARGET_NAME,
        "target_contract": "../E028_definitive_opportunity_score_abt/target_contract.json",
        "feature_policy": "../E029_drift_sanitized_release_candidate/results/feature_policy.json",
        "roles": {
            role: roles.loc[roles["role"].eq(role), "column"].tolist()
            for role in roles["role"].unique()
        },
        "categorical_model_features": model_cats,
        "numeric_model_features": model_nums,
        "forbidden_materialized_columns": sorted(FORBIDDEN),
        "release_stage_policy": {
            "T0_cold": "neutral",
            "T1_first_inquiry": "neutral",
            "T2_engaged": "candidate_pending_prospective_gate",
        },
    }
    write_json("abt_schema.json", schema)

    target_counts = audit["target_status"].value_counts(dropna=False).to_dict()
    summary = {
        "schema_version": "v1",
        "audit_rows": int(len(audit)),
        "audit_unique_leads": int(audit["lead_id"].nunique()),
        "model_ready_rows": int(len(model_ready)),
        "model_ready_unique_leads": int(model_ready["lead_id"].nunique()),
        "target_status_counts": {str(k): int(v) for k, v in target_counts.items()},
        "ambiguous_rows": int(audit["target_status"].eq("AMBIGUOUS_UNKNOWN_EVENT_TIME").sum()),
        "right_censored_rows": int(audit["target_status"].eq("RIGHT_CENSORED").sum()),
        "prior_visit_ineligible_rows": int(audit["target_status"].eq("INELIGIBLE_PRIOR_SCHEDULED_VISIT").sum()),
        "model_feature_count": int(len(model_features)),
        "categorical_model_feature_count": int(len(model_cats)),
        "numeric_model_feature_count": int(len(model_nums)),
        "policy_guardrail_count": int(len(POLICY_GUARDRAILS)),
        "audit_only_count": int(len(AUDIT_ONLY)),
        "forbidden_columns_present_in_materialized_abt": sorted(FORBIDDEN & set(audit.columns)),
        "split_unique_leads": {
            row["split"]: int(row["unique_leads"])
            for row in split_summary.to_dict("records")
        },
        "observation_end": str(audit["target_observation_end"].iloc[0]) if len(audit) else None,
    }
    write_json("abt_summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
