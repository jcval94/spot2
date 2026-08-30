# E017 — 100-record LLM semantic feature pilot report

## Decision

**NOT_SUPPORTED for adding LLM-derived variables to the current ABT.**

## V1

The first real API run used `gpt-5-nano` on 100 rows in five batches.

- input tokens: 12,564
- output tokens: 6,767
- estimated cost: USD 0.003335

V1 exposed a contract-design problem: `incremental_issue=false` for all rows while some rows simultaneously had `new_rule_candidate=true` or `requires_human_review=true`. The redundant model-generated booleans were therefore rejected.

## V2

V2 removed redundant decisions from the LLM and derived them deterministically in Python.

- input tokens: **12,634**
- output tokens: **4,869**
- estimated cost: **USD 0.002579**
- output-token reduction vs V1: ~28%

### By stratum

| Stratum | N | Incremental issue | New rule candidate | Human review |
|---|---:|---:|---:|---:|
| ambiguity_challenge | 25 | 96% | 0% | 0% |
| clean_control | 25 | 0% | 0% | 0% |
| land_semantic_residual | 25 | 8% | 0% | 0% |
| rules_positive | 25 | 8% | 0% | 0% |

No V2 row was classified `residual_actionable`.

No V2 row was a new-rule candidate.

## Interpretation

The clean-control result is good: no residual issues were created in that stratum.

However, the apparently strong 96% result in `ambiguity_challenge` is **not incremental value**. That stratum was constructed using deterministic ambiguity patterns already observable without an LLM. The LLM mostly confirmed those known patterns.

The residual Land and Rules-positive cases were also combinations already represented by deterministic flags such as:

- `rule_land_building_copy_flag`
- `rule_ambiguity_candidate_flag`
- direct rule conflicts

Therefore the pilot did not discover a new actionable semantic feature family.

## Business/engineering decision

Per the pre-declared rule:

> if the variable can be obtained another way without API cost, use the free method.

The LLM outputs are **not promoted** into T0/T1/T2 ABTs.

Instead E017 adds a deterministic semantic sidecar with:

- `rule_security_ambiguity_flag`
- `rule_retail_adaptive_use_flag`
- `rule_semantic_ambiguity_flag`
- `rule_semantic_signal_count`
- `rule_semantic_review_tier`

These may be tested as a low-cost challenger in a later predictive ablation.

## Reproducibility

Workflow run: `33296462871`

Artifact ID: `9727563377`

Model: `gpt-5-nano`

The full 100-row output is kept as workflow artifact and is not summarized into invented human labels.


## Deterministic semantic sidecar — full catalog

The free rule sidecar was executed over all 3,000 spots:

- direct conflict flag: **322** (10.73%);
- Land × building-copy: **230** (7.67%);
- security ambiguity (claim + basic/cctv): **327** (10.90%);
- Retail adaptive-use language: **109** (3.63%);
- any semantic ambiguity flag: **429** (14.30%);
- listings with at least one semantic signal: **890**;
- listings with two simultaneous signals: **91**.

Review-tier distribution:

- none: 2,110;
- ambiguity: 386;
- direct_conflict: 322;
- cross_field: 182.

This sidecar is generated without OpenAI API calls.


## Governance conclusion

E017 is closed as:

- **D058 SUPPORTED**: Rules-first / residual-only is the correct LLM evaluation pattern for the current data;
- **D059 NOT_SUPPORTED**: LLM-derived variables are not justified for the current ABT;
- **D060 SUPPORTED**: the deterministic semantic sidecar is the reusable output.

Decision record: [DECISION_LLM_FEATURES.md](../DECISION_LLM_FEATURES.md)

Run trace: [RUN_HISTORY.md](RUN_HISTORY.md)
