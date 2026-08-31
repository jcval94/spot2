# Double-counting audit — post-recovery

## Verdict

**PASS_AFTER_DEDUPLICATION.**

The previous audit is superseded because Lead Quality is no longer featureless.

## Recovered Lead Quality ownership

`LQ_RECOVERY_R4_STATIC_MATCH_V1` owns three selected-Spot features:

1. area closeness;
2. geographic fit;
3. structural-attribute completeness.

It uses **no Availability** and no outcome/current-state field.

## Inventory ownership

Frozen Inventory independently owns:

- PIT candidate existence;
- modality compatibility;
- tiered geography/sector relaxation;
- area fit;
- backward-as-of Availability;
- freshness/confidence;
- fallback state;
- budget only if a future versioned historical price source becomes available.

## Rejected integration

`P_quality × InventoryServiceability` is now prohibited as a final score because both factors contain continuous matching information.

The clean-room diagnostic is retained to make the trade-off visible, not to optimize it:
- top-15 pure Lead Quality Lift: 0.977x;
- top-15 joint-exact Lift: 1.244x.

That is evidence of serviceability over-weighting, not a free win.

## Canonical V2

`OpportunityScoreV2 = P_quality × InventoryActionabilityGate`

The gate is binary and only suppresses true `NO_RESULT`. Continuous `inventory_serviceability` and `inventory_confidence` are reported separately and cannot re-rank actionable leads.

This is considered a necessary operational feasibility gate, not a second continuous matching score.

## Explicit exclusions

- E018 Semantic Rules: NOT_SUPPORTED, excluded.
- Availability inside Lead Quality: excluded.
- `lead_score_internal`: prohibited.
- current/unversioned Spot prices: prohibited from PIT scoring.
- procedural holdout: not used for formula/capacity/K selection.
