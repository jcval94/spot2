# Final methodological leakage audit — post-recovery

## Overall verdict

**READY — zero active BLOCKERS.**

Authority:
- Lead Quality: `LQ_RECOVERY_R4_STATIC_MATCH_V1`;
- Opportunity: `OPPORTUNITY_ACTIONABILITY_GATE_V2_FROZEN_2026-08-30`;
- capacity: P80 / top 20%;
- fallback: K=3;
- Inventory scalar: unchanged `INV_SERVICEABILITY_V1_FROZEN_2026-08-30`.

This file supersedes the prior final audit for every claim that depended on the old Base-Rate Lead Quality or V1 multiplicative score.

## Target, time and split

Target, maturity semantics, scoring stage and split contract did not change during recovery. T1 remains first-inquiry score time and eventual `scheduled_visit` under the frozen target contract.

The recovered selected Spot passes an explicit existence check: **0 / 5,000** selected Spots have `created_at > score_time`.

Temporal OOF alignment passes with 2,390 validation predictions and no fold-role, partition, score-time or target mismatches.

## New Feature Engineering

The final three recovered features are built from the selected inquiry Spot and PIT-defensible structural information:
- area closeness;
- geographic fit;
- attribute completeness.

No Availability, response, internal score, Market Context or mutable current price enters Lead Quality.

## Calibration

Calibration is RAW. The obsolete Base-Rate calibrator/probability is not reused.

## Inventory and fallback

Inventory candidate construction, backward as-of Availability and scalar serviceability remain frozen and outcome-independent.

Prompt 11.6 changes only recommendation list depth from K=5 to K=3, supported by clean-room list completion without labels. `NO_RESULT` and `VERIFY_AVAILABILITY` remain explicit.

## Opportunity Score and double counting

The old continuous multiplicative score is invalidated.

V2 uses `P_quality × InventoryActionabilityGate`; continuous serviceability is not multiplied. Row-wise verification finds **0 / 5,000 formula mismatches**.

The product table has **5,000 unique lead rows**, no forbidden outcome/internal-score columns, and no fallback list above K=3.

## Capacity

Capacity is recalculated on DEVELOPMENT temporal OOF at 5/10/15/20. The selected P80/top-20 policy has macro Lead Quality Lift **1.124x**.

The procedural holdout was not used for this selection.

## Claims

Lead Quality, serviceability and joint operational success are reported separately. Serviceability and joint proxies are not called conversion.

## Historical evidence handling

- E018: Semantic Rules NOT_SUPPORTED for scoring and excluded.
- E019: top-15/P85 and Availability 30d are supporting historical evidence only.
- E020: K=3 and combined proxy findings are supporting historical evidence only.
- No E019/E020 final metric is copied as an AssessmentSol1 result.

## Remaining limitations

The non-pristine June holdout, unversioned Spot prices, weak top-5 Lead Quality tail, high actionability coverage and tied score mass remain explicit limitations. None creates an active leakage/blocker under the current contract.

See `POST_RECOVERY_RED_TEAM.md` for the full reexecution matrix.
