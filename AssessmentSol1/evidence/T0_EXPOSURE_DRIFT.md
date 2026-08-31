# T0_EXPOSURE_DRIFT — Cold Start

**Decision:** `NEUTRAL_EVIDENCE_BACKED`.

T0 score time is `lead.created_at`. Only intake information is allowed as predictor input.

> **T0 and T1 probabilities estimate different quantities.**

T0 estimates whether at least one inquiry **initiated within 30 days of lead creation** eventually has `scheduled_visit`. T1 estimates whether the deterministic first inquiry itself eventually has `scheduled_visit`. Their probabilities must not be compared as interchangeable scores.

## Temporal CV result

| Model | Macro ROC AUC | Macro AP | Brier | Log Loss |
|---|---:|---:|---:|---:|
| T0 Base Rate | 0.5000 | 0.4803 | **0.2631** | **0.7207** |
| T0 Intake Logistic | 0.4947 | 0.4856 | 0.2642 | 0.7234 |

The intake model changes AP by only **+0.0053**, remains below random-ranking AUC, and slightly worsens both proper probability scores. It fails the pre-registered T0 promotion rule.

## Exposure drift

Future exposure is highly nonstationary:

| Cohort | Target rate | Mean inquiries in 30d | Leads with ≥1 inquiry | Mean inquiries if exposed |
|---|---:|---:|---:|---:|
| 2025H1 | 30.78% | 1.86 | 81.02% | 2.30 |
| 2025H2 | 42.16% | 3.01 | 94.48% | 3.18 |
| 2026Q1 | 52.90% | 3.87 | 97.95% | 3.95 |
| 2026 Apr | 52.67% | 3.97 | 100.00% | 3.97 |

The target rate rises together with opportunity to generate inquiries. This is a **target/exposure mechanism**, not a legitimate T0 predictor.

Future inquiry count, whether the lead will be exposed, requested Spots, Availability and downstream outcomes remain forbidden at T0.

## Operational conclusion

T0 does **not** justify a discriminative cold-start model with the supplied intake variables.

A population prior may be reported for planning, but T0 should not be used to rank newly created leads. Additional pre-inquiry signals or an exposure-controlled target would be required before revisiting a predictive cold-start product.

Evidence:
- `models/t0/metrics/fold_metrics.csv`
- `models/t0/metrics/macro_metrics.csv`
- `models/t0/metrics/exposure_drift.csv`
