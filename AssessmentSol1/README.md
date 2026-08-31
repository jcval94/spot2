# AssessmentSol1 — clean-room definitive assessment

Status: **PROMPT 11.6 COMPLETE. Post-recovery system frozen with zero active BLOCKERS. Prompt 12 has not been executed yet.**

This directory is the only writable home for the definitive Spot2 assessment. Historical experiments may be read as prior evidence but are never runtime dependencies.

## Frozen foundations

- target: `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`;
- T1 maturity: 14 days;
- split contract: `SPLIT_V1_T1_CALENDAR_FROZEN_2026-08-30`;
- point-in-time ABT architecture: unchanged by recovery;
- Lead Quality champion: **`LQ_RECOVERY_R4_STATIC_MATCH_V1`**;
- Lead Quality calibration: **RAW**;
- Inventory scalar: **`INV_SERVICEABILITY_V1_FROZEN_2026-08-30`**, unchanged;
- fallback maximum: **K=3**;
- Opportunity Score: **`OPPORTUNITY_ACTIONABILITY_GATE_V2_FROZEN_2026-08-30`**;
- capacity policy: **P80 / top 20% within T1**;
- post-recovery red team: **PASS, 0 blockers**.

## Recovered T1 Lead Quality

The previous `BASE_RATE + RAW` model is historical evidence only. Prompt 11.5 recovered a small regularized Logistic ranker using:

1. selected-Spot area closeness;
2. selected-Spot geographic fit;
3. selected-Spot attribute completeness.

No Availability is used in Lead Quality.

Frozen DEVELOPMENT temporal-OOF evidence:
- Lift@5: 0.859x;
- Lift@10: 1.075x;
- Lift@20 recovery gate: 1.115x;
- AP: 0.2186 versus base-rate AP 0.2083.

Prompt 11.6 re-ranks capacities with an explicit deterministic tie policy and selects top 20%, with macro Lead Quality Lift 1.124x.

The top-5 weakness remains explicit.

## Post-recovery Opportunity architecture

The old formula `P_quality × InventoryServiceability` is **invalidated** after recovery because Lead Quality now contains selected-Spot matching context.

Canonical V2:

```
OpportunityScoreV2 = P(LeadQuality_recovered) × InventoryActionabilityGate
```

Continuous Inventory Serviceability remains a separate output. The gate is binary and only prevents true `NO_RESULT` leads from being treated as operationally actionable.

This removes continuous double counting. The rejected raw multiplicative product remains diagnostic-only because it improves exact-serviceability concentration while harming pure Lead Quality capture.

## Capacity and fallback

Capacity was recalculated on DEVELOPMENT OOF only at 5/10/15/20. The clean-room result is **P80/top 20%**, not the historical E019 P85/top-15 prior.

Fallback list depth is independently re-supported at **K=3**:
- any result: 4,361/4,368 DEVELOPMENT leads;
- at least 3 recommendations: 4,051/4,368;
- at least 5 recommendations: 3,696/4,368.

Inventory scalar/ranking itself was not rebuilt.

## Holdout governance

June remains `DIAGNOSTIC_ONLY_NON_PRISTINE` because of the documented earlier incident. It was not used to select:
- recovered Lead Quality;
- V2 formula;
- P80 capacity;
- K=3.

Post-recovery confirmation requires genuinely new/hidden data.

## Historical upstream evidence

- E018 Semantic Rules: **NOT_SUPPORTED for scoring**; excluded.
- E019: historical top-15/P85 and Availability-30d evidence only.
- E020: historical K=3/combined-proxy evidence only.
- No E019/E020 metric is copied as an AssessmentSol1 result.

## Current authority

Start here:
- `recovery_downstream/POST_RECOVERY_DECISION.md`
- `recovery_downstream/POST_RECOVERY_FINAL_STATE.json`
- `models/lead_quality_recovery/RECOVERY_DECISION.md`
- `opportunity_score/SCORE_CONTRACT.md`
- `opportunity_score/frozen_score_config.json`
- `inventory/frozen_inventory_config.json`
- `audit/FINAL_LEAKAGE_AUDIT.md`
- `audit/POST_RECOVERY_RED_TEAM.md`

**POST-RECOVERY SYSTEM FROZEN — CONTINUE TO PROMPT 12**
