# LLM decision

## Final decision

**SUPPORTED as a sampled Semantic Inventory / Catalog QA discovery tool.**

**NOT_SUPPORTED as:**
- a Lead Quality predictor;
- a Lead Opportunity Score dependency;
- a fallback-ranking model;
- an automatic catalog-quality gate;
- a substitute for human gold;
- a permanent API dependency for patterns that can be encoded deterministically.

## Production architecture

```
structured data + listing copy
    ↓
deterministic Rules-first baseline
    ↓
unresolved semantic residual
    ↓
sampled LLM discovery
    ↓
human validation
    ↓
recurring validated pattern → deterministic Rules vN
```

The goal is not to maximize LLM usage. The goal is to use an LLM only where unstructured language contains information that deterministic rules do not yet capture economically.

## Evidence basis

### Real LLM use demonstrated

E017 is canonical and merged:
- real `gpt-5-nano` run;
- 100 records;
- Structured Outputs;
- cost ≈ USD 0.002579;
- 0/100 new rule candidates;
- 0/100 residual actionable.

PR #19 adds supplemental live evidence:
- 340 technically valid outputs;
- cost ≈ USD 0.053522;
- S001 sensitivity 76%;
- specificity 28%.

This shows the API/model is technically viable and inexpensive, but insufficiently specific for unattended QA.

### Rules-first value demonstrated

AssessmentSol1 independently reproduces the deterministic semantic sidecar over all 3,000 listings.

The reusable semantic information from E017 therefore survives without API inference.

### Scoring value rejected

E018 is canonical and closed:
- baseline macro Lift@10: 1.267x;
- + Rules: 1.196x;
- ΔLift@10: -0.0716x;
- IC95%: [-0.1438, +0.1251].

The rules do not enter final Lead Quality.

There will be no further post-hoc subset search on the same historical OOF to rescue Lift.

## Human-gold limitation

No complete human-gold set exists.

**Human precision/recall is unavailable.**

Incremental LLM candidates are review candidates, not positives.

## Lead Opportunity Score independence

The final production Lead Opportunity Score has **no runtime dependency on OpenAI or any LLM**.

Its reproduction requires no API call, no LLM cache and no prompt execution.

LLM failure, API unavailability, budget exhaustion or model deprecation cannot prevent the primary score from being produced.

## Final narrative

We used an LLM where the dataset genuinely contained unstructured language.

A Rules-first baseline captured repeatable inconsistencies deterministically.

The LLM was inexpensive and technically reliable as a semantic discovery tool, but neither LLM-derived features nor the resulting deterministic semantic rules demonstrated incremental Lead Quality ranking value.

Therefore the production Lead Opportunity Score remains independent of LLM inference. The LLM is retained as a sampled Catalog/Inventory QA discovery tool.

This is a model/product-governance decision, not a failed attempt to force AI into the predictor.
