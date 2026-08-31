# Final Artifact Index

## Current frozen authority

- Lead Quality: `LQ_RECOVERY_R4_STATIC_MATCH_V1`
- Opportunity: `OPPORTUNITY_ACTIONABILITY_GATE_V2_FROZEN_2026-08-30`
- Formula: `lead_quality_probability * inventory_actionability_gate`
- Capacity: `P80 / top 20% within T1`
- Fallback: `K=3`


Opportunity Score is an operational prioritization score, **not a jointly calibrated probability**.

## Start here

1. **Executive one-pager**
   - `EXECUTIVE_ONE_PAGER.html`
   - `EXECUTIVE_ONE_PAGER.md`

2. **Presentation**
   - `presentation/index.html`

3. **Final notebook**
   - `notebook/final_assessment.ipynb`
   - `notebook/final_assessment.html`

4. **Assessment Report**
   - `ASSESSMENT_REPORT.md`

5. **Reproducibility**
   - `REPRODUCIBILITY.md`

6. **Methodology defense**
   - `FINAL_DEFENSE_QA.md`

## Frozen source snapshot

`source_snapshot.json`

This packages the exact final authorities and headline metrics used by the final deliverables.

## Primary source-of-truth artifacts

| Domain | Artifact |
|---|---|
| Target | `../target/TARGET_DECISION.md` |
| Split | `../splits/SPLIT_CONTRACT.md` |
| Recovery decision | `../models/lead_quality_recovery/RECOVERY_DECISION.md` |
| Lead Quality config | `../models/lead_quality_recovery/frozen_recovered_model_config.json` |
| Post-recovery state | `../recovery_downstream/POST_RECOVERY_FINAL_STATE.json` |
| Capacity re-evaluation | `../recovery_downstream/CAPACITY_REEVALUATION.csv` |
| End-to-end re-evaluation | `../recovery_downstream/END_TO_END_REEVALUATION.csv` |
| Inventory config | `../inventory/frozen_inventory_config.json` |
| Fallback policy | `../inventory/FALLBACK_POLICY.md` |
| Opportunity config | `../opportunity_score/frozen_score_config.json` |
| Final leakage audit | `../audit/final_audit.json` |
| LLM decision | `../llm/LLM_DECISION.md` |
| LLM gate | `../llm/results/prompt12_gate.json` |

## Evidence classification

Final deliverables use four provenance labels conceptually:

- **ASSESSMENTSOL1_FROZEN** — canonical frozen clean-room authority.
- **ASSESSMENTSOL1_REPRODUCED** — a clean-room diagnostic/reproduction derived inside AssessmentSol1.
- **UPSTREAM_SUPPORTING** — historical experiment evidence used only for context.
- **DIAGNOSTIC_ONLY** — useful to explain a rejected path, never current production authority.

## Closed historical lines

- E018 Semantic Rules → supporting decision only; final role = Inventory/Catalog QA.
- E019 P85/top15 → supporting history only; final capacity = P80/top20.
- E020 continuous/product integration → supporting history only; final score = Opportunity V2 actionability gate.
- Matching/clusters → auxiliary.
- Response-time RF → diagnostic only.

## Packaging prompts

- `PROMPT_13_FINAL_ASSESSMENT.md`
- `PROMPT_14_FINAL_REVIEW.md`
