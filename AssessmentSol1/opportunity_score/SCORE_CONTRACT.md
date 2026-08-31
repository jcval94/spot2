# Lead Opportunity Score Contract — post-recovery V2

**Version:** `OPPORTUNITY_ACTIONABILITY_GATE_V2_FROZEN_2026-08-30`

## Canonical formula

```
InventoryActionabilityGate =
    1  if frozen fallback status is KNOWN_AVAILABLE,
       TIER3_ONLY_EXPERIMENTAL, or VERIFY_AVAILABILITY
    0  otherwise

OpportunityScoreV2 = P(LeadQuality_recovered) × InventoryActionabilityGate
PublishedScore = 100 × OpportunityScoreV2
```

The score is frozen only after the Prompt 11.6 dependency reevaluation. No exponent, weight search, learned blender, stacking model or holdout-tuned adjustment is allowed.

## Why V1 was invalidated

V1 multiplied Lead Quality by continuous Inventory Serviceability. That was coherent only while Lead Quality was a featureless Base Rate.

The recovered champion `LQ_RECOVERY_R4_STATIC_MATCH_V1` now uses selected-Spot area closeness, geographic fit and attribute completeness. Continuous Inventory Serviceability also contains matching/serviceability strength. Multiplying both therefore double-counts part of the matching construct.

The V1 product remains a diagnostic challenger only. It is not an allowed final product score.

## Lead Quality

- target: `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`;
- model: `LQ_RECOVERY_R4_STATIC_MATCH_V1`;
- calibration: RAW;
- Availability is prohibited from Lead Quality;
- Semantic Rules / E018 are not used.

## Inventory

The scalar `INV_SERVICEABILITY_V1_FROZEN_2026-08-30` remains independently frozen and is **reported separately**. It is not multiplied into V2.

The actionability gate uses only the final frozen fallback state. `VERIFY_AVAILABILITY` stays actionable because UNKNOWN does not mean unavailable. A true `NO_RESULT` gates the scalar score to zero.

Fallback list depth is K=3 after an independent clean-room DEVELOPMENT list-completion audit. Candidate construction, PIT Availability, serviceability scalar and deterministic ranking are unchanged.

## Capacity

The canonical operating capacity is **P80 / top 20% within T1**. It was selected from DEVELOPMENT temporal OOF only after comparing 5/10/15/20. Numeric score cutoffs in `frozen_score_config.json` are display/reference thresholds; the capacity authority is percentile ranking with tie-break:

1. V2 score descending;
2. lead_id ascending.

## Product outputs

The product row contains no target, broker-response or hidden outcome field. Inventory Serviceability, confidence, exact-serviceable state and fallback recommendations remain visible beside V2 so that the scalar score cannot conceal operational trade-offs.

June remains `DIAGNOSTIC_ONLY_NON_PRISTINE` and was not used to select V2, P80 or K=3.
