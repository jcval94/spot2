from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from semantic_recovery_common import VARIANTS, development_ladder, final_test, load_abt

HERE = Path(__file__).resolve().parent
E031 = HERE / "E031_semantic_feature_engineering_ladder"
E032 = HERE / "E032_t0_semantic_recovery"
E033 = HERE / "E033_t1_semantic_recovery"
E034 = HERE / "E034_general_feature_engineering_catalog"

for d in [E031, E032, E033, E034]:
    (d / "results").mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


def stage_report(stage: str, ladder: pd.DataFrame, choice: dict) -> str:
    cols = [
        "variant","roc_auc","average_precision","ap_over_prevalence",
        "lift_top_10pct","recall_top_20pct","brier","n_cat","n_num",
    ]
    return (
        f"## {stage}\n\n"
        + ladder[cols].to_markdown(index=False)
        + "\n\n"
        + f"Selected on validation: **{choice['variant']}**. "
        + f"Qualified gate: **{choice['qualified_on_validation']}**.\n"
    )


def recovery_report(title: str, result: dict) -> str:
    c = result["candidate_metrics"]
    b = result["atomic_baseline_metrics"]
    ci = result["candidate_bootstrap"]
    d = result["delta_vs_atomic"]
    return f"""# {title}

**Status: {result['status']}**

Selected variant: **{result['selected_variant']}**

| Metric | Candidate | Atomic baseline |
|---|---:|---:|
| ROC-AUC | {c['roc_auc']:.4f} | {b['roc_auc']:.4f} |
| AP | {c['average_precision']:.4f} | {b['average_precision']:.4f} |
| AP / prevalence | {c['ap_over_prevalence']:.3f}x | {b['ap_over_prevalence']:.3f}x |
| Lift@10 | {c['lift_top_10pct']:.3f}x | {b['lift_top_10pct']:.3f}x |
| Recall@20 | {c['recall_top_20pct']:.3f} | {b['recall_top_20pct']:.3f} |
| Brier | {c['brier']:.4f} | {b['brier']:.4f} |

## Absolute uncertainty

- AUC 95% lead-bootstrap: **[{ci['roc_auc']['ci95_low']:.4f}, {ci['roc_auc']['ci95_high']:.4f}]**.
- AP/prevalence 95%: **[{ci['ap_over_prevalence']['ci95_low']:.3f}, {ci['ap_over_prevalence']['ci95_high']:.3f}]**.
- Lift@10 95%: **[{ci['lift_top_10pct']['ci95_low']:.3f}, {ci['lift_top_10pct']['ci95_high']:.3f}]**.

## Delta vs atomic sanitized baseline

- Delta AUC: **{d['roc_auc']['point_delta']:+.4f}**, CI95% [{d['roc_auc']['ci95_low']:+.4f}, {d['roc_auc']['ci95_high']:+.4f}].
- Delta AP: **{d['average_precision']['point_delta']:+.4f}**, CI95% [{d['average_precision']['ci95_low']:+.4f}, {d['average_precision']['ci95_high']:+.4f}].
- Delta Lift@10: **{d['lift_top_10pct']['point_delta']:+.3f}x**, CI95% [{d['lift_top_10pct']['ci95_low']:+.3f}, {d['lift_top_10pct']['ci95_high']:+.3f}].

## Recovery gate

RECOVERED requires simultaneously:

1. lower AUC CI95% > 0.50;
2. AP/prevalence >= 1.05;
3. Lift@10 >= 1.10;
4. candidate AP > atomic baseline AP.

PROMISING_NOT_CONFIRMED requires point AUC > 0.50, AP/prevalence >= 1.03 and Lift@10 >= 1.05.

No temporal clocks, Availability LeadQuality signal, broker outcome/prior or current-state Spot aggregates were introduced.
"""


def catalog(t0: dict, t1: dict) -> pd.DataFrame:
    rows = [
        ["scale_log_transforms","T0/T1/T2","TESTED_E031","model_candidate","log1p area, budget, urgency, message length; reduces scale/outlier sensitivity","PIT safe"],
        ["budget_mid_width_specificity","T0/T1","TESTED_E031","model_candidate","midpoint, width, relative width, completeness","PIT safe"],
        ["geo_search_specificity","T0","TESTED_E031","model_candidate","count/quality of preferred geography fields","PIT safe"],
        ["search_need_semantic","T0/T1","TESTED_E031","model_candidate","rent/sale/flexible semantic state","PIT safe"],
        ["t0_to_t1_need_transition","T1/T2","TESTED_E031","model_candidate","requested modality and area/budget shifts vs intake","PIT safe"],
        ["dynamic_need_soft_profile","T1/T2","TESTED_E031","model_candidate","train-only K=5 hard profile + centroid distances + ambiguity margin","Outcome-free; fit train only"],
        ["search_need_soft_profile","T0","TESTED_E031","model_candidate","train-only K=3 need profile + centroid distances","Outcome-free; fit train only"],
        ["spot_physical_soft_profile","T1/T2","TESTED_E031","model_candidate","train-only K=4 physical profile + distances","Fit unique train Spots only"],
        ["spot_location_soft_profile","T1/T2","TESTED_E031","model_candidate","train-only K=7 location profile + distances","Fit unique train Spots only"],
        ["lead_spot_directional_fit","T1/T2","TESTED_E031","model_candidate","absolute log area/budget mismatch, within-budget, within-20% area","PIT safe"],
        ["semantic_profile_interactions","T0/T1/T2","TESTED_E031","model_candidate","Need x source/sector; DynamicNeed x PH/LOC; transition x PH","No outcome-derived cell multipliers"],
        ["missingness_as_signal","T0/T1/T2","NEXT_CHALLENGER","model_candidate","explicit missingness pattern rather than implicit imputer only","Verify stability by cohort"],
        ["rolling_behavior_velocity","T2","NEXT_CHALLENGER","model_candidate","recent inquiry/unique-spot/asked-visit intensity in trailing windows","Strict as-of windows; avoid raw funnel clocks"],
        ["lead_preference_entropy","T2","NEXT_CHALLENGER","model_candidate","diversity of sectors/locations/spots contacted before score","Strict historical events only"],
        ["price_relative_to_local_inventory","T1/T2","NEXT_CHALLENGER","model_candidate","spot price percentile vs contemporaneous same sector/location inventory","Must be as-of; train-only/reference window"],
        ["geo_distance_to_preference_centroid","T1/T2","NEXT_CHALLENGER","model_candidate","distance between Spot and preferred geo centroid","Needs canonical coordinates for preferred area"],
        ["cluster_uncertainty_margin","T0/T1/T2","TESTED_E031","model_candidate","nearest-centroid distance and first-vs-second margin","Outcome-free"],
        ["behavioral_persona_BP","T0","REJECT_AS_PRIMARY","interpretability_only","stable semantic clusters but worsened AP/Lift in prior evidence","Can remain diagnostic"],
        ["broker_supply_cluster","T1/T2","REJECT","none","failed balance twice","Do not force K"],
        ["broker_service_profile","T1/T2","ROUTING_ONLY","routing_candidate","useful segmentation but no robust marginal lift","Separate Lead x Spot x Broker problem"],
        ["availability_state_freshness","T1/T2","POLICY_GUARDRAIL","policy_guardrail","serviceability/freshness, not LeadQuality","Backward as-of only"],
        ["market_context","T0/T1/T2","BLOCKED","none","potential macro context","Blocked until effective/publication time exists"],
        ["raw_calendar_progress_clocks","T0/T1/T2","BLOCKED","audit_only","score month/hour/weekday, days from creation, inquiry number","Strong drift proxy"],
        ["prior_searches","T0/T1/T2","BLOCKED","audit_only","ablation showed deterioration when included","Do not reintroduce"],
        ["target_encoded_high_cardinality","T0/T1/T2","NEXT_CHALLENGER_HIGH_RISK","model_candidate","cross-fitted encoding for source/location categories","Must be fold-safe and temporal"],
        ["text_semantic_embedding","T1/T2","DATA_GAP","future_candidate","message meaning beyond length","Raw inquiry text not in canonical ABT"],
    ]
    df = pd.DataFrame(
        rows,
        columns=["family","stages","status","recommended_role","idea","guardrail"],
    )
    df["t0_recovery_status"] = t0["status"]
    df["t1_recovery_status"] = t1["status"]
    return df


def main() -> None:
    abt = load_abt()

    ladders = []
    choices = {}
    for stage in ["T0_cold", "T1_first_inquiry"]:
        ladder, choice = development_ladder(stage, abt)
        ladders.append(ladder)
        choices[stage] = choice

    ladder_df = pd.concat(ladders, ignore_index=True)
    ladder_df.to_csv(E031 / "results" / "validation_ladder.csv", index=False)
    write_json(E031 / "results" / "selected_variants.json", choices)

    e31 = "# E031 — Semantic Feature Engineering ladder\n\n"
    e31 += "**Important:** selection uses only E030 train/validation. E030 test is not used by this ladder.\n\n"
    for stage in ["T0_cold", "T1_first_inquiry"]:
        e31 += stage_report(stage, ladder_df[ladder_df.stage.eq(stage)], choices[stage])
    (E031 / "results" / "REPORT.md").write_text(e31, encoding="utf-8")

    t0 = final_test("T0_cold", choices["T0_cold"]["variant"], abt)
    t1 = final_test("T1_first_inquiry", choices["T1_first_inquiry"]["variant"], abt)

    write_json(E032 / "results" / "summary.json", t0)
    write_json(E033 / "results" / "summary.json", t1)
    (E032 / "results" / "REPORT.md").write_text(
        recovery_report("E032 — T0 semantic recovery", t0), encoding="utf-8"
    )
    (E033 / "results" / "REPORT.md").write_text(
        recovery_report("E033 — T1 semantic recovery", t1), encoding="utf-8"
    )

    cat = catalog(t0, t1)
    cat.to_csv(E034 / "results" / "feature_engineering_catalog.csv", index=False)
    summary = {
        "t0_status": t0["status"],
        "t0_selected_variant": t0["selected_variant"],
        "t1_status": t1["status"],
        "t1_selected_variant": t1["selected_variant"],
        "tested_families": VARIANTS,
        "next_challengers": cat.loc[
            cat.status.str.startswith("NEXT_CHALLENGER"), "family"
        ].tolist(),
        "blocked_or_rejected": cat.loc[
            cat.status.isin(["BLOCKED","REJECT","REJECT_AS_PRIMARY"]), "family"
        ].tolist(),
    }
    write_json(E034 / "results" / "summary.json", summary)
    (E034 / "results" / "REPORT.md").write_text(
        "# E034 — General Feature Engineering catalog\n\n"
        + f"- T0 recovery: **{t0['status']}** using **{t0['selected_variant']}**.\n"
        + f"- T1 recovery: **{t1['status']}** using **{t1['selected_variant']}**.\n\n"
        + "The catalog separates tested model candidates, next challengers, routing-only features, policy guardrails and blocked ideas.\n\n"
        + cat.to_markdown(index=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
