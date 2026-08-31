# Inventory Serviceability — frozen Prompt 9

Inventory is a separate, deterministic, point-in-time serviceability construct. It does not modify or consume the frozen Lead Quality model.

Canonical authority:

- `frozen_inventory_config.json`
- `SERVICEABILITY_CONTRACT.md`
- `MATCHING_POLICY.md`
- `FALLBACK_POLICY.md`
- `FRESHNESS_POLICY.md`
- `build_inventory.py`
- `rank_fallbacks.py`

Selection was restricted to T1 DEVELOPMENT (`score_time < 2026-05-01 UTC`). No target/outcome, CALIBRATION period or June procedural-holdout result was used to choose Inventory rules.

## Guardrails

1. Spot must satisfy `spots.created_at <= score_time`.
2. Modality compatibility is a hard constraint.
3. Structural Spot fields use the declared AssessmentSol1 invariance assumption; mutable current-state fields remain blocked.
4. Availability is strict backward-as-of only.
5. Missing prior snapshot remains `UNKNOWN`; `UNKNOWN != UNAVAILABLE`.
6. Stale backward snapshots remain historically known and reduce `inventory_confidence`.
7. `competing_inquiries_30d` is blocked because its effective window semantics are unproven.
8. Tier 3 is always `TIER_3_EXPERIMENTAL`.
9. Current unversioned Spot prices are not used historically; canonical budget fit is explicitly unverified.
10. Ranking and reason codes are deterministic; no LLM or outcome optimization is used.

## Intraday caveat

`availability_snapshot.snapshot_date` is date-only. Same-day use therefore relies on the previously documented business-date assumption. The pre-P8 strict-previous-day sensitivity was mild, but production should require an ingestion/event timestamp or a documented publication SLA.

## Evidence

`outputs/` contains DEVELOPMENT policy evidence, `figures/` compact visual evidence, and `examples/` deterministic fallback cases. `TEMPORAL_CORRECTION.md` records the stale-vs-unknown inconsistency corrected in this phase.

The exact Polars Inventory path was syntax-checked but could not be executed in the current tool runtime because Polars is unavailable. The policy audit was independently recomputed directly from raw repository blobs; `tests/test_inventory.py` is the committed exact-runtime gate.
