# EDA base — Spot2 multi-head opportunity model

> Migrado a la estructura gobernada actual. La evidencia central de este EDA y su extensión profunda es [EV-009](../../Evidencias/EV-009_eda_profundo.md).

## Scope

This folder contains the exploratory data analysis that precedes feature engineering and modeling for the proposed multi-head design.

**This is intentionally EDA only.** It does not fit a model, choose transformations, tune thresholds, or claim causal effects.

The analysis is organized around the information that becomes available as a lead progresses through the funnel:

- **T0 — lead creation**
- **T1 — first inquiry**
- **T2 — second inquiry**, excluding leads that already scheduled a visit before the scoring moment
- **T3 — third inquiry**, used only to assess whether a later head has enough support

The future modeling decision is deliberately left open. The EDA asks whether the data support distinct scoring moments and what information/risks exist at each one.

## Data used

All candidate-visible tables are included:

| Table | Rows | Grain |
|---|---:|---|
| leads | 5,000 | one row per lead |
| inquiries | 22,576 | one lead–spot interaction |
| spots | 3,000 | one commercial listing |
| spot_attributes | 3,000 | one row per spot |
| market_context | 500 | state × municipality × corridor × sector × month |
| availability_snapshot | 30,000 | one spot-availability observation in time |

The hidden `outcomes` table is not used.

## Proxy used only for exploratory comparisons

To compare observed behavior across stages, the EDA uses the same candidate-visible proxy already established in the repository:

> a lead is positive when a `broker_response == scheduled_visit` event is observed within the next 30 days from the scoring anchor.

This is **not hidden conversion ground truth**.

The exact visit-scheduling timestamp is not present; the event is attached to `inquiry_at`. The maximum observed inquiry is 2026-07-13, so 30-day analyses apply right-censoring at approximately 2026-06-13.

## Executive findings

### 1. The relational structure is unusually clean

The core tables have no duplicated primary keys. The EDA found:

- 0 orphan inquiries against leads;
- 0 orphan inquiries against spots;
- 0 orphan spot-attribute rows;
- 0 orphan availability snapshots;
- 0 inquiries before lead creation;
- 0 inquiries before spot creation;
- 0 inquiry modality incompatibilities.

This means the central analytical risk is **not broken entity integrity**. It is temporal correctness: knowing whether a field really existed at the scoring time.

See: `tables/join_quality.csv`.

### 2. Much of the apparent missingness is structural

The largest null rates are modality-dependent price/budget fields:

- lead sale-budget fields: about 50%;
- inquiry sale budget: about 50%;
- spot sale-price fields: about 40%;
- lead rent-budget fields: about 30%;
- spot rent-price fields: about 25%.

Those values should not be interpreted as generic poor data quality because rent-only rows are expected to lack sale values and vice versa.

Non-structural missingness still matters:

- `preferred_corridor`: 7.6% of leads;
- `company_size`: 5.1%;
- `industry`: 3.0%;
- inquiry `urgency_days`: 30.6%;
- `broker_response_hours`: 15.1%;
- several spot attributes have 8–20% missingness.

There are also domain-specific zero patterns. For example, `vertical_height_m == 0` occurs in about 84% of Land listings and essentially not in the other sectors. Treating all numeric zeros identically would be misleading.

See: `figures/14_missingness_top.svg`, `tables/missingness.csv`, and `tables/attribute_sentinel_diagnostic.csv`.

### 3. T0, T1 and T2 are plausible heads; T3 starts to fragment

After applying a 30-day right-censoring rule:

| Stage | Eligible rows | Share of all leads | Exploratory proxy rate |
|---|---:|---:|---:|
| T0 | 4,836 | 96.7% | 41.9% |
| T1 | 4,794 | 95.9% | 44.5% |
| T2 | 3,392 | 67.8% | 40.2% |
| T3 | 2,302 | 46.0% | 34.6% |

T0 and T1 retain almost the entire lead population. T2 still has enough observations to justify investigation. T3 loses more than half of the original population and becomes much more selected.

This is evidence **against creating a new head for every micro-event**. A compact T0/T1/T2 structure is more defensible to test later.

See: `figures/05_proxy_rate_by_head.svg`, `figures/10_stage_coverage.svg`, and `tables/stage_summary.csv`.

### 4. Static lead segments separate the proxy only weakly

At T0, scheduled-visit proxy rates by sector, modality and user type are fairly close. The same is broadly true at T1.

This agrees with the existing repository experiment where the conservative T0 model had little discriminative power. The EDA therefore does not suggest that a simple demographic/static segmentation will solve the problem.

See: `tables/proxy_rates_by_segment.csv`.

### 5. Time to first interaction is one of the clearest raw patterns

At T1, the future 30-day proxy changes strongly with elapsed time from lead creation to first inquiry:

| First inquiry delay | n | Future proxy rate |
|---|---:|---:|
| < 1 day | 840 | 56.8% |
| 1–3 days | 1,240 | 51.1% |
| 3–7 days | 1,370 | 45.9% |
| 7–30 days | 931 | 31.0% |
| ≥ 30 days | 413 | 25.4% |

This is an association, not a causal statement. It does, however, support the central multi-head premise: **behavioral timing reveals information that is absent at lead creation**.

By contrast, declared urgency, inquiry channel and `asked_visit` are much flatter.

See: `figures/07_first_inquiry_lag_vs_proxy.svg` and `tables/t1_breakdowns.csv`.

### 6. There is large temporal drift in the proxy

The T0 30-day proxy rises from roughly 20–22% for early-2025 lead cohorts to above 50% for several 2026 cohorts.

The number of new leads per month is comparatively stable, while inquiry volume grows substantially over time.

That pattern should **not** automatically be called seasonality. It could reflect synthetic-data generation, lifecycle accumulation, operational changes, cohort composition or genuine time drift.

For the future model, this makes random train/test splits indefensible. Temporal validation will be mandatory.

See: `figures/06_proxy_rate_by_lead_cohort_month.svg` and `tables/proxy_by_lead_month.csv`.

### 7. Lead Quality and Inventory Availability look like distinct phenomena

Availability snapshots cover all 3,000 spots historically, with about 10 snapshots per spot on median. Roughly 60% of latest spot states are available.

For censored T1 observations, a valid snapshot on or before scoring time is available for about **85%** of rows.

Within those covered T1 cases, the future scheduled-visit proxy is almost identical:

- as-of spot unavailable: ~46.1%;
- as-of spot available: ~46.0%.

The right interpretation is not that availability is irrelevant. The proxy describes lead progression, while inventory capacity is a different business question. This supports keeping an inventory/matching component distinct from the lead-quality head rather than expecting one target to absorb both.

See: `figures/08_t1_availability_vs_proxy.svg` and `tables/availability_at_t1.csv`.

### 8. Retail currently has the tightest demand/supply balance

Lead mix and latest available inventory are not perfectly aligned:

| Sector | Lead share | Latest available inventory share | Leads / latest available spot |
|---|---:|---:|---:|
| Industrial | 25.0% | 29.3% | 2.36 |
| Office | 29.0% | 29.9% | 2.69 |
| Retail | 30.6% | 23.9% | **3.54** |
| Land | 15.5% | 16.9% | 2.53 |

Retail is the clearest current mismatch. At corridor level, the largest current lead-to-available-spot ratios include Angelópolis–Lomas, Centro León and Metepec–Toluca.

These are **current-state descriptive ratios**, not historically safe model inputs.

See: `figures/04_demand_vs_available_inventory_sector.svg`, `figures/13_corridor_pressure.svg`, `tables/sector_balance.csv`, and `tables/corridor_pressure.csv`.

### 9. Market dynamics differ materially by sector, but context coverage is sparse

Across `market_context`:

- Industrial has high mean occupancy (~87.6%) and slower median absorption (~170 days);
- Office has high occupancy (~82.7%) and median absorption around 119 days;
- Retail absorbs fastest (~92 days median);
- Land has the lowest occupancy (~59.6%) and slowest absorption (~237 days median).

However, an exact lead preference + sector + lead-month join covers only about **23%** of T0 rows.

Also, a monthly market row is not automatically point-in-time safe: its publication/availability timestamp is unknown.

See: `figures/11_market_occupancy_by_sector.svg`, `figures/12_market_absorption_by_sector.svg`, and `tables/market_sector_summary.csv`.

### 10. Faster broker response is not a winning raw signal in this dataset

Observed scheduled-visit shares are roughly flat across response-time buckets:

- ≤2h: 19.1%
- 2–6h: 20.0%
- 6–12h: 19.7%
- 12–24h: 19.9%
- 24–48h: 21.5%
- >48h: 19.2%

More importantly, `broker_response_hours` is not available at T1 scoring time. It belongs to the future relative to that head.

The EDA therefore does not support presenting faster response as a predictive or causal finding from this candidate dataset.

See: `figures/09_response_time_vs_scheduled_visit.svg` and `tables/response_time_diagnostic.csv`.

### 11. Broker repetition exists, but no broker master table exists

The 3,000 spots reference 300 brokers. A broker owns around 10 spots on median, and the inquiry history provides repeated observations per broker.

That makes broker behavior worth studying later, but broker profile variables would have to be constructed strictly **as of each scoring time**. A full-dataset broker average joined back to historical observations would leak future information.

### 12. Raw lead-vs-spot scale differs strongly by sector

The raw distributions show that lead requested area/budget and listing area/price behave very differently by sector. For example, Industrial and Land listings are much larger than the median requested lead area, whereas Office and Retail show the opposite pattern.

This is deliberately left as an EDA observation. No compatibility ratios or transformations are created here.

See: `tables/raw_distribution_summary.csv`.

## Temporal information audit

`tables/stage_information_audit.csv` records what is observable at each candidate head.

Key guardrails:

- `broker_response` and `broker_response_hours` are **not T1 features**;
- current-state spot fields such as `days_on_market`, `total_inquiries`, `total_views` and `is_active` are unsafe for historical scoring unless reconstructed;
- availability requires the latest snapshot with `snapshot_date <= scoring_time`;
- market context is conditional until its true information-availability timestamp is known;
- broker history is valid only when computed from events strictly before scoring.

A particularly useful diagnostic is that `spots.total_inquiries` exactly matches the inquiry table count for only about **7%** of spots. This is consistent with it being a current-state aggregate rather than a historical snapshot.

## Figures

1. `01_lead_mix_sector.svg`
2. `02_lead_mix_modality.svg`
3. `03_lead_mix_user_type.svg`
4. `04_demand_vs_available_inventory_sector.svg`
5. `05_proxy_rate_by_head.svg`
6. `06_proxy_rate_by_lead_cohort_month.svg`
7. `07_first_inquiry_lag_vs_proxy.svg`
8. `08_t1_availability_vs_proxy.svg`
9. `09_response_time_vs_scheduled_visit.svg`
10. `10_stage_coverage.svg`
11. `11_market_occupancy_by_sector.svg`
12. `12_market_absorption_by_sector.svg`
13. `13_corridor_pressure.svg`
14. `14_missingness_top.svg`

## Reproduce

From the repository root:

```bash
python experimentos/eda_profundo/base_eda/run_eda.py --repo-root . --out-dir experimentos/eda_profundo/base_eda
```

The script reads only `data/candidate/csv/` and writes results back into this folder.

For a notebook entry point, open `experimentos/eda_profundo/base_eda/EDA.ipynb`.

## What this EDA supports — and what it does not

The EDA supports testing a compact multi-head design because information availability and population composition change meaningfully between lead creation and later interactions.

It **does not yet** establish:

- the final feature set;
- the final number of heads;
- the best modeling family;
- the optimal target horizon;
- causal effects;
- an Opportunity Score formula;
- a fallback recommender.

Those belong to the next phases: feature engineering and controlled model experiments.
