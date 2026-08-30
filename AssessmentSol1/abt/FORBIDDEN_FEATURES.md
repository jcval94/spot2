# FORBIDDEN_FEATURES

These fields may not appear in any Lead Quality model feature matrix.

## Critical outcome leakage

- `inquiries.broker_response`
- `inquiries.broker_response_hours`

They are outcome-only. Target B may audit reconstructed response timing, but the frozen primary T1 label does not use response hours.

## Internal score

- `leads.lead_score_internal`

## Current/extract Spot state

- `spots.days_on_market`
- `spots.total_views`
- `spots.total_inquiries`
- `spots.is_active`

## Market Context

All `market_context` aggregates remain blocked for principal modeling because no publication/effective timestamp is available:

- `similar_available_spots`
- `avg_price_sqm_mxn`
- `recent_occupancy_rate`
- `absorption_velocity_days`
- `recent_inquiry_volume`

## Unversioned potentially mutable Spot fields

Not promoted as Lead Quality model features in this phase:

- `broker_id`
- `title`
- `description`
- `price_sqm_mxn_rent`
- `price_sqm_mxn_sale`
- `price_total_mxn_rent`
- `price_total_mxn_sale`
- `maintenance_cost_mxn`

These may be re-opened only with an explicit historical immutability/versioning contract.

## Conditionally blocked

`availability_snapshot.competing_inquiries_30d` is carried as audit context only until the 30-day window direction is proven trailing/as-of.
