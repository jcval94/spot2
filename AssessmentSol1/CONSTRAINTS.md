# Constraints

## Write boundary

Allowed writes for the definitive assessment:

- `AssessmentSol1/**`
- `.github/**` only when required to execute an experiment

For PROMPT 0 no `.github/**` change is required.

Everything else is read-only, including `data/**`, `experimentos/**`, `.agents/**`, root README files, `assessment.md`, and `feature_dictionary.md`.

## Runtime independence

`AssessmentSol1` must not depend at runtime on historical experiment outputs or fitted artifacts. Reading historical source code/evidence during research is allowed; copying fitted state is not.

## Point-in-time doctrine

A field can be used downstream only after answering both questions:

1. Did the value exist at or before `score_time`?
2. Can that historical value be reconstructed without looking at future state?

“Present in a row” is not sufficient evidence that it was known at scoring time.

## Research contamination doctrine

Previously inspected periods are not a pristine unseen holdout. When a frozen protocol later evaluates a reserved historical period that has already influenced human decisions, call it a **procedural final holdout**, not a pristine unseen holdout.

Truly new confirmation requires a new post-freeze cohort or external hidden evaluation.

## Phase-0 prohibitions

Do not train models, optimize FE, select target definitions by model performance, or inspect/open a final test in this phase.
