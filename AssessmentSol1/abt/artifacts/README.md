# P4 artifact authority

Current temporal-validity authority is:

- `p4_qa_summary.json`
- `p4_artifact_manifest.json`
- `AUTHORITY.json`

The current P4 QA status is **PASS** under `INDEPENDENT_RAW_EQUIVALENCE_AUDIT`.

That execution independently reconstructed the frozen P4 grains and temporal gates directly from raw candidate data and did **not** consume P3 artifacts. It verified, among other invariants:

- T0/T1/T2 audit and model-ready counts;
- unique split membership;
- zero selected future Spots;
- zero future Availability snapshots;
- the 1,114,990-row logical candidate universe;
- P4 stale/missing Availability semantics.

## Exact Polars materialization

`validate_abts.py` remains the canonical exact builder/materialization path and, in an environment with Polars, writes the eight full Parquet views.

The active execution environment used for P8 did not contain Polars, so those full Parquet files were not regenerated here. This is a **final reproducibility follow-up**, not a temporal-validity or P8-selection blocker, because P8 rebuilt its stage populations directly from raw under the frozen contracts.

## Superseded artifacts

Older P3 artifacts such as `score_spine`, `lead_quality_*`, `candidate_spots`, `inventory_serviceability_state`, `qa_summary.json`, and `artifact_manifest.json` are historical evidence only and are forbidden as downstream inputs.
