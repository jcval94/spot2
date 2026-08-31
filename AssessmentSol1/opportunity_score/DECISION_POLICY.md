# Decision and Capacity Policy

## Operational assumption

No real Growth handling capacity is supplied by the assessment. The declared default is therefore **top 10% of T1 leads**. This is an operational scenario, not a statistically optimal universal threshold.

Capacity reporting is also produced for top 5% and top 20%.

The central metric is cumulative gain / Recall@capacity:

> If Growth can work only the top X% of leads, what fraction of observed positives is contained there?

For each capacity the evaluation reports N leads, positives captured, Recall@X, Precision@X, Lift@X and cumulative gains.

## Priority bands

Bands were frozen from the **score distribution only** across DEVELOPMENT + CALIBRATION (N=4,680). No target label and no June result was used.

| Band | Reference capacity | Minimum published score |
|---|---:|---:|
| PRIORITY | top 5% | 20.2386392017 |
| HIGH | 5–10% | 20.0856578481 |
| MEDIUM | 10–20% | 19.7356275314 |
| LOW | remaining | below 19.7356275314 |

Reference counts are exactly 234 PRIORITY, 234 HIGH, 468 MEDIUM and 3,744 LOW.

`PRIORITY + HIGH` corresponds to the declared top-10% operating scenario.

If future batches create a tie exactly on a boundary, the deterministic tie-break is:

1. Opportunity Score descending;
2. Inventory confidence descending;
3. lead_id ascending.

The numeric threshold remains frozen; the tie-break is for deterministic capacity extracts, not a way to retune the score.

## DEVELOPMENT comparison

Only the required systems are compared:

A. clean Lead Quality only;
B. Inventory only;
C. multiplicative Opportunity Score.

No D alternative was pre-registered for score blending, so none is introduced.

Lead Quality-only Top-X metrics are undefined because the frozen probability is constant. Inventory and Opportunity have identical rankings by construction.

### DEVELOPMENT descriptive capacity

| System | Capacity | N | Positives | Recall | Precision | Lift |
|---|---:|---:|---:|---:|---:|---:|
| Inventory / Opportunity | 5% | 219 | 39 | 4.38% | 17.81% | 0.87x |
| Inventory / Opportunity | 10% | 437 | 87 | 9.78% | 19.91% | 0.98x |
| Inventory / Opportunity | 20% | 874 | 179 | 20.11% | 20.48% | 1.01x |

DEVELOPMENT has 890 observed positives among 4,368 labeled leads.

This does **not** demonstrate positive-outcome enrichment. The combined system currently ranks serviceability; the frozen Lead Quality component contributes no discrimination.

## External benchmark

`lead_score_internal` is never a predictor or blender input. Its origin and historical availability are not guaranteed, so it may appear only as `NON_DEPLOYABLE_REFERENCE`.

Its reference results cannot modify model, formula, thresholds or capacity policy.

## Fallback decision

A lead may be high priority while exact inventory is not serviceable. The output therefore keeps the Inventory fallback state and Spot recommendations next to the scalar score. A single score never overwrites explicit Tier / UNKNOWN / Tier-3 trade-offs.
