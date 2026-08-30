# E019 — Operational policy closure

**Conclusion: SUPPORTED / DECISION-READY for the three requested gaps.**

## 1. Capacity frontier and final Lead Quality threshold

Metrics are calculated independently inside each temporal fold and stage using `pooled_catboost_trajectory`; probabilities from different folds are never rank-mixed.

| Stage | Capacity | Mean Lift | Mean Recall | Median raw cutoff |
|---|---:|---:|---:|---:|
| T0 | 10% | 0.995x | 10.1% | 0.471 |
| T0 | 15% | 0.986x | 14.9% | 0.470 |
| T1 | 10% | 1.126x | 11.4% | 0.502 |
| T1 | **15%** | **1.122x** | **17.0%** | **0.488** |
| T1 | 20% | 1.094x | 22.0% | 0.479 |
| T2 | 10% | 1.457x | 14.6% | 0.478 |
| T2 | **15%** | **1.457x** | **21.9%** | **0.456** |
| T2 | 20% | 1.428x | 28.6% | 0.430 |

### Final policy

- **T0:** no high-priority threshold. Keep score for monitoring / standard queue.
- **T1:** prioritize the top **15%** within T1.
- **T2:** prioritize the top **15%** within T2.
- **Raw probability cutoffs are not frozen.** Use stage-relative P85 because absolute score thresholds vary materially across temporal folds.

At T1, moving from 10% to 15% increases recall by ~48.5% relative (11.4% -> 17.0%) while losing only ~0.004x lift.

At T2, moving from 10% to 15% increases recall by ~50.3% relative (14.6% -> 21.9%) with essentially unchanged lift.

This makes 15% the most defensible default capacity absent a business-provided staffing limit. If Growth later supplies a hard daily capacity, the same curve can map that capacity to the corresponding percentile.

## 2. Explicit P(availability)

### Candidate-level probability

At score time t:

1. select the latest inventory snapshot with `snapshot_date <= t`;
2. if the candidate spot is available now, set:
   `p_spot_available_30d = 1`;
3. if unavailable now, estimate:
   `P(available within 30d | unavailable now, sector)`
   from already-matured historical observations only, with sector estimates shrunk toward the historical global rate;
4. if no as-of snapshot exists, use the historical sector prior only with a **LOW_CONFIDENCE** flag; never call it confirmed availability.

### Lead-level serviceability probability

Let C(lead,t) be the compatible fallback pool produced by the point-in-time matching policy.

`P_availability(lead,t) = max_{spot in C(lead,t)} p_spot_available_30d(spot,t)`

Why max rather than an independence product:

- the business question is whether at least one viable option can serve the lead;
- listing availabilities are not independent;
- max avoids artificial saturation when many correlated listings exist;
- it remains transparent and monotonic.

### Temporal validation

Availability target:

- y=1 if the spot is available at t, or a future observed snapshot within 30 days is available;
- if unavailable at t and no future snapshot is observed within 30 days, censor the row;
- calibration training requires the complete 30-day label to mature before the test period.

| Fold | Train N | Test N | Test window | AUC | Brier | Log loss |
|---|---:|---:|---|---:|---:|---:|
| 1 | 3,270 | 3,459 | 2025-09-14 to 2025-12-19 | 0.896 | 0.0671 | 0.189 |
| 2 | 6,543 | 3,462 | 2025-12-19 to 2026-03-01 | 0.884 | 0.0663 | 0.190 |
| 3 | 9,894 | 3,481 | 2026-03-01 to 2026-05-03 | 0.866 | 0.0741 | 0.214 |
| 4 | 13,242 | 3,466 | 2026-05-03 to 2026-07-13 | 0.885 | 0.0600 | 0.175 |
| **Macro** | — | **13,868 test rows** | 4 folds | **0.883** | **0.0669** | **0.192** |

Observable availability events available for fold construction: **17,323**.

The target positive rate is ~90.3%, so AUC must not be presented without Brier/log-loss.

## 3. Why days_until_available is not in the final probability

Among currently unavailable spots with an observable 30-day future:

| days_until_available | Observed available within 30d |
|---|---:|
| 1–7 | 66.5% |
| 8–14 | 67.0% |
| 15–30 | 64.3% |
| 31–60 | 69.3% |
| >60 | 67.7% |

The variable does not provide a monotonic probability gradient in this synthetic dataset. Using a handcrafted linear or logistic decay would create false precision. The final probability therefore uses the much more defensible current as-of state plus historical sector transition calibration.

## Leakage review

| Element | Status | Reason |
|---|---|---|
| OOF threshold frontier | ALLOW | ranking is computed within fold and stage |
| latest availability snapshot | ALLOW | snapshot_date <= score time |
| future snapshot | TARGET ONLY | never used in X |
| 30-day availability label | ALLOW | future defines y only |
| expanding calibration history | ALLOW | label_mature_at < test_start |
| current is_active | BLOCKED | not used |
| fixed global raw threshold | REJECTED | unstable score scale across folds |

**LEAKAGE_CHECK = PASS**

## Closure

The requested assessment items now become:

| Item | Final status |
|---|---|
| Threshold/capacity | **CLOSED — top 15% at T1/T2; T0 no priority gate** |
| Final threshold | **CLOSED — stage-relative P85** |
| Explicit P(availability) | **CLOSED — calibrated 30-day spot probability + max over compatible fallback candidates** |

This does not yet claim that the complete Lead Opportunity Score formula and fallback @K evaluation are closed; those remain a separate end-to-end integration question.
