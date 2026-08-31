# Reproducibility — Final Assessment

## Scope

The final assessment is self-contained under `AssessmentSol1/**`.

Runtime code must not import fitted artifacts or executable dependencies from `experimentos/**`.

## Authoritative state

Before running anything, verify:

```text
Lead Quality   LQ_RECOVERY_R4_STATIC_MATCH_V1
Opportunity    OPPORTUNITY_ACTIONABILITY_GATE_V2_FROZEN_2026-08-30
Formula        lead_quality_probability * inventory_actionability_gate
Capacity       P80 / top 20% within T1
Fallback       K=3
Final audit    READY / 0 blockers
LLM gate       PASS
```

Machine-readable consolidated snapshot:

`AssessmentSol1/final/source_snapshot.json`

## Python environment

The project dependency declaration is:

`AssessmentSol1/pyproject.toml`

Recommended from repository root:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e AssessmentSol1
```

If the project uses an existing managed environment, use that environment instead of changing dependency versions during final evaluation.

## 1. Run final tests

From repository root:

```bash
pytest -q AssessmentSol1/tests
```

Important:

The active ChatGPT/GitHub editing environment used for Prompt 13 does not expose a checked-out repository runtime, so this exact pytest invocation was **not** executed during packaging. The post-recovery audit instead remains the authoritative executed validation record:

`AssessmentSol1/audit/final_audit.json`

Do not replace this caveat with an invented test PASS.

## 2. Rebuild the main Opportunity Score

The scoring subsystem has no LLM dependency.

```bash
python AssessmentSol1/opportunity_score/build_score.py
python AssessmentSol1/opportunity_score/evaluate_score.py
```

Expected frozen config:

`AssessmentSol1/opportunity_score/frozen_score_config.json`

The formula must remain:

```text
lead_quality_probability * inventory_actionability_gate
```

If an output uses the old continuous multiplication `lead_quality_probability * inventory_serviceability`, stop: that is a stale V1/diagnostic artifact.

## 3. Validate Lead Quality authority

Recovery config:

`AssessmentSol1/models/lead_quality_recovery/frozen_recovered_model_config.json`

Recovery decision:

`AssessmentSol1/models/lead_quality_recovery/RECOVERY_DECISION.md`

The final champion must be:

`LQ_RECOVERY_R4_STATIC_MATCH_V1`

Do not use the old Base Rate state as the final model.

## 4. Capacity evidence

Frozen final frontier:

`AssessmentSol1/opportunity_score/outputs/capacity_metrics.csv`

Expected DEVELOPMENT OOF macro Lift:

| Capacity | Lift |
|---:|---:|
| 5% | 0.8593 |
| 10% | 1.0754 |
| 15% | 1.0841 |
| 20% | 1.1243 |

Selected:

`P80 / top 20% within T1`

## 5. Inventory and fallback

Config:

`AssessmentSol1/inventory/frozen_inventory_config.json`

Expected:
- backward as-of availability;
- K=3;
- `NO_RESULT` allowed;
- no fallback list longer than 3.

## 6. LLM audit reproduction

The score does not require this step.

Deterministic Rules-first reproduction:

```bash
python AssessmentSol1/llm/run_llm_audit.py --mode rules
```

This performs no OpenAI API call.

A paid live rerun is not required for the assessment.

## 7. Notebook

Open:

`AssessmentSol1/final/notebook/final_assessment.ipynb`

The notebook contains strict assertions for:
- recovered champion;
- target;
- Opportunity V2;
- P80/top20;
- K=3;
- final audit READY;
- LLM PASS.

A rendered standalone companion is:

`AssessmentSol1/final/notebook/final_assessment.html`

## 8. Presentation

Standalone HTML:

`AssessmentSol1/final/presentation/index.html`

No external JavaScript, font, image or network dependency is required.

Keyboard:
- Right / Page Down / Space → next
- Left / Page Up → previous

## 9. Stale-result guard

Any final deliverable containing one of the following as current authority must be treated as stale:

- Base Rate as final Lead Quality champion;
- CatBoost as final champion;
- Opportunity Score V1;
- continuous `P_quality × InventoryServiceability` as production formula;
- P85/top15 as final capacity;
- fallback K other than 3;
- Semantic Rules as Lead Quality features.

Historical references are allowed only when clearly labeled as historical/supporting/diagnostic.

## 10. Source-of-truth order

When values conflict, use this priority:

1. `AssessmentSol1/recovery_downstream/POST_RECOVERY_FINAL_STATE.json`
2. frozen Lead Quality / Inventory / Opportunity configs under `AssessmentSol1/**`
3. `AssessmentSol1/audit/final_audit.json`
4. post-recovery output CSVs under `AssessmentSol1/**`
5. `AssessmentSol1/final/source_snapshot.json` as packaging snapshot
6. upstream historical experiment evidence only for context

AssessmentSol1 always wins over unreproduced E018/E019/E020 historical metrics.
