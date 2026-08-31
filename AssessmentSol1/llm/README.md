# LLM / AI — self-contained Prompt 12 closure

Status: **CLOSED / REQUIREMENT SATISFIED / NO SCORE DEPENDENCY**.

The assessment demonstrates real AI usage through a semantic Inventory/Catalog QA use case, while deliberately keeping the final Lead Opportunity Score independent of live LLM inference.

## Use case

**Semantic Inventory Quality / Semantic Rule Discovery**

The LLM is used only on genuinely unstructured listing language and only after deterministic rules.

It is not used for:
- conversion probability;
- final Lead Quality;
- Opportunity Score;
- fallback ranking;
- deterministic explanations.

## Rules-first architecture

```
structured data + listing copy
→ deterministic rules
→ unresolved semantic residual
→ sampled LLM discovery
→ human validation
→ recurring validated pattern becomes deterministic rule
```

## Files

- `UPSTREAM_EVIDENCE.md` — E017/E018 canonical provenance and open PR #19 status;
- `prompt.md` — real residual semantic-audit prompt;
- `response.schema.json` — strict Structured Output schema;
- `RULES_BASELINE.md` — deterministic baseline and clean-room reproduction;
- `LABELING_GUIDELINES.md` — human-gold policy;
- `run_llm_audit.py` — self-contained runner, rules, cache, hard budget and evaluator;
- `cache/` — hash-addressed optional live-output cache;
- `results/` — reproduced Rules evidence and optional runner outputs;
- `LLM_EVALUATION.md` — evaluation separated by evidence type;
- `LLM_DECISION.md` — final governance decision;
- `usage_summary.csv` — real historical API usage/cost summary;
- `AI_USAGE.md` — broader assessment AI disclosure.

## Reproduce without an API

Default execution is deterministic:

```bash
python AssessmentSol1/llm/run_llm_audit.py --mode rules
```

This reads raw:
- `data/candidate/csv/spots.csv`;
- `data/candidate/csv/spot_attributes.csv`.

It writes only under `AssessmentSol1/llm/results/`.

No OpenAI package, key or network call is needed for `--mode rules`.

## Optional live residual audit

A new paid run is **not required** for the assessment. Existing E017 evidence already demonstrates real use.

If a future reproducibility check is deliberately requested:

```bash
pip install openai
export OPENAI_API_KEY=...
python AssessmentSol1/llm/run_llm_audit.py \
  --mode live \
  --model gpt-5-nano \
  --limit 100 \
  --hard-budget-usd 0.10
```

Safety behavior:
- live mode is opt-in;
- default hard max = 100 records;
- default hard budget = USD 0.10;
- `store=False`;
- Structured Outputs via JSON Schema;
- conservative cost reservation occurs before every uncached request;
- cache key covers model + prompt + schema + payload;
- a cache hit performs no new API request.

The runner freezes the historical GPT-5 nano price table used by E017 (USD 0.05 / 1M input, USD 0.40 / 1M output). A different model requires explicit price overrides rather than silently guessing cost.

## Current evidence

### E017 — canonical

Real `gpt-5-nano` V2 pilot:
- 100 records;
- cost ≈ **USD 0.002579**;
- 0/100 new rule candidates;
- 0/100 residual actionable.

Decision: **LLM-derived ABT features NOT_SUPPORTED**.

### E018 — canonical

- baseline Lift@10: 1.267x;
- + Semantic Rules: 1.196x;
- ΔLift@10: -0.0716x;
- IC95%: [-0.1438, +0.1251].

Decision: **Semantic Rules NOT_SUPPORTED for Lead Quality scoring**.

### PR #19 — open supplemental evidence

- 240/240 holdout valid;
- 100/100 challenge valid;
- cost ≈ USD 0.053522;
- S001 sensitivity 76%;
- specificity 28%.

Decision: technically useful for semantic discovery, too prone to over-flagging for automatic QA.

## Human gold

No complete human-gold labels exist.

**Human precision/recall unavailable.**

LLM candidates are not treated as positives, and another model is not used as ground truth.

## Final system boundary

Nothing under `AssessmentSol1/llm/**` is imported by the Lead Quality, Inventory, Opportunity Score or capacity-policy runtime.

The primary Lead Opportunity Score remains reproducible when:
- the OpenAI API is unavailable;
- no API key exists;
- the LLM cache is empty;
- the LLM budget is zero.
