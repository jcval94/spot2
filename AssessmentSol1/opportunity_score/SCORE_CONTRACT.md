# Lead Opportunity Score Contract

**Version:** `OPPORTUNITY_MULTIPLICATIVE_V1_FROZEN_2026-08-30`

## Primary formula

The published product score is:

```
OpportunityScore = P(LeadQuality) × InventoryServiceability
PublishedScore = 100 × OpportunityScore
```

Both factors are frozen 0–1 quantities. No exponent, weight, learned blender, stacking model, post-hoc rescaling or holdout-tuned adjustment is allowed.

## Frozen inputs

### Lead Quality

The frozen T1 champion is `BASE_RATE + RAW` with probability **0.20375457875457875**.

It has no model features. Therefore the clean Lead Quality construct contains no selected-Spot, matching or Inventory context.

A pre-registered selected-Spot challenger existed as Ablation E. It was explicitly `CHALLENGER_ONLY`, was not promoted, and is excluded from this score. This prevents double counting of matching/serviceability information.

### Inventory

Inventory uses `INV_SERVICEABILITY_V1_FROZEN_2026-08-30`. Its score is deterministic, PIT, and separate from Lead Quality. Snapshot freshness remains an independent `inventory_confidence`; it is not multiplied into the Opportunity Score.

Because current Spot prices are unversioned, canonical Inventory remains `PARTIAL_PIT_NO_VERSIONED_PRICE`; Opportunity Score inherits that limitation rather than silently filling a budget component.

## Consequence of the frozen Lead Quality champion

Because `P(LeadQuality)` is constant for every T1 lead, the multiplicative score is a positive monotonic transformation of Inventory Serviceability:

```
OpportunityScore = 0.20375457875457875 × InventoryServiceability
```

Therefore **Inventory-only and Opportunity Score have exactly the same ranking**. The multiplication is retained because it is the requested conceptual architecture and preserves the two-factor decomposition; it must not be presented as adding ranking lift beyond Inventory in this frozen assessment.

Lead Quality alone has tied scores and therefore no valid Top-X ranking metrics.

## Published columns

One row per T1 lead contains at least:

- `lead_id`
- `score_time`
- `lead_quality_probability`
- `lead_quality_score_0_100`
- `inventory_serviceability`
- `inventory_confidence`
- `opportunity_score_0_100`
- `priority_band`
- `exact_spot_serviceable`
- `fallback_status`
- `fallback_spot_ids`
- `fallback_relaxation_tier`
- `reason_codes`
- `model_version`
- `inventory_version`
- `data_fingerprint`

Target/outcome columns are never part of the product scoring table.

## Evaluation boundary

Formula and policy are frozen before the June procedural holdout diagnostic. June remains `DIAGNOSTIC_ONLY_NON_PRISTINE` because of the previously documented holdout incident. No June result may change this contract.
