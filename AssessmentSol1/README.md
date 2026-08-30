# AssessmentSol1 — clean-room definitive assessment

Status: **PROMPT 0 / information-boundary gate complete**.

This directory is the only runtime/home for the definitive Spot2 assessment. Historical experiments, pull requests, commits and evidence may be read to avoid repeating mistakes, but they are **not runtime dependencies**.

## Clean-room rule

The definitive solution must be rebuildable from the read-only raw candidate data under `data/candidate/**` plus code/configuration committed inside `AssessmentSol1/**`.

Never import historical:

- ABTs;
- OOF predictions;
- trained models;
- scalers/preprocessors;
- clusterers;
- target encoders;
- fitted calibrators;
- generated feature matrices.

Historical code can be inspected to understand a decision, but any accepted logic must be reimplemented here and rerun from raw data.

## PROMPT 0 outcome

This phase intentionally does **not**:

- train a model;
- optimize feature engineering;
- choose a target because it scores better;
- open a final test;
- claim any historical period is pristine/unseen.

It establishes:

1. source/evidence provenance;
2. research-contamination policy;
3. scoring-instant information boundaries for T0/T1/T2;
4. inventory, broker-response and market-context temporal contracts;
5. explicit accepted/rejected/pending decisions.

See:

- [CONSTRAINTS.md](CONSTRAINTS.md)
- [PLAN.md](PLAN.md)
- [evidence/SOURCE_EVIDENCE_MAP.md](evidence/SOURCE_EVIDENCE_MAP.md)
- [audit/SCORING_INSTANT_GATE.md](audit/SCORING_INSTANT_GATE.md)
- [evidence/RESEARCH_CONTAMINATION.md](evidence/RESEARCH_CONTAMINATION.md)
