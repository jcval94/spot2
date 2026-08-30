# Inventory temporal contract

Inventory remains conceptually separate from Lead Quality.

At score time `t`:

1. a Spot must satisfy `spots.created_at <= t`;
2. candidate structural fields are used under an explicit structural-invariance modeling assumption, not source-proven version history;
3. raw mutable/current-state fields (`days_on_market`, `total_views`, `total_inquiries`, `is_active`) remain FORBIDDEN;
4. Availability uses only the latest snapshot with `snapshot_date <= score_date`;
5. no future/nearest snapshot may be selected;
6. if no backward snapshot exists, Availability is `UNKNOWN`;
7. a stale backward snapshot is still historically **known**; staleness is represented separately by `snapshot_age_days` / `freshness_bucket`;
8. `competing_inquiries_30d` remains blocked until its window direction is proven;
9. Market Context is EDA-only until publication/effective timing exists.

## Intraday observation-time caveat

`availability_snapshot.snapshot_date` is date-only. It does not prove what time of day a snapshot became observable.

The current P4 rule therefore relies on a **business-date assumption** for same-day snapshots. A pre-P8 sensitivity audit compared it with a stricter rule that uses only `snapshot_date < score_date`.

Observed candidate-level sensitivity:

| Cohort | Current coverage | Strict previous-day coverage | Same-day share among covered | No-serviceable current | No-serviceable strict |
|---|---:|---:|---:|---:|---:|
| 2025H1 | 54.03% | 53.11% | 3.44% | 9.65% | 10.15% |
| 2025H2 | 97.21% | 96.54% | 3.15% | 0.00% | 0.00% |
| 2026Q1 | 99.98% | 99.52% | 3.66% | 0.00% | 0.00% |
| 2026-Apr | 100.00% | 99.46% | 4.54% | 0.00% | 0.00% |
| 2026-May CAL | 100.00% | 99.63% | 4.05% | 0.00% | 0.00% |

This does **not** prove same-day observability. It shows the current dataset is only mildly sensitive to a conservative previous-day-only rule, while the underlying semantics remain conditional.

Before a production implementation, require an ingestion/event timestamp or a documented SLA defining when a business-date snapshot becomes usable.
