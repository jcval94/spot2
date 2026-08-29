---
name: spot2-leakage
description: Use when reviewing Spot2 features, targets, joins, snapshots, aggregates, broker profiles, market context, or external enrichment for point-in-time correctness and leakage before an experiment is accepted.
---

# Spot2 Leakage Guardian

## Purpose

Determine whether information could truly have been known when a prediction was generated.

Central question: **Was this information available at the exact scoring time?**

A column existing in the dataset is not evidence that it was historically available.

## Required inputs

Establish explicitly:

- scoring timestamp or scoring stage;
- target definition and horizon;
- feature list;
- source table for each new feature;
- joins and snapshot-selection rules;
- historical aggregations;
- external enrichment, when used.

If scoring time cannot be identified, the review is incomplete.

## Status values

Classify every reviewed feature, join, aggregate, or snapshot rule as:

- `ALLOW`: clearly available at scoring time.
- `BLOCK`: uses information not available yet.
- `CONDITIONAL`: safe only if an explicit condition is satisfied.
- `UNKNOWN`: insufficient evidence.

`UNKNOWN` never becomes `ALLOW` silently.

## Evidence contract

For every material item record:

- `element`
- `source`
- `scoring_time`
- `information_available_at`
- `status`
- `evidence`

For `CONDITIONAL`, also record whether the condition was satisfied.

Core rule:

`information_available_at <= scoring_time`

## Known scoring stages

### T0 — lead creation
`scoring_time = leads.created_at`

Only information available when the lead was created is eligible.

### T1 — first inquiry
`scoring_time = first inquiry_at`

T0-safe information plus information contained in the first inquiry may be eligible. The later broker response is not available at T1.

### T2 and later
No universal definition exists. The experiment must declare the event or timestamp that defines scoring.

## Future outcome vs future feature

Future events may be used to determine the label.

For example, `scheduled_visit within 30 days` may look forward to determine `y`.

Those future events cannot therefore be used in `X`.

Rule: **The future may define what happened. It may not help predict itself.**

## Historical aggregates

Any historical aggregate must use only events satisfying:

`event_time <= scoring_time`

This includes prior lead activity, broker history, spot activity, conversion rates, inquiry volumes, and historical performance.

Never calculate a full-dataset aggregate first and join it retrospectively unless a point-in-time construction proves that future observations were excluded.

## Current-state fields

Treat fields such as these as `BLOCK` for historical scoring unless their historical value can be reconstructed:

- `days_on_market`
- `total_inquiries`
- `total_views`
- `is_active`

## Broker profiles

Broker-derived features are `CONDITIONAL`.

They are eligible only when constructed from observations available before each row's scoring time.

A profile computed using the entire dataset and then joined to historical rows is not point-in-time safe.

## Availability snapshots

For scoring at time `t`, use only availability information observable at or before `t`.

Do not use the nearest future snapshot to describe historical inventory. Document the snapshot-selection rule.

## Market context

A row keyed by month is not automatically safe for every day in that month.

Monthly aggregates are `CONDITIONAL` until their construction is known.

Safe examples include a snapshot already published before scoring, an explicitly as-of aggregate, or the latest fully closed period available at scoring time.

## External data

Apply the same rule to external enrichment. When material, record effective date, publication date, and source version or snapshot.

## Joins

Review joins as first-class leakage risks. Check temporal eligibility, cardinality, future rows, snapshot selection, precomputed aggregates, and row multiplication.

## Workflow

1. Fix the scoring time.
2. Separate target construction from feature construction.
3. Inventory newly introduced features and joins.
4. Determine information availability for each.
5. Review aggregates and snapshots.
6. Review external data.
7. Classify every material item.
8. Fail the check if any used item remains unsafe.

## Required output

Produce a table equivalent to:

| Element | Status | Available from | Evidence / reason |
|---|---|---|---|
| ... | ALLOW/BLOCK/CONDITIONAL/UNKNOWN | ... | ... |

Then state either:

`LEAKAGE_CHECK = PASS`

or

`LEAKAGE_CHECK = FAIL`

PASS requires no used `BLOCK` or `UNKNOWN` items, and every used `CONDITIONAL` item must have its condition explicitly satisfied.

## Final checks

Before returning PASS, verify that all added features were reviewed, target events were not copied into features, broker aggregates are historical, availability uses non-future snapshots, market context has a defensible as-of interpretation, and joins cannot access future observations.

When uncertain, prefer losing a feature over losing the validity of the experiment.
