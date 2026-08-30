# E018 — Semantic Rules Lift Ablation

**Conclusion: NOT_SUPPORTED.**

Question: does the free E017 semantic rule sidecar improve ranking lift over the canonical E016 ABT? Metrics are computed within each temporal test fold and then averaged; raw probabilities from different folds are never rank-mixed.

## Cross-validated fold-mean results

| Scope | Variant | AP | AUC | Lift@10% | Recall@20% |
|---|---|---:|---:|---:|---:|
| T1_first_inquiry | baseline | 0.5470 | 0.5734 | 1.199x | 0.2309 |
| T1_first_inquiry | semantic_rules | 0.5486 | 0.5860 | 1.136x | 0.2187 |
| T2_engaged | baseline | 0.4773 | 0.6392 | 1.336x | 0.2825 |
| T2_engaged | semantic_rules | 0.4795 | 0.6367 | 1.256x | 0.2699 |
| MACRO | baseline | 0.5122 | 0.6063 | 1.267x | 0.2567 |
| MACRO | semantic_rules | 0.5141 | 0.6114 | 1.196x | 0.2443 |

## Paired bootstrap deltas: semantic_rules - baseline

| Scope | Metric | Delta | 95% CI | P(delta>0) |
|---|---|---:|---:|---:|
| T1_first_inquiry | lift_top_10pct | -0.0627 | [-0.2456, +0.1481] | 33.5% |
| T1_first_inquiry | average_precision | +0.0016 | [-0.0263, +0.0272] | 53.1% |
| T1_first_inquiry | roc_auc | +0.0126 | [-0.0103, +0.0366] | 82.9% |
| T2_engaged | lift_top_10pct | -0.0804 | [-0.1562, +0.2059] | 60.9% |
| T2_engaged | average_precision | +0.0022 | [-0.0156, +0.0184] | 59.2% |
| T2_engaged | roc_auc | -0.0025 | [-0.0138, +0.0092] | 36.3% |
| MACRO | lift_top_10pct | **-0.0716** | **[-0.1438, +0.1251]** | **45.0%** |
| MACRO | average_precision | +0.0019 | [-0.0153, +0.0167] | 57.6% |
| MACRO | roc_auc | +0.0051 | [-0.0087, +0.0188] | 75.9% |

## Fold-level Lift@10%

### T1

| Fold | Baseline | Semantic Rules | Delta |
|---:|---:|---:|---:|
| 1 | 1.108x | 1.108x | +0.000 |
| 2 | 1.230x | 1.185x | -0.046 |
| 3 | 1.262x | 1.221x | -0.041 |
| 4 | 1.193x | 1.029x | -0.165 |

### T2

| Fold | Baseline | Semantic Rules | Delta |
|---:|---:|---:|---:|
| 1 | 1.231x | 0.663x | -0.568 |
| 2 | 1.131x | 1.406x | +0.275 |
| 3 | 1.521x | 1.521x | +0.000 |
| 4 | 1.461x | 1.433x | -0.029 |

The fold pattern is not stable enough to claim lift improvement.

## Semantic coverage

OOF diagnostic rows with >=1 semantic signal: **29.8%**.

### Review-tier outcome rates

| Stage | Tier | N | Share | scheduled_visit_30d rate |
|---|---|---:|---:|---:|
| T1 | ambiguity | 269 | 14.5% | 53.2% |
| T1 | cross_field | 100 | 5.4% | 54.0% |
| T1 | direct_conflict | 178 | 9.6% | 52.8% |
| T1 | none | 1,311 | 70.6% | 46.5% |
| T2 | ambiguity | 490 | 13.5% | 35.9% |
| T2 | cross_field | 214 | 5.9% | 35.5% |
| T2 | direct_conflict | 388 | 10.7% | 32.5% |
| T2 | none | 2,549 | 70.0% | 37.6% |

This reversal is descriptive, not causal. Conditioning on reaching T2 changes the population and can alter associations.

## Interpretation

The semantic Rules are useful for **inventory quality**, but they are not demonstrated Lead Quality ranking features.

Two things can both be true:

1. the Rules expose real semantic/cross-field anomalies in listings;
2. those anomalies do not help identify the top-decile leads most likely to schedule a visit.

Smooth ranking metrics are essentially neutral/slightly positive in point estimates (macro AP +0.0019; macro AUC +0.0051), while the business metric requested here, Lift@10%, falls by 0.0716x in point estimate. The lift interval crosses zero, so E018 does **not** prove harm; it does show there is no evidence strong enough to promote the Rules for ranking.

## Decision

**Do not add the semantic Rules to the canonical scoring ABT.**

Keep them as an Inventory QA / Catalog Quality sidecar.

If they are tested again for scoring, it should be a new hypothesis with a materially different representation or information source, not repeated subset-search on E018 after seeing the outcome.

## Methodological correction

An earlier E018 run concatenated raw probabilities from independently trained temporal folds before calculating OOF ranking metrics. CatBoost probability scales differed materially across folds, so global ranking across folds was invalid.

That run was discarded.

The authoritative run computes metrics **inside each test fold**, averages fold metrics, and uses a paired bootstrap that resamples leads within each fold before aggregating deltas.

## Decision rule

SUPPORTED required macro ΔLift@10% 95% CI entirely above zero and no material macro AP degradation (>0.001 absolute).

A positive point estimate with an interval crossing zero would be INCONCLUSIVE.

A non-positive macro lift with bootstrap probability of improvement below 50% is NOT_SUPPORTED.

Observed: ΔLift@10% = -0.0716 and P(delta>0) = 45.0% → **NOT_SUPPORTED**.

## Leakage / semantics

No LLM output is used. Features are deterministic functions of listing copy + spot attributes.

They are treated as contemporaneous listing metadata, consistent with the static Spot representation in E016.

Because the dataset does not version listing copy/attributes over time, production use would require confirming that these fields are immutable or reconstructable as-of score time.

## Reproducibility

Authoritative workflow run: `33297920881`

Artifact: `9728035555`

OOF diagnostic population: 5,499 rows / 1,858 unique leads.
