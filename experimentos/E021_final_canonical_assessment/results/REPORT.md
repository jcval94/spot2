# E021 — Final canonical assessment benchmark

## Feature Engineering PIT

- Core safe features: 41.
- Full canonical PIT features: 161.
- Macro AP: 0.5019 -> 0.4856.
- Macro Lift@10: 1.265x -> 1.209x.
- Paired bootstrap AP delta: -0.0163, 95% CI [-0.0300, -0.0007].
- Predictive promotion decision: NOT_SUPPORTED.

The full set remains the canonical audit representation; this decision only governs incremental scoring value.

## Canonical end-to-end

- Joint AUC: 0.570 -> 0.647.
- Joint AP: 0.415 -> 0.467.
- Joint Lift@10: 1.211x -> 1.369x.
- Joint Recall@20: 23.4% -> 26.3%.
- Final-fold P85 joint positives: 85 -> 98 (delta +13).

## Error analysis

Operational FP/FN are evaluated at P85 inside fold and stage for T1/T2. T0 remains cold-start with no priority gate.

| Dimension | Segment | n | Positive rate | FN share | AP |
|---|---|---:|---:|---:|---:|
| stage | T1_first_inquiry | 1814 | 47.1% | 40.0% | 0.523 |
| sector | Land | 830 | 42.9% | 35.8% | 0.543 |
| modality | both | 1040 | 42.5% | 34.5% | 0.549 |
| user_type | tenant_direct | 2041 | 42.0% | 34.3% | 0.534 |
| user_type | developer | 260 | 40.8% | 33.5% | 0.472 |

Detailed segment metrics: error_analysis_summary.csv.
Concrete high-confidence FP/FN cases: error_examples.csv.

## Leakage

- ABTs rebuilt directly from data/candidate through E016.
- Current broker response and blocked mutable current-state features remain excluded.
- Availability remains backward-as-of.
- Lead cohorts stay intact inside rolling temporal folds.
- Ranking metrics are calculated inside fold/stage before aggregation.

LEAKAGE_CHECK = PASS
