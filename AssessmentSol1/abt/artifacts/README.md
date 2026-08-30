# P4 artifact authority

Files prefixed by the P4 object names below are authoritative after running `validate_abts.py`:

- `abt_t0_*`
- `abt_t1_*`
- `abt_t2_*`
- `inventory_candidates_*`
- `p4_qa_summary.json`
- `p4_artifact_manifest.json`

Older P3 artifacts such as `score_spine`, `lead_quality_*`, `candidate_spots`, and `inventory_serviceability_state` are historical evidence only and are never inputs to P4 builders.

A P4 artifact set is valid only when `p4_qa_summary.json` reports `status = PASS` and its manifest hashes correspond to the current materialization.
