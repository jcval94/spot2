# Target — P2 frozen

The primary Lead Quality target is frozen **before feature engineering/modeling** as:

`T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`

Question:

> Will the deterministic first inquiry eventually be recorded with `broker_response == "scheduled_visit"`?

Historical training-label maturity: **14 days**. This is a maturity buffer only; it is not an outcome horizon.

The decision came from a non-model bake-off of Targets A/B/C using business semantics, temporal identifiability, label coverage, prevalence stability, censoring and implementation feasibility. No AUC/AP/Lift was computed or used.

Authoritative artifacts:

- `TARGET_OPTIONS.md`
- `TARGET_DECISION.md`
- `TARGET_CONTRACT.md`
- `target_contract.json`
- `build_targets.py`
- `target_audit.csv`
- `target_cohort_summary.csv`
- `target_summary.json`

Historical E028 is evidence only. Its fitted/generated artifacts are not runtime dependencies and its target was not inherited by tradition.
