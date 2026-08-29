# Modelo 3 — shared backbone + stage heads

## Decision

**SUPPORTED** — multi-head improves macro AP vs pooled by +0.012, with ROC-AUC delta +0.006.

- T0_cold: lead creation.
- T1_first_inquiry: first observable intent event.
- T2_engaged: second and later inquiries before conversion.

Target: future \`scheduled_visit\` response event within 30 days from each scoring timestamp.

## Test metrics

| Model | Stage | ROC AUC | Avg Precision | Brier | Log loss | Lift@10% |
|---|---|---:|---:|---:|---:|---:|
| multihead_calibrated | T0_cold | 0.514 | 0.503 | 0.251 | 0.696 | 0.97x |
| multihead_calibrated | T1_first_inquiry | 0.490 | 0.508 | 0.251 | 0.696 | 0.99x |
| multihead_calibrated | T2_engaged | 0.595 | 0.515 | 0.244 | 0.682 | 1.39x |
| multihead_calibrated | MACRO | 0.533 | 0.508 | 0.249 | 0.691 | 1.12x |
| pooled_calibrated | T0_cold | 0.534 | 0.511 | 0.251 | 0.695 | 1.05x |
| pooled_calibrated | T1_first_inquiry | 0.474 | 0.503 | 0.251 | 0.695 | 1.08x |
| pooled_calibrated | T2_engaged | 0.572 | 0.476 | 0.246 | 0.686 | 1.10x |
| pooled_calibrated | MACRO | 0.527 | 0.497 | 0.249 | 0.692 | 1.08x |
| separate_logistic | T0_cold | 0.483 | 0.498 | 0.295 | 0.799 | 0.97x |
| separate_logistic | T1_first_inquiry | 0.491 | 0.510 | 0.279 | 0.760 | 1.05x |
| separate_logistic | T2_engaged | 0.535 | 0.488 | 0.269 | 0.747 | 1.28x |
| separate_logistic | MACRO | 0.503 | 0.499 | 0.281 | 0.768 | 1.10x |

## Population

- Eligible snapshots: 19,715.
- Unique leads: 4,841.
- All snapshots for a lead stay in the same temporal cohort.

| Split | Stage | Rows | Positive rate |
|---|---|---:|---:|
| test | T0_cold | 727 | 49.4% |
| test | T1_first_inquiry | 699 | 50.4% |
| test | T2_engaged | 1,297 | 43.2% |
| train | T0_cold | 3,388 | 32.4% |
| train | T1_first_inquiry | 3,379 | 35.5% |
| train | T2_engaged | 7,248 | 26.6% |
| val | T0_cold | 726 | 46.8% |
| val | T1_first_inquiry | 723 | 47.9% |
| val | T2_engaged | 1,528 | 34.2% |

## Leakage controls

- \`lead_score_internal\` is blocked.
- Current/future broker response outcome and response time are not model inputs.
- Historical response features require response_event_at <= scoring time.
- Mutable spot snapshot fields (\`total_views\`, \`total_inquiries\`, \`days_on_market\`, \`is_active\`) are excluded.
- Availability uses only the latest snapshot at or before scoring time.
- Right-censored snapshots and post-conversion snapshots are excluded.

## Interpretation

This directly tests the architectural question: whether stage-specific heads add value beyond a single model that simply receives stage as a feature. A win for multi-head supports stage-specific decision/calibration behavior while retaining shared statistical strength.

The dataset is synthetic and \`scheduled_visit\` is a proxy, so this supports a predictive architecture decision rather than a causal claim.
