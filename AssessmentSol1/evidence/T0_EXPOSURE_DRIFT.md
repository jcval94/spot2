# T0_EXPOSURE_DRIFT — PROMPT 8

Target: `T0_30D_INQUIRY_INITIATION_PROGRESS_V1`.  
Score time: `leads.created_at`.

**T0 and T1 probabilities estimate different quantities.**

This audit intentionally uses future 30-day inquiry exposure only to understand the T0 target. Exposure variables are never predictors.

| Cohort | N | T0 target rate | Mean inquiries in 30d | Leads with ≥1 inquiry | Mean inquiries if exposed |
|---|---:|---:|---:|---:|---:|
| 2025H1 | 1,660 | 30.78% | 1.86 | 81.02% | 2.30 |
| 2025H2 | 1,684 | 42.16% | 3.01 | 94.48% | 3.18 |
| 2026Q1 | 828 | 52.90% | 3.87 | 97.95% | 3.95 |
| 2026-Apr | 262 | 52.67% | 3.97 | 100.00% | 3.97 |

## Finding

The T0 target moves by roughly **+22 percentage points** from 2025H1 to 2026Q1/Apr while 30-day inquiry exposure roughly doubles.

This is consistent with the inherited concern that the T0 progress target is highly exposure-sensitive. It does not prove causality, but the direction and magnitude are large enough that calendar/process exposure is a major alternative explanation for apparent T0 predictability.

## Model result

Fold-specific Base Rate vs intake-only L2 Logistic:

- macro AP: **0.4803 → 0.4831**;
- macro AUC: **0.5000 → 0.4934**;
- Brier: **0.2631 → 0.2665**;
- Log Loss: **0.7207 → 0.7294**.

The Logistic fails the pre-registered promotion rule on effect size, AUC and Brier.

## Decision

**NEUTRAL_EVIDENCE_BACKED.**

T0 is useful as a cold-start stage and for communicating uncertainty, but the delivered intake information does not support a defensible discriminative ranking model under temporal validation.

No future exposure count is promoted as a predictor.
