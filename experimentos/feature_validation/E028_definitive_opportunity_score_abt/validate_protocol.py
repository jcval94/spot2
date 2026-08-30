from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from target_contract import (
    AB_OUTCOME_NAME,
    HORIZON_DAYS,
    build_lead_ab_outcome,
    prepare_candidate_events,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "dry_run_results"
OUT.mkdir(parents=True, exist_ok=True)

EXPERIMENT_ID = "E028_definitive_opportunity_score_abt"
REQUIRED_PER_ARM = 9806
REQUIRED_TOTAL = REQUIRED_PER_ARM * 2
PRODUCTION_EVENT_TIME_COMPLETENESS_GATE = 0.995


def stable_uniform(lead_id: object, stratum: str) -> float:
    """Deterministic pseudo-random number for the offline A/A dry run only."""
    payload = f"{EXPERIMENT_ID}|{stratum}|{lead_id}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    value = int.from_bytes(digest[:8], "big", signed=False)
    return value / float(2**64)


def chi_square_1df_survival(x: float) -> float:
    return math.erfc(math.sqrt(max(x, 0.0) / 2.0))


def read_event_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read only the raw tables needed to validate assignment and outcome."""
    data = ROOT / "data" / "candidate" / "csv"
    leads = pd.read_csv(data / "leads.csv", parse_dates=["created_at"])
    inquiries = pd.read_csv(data / "inquiries.csv", parse_dates=["inquiry_at"])
    return leads, inquiries


def build_outcome(
    leads: pd.DataFrame,
    inquiries: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Timestamp]:
    """Build the retrospective analogue of the prospective E028 outcome."""
    events = prepare_candidate_events(inquiries)
    candidates = [events["inquiry_at"].max(), events["response_event_at"].max()]
    observation_end = max(x for x in candidates if pd.notna(x))
    cutoff = observation_end - pd.Timedelta(days=HORIZON_DAYS)

    base = leads[leads["created_at"] <= cutoff].copy()
    base = base.drop_duplicates("lead_id", keep="first")
    base["assignment_at"] = base["created_at"]

    labeled = build_lead_ab_outcome(
        base,
        inquiries,
        assignment_col="assignment_at",
    )
    # Assignment at creation should normally make prior-visit ineligibility zero,
    # but keep the contract general and remove any such rows symmetrically.
    labeled = labeled[
        ~labeled["target_status"].isin(
            ["RIGHT_CENSORED", "INELIGIBLE_PRIOR_SCHEDULED_VISIT"]
        )
    ].copy()
    return labeled, pd.Timestamp(observation_end)


def assign_aa(d: pd.DataFrame) -> pd.DataFrame:
    """Offline A/A assignment plumbing check.

    Production should use a persistent server-side assignment table and,
    when supported, permuted blocks inside the same declared strata.
    """
    out = d.copy()
    parts = []
    for col in ["search_sector", "search_modality", "user_type"]:
        parts.append(out[col].astype("string").fillna("__MISSING__"))
    out["stratum"] = parts[0] + "|" + parts[1] + "|" + parts[2]
    u = [
        stable_uniform(lead_id, stratum)
        for lead_id, stratum in zip(out["lead_id"], out["stratum"])
    ]
    out["arm"] = np.where(np.asarray(u) < 0.5, "Control", "Treatment")
    return out


def main() -> None:
    leads, inquiries = read_event_data()
    prepared_events = prepare_candidate_events(inquiries)

    duplicate_leads = int(leads["lead_id"].duplicated().sum())
    d, observation_end = build_outcome(leads, inquiries)
    d = assign_aa(d)

    d["outcome_observed"] = d["target_status"].isin(["POSITIVE", "NEGATIVE"])
    d["outcome_ambiguous"] = d["target_status"].eq(
        "AMBIGUOUS_UNKNOWN_EVENT_TIME"
    )
    observable = d[d["outcome_observed"]].copy()

    arm = (
        d.groupby("arm", as_index=False)
        .agg(
            n=("lead_id", "size"),
            outcome_observed_n=("outcome_observed", "sum"),
            ambiguous_n=("outcome_ambiguous", "sum"),
        )
    )
    observed_arm = (
        observable.groupby("arm", as_index=False)
        .agg(
            positives=(AB_OUTCOME_NAME, "sum"),
            observed_rate=(AB_OUTCOME_NAME, "mean"),
        )
    )
    arm = arm.merge(observed_arm, on="arm", how="left")
    arm["outcome_observability_rate"] = arm["outcome_observed_n"] / arm["n"]
    arm["ambiguity_rate"] = arm["ambiguous_n"] / arm["n"]

    counts = arm.set_index("arm")["n"].to_dict()
    n_control = int(counts.get("Control", 0))
    n_treatment = int(counts.get("Treatment", 0))
    total = n_control + n_treatment
    expected = total / 2.0
    chi2 = (
        ((n_control - expected) ** 2 + (n_treatment - expected) ** 2) / expected
        if expected > 0
        else math.nan
    )
    srm_p = chi_square_1df_survival(chi2) if np.isfinite(chi2) else math.nan

    rates = arm.set_index("arm")["observed_rate"].to_dict()
    pseudo_delta = float(
        rates.get("Treatment", math.nan) - rates.get("Control", math.nan)
    )

    strata = (
        d.groupby(["stratum", "arm"], as_index=False)
        .agg(n=("lead_id", "size"))
        .pivot(index="stratum", columns="arm", values="n")
        .fillna(0)
        .reset_index()
    )
    for col in ["Control", "Treatment"]:
        if col not in strata:
            strata[col] = 0
    strata["total"] = strata["Control"] + strata["Treatment"]
    strata["treatment_share"] = np.where(
        strata["total"] > 0,
        strata["Treatment"] / strata["total"],
        np.nan,
    )
    strata["abs_deviation_from_half"] = (
        strata["treatment_share"] - 0.5
    ).abs()

    scheduled = prepared_events[
        prepared_events["broker_response"].eq("scheduled_visit")
    ]
    scheduled_missing_time_rate = (
        float(scheduled["response_event_at"].isna().mean())
        if len(scheduled)
        else math.nan
    )

    n_ambiguous = int(d["outcome_ambiguous"].sum())
    n_observable = int(d["outcome_observed"].sum())
    positive_observed = float(observable[AB_OUTCOME_NAME].sum())
    target_observability = float(n_observable / len(d)) if len(d) else math.nan

    lower_rate = (
        float(positive_observed / len(d))
        if len(d)
        else math.nan
    )
    upper_rate = (
        float((positive_observed + n_ambiguous) / len(d))
        if len(d)
        else math.nan
    )

    strata.to_csv(OUT / "strata_balance.csv", index=False)
    arm.to_csv(OUT / "aa_arm_summary.csv", index=False)

    summary = {
        "experiment_id": EXPERIMENT_ID,
        "purpose": (
            "A/A assignment and target-plumbing dry run only; "
            "not an estimate of treatment effect."
        ),
        "observation_end": str(observation_end),
        "horizon_days": HORIZON_DAYS,
        "source_leads": int(len(leads)),
        "duplicate_lead_ids": duplicate_leads,
        "mature_candidate_leads": int(len(d)),
        "target_status_counts": {
            str(k): int(v)
            for k, v in d["target_status"].value_counts(dropna=False).items()
        },
        "offline_outcome_observable_leads": n_observable,
        "offline_outcome_observability_rate": target_observability,
        "scheduled_visit_rows_missing_event_time_rate": scheduled_missing_time_rate,
        "observed_primary_rate_among_observable": (
            float(observable[AB_OUTCOME_NAME].mean())
            if len(observable)
            else math.nan
        ),
        "primary_rate_uncertainty_from_unknown_event_time": {
            "lower_bound_assume_ambiguous_negative": lower_rate,
            "upper_bound_assume_ambiguous_positive": upper_rate,
            "note": (
                "This range is only a retrospective data-quality bound. "
                "The prospective A/B requires actual backend event timestamps."
            ),
        },
        "aa_assignment": {
            "control": n_control,
            "treatment": n_treatment,
            "treatment_share": (
                float(n_treatment / total) if total else math.nan
            ),
            "chi_square_1df": float(chi2),
            "srm_p_value": float(srm_p),
            "pseudo_treatment_minus_control_pp_observable_only": (
                pseudo_delta * 100.0
            ),
            "note": (
                "The pseudo-delta must not be interpreted causally because "
                "both arms receive no treatment."
            ),
        },
        "strata": {
            "n_strata": int(len(strata)),
            "min_stratum_n": (
                int(strata["total"].min()) if len(strata) else 0
            ),
            "max_abs_treatment_share_deviation": (
                float(strata["abs_deviation_from_half"].max())
                if len(strata)
                else math.nan
            ),
        },
        "power_plan": {
            "alpha": 0.05,
            "power": 0.80,
            "absolute_mde": 0.02,
            "required_matured_per_arm": REQUIRED_PER_ARM,
            "required_matured_total": REQUIRED_TOTAL,
            "current_candidate_fraction_of_required": (
                float(len(d) / REQUIRED_TOTAL)
            ),
            "current_dataset_is_powered_for_definitive_test": bool(
                len(d) >= REQUIRED_TOTAL
            ),
            "note": (
                "Retrospective candidate-data feasibility only. "
                "The prospective RCT requires the full pre-registered sample."
            ),
        },
        "outcome_timestamp_quality": {
            "production_completeness_gate": (
                PRODUCTION_EVENT_TIME_COMPLETENESS_GATE
            ),
            "candidate_observability_passes_production_gate": bool(
                target_observability
                >= PRODUCTION_EVENT_TIME_COMPLETENESS_GATE
            ),
            "production_requirement": (
                "Actual backend scheduled_visit timestamp completeness >=99.5%; "
                "missing production event time is an instrumentation blocker, "
                "never a negative label."
            ),
        },
        "checks": {
            "unique_lead_assignment": duplicate_leads == 0,
            "full_30d_maturation": True,
            "srm_threshold_pass": (
                bool(srm_p >= 0.001) if np.isfinite(srm_p) else False
            ),
            "outcome_one_row_per_lead": bool(d["lead_id"].is_unique),
            "ambiguous_labels_not_coerced_to_zero": bool(
                d.loc[d["outcome_ambiguous"], AB_OUTCOME_NAME]
                .isna()
                .all()
            ),
        },
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report = f"""# E028 protocol dry run

**This is an A/A instrumentation test, not an A/B treatment-effect result.**

- Mature candidate leads: {len(d):,}
- Offline outcome observability: {target_observability:.2%}
- Scheduled-visit rows missing event time: {scheduled_missing_time_rate:.2%}
- Observed primary target rate (observable only): {summary['observed_primary_rate_among_observable']:.2%}
- Ambiguous unknown-event-time labels: {n_ambiguous:,}
- Primary-rate retrospective uncertainty: {lower_rate:.2%} to {upper_rate:.2%}
- Control/Treatment pseudo assignment: {n_control:,} / {n_treatment:,}
- SRM p-value: {srm_p:.4g}
- Pseudo A/A delta (observable only): {pseudo_delta*100:+.2f} pp
- Required matured sample for +2 pp MDE: {REQUIRED_TOTAL:,}
- Current candidate data covers: {summary['power_plan']['current_candidate_fraction_of_required']:.1%} of that requirement

## Interpretation

Passing this dry run means assignment and target plumbing are internally coherent.
Candidate-data AMBIGUOUS labels expose retrospective event-time limitations and are
never coerced to zero. Production must instrument the actual scheduled_visit
timestamp; failure to do so is a launch blocker.

This dry run does **not** provide causal evidence for the Opportunity system.
The definitive E028 must still be run prospectively with a frozen Treatment
artifact and full 30-day maturation.
"""
    (OUT / "REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
