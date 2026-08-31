# Temporal semantics — P1

## Time vocabulary

- **Event time:** when the underlying business event occurred.
- **Observation time:** when Spot2/data systems could first have observed the value.
- **Effective time:** when the value should be considered valid for a historical decision.
- **Extraction/current state:** a value present in the delivered extract without evidence of when that state became true.

These clocks are not interchangeable. A field being physically present in the raw file does not prove it was known at a prior score time.

## Source decisions

### leads

`created_at` is the T0 event anchor. Intake fields are treated as the original T0 snapshot. Historical counters are conditional on proving they summarize only pre-`created_at` activity. `lead_score_internal` is FORBIDDEN regardless of physical availability.

### inquiries

The current inquiry's request fields are observed at `inquiry_at` and therefore form the T1/T2 current-request information set. Broker response fields are post-inquiry. Because no reliable response-event timestamp exists, they are not point-in-time reconstructable in P1 and remain audit-only.

### spots

`created_at` proves entity existence, not the effective time of every delivered listing field. Descriptive/pricing/copy fields have no version history and are conditional until immutability or effective-time provenance is proven.

`days_on_market`, `total_inquiries`, `total_views`, and `is_active` are extraction/current-state fields and are FORBIDDEN in historical backtests.

### spot_attributes

No attribute-level timestamp exists in raw data. For the definitive assessment, AssessmentSol1 adopts an **explicit modeling assumption that all `spot_attributes` values are immutable over the life of the Spot**. The original assessment does not supply attribute version history or explicitly guarantee this immutability.

Therefore the current delivered values are authorized at T1/T2 when the selected Spot itself already exists:

`spots.created_at <= score_time`.

This is an explicit modeling assumption adopted inside AssessmentSol1 after project review; it is **not stated in the original candidate package** and is not temporal provenance inferred from raw data. We do not invent an attribute event/observation timestamp; the effective-time contract is simply “invariant from Spot creation.”

### availability_snapshot

`snapshot_date` is the only effective-date candidate. Historical joins must be backward-as-of and may never select a future snapshot. The ingestion/observation timestamp is still absent, so use remains conditional on the business-date assumption.

`competing_inquiries_30d` is separately blocked until “30d” is proven to be a trailing/as-of window rather than a retrospective/forward aggregate.

### market_context

`month` is a reporting-period label, not a publication clock. No publication/effective timestamp exists. Entire source is **EDA_ONLY** for P1/backtest.

## Stage implications

- **T0:** lead intake only. No selected inquiry/spot context. Inventory-wide state is conditional and must be constructed only from historically existing spots/snapshots.
- **T1:** current first inquiry is known at `inquiry_at`; current broker response is not. `spot_attributes` are authorized under the explicit immutability assumption when `spots.created_at <= score_time`; other unversioned Spot fields retain their own temporal policy. Availability is backward-as-of only.
- **T2:** same as T1, including immutable `spot_attributes` for historically existing Spots, plus prior events that were actually observable before the current `inquiry_at`. Raw broker response fields do not provide a reliable clock, so no response-history feature is authorized in P1.

The authoritative column-by-column ontology is `temporal_column_registry.csv`.
