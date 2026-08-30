# AI / LLM usage in the assessment

The original Spot2 assessment requires explicit AI use. AssessmentSol1 uses an LLM as a **methodology and analysis copilot**, not as a hidden label source and not as an ungoverned production feature.

## What the LLM was used for

- challenge the temporal information set at T0/T1/T2;
- identify leakage traps and missing observation clocks;
- structure the target bake-off and maturity discussion;
- propose stage-aware deterministic Feature Engineering;
- review ABT/feature/model contracts for internal contradictions;
- generate hypotheses for EDA/drift checks;
- audit model-selection logic and reporting edge cases;
- help communicate why a simple/neutral model can be the correct result.

All accepted logic is implemented/documented inside `AssessmentSol1/**`; historical fitted artifacts are not imported.

## Representative prompt

> Audit the assessment as a point-in-time prediction problem. For every candidate feature, state the exact score time, earliest observable time, transformation, leakage risk and model role. Reject any feature whose observation/effective time cannot be defended. Keep Lead Quality separate from Inventory, use backward-as-of Availability only, freeze target/splits before model comparison, and do not search for lift after seeing the procedural holdout.

## What worked

The LLM was useful for:
- adversarial temporal reasoning;
- turning exploratory findings into explicit contracts/tests;
- distinguishing business hypotheses from model-eligible features;
- documenting tradeoffs and negative results.

## What did not work / was not promoted

Historical E017/E018 evidence showed that listing-copy LLM/semantic-rule features did **not** provide reliable incremental LeadQuality lift. They remain QA/research evidence only.

No `llm_*` field is a current LeadQuality feature.

## Final-deliverable requirement

The final notebook/HTML must include this prompt/use summary and explicitly state that the LLM influenced the analytical process, while final numerical claims come from raw-data-derived AssessmentSol1 evidence.
