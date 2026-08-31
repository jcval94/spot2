# FORBIDDEN_FEATURES — P4 hard gate

A feature is blocked if either its value is post-outcome/current-state **or** its historical observability cannot be demonstrated at `score_time`.

## Outcome leakage — label only

- `inquiries.broker_response`
- `inquiries.broker_response_hours`

The current response may be read only inside target construction. Neither current nor historical broker-response fields enter T0/T1/T2 predictive features. For T2 cohort eligibility only, a prior scheduled visit may be used when response timing is reconstructible and proves it was known by score_time; untimed prior success makes stage membership AMBIGUOUS.

## Internal score

- `leads.lead_score_internal`

Its inputs and generation time are unknown.

## Current/extract Spot state

- `spots.days_on_market`
- `spots.total_views`
- `spots.total_inquiries`
- `spots.is_active`

These are not reconstructible historical states from the delivered extract.

## Unversioned mutable Spot fields

Blocked from P4 model-ready objects:

- `spots.broker_id`
- `spots.title`
- `spots.description`
- `spots.price_sqm_mxn_rent`
- `spots.price_sqm_mxn_sale`
- `spots.price_total_mxn_rent`
- `spots.price_total_mxn_sale`
- `spots.maintenance_cost_mxn`

They may be reopened only with a version/effective-time or explicit immutability contract.

## Availability aggregate with unproven window direction

- `availability_snapshot.competing_inquiries_30d`

P4 does **not select this column at all**. It remains blocked until “30d” is proven trailing/as-of rather than retrospective/forward-looking.

## Market Context

All principal modeling use remains blocked because `month` is not a publication/effective timestamp:

- `similar_available_spots`
- `avg_price_sqm_mxn`
- `recent_occupancy_rate`
- `absorption_velocity_days`
- `recent_inquiry_volume`

`market_context` is EDA-only in P4 and no P4 ABT builder reads it.

## Separation guardrail

The following are not globally forbidden, but are forbidden from the **principal LeadQuality model-ready views**:

- selected/current Spot identifier;
- Spot structural fields;
- Spot physical attributes;
- Matching-derived fields;
- Availability-derived fields.

They belong to Matching/Inventory and can be evaluated later as an explicit ablation or combined decision layer, not silently mixed into LeadQuality.

## Temporal-lineage gate

Even if a column is not named above, it cannot become a model feature unless `COLUMN_LINEAGE.csv` provides a defensible non-UNKNOWN `available_at`, role, stage, justification, and evidence.
