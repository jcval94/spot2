# Inventory Serviceability — frozen scalar with post-recovery K=3 revision

Inventory is a separate, deterministic, point-in-time serviceability construct.

The scalar/ranking policy was frozen before Lead Quality recovery and did not consume Lead Quality outcomes or probabilities. Lead Quality later changed to `LQ_RECOVERY_R4_STATIC_MATCH_V1`; that does **not** invalidate the Inventory scalar because the Inventory selection/build was outcome-independent.

Canonical authority:
- `frozen_inventory_config.json`
- `SERVICEABILITY_CONTRACT.md`
- `MATCHING_POLICY.md`
- `FALLBACK_POLICY.md`
- `FRESHNESS_POLICY.md`
- `build_inventory.py`
- `rank_fallbacks.py`

Selection was restricted to T1 DEVELOPMENT. No target/outcome, CALIBRATION period or June procedural-holdout result was used to choose Inventory rules.

## Post-recovery revision

Only maximum fallback list depth changed: **K=5 → K=3**.

Clean-room DEVELOPMENT evidence:
- any result: 4,361 / 4,368;
- at least 3 recommendations: 4,051 / 4,368;
- at least 5 recommendations: 3,696 / 4,368.

Candidate construction, PIT Availability, serviceability scalar, confidence and deterministic rank order are unchanged.

## Guardrails

1. Spot must satisfy `spots.created_at <= score_time`.
2. Modality compatibility is a hard constraint.
3. Mutable/current Spot fields remain blocked where PIT provenance is insufficient.
4. Availability is strict backward-as-of only.
5. Missing prior snapshot remains `UNKNOWN`; `UNKNOWN != UNAVAILABLE`.
6. Stale backward snapshots reduce confidence rather than becoming future information.
7. `competing_inquiries_30d` remains blocked.
8. Tier 3 remains explicitly experimental.
9. Current unversioned Spot prices are not used historically; canonical budget fit remains unverified.
10. Fallback emits at most K=3 recommendations and known unavailable inventory is never recommended.
