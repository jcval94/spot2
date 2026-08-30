# Audit

PROMPT 0 audit artifacts:

- [SCORING_INSTANT_GATE.md](SCORING_INSTANT_GATE.md)
- write-scope verification is recorded after the branch comparison is completed.

Future phases add raw-integrity, leakage, split, target and reproducibility audits here.
\n## P1 raw-data gate\n\n- `../evidence/DATA_AUDIT.md`\n- `../evidence/TEMPORAL_SEMANTICS.md`\n- `../evidence/data_audit.json`\n- `../evidence/data_schema.csv`\n- `../evidence/temporal_column_registry.csv`\n- `../src/assessment_sol1/raw_audit.py`\n- `../tests/test_raw_data_contracts.py`\n\nP1 does not construct a target.\n