# Raw data audit — P1

**Status: PASS WITH SOURCE-SPECIFIC BLOCKS.**  
Canonical execution format: **Parquet** under `data/candidate/parquet/**`. CSV is used only as an independent parity reference and is never concatenated with Parquet.

## 1. CSV ↔ Parquet canonical-source gate

All six table pairs match on row count, ordered schema, per-column null counts and numeric/boolean extrema. Parquet files were written by Polars with ZSTD compression. Long BYTE_ARRAY min/max footer statistics are not treated as exact equality evidence because Parquet may store truncated bounds; `raw_audit.py` performs exact logical frame parity when run in the repository.

| Table | Rows | Cols | Parity |
|---|---:|---:|---|
| leads | 5,000 | 20 | PASS |
| inquiries | 22,576 | 13 | PASS |
| spots | 3,000 | 25 | PASS |
| spot_attributes | 3,000 | 12 | PASS |
| availability_snapshot | 30,000 | 6 | PASS |
| market_context | 500 | 10 | PASS |

Physical SHA-256 and Git blob hashes are persisted in `data_audit.json`. Physical hashes are expected to differ across formats. All 12 raw files (six CSV + six Parquet) were introduced together in commit `8f850cf152bbbefb2f0b8af897e4c94916c88bb6` (`Add files via upload`), alongside the assessment and feature dictionary.

## 2. Grain, keys and relational integrity

| Source | Grain | PK | Duplicate PK rows | Exact duplicates |
|---|---|---|---:|---:|
| leads | one row per lead | `lead_id` | 0 | 0 |
| inquiries | one row per lead↔spot inquiry event | `inquiry_id` | 0 | 0 |
| spots | one row per spot listing extract/current record | `spot_id` | 0 | 0 |
| spot_attributes | one unversioned attribute row per spot | `spot_id` | 0 | 0 |
| availability_snapshot | one availability snapshot per spot-date (snapshot_id PK) | `snapshot_id` | 0 | 0 |
| market_context | one market aggregate per state×municipality×corridor×sector×month | `state + municipality + corridor + sector + month` | 0 | 0 |

FK audit: **0 orphans** for Inquiry→Lead, Inquiry→Spot, SpotAttributes→Spot and Availability→Spot.

Observed cardinalities:
- inquiries/lead: mean 4.515, median 5, max 8;
- inquiries/spot: mean 7.530, median 7, max 22; 2 spots have no inquiry;
- availability snapshots/spot: mean 10, median 10, max 24;
- spots/broker: mean 10, median 10, max 18.

Temporal relational consistency also passes: 0 inquiries before lead creation, 0 inquiries before spot creation, 0 availability snapshots before spot creation, 0 duplicate `spot_id × snapshot_date`, and 0 availability state contradictions.

## 3. Temporal ranges

- leads.created_at: **2025-01-01 → 2026-06-30**
- inquiries.inquiry_at: **2025-01-01 10:21:59 → 2026-07-13 17:35:37**
- spots.created_at: **2024-01-01 → 2026-06-30**
- availability_snapshot.snapshot_date: **2024-12-28 → 2026-06-30**
- market_context.month: **2024-01-01 → 2026-06-01**

All date fields parse and no audited event date is after the audit date or before year 2000.

## 4. Missingness and outliers

Missingness is not automatically bad data. Several large rates are structural by modality:

- Lead sale budgets: ~50–52% null overall; rent budgets: ~30–32% null overall.
- Spot sale prices: 39.73% null; rent/maintenance: 25.37% null, exactly aligned with modality for spot prices.
- Inquiry sale budget: 49.90% null; rent budget: 29.55% null.
- Inquiry urgency: 30.64% null — interpret as “not stated”, not median urgency.
- `broker_response_hours`: 15.05% null and semantically inconsistent; see below.

IQR flags identify heavy-tailed business distributions, not rows to delete. Examples:
- spots.area_sqm: 11.83% outside 1.5×IQR, max 136,403 m²;
- spots.maintenance_cost_mxn: 12.59%, max MXN 1,665,495.14;
- inquiries.requested_area_sqm: 11.57%, max 40,920.9 m²;
- leads.prior_searches: 13.06%, max 60;
- leads.prior_inquiries: 12.90%, max 199.

No automatic trimming/removal is authorized by this audit.

## 5. Inquiries — broker response semantics

`broker_response` and `broker_response_hours` are **AUDIT_ONLY in P1**. `broker_response_hours` is not used to build a feature or target.

Observed:
- accepted: 10,202 rows; **1,522 missing hours**;
- rejected: 3,395; **506 missing hours**;
- scheduled_visit: 4,496; **673 missing hours (14.97%)**;
- no_response: 4,483; **3,786 have response hours populated**.

Thus **2,701 realized statuses** (accepted/rejected/scheduled_visit) have no timing, while 3,786 no-response rows paradoxically have timing. There are no negative response-hour values.

Without a true response-event timestamp, these fields do not provide a reliable point-in-time event clock.

## 6. Spots — extract/current-state fields

The following raw columns are **FORBIDDEN for historical backtest**:

- `days_on_market`
- `total_inquiries`
- `total_views`
- `is_active`

There is no observation/effective timestamp for their current state. More strongly, `spots.total_inquiries` equals the count reconstructible from `inquiries` for only **212/3,000 spots (7.07%)**. It therefore cannot be assumed to be an event count with the same semantics.

A new as-of feature may later be reconstructed from raw events, but that does not rehabilitate the raw current-state column.

## 7. Availability

The only safe historical join is **backward as-of**: latest `snapshot_date <= score_time`.

Across all 22,576 inquiries:
- backward coverage: **20,856 / 22,576 = 92.38%**;
- lag median: **6.61 days**;
- p90: **58.66 days**;
- p95: **83.35 days**;
- max: **261.52 days**;
- 4.20% of covered inquiries have lag >90 days.

Coverage is highly non-stationary: 6.46% in Jan-2025, 84.69% in Jun-2025, 96.57% in Sep-2025 and 100% from Jan-2026 onward.

A direct `spot_id` join produces **226,151 rows**, a **10.017× explosion**. A nearest-time join would choose a **future snapshot for 7,758 inquiries (34.36%)**. Both are prohibited.

`competing_inquiries_30d` remains **blocked** until the direction/effective semantics of its 30-day window are proven.

## 8. Market context

`market_context` has a month period label but **no publication timestamp and no effective/observation timestamp**. Same-month matching covers only **5,383/22,576 inquiries = 23.84%**, but coverage does not solve leakage.

Decision: **EDA_ONLY**. No market aggregate is authorized for historical model/backtest use until publication/effective-time semantics exist. A condition like `month <= score_month` is insufficient.

## 9. Spot attributes

`spot_attributes` has no timestamp at all. The 1:1 FK is clean, but historical availability of the attribute values cannot be proven.

Decision: **BLOCKED_PENDING_TEMPORAL_PROVENANCE** for predictive backtests. It may be reopened only if the source owner confirms that attributes are immutable and available from spot creation, or provides version/effective timestamps.

## Gate

**PASS.** Every source/column has an explicit temporal status in `temporal_column_registry.csv`. Anything without a defensible event/observation/effective-time contract is blocked or EDA-only. No target is constructed in P1.
