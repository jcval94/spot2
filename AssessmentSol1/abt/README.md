# P4 point-in-time ABTs

Authoritative P4 builders:

- `build_t0.py` — cold-start/sensitivity, one row per lead;
- `build_t1.py` — principal first-inquiry ABT, one row per lead;
- `build_t2.py` — second+ inquiry challenger, one row per inquiry;
- `build_inventory_candidates.py` — separate `score_id × candidate_spot_id` Matching/Inventory table;
- `validate_abts.py` — materializes all P4 views from raw sources and enforces the temporal gate.

Run from the repository root:

```bash
python AssessmentSol1/abt/validate_abts.py
```

The validator rebuilds from `data/candidate/**` and writes:

- `abt_t0_audit_all_rows.parquet`
- `abt_t0_model_ready.parquet`
- `abt_t1_audit_all_rows.parquet`
- `abt_t1_model_ready.parquet`
- `abt_t2_audit_all_rows.parquet`
- `abt_t2_model_ready.parquet`
- `inventory_candidates_audit_all_rows.parquet`
- `inventory_candidates_model_ready.parquet`
- `p4_qa_summary.json`
- `p4_artifact_manifest.json`

under `AssessmentSol1/abt/artifacts/`.

The older P3 files (`build_score_spine.py`, `build_lead_quality_abt.py`, `build_candidate_spots.py`, `build_inventory_state.py`) are superseded and must not be used for downstream P4 modeling. They remain only to preserve prior research chronology.


## Current gate status

An independent raw-equivalence execution has now produced:

- `artifacts/p4_qa_summary.json` with `status = PASS`;
- `artifacts/p4_artifact_manifest.json`;
- `artifacts/AUTHORITY.json`.

This closes the P4 **temporal-validity gate** for downstream stage analysis without reusing P3 outputs.

The exact Polars builder/materialization command above remains recommended before final packaging to prove code-path reproducibility and regenerate the full Parquet views.
