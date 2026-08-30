# ABT_CONTRACT — definitive point-in-time analytical tables

## Scope

All ABTs are rebuilt from `data/candidate/parquet/**`. Historical ABTs, fitted objects and generated matrices under `experimentos/**` are evidence only and are never runtime inputs.

The frozen P2 target contract remains authoritative.

## 1. Score spine

Canonical grain:

`lead_id × stage × score_time`

with unique `prediction_key`.

Stages:

- **T0** — `leads.created_at`.
- **T1** — deterministic first inquiry: minimum `inquiry_at`, then minimum `inquiry_id` as tie-break metadata.
- **T2** — every second-or-later inquiry, at its own `inquiry_at`.

Prediction keys are deterministic:

- `L{lead_id}:T0`
- `L{lead_id}:T1:I{inquiry_id}`
- `L{lead_id}:T2:I{inquiry_id}`

The spine is split-agnostic. No train/eval membership is embedded in the ABT.

## 2. Lead Quality Snapshot ABT

Two views are produced.

### audit_all_snapshots

Keeps every score snapshot and one mutually exclusive `target_status`:

- `POSITIVE`
- `NEGATIVE`
- `AMBIGUOUS`
- `CENSORED`
- `INELIGIBLE`

### model_ready

Contains only `POSITIVE`/`NEGATIVE` rows with valid stage membership and mature labels.

It does not contain forbidden raw predictors.

### T0 label

Uses frozen secondary target `T0_30D_INQUIRY_INITIATION_PROGRESS_V1`:

there exists an inquiry initiated in `[lead.created_at, lead.created_at + 30d]` that eventually has recorded status `scheduled_visit`.

Maturity: 30-day initiation window + 14-day label-finality buffer.

### T1 label

Uses frozen primary target `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`.

Maturity: 14 days. The 14 days are label maturity, not an outcome horizon.

### T2 label

Current second-or-later inquiry eventually has `broker_response == scheduled_visit`, with 14-day maturity.

Historical stage membership is conservative:

1. if a prior scheduled_visit has a reconstructable response time `<= score_time`: `INELIGIBLE`;
2. if a prior scheduled_visit exists but its response time is missing and therefore may already have occurred: `AMBIGUOUS`;
3. otherwise the current T2 snapshot is eligible.

No current-inquiry response field is a feature.

## 3. Historical inquiry features

Only inquiry request/event rows with:

`prior.inquiry_at < current.score_time`

may enter history.

Same-timestamp inquiries are not considered historical merely because their `inquiry_id` is smaller.

The first safe history features are deterministic event-only summaries:

- prior inquiry count;
- prior unique Spot count;
- prior asked-visit count/rate;
- prior message-length mean;
- prior known-urgency count/mean.

No broker-response history is promoted as a Lead Quality model feature in this ABT.

## 4. Spot policy

### Explicitly forbidden current/extract state

Never model from raw:

- `days_on_market`
- `total_views`
- `total_inquiries`
- `is_active`

They have no historical state clock.

### Structural Spot fields used only as candidate-policy guardrails

For candidate generation, the following are treated as structural/invariant-by-business-semantics from Spot creation:

- `sector_name`
- `type_name`
- `state`
- `municipality`
- `settlement`
- `corridor`
- `region`
- `lat`
- `lon`
- `area_sqm`
- `modality`

They are not promoted as Lead Quality model features in this phase. The candidate table requires `spots.created_at <= score_time`.

Potentially mutable unversioned Spot fields remain audit-only:

- `broker_id`
- `title`
- `description`
- prices;
- maintenance cost.

### Spot attributes

Per the explicit P2 assumption, `spot_attributes` are immutable over the life of a Spot. They are model-eligible at T1/T2 only when `spots.created_at <= score_time`.

## 5. Inventory Serviceability State

Grain:

`prediction_key × candidate_spot_id`.

Availability is resolved exclusively by backward as-of:

`max(snapshot_date) where snapshot_date <= score_time`.

Never nearest. Never forward.

Definitions:

- `snapshot_found`: a backward snapshot exists;
- `snapshot_age_days`: score_time minus snapshot_date;
- `stale_gt_30d`, `stale_gt_60d`, `stale_gt_90d`;
- `availability_known`: snapshot exists and age <=90d;
- `is_available_asof`: null when availability is not known;
- `days_until_available_asof`: null when availability is not known;
- `competing_inquiries_30d_asof`: retained for audit only because the raw 30-day window direction is still unproven;
- `coverage_status`: `NO_SNAPSHOT`, `STALE_GT_90D`, or `COVERED`.

Absence of snapshot is never interpreted as unavailable.

## 6. Lead × Candidate Spot decision table

Grain:

`prediction_key × candidate_spot_id`.

Candidate policy is deterministic and uses no learned ranking.

Eligibility requires:

- Spot created on/before score time;
- exact requested sector;
- modality compatibility;
- geographic fallback ladder, deduplicated in order:
  1. preferred corridor;
  2. preferred municipality;
  3. preferred state.

The observed current Spot at T1/T2 is always retained as `OBSERVED_CURRENT_OVERRIDE` even if it falls outside the preference policy. This is for audit/comparison, not evidence that it should be recommended.

No N-way candidate join is made into the Lead Quality ABT.

## 7. Market Context

Blocked from all principal model-ready ABTs. `month` is not a defensible publication/effective timestamp.

## 8. Split integrity

These ABTs contain no split/fold assignment. Future splits must remain external and keyed by `prediction_key`/`lead_id`.

The validation API includes an entity-leakage check that fails if a provided split assignment places the same lead in train and evaluation.

## Exit gate

The ABT gate is PASS only if:

- prediction keys are unique;
- every current/request history timestamp is <= the snapshot boundary and all historical inquiries are strictly earlier;
- every Availability snapshot is <= score time;
- no forbidden raw predictor is model-eligible;
- labels have valid mutually exclusive statuses;
- lineage covers every output column;
- stage observability rules pass;
- candidate and inventory joins preserve their intended grain.
