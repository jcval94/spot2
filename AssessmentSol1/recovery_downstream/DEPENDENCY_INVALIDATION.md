# Post-recovery dependency invalidation

Recovery authority: `LQ_RECOVERY_R4_STATIC_MATCH_V1`.

The recovered Lead Quality model changed from a featureless Base Rate to a three-feature selected-Spot logistic ranker. The target, scoring instant and split contract did **not** change. Therefore the PIT Inventory state remains valid, while every artifact that depends on Lead Quality probability or its ranking is stale.

| component | changed | invalidated | rebuild_required | reason |
|---|---|---|---|---|
| target | NO | NO | NO | `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1` unchanged. |
| splits | NO | NO | NO | `SPLIT_V1_T1_CALENDAR_FROZEN_2026-08-30` unchanged. |
| ABT | NO | NO | NO | Population and `score_time` are unchanged; recovery uses PIT-authorized selected-Spot structural fields already available at T1. |
| Feature Engineering | YES | PARTIAL | YES — recovered feature view/predictions only | Final Lead Quality feature set changed to area closeness, geographic fit and attribute completeness. No raw ABT rebuild is required. |
| Lead Quality | YES | YES | YES | Base Rate is superseded by `LQ_RECOVERY_R4_STATIC_MATCH_V1`. |
| calibration | YES | YES | YES — references/predictions | Method remains RAW, but the old constant probability/calibrator dependency is stale. |
| Inventory | NO | NO | NO | Frozen Inventory is PIT, outcome-independent and was selected without Lead Quality. |
| fallback | YES | PARTIAL | YES — recommendation list only | Clean-room list-completion audit supports max K=3 instead of K=5; Inventory scalar/ranking is unchanged. |
| Opportunity Score | YES | YES | YES | Old continuous product double-counts matching information now present in Lead Quality. |
| capacity thresholds | YES | YES | YES | Old top-10 assumption is stale; DEVELOPMENT OOF reevaluation covers 5/10/15/20. |
| figures | YES | YES | YES | Score/ranking-dependent figures must use recovered predictions and V2 score. |
| metrics | YES | YES | YES | Old Base-Rate/Inventory-equivalent metrics are no longer current. |
| leakage audit | YES | YES | YES | Final audit depended on the old featureless Lead Quality and old double-counting PASS. |

## Dependency rule applied

Inventory itself is **not rebuilt**. Only its already-frozen PIT outputs are reused as an independent serviceability/actionability layer.

The old formula `P_quality × InventoryServiceability` is retained only as a diagnostic challenger. With the recovered Lead Quality features it reuses area/geographic matching strength and materially changes ranking; it is therefore not canonical.

The post-recovery canonical integration is:

`OpportunityScoreV2 = P_quality × InventoryActionabilityGate`

where the gate is 1 for `KNOWN_AVAILABLE`, `TIER3_ONLY_EXPERIMENTAL` or `VERIFY_AVAILABILITY`, and 0 only for true `NO_RESULT` states. This prevents continuous matching strength from being counted twice while keeping explicit serviceability/fallback status beside the score.

## Historical upstream evidence

- **E018:** Semantic Rules = **NOT_SUPPORTED for scoring**. They are not inputs to final Lead Quality.
- **E019:** historical P85/top-15 and 30-day Availability results are supporting evidence only. The clean-room capacity decision below is recomputed and does not copy E019 metrics.
- **E020:** historical K=3 and combined-score findings are supporting evidence only. K=3 is independently re-supported here from AssessmentSol1 list completion; E020 score metrics are not reused.
