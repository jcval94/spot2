# Inventory temporal contract

At score time `t`:

1. a Spot must have `spots.created_at <= t`;
2. descriptive Spot/attribute fields are usable historically only if immutability/version semantics are defensible;
3. raw mutable current-state fields are blocked;
4. Availability uses the latest snapshot with `snapshot_date <= t`;
5. no future/nearest snapshot may be selected;
6. stale Availability (>90 days in prior evidence) is treated as unknown for serviceability, not silently available;
7. `competing_inquiries_30d` remains conditional until its window direction is confirmed;
8. Market Context is not inventory truth until effective/publication timing is proven.

LeadQuality and InventoryServiceability are separate concepts. Availability being known does not automatically make it a LeadQuality predictor.
