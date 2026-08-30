# E018 — Semantic Rules Lift Ablation

## Goal

Measure whether the free deterministic semantic variables produced after E017 improve ranking quality over the canonical E016 ABT.

This is **not** an LLM experiment. No OpenAI API call is made.

## Comparison

Identical:

- E016 ABT construction;
- target;
- eligibility/censoring;
- temporal lead cohorts;
- CatBoost hyperparameters;
- folds.

Only change:

- baseline;
- baseline + compact semantic Rules sidecar.

## Tested variables

- `rule_direct_conflict_flag`
- `rule_land_building_copy_flag`
- `rule_security_ambiguity_flag`
- `rule_retail_adaptive_use_flag`
- `rule_semantic_signal_count`
- `rule_semantic_review_tier`

`rule_semantic_ambiguity_flag` is intentionally omitted because it is a deterministic OR of the two ambiguity components and would add redundant information.

## Stages

T1 and T2 only. T0 has no selected Spot at score time, so adding Spot semantic variables there would be semantically invalid.

## Primary metric

**Delta Lift@10%** semantic_rules - baseline.

Paired bootstrap is clustered by `lead_id`.

## Promotion gate

Rules are promoted to the ABT only if:

1. macro ΔLift@10% has 95% bootstrap CI entirely above zero; and
2. macro AP does not fall by more than 0.001 absolute.

Otherwise the variables remain an Inventory QA sidecar.


## Result

**NOT_SUPPORTED.**

Cross-validated fold-mean macro results:

| Variant | AP | AUC | Lift@10% | Recall@20% |
|---|---:|---:|---:|---:|
| Baseline E016 | 0.5122 | 0.6063 | **1.267x** | 0.2567 |
| + Semantic Rules | 0.5141 | 0.6114 | **1.196x** | 0.2443 |

Primary delta:

- ΔLift@10%: **-0.0716x**
- 95% paired-bootstrap CI: **[-0.1438, +0.1251]**
- P(ΔLift > 0): **45.0%**

AP and AUC are essentially neutral/slightly positive in point estimate, but the requested top-decile lift does not improve. Therefore the semantic Rules remain an **Inventory QA sidecar**, not scoring features.

Authoritative run: `33297920881`, artifact `9728035555`.

See [results/REPORT.md](results/REPORT.md) and [results/RUN_HISTORY.md](results/RUN_HISTORY.md).
