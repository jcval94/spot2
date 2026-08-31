# Audit

The final methodological authority is now:

- `FINAL_LEAKAGE_AUDIT.md`
- `LEAKAGE_MATRIX.csv`
- `TEMPORAL_INVARIANTS.csv`
- `DOUBLE_COUNTING_AUDIT.md`
- `STRESS_TEST_REPORT.md`
- `CLAIMS_POLICY.md`
- `final_audit.json`

Prompt-11 stress tests live only under `stress/**`. They are deliberately unsafe/non-deployable and are rejected by `harness.py` in product mode.

Earlier audit evidence remains useful chronology:

- `SCORING_INSTANT_GATE.md`
- `PRE_P8_GATE_STATUS.json`
- `../evidence/DATA_AUDIT.md`
- `../evidence/TEMPORAL_SEMANTICS.md`
- `../evidence/RESEARCH_CONTAMINATION.md`

The final gate may be READY only when `final_audit.json` has zero active BLOCKERS.
