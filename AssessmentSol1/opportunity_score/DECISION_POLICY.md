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

## Priority bands

Bands are **rank-based per scoring batch**, not threshold-forced:

- PRIORITY: first 5%;
- HIGH: 5–10%;
- MEDIUM: 10–20%;
- LOW: remaining.

The DEVELOPMENT full-fit top-5 and top-10 numeric score thresholds are identical because of real score ties. That is retained as evidence rather than hidden with artificial epsilon changes. Exact assignment therefore uses score descending, then lead_id ascending.

## Fallback

Maximum recommendation list depth is **K=3**. `NO_RESULT` remains preferable to inventing or excessively relaxing a candidate. UNKNOWN Availability may surface as `VERIFY_AVAILABILITY`; known unavailable inventory is never recommended.

## Claims

Lead Quality, serviceability and their joint operational proxy are separate objectives. None is commercial conversion.
