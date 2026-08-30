# TARGET_CONTRACT — P2 frozen specification

The machine-readable authority is `target_contract.json`.

## Primary target

**ID:** `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`

**Stage:** T1

**Grain:** one target row per lead at the deterministic first inquiry.

**Score time:**

`min(inquiries.inquiry_at)` by `lead_id`, with ascending `inquiry_id` only as a deterministic tie-break.

**Scoring instant:** immediately after that inquiry is persisted and before its broker response is known.

**Positive label:**

`first_inquiry.broker_response == "scheduled_visit"`

**Negative label:**

first inquiry has another non-null broker response.

**Missing response status:**

AMBIGUOUS / excluded, never negative.

**Maturity:**

`score_time + 14 days <= max(raw inquiries.inquiry_at)`.

The current raw activity horizon is `2026-07-13T17:35:37Z`.

The latest raw inquiry timestamp is a conservative maturity proxy because the extraction timestamp is absent.

## Critical semantic statement

The target means:

> the first inquiry **eventually** receives the recorded status scheduled_visit.

It does **not** mean:

- visit scheduled inside 14 days;
- lead converts commercially;
- any later inquiry succeeds;
- scheduled visit occurred at `inquiry_at + broker_response_hours`.

`broker_response_hours` is not used by the primary target.

## Outcome isolation

The following are outcome-only raw fields:

- `broker_response`
- `broker_response_hours`

They may be read by target/audit construction only.

They are forbidden from:

- T0/T1/T2 score-time features;
- feature engineering inputs;
- preprocessing fitted to model inputs;
- inventory score inputs;
- Opportunity Score inputs.

A test fails if either is explicitly passed as a feature field.

## Boundary policy for audited Target B

For the E028-style alternative only:

`score_time < response_event_at <= score_time + 30 days`

where:

`response_event_at = inquiry_at + broker_response_hours`.

- event exactly at score time: negative/not future;
- event exactly at +30d: positive;
- scheduled_visit with missing response hours and inquiry initiated inside the possible window: ambiguous unless another timed positive already proves the label;
- incomplete 30d observation window: right-censored.

These rules exist to audit B. They do not authorize `broker_response_hours` as a model feature.

## Target C policy

T1 C30 means:

> at least one inquiry initiated in `[score_time, score_time + 30d]` eventually receives scheduled_visit.

The inquiry initiation is within 30 days; the actual visit-scheduling time is not claimed.

Maturity is after the initiation window:

`score_time + 30d + 14d <= activity_horizon`.

## Versioning and immutability

This target is frozen before feature engineering/modeling.

It can change only after a **target contract version bump** caused by:

- changed business definition;
- authoritative conversion/outcome data becoming available;
- true response/scheduled-visit event timestamp instrumentation;
- proven source-semantic change;
- discovered label-construction defect.

It cannot change because another target yields higher AUC/AP/Lift.
