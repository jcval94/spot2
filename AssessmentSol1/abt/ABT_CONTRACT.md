# ABT_CONTRACT — P4 point-in-time analytical tables

## Authority and clean-room boundary

This P4 contract supersedes the P3 combined `score_spine` / `lead_quality_abt` design for downstream modeling.

All builders reconstruct directly from `data/candidate/{parquet,csv}/**`. No builder reads:

- `experimentos/**` as runtime input;
- historical ABTs;
- prior model matrices;
- prior fitted preprocessors;
- previously materialized files under `AssessmentSol1/abt/artifacts/**`.

Prior work is evidence only. `AssessmentSol1/target/TARGET_CONTRACT.md` remains the frozen target authority.

## Four separate analytical objects

### 1. `abt_t0` — cold-start / sensitivity

**Grain:** exactly one row per `lead_id`.

**Score time:** `leads.created_at`.

**Information set:** intake-only LeadQuality fields that are assumed captured with the lead record.

No inquiry payload, selected Spot, Spot attributes, Availability, Matching result, response field, or Market Context enters the model-ready view.

The T0 label remains a sensitivity target, not the principal assessment target:

`T0_30D_INQUIRY_INITIATION_PROGRESS_V1`.

A positive means that an inquiry initiated in `[lead.created_at, lead.created_at + 30d]` eventually carries recorded `scheduled_visit`. Maturity requires 30 days plus the 14-day finality buffer.

### 2. `abt_t1` — PRINCIPAL

**Grain:** exactly one row per lead with a first inquiry.

**Identifiers:**

- `lead_id`;
- `first_inquiry_id`;
- `score_id`;
- `score_time`.

**Deterministic first inquiry:** sort by `(lead_id, inquiry_at, inquiry_id)` and select `inquiry_number == 1`.

**Score time:** first inquiry `inquiry_at`.

**Scoring instant:** after the current request payload is persisted and before the current `broker_response` is known.

**Primary target:** `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`.

Outcome fields are read only inside label construction and are never selected into either ABT view.

### 3. `abt_t2` — CHALLENGER

**Grain:** exactly one row per `inquiry_id` from the second interaction onward.

**Stage membership:** deterministic `inquiry_number >= 2` under `(inquiry_at, inquiry_id)` ordering.

Current inquiry request fields are allowed.

Historical inquiry features require:

`prior.inquiry_at < current.score_time`.

Same-timestamp inquiries are **not** historical, even if their `inquiry_id` sorts earlier.

Broker-response history is never used as a predictive feature. For the frozen T2 cohort gate only, a prior `scheduled_visit` may affect stage membership when its response time is reconstructible and proves the event occurred on/before the current score time. A prior `scheduled_visit` with missing response timing makes T2 stage membership `AMBIGUOUS`; it is never silently treated as known or absent.

The current inquiry response may be read only to construct the current T2 challenger label.

### 4. `inventory_candidates`

**Grain:** unique `score_id × candidate_spot_id`.

This object remains physically and semantically separate from LeadQuality.

It is built from T0/T1/T2 score definitions plus raw lead, Spot, Spot-attribute, and Availability sources. The builder invokes the stage builders directly; it does not read their materialized ABT files.

## Logical blocks

The architecture has four explicit blocks.

### A. LeadQuality

Primary model inputs:

- lead intake fields;
- stated need/preferences;
- current inquiry intent/refinement at T1/T2;
- strict-prior inquiry request history at T2 only.

### B. Matching

Kept outside the primary LeadQuality feature set. Matching includes:

- candidate-policy tier/rank;
- sector/modality compatibility;
- candidate geography;
- candidate structural area;
- request/lead area-reference deltas;
- current observed Spot indicator for audit/comparison.

### C. Inventory

Kept outside the primary LeadQuality feature set. Inventory includes:

- Spot physical attributes under the explicit AssessmentSol1 immutability assumption;
- backward-as-of Availability state;
- snapshot freshness/coverage semantics.

### D. Audit / policy

Contains identifiers, temporal anchors, maturity timestamps, source flags, lineage guardrails, and observability checks. Audit/policy fields are not automatically model features.

## Spot policy

A candidate Spot can exist only if:

`spots.created_at <= score_time`.

Structural fields used for candidate policy/matching remain under an explicit **AssessmentSol1 structural-invariance assumption** that they describe the Spot from creation. This is not source-proven version history:

- sector/type;
- state/municipality/settlement/corridor/region;
- lat/lon;
- area;
- modality.

The following current/extract state fields are forbidden:

- `days_on_market`;
- `total_views`;
- `total_inquiries`;
- `is_active`.

Potentially mutable, unversioned listing fields remain blocked from P4 modeling:

- broker;
- title/description;
- prices;
- maintenance cost.

`spot_attributes` remain authorized only under the frozen immutability assumption from the target contract, and only for Spots that already existed at score time. They belong to Inventory/Matching, not the principal LeadQuality model.

## Candidate policy

The deterministic policy universe uses:

1. exact requested sector;
2. compatible modality;
3. geographic fallback, deduplicated in this order:
   - preferred corridor;
   - preferred municipality;
   - preferred state.

At T1/T2, the observed current Spot may be retained as `OBSERVED_CURRENT_OVERRIDE` for audit/comparison if and only if it existed at `score_time`. It does not become a LeadQuality feature.

## Availability contract

Availability is resolved **only** by backward as-of:

`max(snapshot_date) where snapshot_date <= score_time`.

Never nearest. Never forward.

Required fields:

- `availability_known`;
- `is_available_asof`;
- `days_until_available_asof`;
- `snapshot_age_days`;
- `freshness_bucket`.

Additional explicit state:

- `availability_state ∈ {AVAILABLE, UNAVAILABLE, UNKNOWN}`.

Definitions:

- `availability_known = true` iff a backward snapshot exists;
- a stale snapshot is still historically known; staleness is represented separately in `snapshot_age_days` / `freshness_bucket`;
- if no backward snapshot exists, `availability_state = UNKNOWN`, `is_available_asof = null`, and `days_until_available_asof = null`.

Missing snapshot is never coerced to unavailable.

`competing_inquiries_30d` is not selected into any P4 ABT until its 30-day window semantics are proven point-in-time.

## Market Context

`market_context` remains EDA-only because `month` is not a defensible publication/effective timestamp. No P4 builder reads it.

## Views

Every analytical object has explicit views:

- `*_audit_all_rows`: preserves censored, ambiguous, policy/audit context and UNKNOWN inventory coverage;
- `*_model_ready`: contains only temporally authorized columns for the intended modeling block.

For T0/T1/T2, model-ready retains only mature binary labels (`POSITIVE` / `NEGATIVE`). CENSORED and AMBIGUOUS rows remain in audit.

For `inventory_candidates`, model-ready does not drop UNKNOWN Availability rows; unknownness is an explicit state, not an exclusion criterion.

## Column lineage gate

`COLUMN_LINEAGE.csv` is authoritative for every output column and must contain:

- `column`;
- `source`;
- `meaning`;
- `available_at`;
- `transform`;
- `role`;
- `stage`;
- `future_risk`;
- `justification`;
- `evidence`.

Allowed roles:

- `identifier`;
- `target`;
- `model_feature`;
- `matching_feature`;
- `inventory_feature`;
- `policy_guardrail`;
- `audit_only`;
- `forbidden`.

A column cannot be a model feature if its `available_at` is unknown. T0/T1/T2 LeadQuality model-ready views cannot contain Matching/Inventory roles.

## Tests and exit gate

P4 is PASS only if all of the following hold:

1. unique grain for T0, T1, T2, and inventory candidates;
2. exact row-count reconciliation with raw leads/inquiries; no unintended row explosion;
3. T2 history is strictly earlier than score time;
4. every candidate Spot existed by score time;
5. every selected Availability snapshot is backward-as-of;
6. missing Availability remains UNKNOWN;
7. forbidden/current-state/outcome fields are absent from model-ready views;
8. T0/T1/T2 stage observability rules pass;
9. Market Context is unused;
10. `competing_inquiries_30d` is unused;
11. no split/fold assignment is embedded in ABTs;
12. if an external split assignment exists, a lead cannot cross partitions/folds;
13. every emitted column has complete lineage;
14. every promoted feature has demonstrated temporal availability.
