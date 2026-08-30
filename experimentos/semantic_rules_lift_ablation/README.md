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
