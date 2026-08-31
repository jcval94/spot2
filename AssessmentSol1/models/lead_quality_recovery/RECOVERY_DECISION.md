# Recovery decision

## RECOVERED — CONTINUE TO PROMPT 12

The Lead Quality ranking gate is now satisfied on **temporal DEVELOPMENT OOF only**.

### Recovered champion

`LQ_RECOVERY_R4_STATIC_MATCH_V1`

Model: small regularized Logistic ranking model.

Features:

1. `selected_spot_area_closeness`
2. `selected_spot_geographic_fit`
3. `selected_spot_attribute_completeness`

No Availability is used.

### Gate

| Requirement | Result | Status |
|---|---:|---|
| Lift@10 > 1 | **1.0754** | PASS |
| Lift@20 > 1 | **1.1146** | PASS |
| AP > base-rate AP | **0.2186 > 0.2083** | PASS |
| Lift@10 > 1 in majority folds | **4/4** | PASS |
| Lift@20 > 1 in majority folds | **3/4** | PASS |
| leakage violations | **0** | PASS |
| procedural holdout used | **NO** | PASS |

Additional metrics:

- ROC AUC: 0.5134
- Brier: 0.164983 versus Base Rate 0.165002
- Lift@5: 0.8593

The top-5% weakness is retained as an explicit limitation. The model is useful enough for the requested top-10/top-20 ranking gate, not a high-separation classifier.

### Uncertainty

Bootstrap macro ΔLift@10 versus random-ranking Lift=1:

- point: +0.0754
- IC95%: [-0.2165, +0.2799]
- P(Δ>0): 59.5%

The interval is wide and crosses zero. Prompt 11.5 explicitly says not to require an artificial IC95% entirely above 1. The stronger evidence for the gate is temporal point stability: Lift@10 >1 in all four validation windows.

### Why this champion

R4_MATCH_INTERACTION has slightly higher AP/AUC, but the improvement is marginal and adds unnecessary interaction complexity.

Inverse ablation shows:

- modality match is constant/redundant;
- sector match hurts generalization;
- dropping area destroys Lift@10;
- dropping attribute completeness destroys Lift@10 fold stability.

The final model is therefore the smallest stable candidate.

### Important downstream consequence

This recovery changes the conceptual Lead Quality architecture. Lead Quality now contains selected-Spot matching context that overlaps with the frozen Inventory construct.

Therefore the **Prompt-10 Opportunity Score is invalidated and must not be executed or interpreted as current** until the next integration step explicitly removes double counting. The Inventory contract itself remains unchanged; only its use in a combined score must be revisited.

The June procedural holdout remains sealed from this recovery and cannot be used to choose or validate the recovered champion.

### Target

Target remains:

`T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`

No target reopening or version change was needed.


## Prompt 11.6 downstream resolution

The downstream invalidation described above has now been resolved without reopening the recovery model.

- Inventory scalar remains frozen and unchanged.
- V1 `P_quality × InventoryServiceability` remains invalidated.
- Canonical integration is `OPPORTUNITY_ACTIONABILITY_GATE_V2_FROZEN_2026-08-30`.
- Capacity was recalculated on DEVELOPMENT OOF and frozen at P80/top 20%.
- Fallback list depth was revised independently to K=3.
- Final post-recovery red team: PASS, 0 blockers.
- June was not used for any of these selections.

Authority: `../../recovery_downstream/POST_RECOVERY_FINAL_STATE.json`.

**POST-RECOVERY SYSTEM FROZEN — CONTINUE TO PROMPT 12**
