# Open questions

These must be resolved before their affected data can be promoted.

1. **Market Context effective time.** Does `month` mean values known at month start, month end, or computed retrospectively? Is there a publication timestamp?
2. **Spot field mutability.** Are descriptive fields/prices/location immutable after `spots.created_at`? If editable, where is version history?
3. **Spot Attributes effective time.** `spot_attributes` has no timestamp. Were values known at spot creation, and can they change?
4. **Availability ingestion time.** Is `snapshot_date` the actual effective/known date or only a business date?
5. **`competing_inquiries_30d` window direction.** Is it trailing 30 days as-of snapshot, forward-looking, or generated retrospectively?
6. **Historical counters in leads.** Are `prior_searches`, `prior_inquiries`, `has_converted_before` frozen strictly before `leads.created_at`?
7. **Broker response event identity/timestamp.** Candidate data reconstructs timing from hours and has missing/inconsistent values. Is there a backend event timestamp/id in production?
8. **Raw inquiry text.** It is absent; `message_length` is not a semantic substitute.
9. **Canonical preferred-geo coordinates.** Needed before defensible distance-to-preference features.
10. **True commercial outcome.** There is no candidate-visible close/lease/revenue label with effective timing.
11. **Independent future evidence.** What new post-freeze cohort or hidden evaluator will provide genuinely unseen confirmation?
