# Inventory Serviceability Contract

**Version:** `INV_SERVICEABILITY_V1_FROZEN_2026-08-30`  
**Question:** for a lead evaluated at `score_time`, can the inventory that was knowable at that moment reasonably serve the expressed need?

Inventory Serviceability is **not** Lead Quality and does not estimate whether the lead will convert. `AssessmentSol1/models/lead_quality/**` is frozen and is not an input to this policy.

## Point-in-time contract

A Spot may enter the candidate universe only when `spots.created_at <= score_time`. A later Spot is `FORBIDDEN_FUTURE_SPOT`.

Spot structural fields are used only under the already-declared AssessmentSol1 structural-invariance assumption. Mutable extraction-state fields (`days_on_market`, `total_inquiries`, `total_views`, `is_active`) are forbidden.

Availability is selected by strict backward as-of: the last `snapshot_date <= score_date`, with deterministic `snapshot_id` tie-break on duplicate Spot/date observations. A missing prior snapshot is `UNKNOWN`; it is never rewritten to `UNAVAILABLE`. A stale prior observation remains historically known and lowers `inventory_confidence` instead of changing `availability_state`.

`competing_inquiries_30d` is forbidden because its retrospective window semantics/effective timestamp are not proven. `market_context` is not used.

## Hard constraint and tiers

Modality compatibility is a hard gate. Geography and sector form explicit relaxation tiers:

- `TIER_0`: same sector + preferred corridor.
- `TIER_1`: same sector + preferred municipality.
- `TIER_2`: same sector + preferred state.
- `TIER_3_EXPERIMENTAL`: modality compatible, different sector, but within preferred corridor/municipality/state. It is never presented as equivalent fallback.

## Components

`area_fit_relative = max(0, 1 - |candidate_area-requested_area|/requested_area)` is canonical. The log-ratio alternative is retained only as DEVELOPMENT evidence.

Availability states are `AVAILABLE_NOW`, `AVAILABLE_WITHIN_URGENCY`, `UNAVAILABLE`, and `UNKNOWN`. Snapshot age is separate from state.

Budget is intentionally incomplete in the canonical historical assessment. Current `spots.price_*` values have no historical effective/version timestamp, so using them at prior `score_time` would violate PIT. Therefore canonical `budget_fit` and `budget_gap` are null with `UNKNOWN_PRICE_NOT_PIT` when a budget was expressed. A unit-safe budget function is implemented for a future versioned price source: rent compares MXN/month to `price_total_mxn_rent`; sale compares total MXN to `price_total_mxn_sale`. Missing budgets are never invented.

Physical attributes are not promoted to a preference score unless the lead actually expressed the corresponding need. The current schema therefore reports physical fit as not applicable rather than fabricating preferences.

## Serviceability output

For every scored lead the service returns, at minimum:

- `exact_spot_serviceable`
- `viable_spot_count`
- `available_viable_count`
- `unknown_availability_count`
- `serviceability_score` in `[0,1]`
- `inventory_confidence`
- `fallback_available`
- `tier3_experimental_available`
- `serviceability_completeness`

`serviceability_score` summarizes match quality under a tier cap; `inventory_confidence` remains separate. A high match from an old snapshot must not communicate the same certainty as a recent observation.

Because price is not PIT reconstructable, this frozen version is explicitly `PARTIAL_PIT_NO_VERSIONED_PRICE`. It does not conceal this limitation inside the scalar score.

## Selection boundary

Policy choices were made only on T1 DEVELOPMENT (`score_time < 2026-05-01 UTC`, 4,368 leads). CALIBRATION, the consumed June procedural holdout, target labels, Lead Quality predictions and hidden outcomes were not used to select Inventory rules.

The frozen authority is `frozen_inventory_config.json`. Every recommendation must be reproducible from raw sources plus that config using information knowable at `score_time`.
