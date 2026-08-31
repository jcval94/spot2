# Decision and Capacity Policy — post-recovery

## Frozen capacity

The post-recovery default is **top 20% / P80 within T1**.

This was selected on the four frozen DEVELOPMENT temporal validation folds using recovered OOF predictions. The procedural holdout was not consulted.

| Capacity | Macro Lead Quality Lift | Status |
|---:|---:|---|
| 5% | 0.859x | reject: weak top tail |
| 10% | 1.075x | passes |
| 15% | 1.084x | passes |
| 20% | **1.124x** | **selected** |

The historical E019 P85/top-15 result was a prior, not an automatic decision. The current clean-room evidence selects P80.

## Guardrail against serviceability over-weighting

The rejected raw product `P_quality × InventoryServiceability` raises exact-serviceability concentration but degrades the primary Lead Quality ranking. At top 15% its pure Lead Quality Lift is 0.977x while its joint-exact Lift is 1.244x.

This trade-off is explicit. V2 does not buy joint-exact performance by silently sacrificing Lead Quality.

## Display bands

Reference thresholds are derived from the DEVELOPMENT full-fit V2 score distribution without labels:

- PRIORITY: top 5%, score >= 22.298344072628932
- HIGH: 5–10%, score >= 22.298344072628932
- MEDIUM: 10–20%, score >= 21.307940332937303
- LOW: remaining

They are display thresholds. Exact operational capacity is rank-based percentile with score-desc / lead_id-asc tie-break.

## Fallback

Maximum recommendation list depth is **K=3**. `NO_RESULT` remains preferable to inventing or excessively relaxing a candidate. UNKNOWN Availability may surface as `VERIFY_AVAILABILITY`; known unavailable inventory is never recommended.

## Claims

Lead Quality, serviceability and their joint operational proxy are separate objectives. None is commercial conversion.
