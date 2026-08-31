# AssessmentSol1 — Final Spot2 Lead Opportunity Assessment

Status: **READY TO SUBMIT. Prompt 13 packaging and Prompt 14 final red-team are complete with zero active blockers.**

This directory is the clean-room source of truth for the definitive Spot2 assessment. Historical experiments may be cited as upstream supporting evidence but are not runtime dependencies and do not override reproduced/frozen AssessmentSol1 results.

## Start here

Evaluator-facing deliverables:

1. `final/EXECUTIVE_ONE_PAGER.html`
2. `final/presentation/index.html`
3. `final/ASSESSMENT_REPORT.md`
4. `final/notebook/final_assessment.html`
5. `final/notebook/final_assessment.ipynb`
6. `final/REPRODUCIBILITY.md`
7. `final/ARTIFACT_INDEX.md`

Machine-readable packaging state:

- `final/source_snapshot.json`
- `final/PROMPT_13_STATE.json`

## Frozen final system

- scoring moment: **T1 / first inquiry**;
- target: `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`;
- Lead Quality champion: **`LQ_RECOVERY_R4_STATIC_MATCH_V1`**;
- model: regularized Logistic Regression;
- calibration: RAW;
- Inventory: **`INV_SERVICEABILITY_V1_FROZEN_2026-08-30`**;
- fallback: **K=3**;
- Opportunity Score: **`OPPORTUNITY_ACTIONABILITY_GATE_V2_FROZEN_2026-08-30`**;
- formula: **`lead_quality_probability * inventory_actionability_gate`**;
- capacity: **P80 / top 20% within T1**;
- post-recovery final audit: **READY / 0 blockers**.

## Why recovery mattered

The previous Base-Rate/no-ranking state is historical only.

Prompt 11.5 recovered modest temporal ranking signal without changing target/splits and without using Availability in Lead Quality.

Recovered features:

1. `selected_spot_area_closeness`;
2. `selected_spot_geographic_fit`;
3. `selected_spot_attribute_completeness`.

Frozen development evidence:

- Lift@5: 0.859x;
- Lift@10: 1.075x;
- Lift@15: 1.084x;
- Lift@20: 1.124x under the post-recovery capacity evaluation.

Top-5 weakness and recovery uncertainty remain explicit limitations.

## Quality vs Opportunity

Lead Quality answers:

> Who shows greater propensity to reach the target outcome?

Inventory answers:

> Can the lead be served using point-in-time-known current/fallback inventory?

Opportunity answers:

> Where do progression propensity and serviceability coincide?

The old continuous product `P_quality × InventoryServiceability` is rejected/diagnostic-only after recovery because it double-counts selected-Spot matching context.

Canonical V2:

```
OpportunityScoreV2 = lead_quality_probability * inventory_actionability_gate
```

It is an operational prioritization score, **not a jointly calibrated probability**.

Use:
- Lead Quality when inventory should not constrain progression prioritization;
- Opportunity Score when progression + serviceability is the operational objective.

## Capacity and fallback

Capacity was recalculated on DEVELOPMENT temporal OOF only.

Final:

**P80 / top20 within T1.**

Fallback was independently revalidated in AssessmentSol1:

**K=3.**

`NO_RESULT` is preferred over indefinite relaxation.

## Historical upstream evidence

These are supporting only:

- E018 Semantic Rules → NOT_SUPPORTED for Lead Quality; final role is Inventory/Catalog QA.
- E019 P85/top15 → historical prior only; final AssessmentSol1 capacity is P80/top20.
- E020 combined score / K findings → historical supporting evidence only; final formula and K come from the clean-room post-recovery rebuild.

Closed architecture roles:

- Matching/clusters = **AUXILIARY**
- Semantic Rules = **INVENTORY / CATALOG QA**
- Response-time RF = **DIAGNOSTIC ONLY**

## LLM / AI

The AI requirement is self-contained under `llm/**`.

Final LLM role:

**sampled Semantic Inventory / Catalog QA discovery**.

The main Lead Opportunity Score requires:
- no OpenAI API call;
- no API key;
- no LLM cache;
- no LLM runtime dependency.

Prompt 12 gate:

`llm/results/prompt12_gate.json`

## Governance and limitations

- June procedural holdout is non-pristine / diagnostic-only.
- Top-5 Lead Quality Lift remains below 1.
- Recovery uncertainty is wide.
- Historical Spot prices are unversioned; precise budget fit is blocked/unknown.
- Score ties require rank-based bands.
- No causal/commercial conversion claim is supported.
- Opportunity Score is not a joint calibrated probability.
- LLM human precision/recall is unavailable.

## Primary authorities

- `models/lead_quality_recovery/RECOVERY_DECISION.md`
- `recovery_downstream/POST_RECOVERY_FINAL_STATE.json`
- `opportunity_score/frozen_score_config.json`
- `inventory/frozen_inventory_config.json`
- `audit/final_audit.json`
- `llm/results/prompt12_gate.json`
- `final/source_snapshot.json`

Final submission authority:
- `final/FINAL_REVIEW.md`
- `final/SUBMISSION_STATE.json`

**READY TO SUBMIT**
