# Post-Recovery Red Team — Prompt 11.6

## Verdict

**PASS — 0 active BLOCKERS.**

This audit supersedes the Prompt-11 audit wherever that audit depended on the old Base-Rate Lead Quality or the V1 multiplicative Opportunity Score.

## Reexecuted checks

| Check | Evidence | Result |
|---|---|---|
| target contract unchanged | `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1` | PASS |
| split contract unchanged | `SPLIT_V1_T1_CALENDAR_FROZEN_2026-08-30` | PASS |
| selected Spot existed by score_time | 0 / 5,000 future Spot rows | PASS |
| selected Spot structural attributes present | 0 missing Spot rows; 0 missing spot_attributes rows | PASS |
| OOF fold alignment | 2,390 rows; F1=607, F2=602, F3=578, F4=603; 0 validation-role mismatches | PASS |
| OOF partition | 0 non-DEVELOPMENT rows | PASS |
| OOF score_time alignment | 0 mismatches | PASS |
| target orientation/alignment | 0 mismatches against first-inquiry `scheduled_visit` definition | PASS |
| calibration | recovered model is RAW; old Base-Rate calibrator is not reused | PASS |
| Availability inside Lead Quality | absent by frozen recovered config and feature formulas | PASS |
| E018 Semantic Rules in scoring | absent / NOT_SUPPORTED | PASS |
| capacity selection | only `DEVELOPMENT_OOF`; 5/10/15/20; no procedural holdout | PASS |
| double counting | continuous `inventory_serviceability` removed from V2 formula | PASS |
| raw multiplicative score | retained diagnostic-only; rejected because it harms pure Lead Quality capture | PASS |
| V2 formula | 0 / 5,000 output mismatches for `100 × p × actionability_gate` | PASS |
| product row grain | 5,000 rows / 5,000 unique leads | PASS |
| forbidden outcome columns | none of target/broker-response/internal-score fields in product output | PASS |
| fallback K | 0 output lists above K=3 | PASS |
| band ties | exact rank-based assignment; no artificial epsilon threshold manipulation | PASS |
| Inventory rebuild | scalar not rebuilt; only list depth revised | PASS |

## Double-counting attack

Recovered Lead Quality uses:
- selected-Spot area closeness;
- selected-Spot geographic fit;
- selected-Spot attribute completeness.

Frozen Inventory uses area, geography/tier, PIT Availability and other serviceability logic.

Therefore V1's continuous product is no longer structurally independent. The clean-room diagnostic confirms this is operationally material: at top 15% the raw multiplicative score has pure Lead Quality Lift **0.977x**, despite joint-exact Lift **1.244x**.

V2 contains only a binary Inventory actionability gate. The continuous Inventory scalar remains visible but cannot change ordering among actionable leads. This is the minimal integration needed to prevent a true `NO_RESULT` lead from appearing operationally actionable without re-counting match strength.

## Capacity attack

Capacity is selected from frozen temporal DEVELOPMENT OOF only:

- top 5%: Lead Quality Lift 0.859x — reject;
- top 10%: 1.075x;
- top 15%: 1.084x;
- top 20%: **1.124x — selected**.

P80/top-20 is therefore a current clean-room result. E019's historical P85/top-15 is not copied.

## Fallback attack

K=3 is supported without outcome labels:

- any result: 4,361 / 4,368 (99.84%);
- at least 3 recommendations: 4,051 / 4,368 (92.74%);
- at least 5 recommendations: 3,696 / 4,368 (84.62%).

K=3 changes list depth only. It does not alter PIT candidate construction, serviceability scalar or whether a lead has any result.

## Known limitations that are not blockers

1. June is not pristine and remains diagnostic-only; no post-recovery independent-confirmation claim is permitted.
2. The active review runtime did not execute the repository's exact Polars/pytest path. The recovery coefficients were independently reconstructed from raw blobs and the persisted product was red-teamed row-wise; run the project tests before external delivery.
3. Current Spot prices remain unversioned and budget fit stays blocked/unknown in canonical Inventory.
4. Top-5 Lead Quality concentration is weak.
5. The V2 actionability gate is 1 for 99.84% of DEVELOPMENT leads, so V2 is intentionally close to recovered Lead Quality; serviceability detail remains a separate product output.
6. Score ties are real; priority bands are rank-based with deterministic `lead_id` tie-break.
