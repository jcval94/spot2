# Definitive point-in-time ABTs — P3 complete

This directory owns the clean-room analytical tables rebuilt only from raw `data/candidate/**`.

## Objects

1. **Lead Quality Snapshot ABT**
   - grain: `lead_id × stage × score_time`
   - unique `prediction_key`
   - T0/T1/T2
   - audit and model-ready views

2. **Inventory Serviceability State**
   - grain: `prediction_key × candidate_spot_id`
   - backward-as-of Availability only
   - explicit missing/stale/known semantics

3. **Lead × Candidate Spot decision table**
   - grain: `prediction_key × candidate_spot_id`
   - deterministic corridor → municipality → state fallback ladder
   - observed current Spot preserved as an audit override

## Authoritative contracts

- `ABT_CONTRACT.md`
- `COLUMN_ROLES.csv`
- `COLUMN_LINEAGE.csv`
- `FORBIDDEN_FEATURES.md`

## Builders

- `build_score_spine.py`
- `build_lead_quality_abt.py`
- `build_candidate_spots.py`
- `build_inventory_state.py`
- `validate_abts.py`

## Evidence

See `artifacts/README.md`, `artifacts/qa_summary.json` and `artifacts/artifact_manifest.json`.

P3 gate: **PASS** under the explicit temporal assumptions documented in the contract.
