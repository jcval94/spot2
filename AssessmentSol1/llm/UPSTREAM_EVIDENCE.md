# Upstream LLM evidence — provenance and canonical status

This file reconstructs the LLM/semantic evidence relevant to Prompt 12. It distinguishes merged canonical evidence, open-PR supplemental evidence, and evidence independently reproduced inside `AssessmentSol1/**`.

No upstream runtime artifact is imported by the final scoring pipeline.

## Evidence map

| Evidence | Repository status | What is authoritative | Decision |
|---|---|---|---|
| E017 / PR #18 | **MERGED / CANONICAL** | 100-record real `gpt-5-nano` pilot, V2 authoritative run | LLM-derived ABT features = **NOT_SUPPORTED** |
| E018 / PR #20 | **MERGED / CANONICAL** | 4-fold temporal predictive ablation of deterministic Semantic Rules | Semantic Rules in Lead Quality scoring = **NOT_SUPPORTED** |
| E015 live / PR #19 | **OPEN / SUPPLEMENTAL** | 240 holdout + 100 S001 challenge live nano run | useful semantic discovery tool; **NOT_SUPPORTED** as automatic QA gate |
| AssessmentSol1 reproduction | **LOCAL CLEAN-ROOM** | deterministic Rules baseline rerun from raw Spot + attribute CSVs | reproduces the free semantic sidecar counts; no API needed |

## E017 — canonical real LLM pilot

Merged through PR #18, head commit:

`9e1f6d4b92ca515edd0720d64be993ec669dc351`

Key upstream blobs:

- evidence: `bc580b78fd82a72efbfcaec6f3a673e1bbbfb892`;
- pilot report: `4a96de2e1d5160d4974559877ba61e1735df05af`;
- decision: `ab1c4cabcfc15ec38dd7ffcce581667167a6ef42`;
- historical runner: `1d7637fb2b61d0c828293c10c22dedc67a762b09`;
- deterministic sidecar builder: `e245452b5a3851fc5aeaf94ffac44e9638f98262`.

Authoritative V2 run:

- workflow: `33296462871`;
- artifact: `9727563377`;
- model: `gpt-5-nano`;
- records: 100;
- input tokens: 12,634;
- output tokens: 4,869;
- estimated cost: **USD 0.002579**;
- clean-control incremental issue rate: 0%;
- new rule candidates: **0/100**;
- residual actionable: **0/100**.

Conclusion:

`LLM-derived ABT features = NOT_SUPPORTED`.

The reusable information was converted into deterministic, zero-inference-cost rules.

A later run `33296587433` failed on a batch ID mismatch. It is not the authoritative run and is not used for metrics.

## E018 — canonical and closed

Merged through PR #20, head commit:

`bc0593d8d580a6748f991d64033e41cacb5da239`

Key upstream blobs:

- evidence: `f5555c3b131bbc7c875755593736f8e511b0bd0d`;
- summary: `b71143182e7bfeb153ee190339ddc349477c2cab`;
- paired bootstrap: `93c1289a21b339715bf3b1a3dca01acd369bf6f9`.

Authoritative run:

- workflow: `33297920881`;
- artifact: `9728035555`;
- baseline macro Lift@10: **1.267x**;
- + Semantic Rules macro Lift@10: **1.196x**;
- ΔLift@10: **-0.0716x**;
- IC95%: **[-0.1438, +0.1251]**;
- P(ΔLift > 0): 45%.

Decision:

`NOT_SUPPORTED for promoting Semantic Rules into Lead Quality scoring`.

Semantic Rules remain an **INVENTORY / CATALOG QA SIDECAR**. No post-hoc subset search is permitted on the same historical OOF in an attempt to recover lift.

## E015 live / PR #19 — supplemental, not canonical

PR #19 remains **OPEN**.

Head commit:

`31c58cb6c43f47ea9945fccef2bbc1b352ecfdc1`

Key PR blobs:

- live evidence: `272cb9abd7573e957509780f8ed9ea787eb75743`;
- live report: `2327d0c6c3196ffc324258438cd4decd96e6acfa`.

Live run:

- workflow: `33296510774`;
- artifact: `9727712667`;
- artifact SHA256: `a7c7d5ebdcd389c50d98917bb9d7adb263a56f9d39cb92da829280e1042f9be7`;
- 240/240 holdout responses technically valid;
- 100/100 S001 challenge responses technically valid;
- 0 API/schema errors;
- cumulative observed cost: **USD 0.053522**;
- S001 sensitivity: **76%**;
- S001 specificity: **28%**;
- precision versus the discovery pattern: 51.35%.

Interpretation:

`gpt-5-nano` was technically stable and very cheap, but over-flagged controls too aggressively for an automatic catalog-quality gate.

The 77 incremental candidates versus Rules v2 in the holdout are **not human gold positives**. Human precision/recall remains unavailable.

## AssessmentSol1 clean-room reproduction

Prompt 12 reproduces the deterministic Rules baseline from the raw `spots.csv` and `spot_attributes.csv`, not from historical fitted artifacts.

Raw Git blobs:

- spots: `3dd32ff87a466e45d5637715725718e4bed9d808`;
- spot_attributes: `9479789b881e408d0626ded8432396ba9fc749b6`.

Reproduced over 3,000 listings:

- direct conflict flag: 322;
- Land × building copy: 230;
- security ambiguity: 327;
- Retail adaptive-use language: 109;
- any semantic ambiguity: 429;
- at least one semantic signal: 890;
- two simultaneous signals: 91;
- review tiers: none 2,110; ambiguity 386; direct_conflict 322; cross_field 182.

These exactly reproduce the canonical E017 deterministic sidecar counts.

## Governance boundary

Evidence status is intentionally asymmetric:

- E017 and E018 may be cited as canonical historical evidence because they are merged.
- PR #19 may be cited only as supplemental live evidence while it remains open.
- AssessmentSol1 owns its own executable rules/prompt/schema/runner/evaluator, so final reproducibility does not depend on `experimentos/**`.
