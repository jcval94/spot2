# POST_SELECTION_DRIFT_AUDIT — before Prompt 8

This audit is intentionally separated from the original DEVELOPMENT-only drift analysis.

- DEVELOPMENT findings retain selection authority.
- CALIBRATION may be inspected now because it has already served its frozen calibration role.
- June is inspected only as **DIAGNOSTIC_ONLY_NON_PRISTINE** because the procedural holdout was previously consumed by the documented incident.
- Nothing in this document changes target, splits, features, champion, or calibration.

Evidence: `outputs/eda/pre_p8_temporal_audit.csv`.

## LeadQuality population

There is **no evidence of severe T1 population drift** into May/June.

| Metric | 2025H1 reference | May CAL | June diagnostic |
|---|---:|---:|---:|
| T1 proxy prevalence | 19.94% | 20.83% | 19.41%* |
| asked_visit rate | 25.30% | 27.88% | 24.48% |
| target area mean | 687.9 | 667.5 | 664.7 |
| requested area mean | 1354.7 | 1324.4 | 1119.5 |
| urgency mean | 118.2 | 122.2 | 123.1 |
| urgency missing | 29.81% | 27.24% | 28.97% |
| message length mean | 222.1 | 229.6 | 235.1 |

*June target rate uses only 273 mature rows; 17 are censored under the frozen 14-day maturity rule.

Categorical Jensen–Shannon divergence versus 2025H1 remains small in May:
- sector: ~0.00083;
- modality: ~0.00071;
- user_type: ~0.00399;
- source: ~0.00504;
- channel: ~0.00061.

June diagnostic values are also small; the largest listed JS is modality at ~0.00251.

**Conclusion:** no LeadQuality target/split repair is justified.

## Clock/process drift

First-inquiry lag remains the clearest non-inventory temporal clock:

- 2025H1 mean: **10.75 days**;
- Apr-2026: **30.43 days**;
- May CAL: **32.48 days**;
- June diagnostic: **21.09 days**.

This supports the existing decision to keep lag/process clocks out of the T1 core. A variable being observable does not make it a durable intent signal.

## Inventory / exposure drift

Inventory remains strongly nonstationary:

- candidate depth mean: **21.97 → 55.98** from 2025H1 to May;
- candidate depth mean June diagnostic: **56.07**;
- Availability coverage: **54.03% → 100%** by May/June.

This is a catalog/coverage/exposure regime change, not evidence that LeadQuality population changed equivalently.

Do not combine these clocks silently into LeadQuality.

## Availability intraday sensitivity

Because `snapshot_date` is date-only, same-day snapshots are semantically conditional.

Same-day snapshots represent about:
- 3.44% of covered candidates in 2025H1;
- 3.15% in 2025H2;
- 3.66% in 2026Q1;
- 4.54% in Apr;
- 4.05% in May.

Using the stricter `snapshot_date < score_date` rule changes May coverage only from **100.00% to 99.63%** and does not create no-serviceable May cases.

Therefore current conclusions are mildly sensitive, but the business-date assumption remains a production caveat.

## Prompt-8 consequence

- T0 must explicitly reproduce exposure drift without using future exposure as a predictor.
- T2 must keep strict-prior trajectory and fold-boundary truncation.
- No calendar/extraction clock is promoted merely because it explains cohort drift.
- June cannot be used to choose a P8 model.
