# LLM evaluation — Rules-first semantic Inventory/Catalog QA

## Evaluation question

Can an LLM add useful semantic discovery value where the dataset genuinely contains unstructured listing language, without creating an unnecessary dependency in the Lead Opportunity Score?

## Evidence classes

The evaluation deliberately separates:

1. deterministic Rules-first reproduction inside AssessmentSol1;
2. canonical real-API E017 evidence;
3. canonical E018 predictive ablation of the deterministic semantic rules;
4. supplemental live PR #19 evidence.

No new paid API run was required for Prompt 12.

## Rules-first baseline — reproduced locally

The AssessmentSol1 rules implementation was independently reconstructed from raw `spots.csv` + `spot_attributes.csv`.

Across 3,000 listings:

| Signal | Count | Share |
|---|---:|---:|
| direct conflict | 322 | 10.73% |
| Land × building copy | 230 | 7.67% |
| security ambiguity | 327 | 10.90% |
| Retail adaptive-use language | 109 | 3.63% |
| semantic ambiguity | 429 | 14.30% |
| at least one semantic signal | 890 | 29.67% |
| two simultaneous signals | 91 | 3.03% |

The review-tier distribution exactly matches canonical E017:
- none: 2,110;
- ambiguity: 386;
- direct_conflict: 322;
- cross_field: 182.

This is the core engineering result: repeatable semantic issues can be converted into zero-inference-cost checks.

## E017 — real GPT-5 nano pilot

Canonical merged evidence:

- 100 real records;
- Structured Outputs;
- input tokens: 12,634;
- output tokens: 4,869;
- estimated cost: **USD 0.002579**;
- clean-control incremental issue rate: 0%;
- new rule candidates: **0/100**;
- residual actionable: **0/100**.

E017 therefore does **not** support promoting `llm_*` variables to the ABT.

The conclusion is not “the LLM was too expensive.” It was extremely cheap. The issue was lack of incremental information beyond repeatable deterministic semantics.

## E018 — downstream predictive value of the free rules

Canonical merged evidence:

| System | Macro Lift@10 |
|---|---:|
| baseline | 1.267x |
| baseline + Semantic Rules | 1.196x |
| delta | **-0.0716x** |

Paired bootstrap IC95% for ΔLift@10:

`[-0.1438, +0.1251]`.

The interval crosses zero, so E018 does not prove statistically conclusive harm. It does prove that the pre-registered promotion gate was not met.

Decision:

**Semantic Rules are not Lead Quality scoring features.**

They remain an Inventory/Catalog QA sidecar.

## E015 live / PR #19 — technical and challenge behavior

PR #19 is still open, so this section is supplemental rather than canonical.

Technical validity:
- 240/240 holdout responses valid;
- 100/100 challenge responses valid;
- 0 API/schema errors;
- cumulative observed cost ≈ **USD 0.053522**.

S001 challenge versus the deterministic discovery-pattern comparator:
- sensitivity: **76%**;
- specificity: **28%**;
- precision versus the pattern: 51.35%.

Interpretation:

The LLM is sensitive enough to be useful for discovery, but it over-flags controls too aggressively for an automatic gate.

The 77 incremental candidates versus Rules v2 are **candidate findings**, not 77 human-confirmed issues.

## Human accuracy

There is no complete real human-gold set in the available evidence.

Therefore:

**human precision/recall unavailable**.

Another LLM is not used as ground truth.

The assessment distinguishes:

| Metric class | Available? |
|---|---|
| technical Structured Output validity | yes |
| Rules overlap | yes |
| challenge behavior versus discovery pattern | yes, supplemental PR #19 |
| candidate novelty | yes |
| real human precision/recall | **no** |
| Lead Quality lift impact of deterministic rules | yes, E018 |

## Cost accounting

Historical real API usage is persisted in `usage_summary.csv`.

Prompt 12 incurs **USD 0 new API cost**.

The self-contained runner includes:
- per-request token usage;
- explicit price table/CLI override;
- pre-request conservative budget reservation;
- hard budget;
- cache hits with zero incremental API cost.

## Final interpretation

The successful product/governance pattern is:

`Rules first → LLM residual discovery → human validation → deterministic promotion`.

The LLM is retained where it has a defensible information advantage: sampled inspection of unresolved language semantics.

It is deliberately excluded where deterministic systems already reproduce the useful information or where predictive lift was not demonstrated.
