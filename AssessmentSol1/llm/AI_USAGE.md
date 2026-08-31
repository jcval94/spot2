# AI / LLM usage in the assessment

The Spot2 assessment contains both analytical AI assistance and a **real executed LLM data-quality experiment**.

## Primary auditable AI use

The production-governed use case is:

**Semantic Inventory Quality / Semantic Rule Discovery**.

Real canonical E017 evidence used `gpt-5-nano` with Structured Outputs on 100 listings.

Authoritative V2:
- input tokens: 12,634;
- output tokens: 4,869;
- estimated cost: USD 0.002579;
- new rule candidates: 0/100;
- residual actionable: 0/100.

This is a real negative/selection result: the LLM was cheap and operationally viable but did not add enough unique semantic information to justify an ABT dependency.

The reusable semantics were encoded as deterministic rules.

E018 then tested those free semantic rules as Lead Quality features and did not support promotion:
- baseline macro Lift@10: 1.267x;
- + Rules: 1.196x;
- Δ: -0.0716x;
- IC95%: [-0.1438, +0.1251].

PR #19 supplies additional open-PR live evidence: 340/340 technically valid outputs at ≈ USD 0.053522, but only 28% specificity on the S001 challenge controls. That evidence is supplemental until merged.

## Rules-first governance

The final loop is:

`deterministic rules → unresolved residual → sampled LLM → human validation → deterministic promotion`.

No stable rule should remain a paid LLM dependency merely because it was discovered with an LLM.

## Human gold

A complete human-gold label set is unavailable.

Therefore human precision/recall is not reported.

LLM candidates are not labels and another LLM is not used as ground truth.

## Main score

No `llm_*` or Semantic Rule feature is in final Lead Quality.

The final Lead Opportunity Score does not import or call the LLM subsystem.

The score is reproducible with no API key, no network call and an empty LLM cache.

## Analytical copilot disclosure

LLMs were also used during the assessment to challenge temporal semantics, leakage risks, target definitions, feature contracts, model-selection logic and documentation. Accepted numerical claims, however, are backed by raw-data-derived AssessmentSol1 evidence or explicitly identified upstream experimental evidence.

See:
- `UPSTREAM_EVIDENCE.md`;
- `LLM_EVALUATION.md`;
- `LLM_DECISION.md`;
- `usage_summary.csv`.
