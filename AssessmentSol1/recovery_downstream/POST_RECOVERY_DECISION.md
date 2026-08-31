# Post-Recovery Decision

## Decision before canonical update

The Lead Quality recovery is frozen and the affected downstream system has been reevaluated from current AssessmentSol1 evidence.

### 1. Lead Quality stays recovered

Champion: `LQ_RECOVERY_R4_STATIC_MATCH_V1`.

Target and splits remain unchanged. The old Base Rate probabilities are stale and must not be reused.

### 2. Inventory scalar stays frozen

`INV_SERVICEABILITY_V1_FROZEN_2026-08-30` remains valid because it is PIT and outcome-independent. Rebuilding it would add churn without addressing the recovery dependency.

### 3. Old multiplicative Opportunity Score is rejected

The original `P_quality × InventoryServiceability` was safe only because Lead Quality was constant. After recovery, Lead Quality itself contains selected-Spot area/geographic matching.

On clean-room DEVELOPMENT OOF, the raw product shows the expected trade-off:

- at top 15%, pure Lead Quality Lift falls from **1.084x** to **0.977x**;
- at the same capacity, the exact-serviceability joint objective reaches **1.244x** Lift.

That is not a free improvement: it sacrifices the primary Lead Quality capture to count matching strength again.

### 4. Canonical Opportunity Score V2

Freeze:

`OpportunityScoreV2 = P_quality × InventoryActionabilityGate`

The gate is 1 when the frozen fallback layer can return a known-available or verification candidate and 0 only on a true `NO_RESULT`.

This preserves the recovered Lead Quality ranking among actionable leads and uses Inventory as an operational feasibility gate rather than a second continuous matching weight.

### 5. Capacity policy

DEVELOPMENT OOF was reevaluated at 5%, 10%, 15% and 20%. No procedural holdout was consulted.

For the recovered/canonical ranking:

| capacity | macro LeadQuality Lift | macro Recall | macro Precision |
|---:|---:|---:|---:|
| 5% | 0.859x | 4.4% | 18.0% |
| 10% | 1.075x | 10.8% | 22.4% |
| 15% | 1.084x | 16.4% | 22.5% |
| 20% | **1.124x** | **22.6%** | **23.3%** |

Freeze **P80 / top 20% within T1**. E019’s historical P85/top-15 is treated as a prior only and is not copied.

Top 5% remains a known weakness and is not recommended.

### 6. Fallback K

The frozen Inventory candidate/ranking logic is unchanged. Only maximum list length is revised.

AssessmentSol1 DEVELOPMENT contains 4368 leads:
- any result: 4361 (99.84%);
- at least 3 recommendations: 4051 (92.74%);
- at least 5 recommendations: 3696 (84.62%).

Therefore freeze **K=3**. This conclusion is independently reproduced from the clean-room output; E020 is only supporting historical evidence.

### 7. End-to-end objective separation

Three different questions remain separate:

- **Lead Quality:** eventual `scheduled_visit` on the first inquiry under the frozen target contract.
- **Serviceability:** PIT Inventory/fallback feasibility; not a conversion target.
- **Joint operational objective:** Lead Quality positive plus serviceability state.

No serviceability metric is renamed as conversion, and no joint proxy is presented as commercial conversion.

### 8. Holdout governance

June remains `DIAGNOSTIC_ONLY_NON_PRISTINE` because of the previously documented incident. It was not used to choose the recovered model, V2 formula, capacity or K.

Canonical artifacts may be updated only after this reevaluation is persisted. The final Prompt-11 red team is still required after those updates.
