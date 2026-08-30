# Decision — LLM-derived features for Spot2

## Decision

**Do not promote LLM-derived semantic variables into the current T0/T1/T2 ABTs.**

Status: **NOT_SUPPORTED** for the tested hypothesis that an LLM adds actionable semantic information beyond deterministic rules on the available listing copy.

## Evidence

E017 used `gpt-5-nano` on a fixed 100-record stress test:

- 25 Rules-positive;
- 25 Land semantic residual;
- 25 ambiguity challenge;
- 25 clean controls.

### V2 authoritative run

- workflow run: `33296462871`;
- artifact: `9727563377`;
- input tokens: **12,634**;
- output tokens: **4,869**;
- estimated API cost: **USD 0.002579**;
- clean-control incremental issue rate: **0%**;
- new rule candidates: **0/100**;
- residual actionable: **0/100**;
- human-review recommendations: **0/100**.

The model labeled 28/100 records as residual ambiguity, but these cases were already representable through deterministic flags used to construct or characterize the challenge strata.

## Why the LLM is rejected as an ABT feature source

The rejection is not based on cost: the pilot was extremely cheap.

It is based on **lack of incremental information**.

A production dependency on an API would add:

- external inference dependency;
- latency;
- model/version drift;
- prompt/schema maintenance;
- reproducibility burden;
- monitoring requirements.

Those costs are not justified when the same signals can be computed deterministically.

## What is retained

The semantic work is retained as free, deterministic features:

- `rule_security_ambiguity_flag`;
- `rule_retail_adaptive_use_flag`;
- `rule_semantic_ambiguity_flag`;
- `rule_semantic_signal_count`;
- `rule_semantic_review_tier`.

These belong to a **Rules semantic sidecar** and may be evaluated later as a predictive challenger.

## Full-catalog effect of the free sidecar

Across 3,000 spots:

- direct conflict flag: **322** (10.73%);
- Land × building-copy: **230** (7.67%);
- security ambiguity: **327** (10.90%);
- Retail adaptive-use language: **109** (3.63%);
- any semantic ambiguity: **429** (14.30%);
- at least one semantic signal: **890**;
- two simultaneous signals: **91**.

Review tiers:

- none: 2,110;
- ambiguity: 386;
- direct_conflict: 322;
- cross_field: 182.

## What could justify revisiting an LLM later

A new LLM experiment is justified only if the information source changes materially, for example:

1. raw inquiry text becomes available;
2. listing copy becomes substantially less templated;
3. new unstructured documents/images appear;
4. Rules leave a measurable long-tail error set that cannot be encoded economically.

That would require a new experiment ID rather than silently expanding E017.

## Final interpretation

E017 is a useful negative result.

It demonstrates that Spot2 tested an LLM with a low-cost, controlled design and **rejected it when it failed to add unique value**. The useful output of the experiment is therefore not an LLM feature family, but a better deterministic semantic feature layer.
