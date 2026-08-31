# Post-freeze procedural holdout diagnostic

The Opportunity Score policy was frozen in `frozen_score_config.json` before this evaluation. The freeze commit is `1d036f69891dd8ba42798596af3888ece68dd76d`.

June remains **DIAGNOSTIC_ONLY_NON_PRISTINE** because the Lead Quality workflow had already documented a procedural-holdout consumption incident. Nothing in this diagnostic changes the formula, priority thresholds, capacity assumption, Lead Quality, Inventory or fallback policy.

## June labeled population

- mature labeled T1 leads: **273**
- observed positives: **53**
- prevalence: **19.41%**

Lead Quality-only Top-X metrics remain undefined because its frozen probability is constant.

Inventory-only and multiplicative Opportunity Score remain ranking-identical.

| Capacity | N | Positives captured | Recall | Precision | Lift |
|---|---:|---:|---:|---:|---:|
| 5% | 14 | 1 | 1.89% | 7.14% | 0.37x |
| 10% | 28 | 3 | 5.66% | 10.71% | 0.55x |
| 20% | 55 | 7 | 13.21% | 12.73% | 0.66x |

At the declared top-10% operational scenario the system concentrates only **3 of 53 observed positives**.

## Interpretation

The diagnostic does not support positive-outcome enrichment. It strengthens the conservative interpretation already visible in DEVELOPMENT:

- clean Lead Quality is a neutral prior;
- the combined ranking is entirely driven by serviceability;
- Inventory Serviceability is useful for answering whether demand can be served, not demonstrated as a conversion predictor;
- the multiplicative score is a coherent product construct but not evidence of incremental ranking lift.

True confirmation requires new/hidden post-freeze data.
