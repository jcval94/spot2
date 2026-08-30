# AssessmentSol1 — clean-room definitive assessment

Status: **PROMPT 3 / definitive point-in-time ABTs complete**.

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

## Completed gates

P0/P1/P2 intentionally do **not**:

- train a model;
- optimize feature engineering;
- choose a target because it scores better;
- open a final test;
- claim any historical period is pristine/unseen.

They establish:

1. source/evidence provenance and research-contamination policy;
2. scoring-instant information boundaries for T0/T1/T2;
3. CSV↔Parquet parity and Parquet as canonical runtime source;
4. raw PK/FK/duplicate/missing/outlier/temporal audits;
5. a column-level temporal ontology for all 86 raw columns;
6. explicit blocking of temporally unsafe sources/fields;
7. a non-model target bake-off and frozen T1 Lead Quality target.

P1 evidence:

- [evidence/DATA_AUDIT.md](evidence/DATA_AUDIT.md)
- [evidence/TEMPORAL_SEMANTICS.md](evidence/TEMPORAL_SEMANTICS.md)
- [evidence/data_schema.csv](evidence/data_schema.csv)
- [evidence/temporal_column_registry.csv](evidence/temporal_column_registry.csv)
- [evidence/data_audit.json](evidence/data_audit.json)
- [config/raw_data_contract.json](config/raw_data_contract.json)

See:

- [CONSTRAINTS.md](CONSTRAINTS.md)
- [PLAN.md](PLAN.md)
- [evidence/SOURCE_EVIDENCE_MAP.md](evidence/SOURCE_EVIDENCE_MAP.md)
- [audit/SCORING_INSTANT_GATE.md](audit/SCORING_INSTANT_GATE.md)
- [evidence/RESEARCH_CONTAMINATION.md](evidence/RESEARCH_CONTAMINATION.md)


P2 target evidence:

- [target/TARGET_OPTIONS.md](target/TARGET_OPTIONS.md)
- [target/TARGET_DECISION.md](target/TARGET_DECISION.md)
- [target/TARGET_CONTRACT.md](target/TARGET_CONTRACT.md)
- [target/target_contract.json](target/target_contract.json)
- [target/target_audit.csv](target/target_audit.csv)
- [target/target_cohort_summary.csv](target/target_cohort_summary.csv)
- [target/target_summary.json](target/target_summary.json)

Frozen primary target: `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1` with 14-day historical maturity. No model performance metric was used to select it.


P3 ABT evidence:

- [abt/ABT_CONTRACT.md](abt/ABT_CONTRACT.md)
- [abt/COLUMN_ROLES.csv](abt/COLUMN_ROLES.csv)
- [abt/COLUMN_LINEAGE.csv](abt/COLUMN_LINEAGE.csv)
- [abt/FORBIDDEN_FEATURES.md](abt/FORBIDDEN_FEATURES.md)
- [abt/artifacts/qa_summary.json](abt/artifacts/qa_summary.json)
- [abt/artifacts/artifact_manifest.json](abt/artifacts/artifact_manifest.json)

The Lead Quality audit ABT contains 27,576 T0/T1/T2 snapshots; 19,298 have valid labels in the model-ready view. Candidate Spot and Inventory Serviceability each have 1,114,990 logical rows and remain separate from the Lead Quality grain.
