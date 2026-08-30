# AssessmentSol1 — clean-room definitive assessment

Status: **PROMPT 4 / point-in-time ABT architecture implemented; runtime materialization gate pending**.

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

## Completed foundational gates

P0/P1/P2 intentionally do **not**:

- train a model;
- optimize feature engineering;
- choose a target because it scores better;
- open a final test;
- claim any historical period is pristine/unseen.

They establish:

1. source/evidence provenance and research-contamination policy;
2. scoring-instant information boundaries for T0/T1/T2;
3. CSV↔Parquet parity and Parquet as canonical preferred raw source;
4. raw PK/FK/duplicate/missing/outlier/temporal audits;
5. a column-level temporal ontology for all raw columns;
6. explicit blocking of temporally unsafe sources/fields;
7. a non-model target bake-off and frozen T1 Lead Quality target.

P1 evidence:

- [evidence/DATA_AUDIT.md](evidence/DATA_AUDIT.md)
- [evidence/TEMPORAL_SEMANTICS.md](evidence/TEMPORAL_SEMANTICS.md)
- [evidence/data_schema.csv](evidence/data_schema.csv)
- [evidence/temporal_column_registry.csv](evidence/temporal_column_registry.csv)
- [evidence/data_audit.json](evidence/data_audit.json)
- [config/raw_data_contract.json](config/raw_data_contract.json)

P2 target evidence:

- [target/TARGET_OPTIONS.md](target/TARGET_OPTIONS.md)
- [target/TARGET_DECISION.md](target/TARGET_DECISION.md)
- [target/TARGET_CONTRACT.md](target/TARGET_CONTRACT.md)
- [target/target_contract.json](target/target_contract.json)
- [target/target_audit.csv](target/target_audit.csv)
- [target/target_cohort_summary.csv](target/target_cohort_summary.csv)
- [target/target_summary.json](target/target_summary.json)

Frozen primary target: `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1` with 14-day historical maturity. No model performance metric was used to select it.

## Prompt 4 — authoritative ABT architecture

The old combined `score_spine` / `lead_quality_*` / `candidate_spots` / `inventory_serviceability_state` artifacts are **superseded evidence**, not downstream inputs.

Authoritative builders now are:

- [abt/build_t0.py](abt/build_t0.py) — T0 cold-start/sensitivity, one row per lead;
- [abt/build_t1.py](abt/build_t1.py) — principal T1, deterministic first inquiry, one row per lead;
- [abt/build_t2.py](abt/build_t2.py) — T2 challenger, one row per second-or-later inquiry;
- [abt/build_inventory_candidates.py](abt/build_inventory_candidates.py) — separate Matching/Inventory object at `score_id × candidate_spot_id`;
- [abt/validate_abts.py](abt/validate_abts.py) — temporal, grain, lineage and split-integrity gate.

Contract and feature authority:

- [abt/ABT_CONTRACT.md](abt/ABT_CONTRACT.md)
- [abt/COLUMN_ROLES.csv](abt/COLUMN_ROLES.csv)
- [abt/COLUMN_LINEAGE.csv](abt/COLUMN_LINEAGE.csv)
- [abt/FORBIDDEN_FEATURES.md](abt/FORBIDDEN_FEATURES.md)

The principal LeadQuality model-ready views contain lead/need/current-inquiry information only. Selected Spot, Spot physical attributes, Matching and Availability are physically separated into the Matching/Inventory object.

Availability is backward-as-of only. Missing snapshot is `UNKNOWN`, never unavailable. `competing_inquiries_30d` and `market_context` remain blocked.

## Runtime gate

From repository root:

```bash
python AssessmentSol1/abt/validate_abts.py
```

A Prompt-4 ABT materialization is authoritative only when:

- `AssessmentSol1/abt/artifacts/p4_qa_summary.json` exists and reports `status = PASS`;
- `p4_artifact_manifest.json` matches the current materialized files.

Until that runtime gate is produced from the current raw package, the older P3 artifact counts must not be cited as Prompt-4 results and the split/modeling phase must not consume them.

See also:

- [CONSTRAINTS.md](CONSTRAINTS.md)
- [PLAN.md](PLAN.md)
- [evidence/SOURCE_EVIDENCE_MAP.md](evidence/SOURCE_EVIDENCE_MAP.md)
- [audit/SCORING_INSTANT_GATE.md](audit/SCORING_INSTANT_GATE.md)
- [evidence/RESEARCH_CONTAMINATION.md](evidence/RESEARCH_CONTAMINATION.md)
