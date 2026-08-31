# Lead Opportunity Score — post-recovery frozen V2

Prompt 11.6 invalidated the old Base-Rate × Inventory product because Lead Quality recovered selected-Spot matching signal.

The canonical T1 score is now:

```
OpportunityScoreV2 = P(LeadQuality_recovered) × InventoryActionabilityGate
```

Continuous `inventory_serviceability` remains a separate output and is **not multiplied** into V2. This removes the double counting exposed by the recovery.

## Frozen decisions

- Lead Quality: `LQ_RECOVERY_R4_STATIC_MATCH_V1`.
- Calibration: RAW.
- Inventory scalar: unchanged `INV_SERVICEABILITY_V1_FROZEN_2026-08-30`.
- Fallback maximum: K=3.
- Capacity: P80 / top 20% within T1.
- E018 Semantic Rules: excluded from scoring.
- E019/E020: supporting historical evidence only.

The score and policy were selected only from DEVELOPMENT temporal OOF. June remains diagnostic/non-pristine and cannot alter them.

Canonical evidence is in `../recovery_downstream/`.
