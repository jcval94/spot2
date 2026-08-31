# Inventory temporal correction — INV-001

**Type:** methodological inconsistency found during Prompt 9.  
**Scope:** Inventory only. Lead Quality target, model, calibration and splits are unchanged.

The superseded P3 `abt/build_inventory_state.py` used `snapshot_age_days > 90` to set `availability_known=false`. `config/scoring_information_contract.json` also retained the phrase `UNKNOWN_FOR_SERVICEABILITY` for stale >90d. That conflicts with the later Inventory contract and Prompt 9: a stale backward observation was still known at `score_time`; age measures confidence, not observability.

## Correction

The frozen Prompt-9 implementation uses:

- no prior backward snapshot -> `UNKNOWN`, confidence 0;
- any prior backward snapshot -> availability state remains known;
- age >90d -> confidence 0.30 and freshness bucket `GT_90D`, never `UNKNOWN` solely because of age.

`competing_inquiries_30d` is also excluded completely from the canonical Inventory builder because its window direction/effective time remains unproven.

The P3 artifacts remain superseded evidence and are not downstream inputs. The machine-readable scoring information contract is updated to match the frozen Prompt-9 semantics.
