# Spot2 Final Assessment

This directory is the evaluator-facing entry point.

## Recommended reading order

### 1. Executive summary

Open:

`EXECUTIVE_ONE_PAGER.html`

For Markdown:

`EXECUTIVE_ONE_PAGER.md`

### 2. Presentation

Open:

`presentation/index.html`

It is standalone and requires no network dependencies.

### 3. Full assessment

Read:

`ASSESSMENT_REPORT.md`

### 4. Reproducible notebook

- `notebook/final_assessment.ipynb`
- `notebook/final_assessment.html`

The executable notebook reads frozen `AssessmentSol1/**` artifacts and contains assertions that reject stale pre-recovery authorities.

### 5. Reproduction instructions

`REPRODUCIBILITY.md`

### 6. Methodology defense

`FINAL_DEFENSE_QA.md`

### 7. Artifact/source map

`ARTIFACT_INDEX.md`

## Final system in one line

**T1 recovered Logistic Lead Quality + PIT Inventory actionability + K=3 fallback → Opportunity Score V2 → P80/top20.**

Production score:

`lead_quality_probability * inventory_actionability_gate`

This is an operational Opportunity Score, **not a jointly calibrated probability**.

## Frozen authority

- Lead Quality: `LQ_RECOVERY_R4_STATIC_MATCH_V1`
- Opportunity: `OPPORTUNITY_ACTIONABILITY_GATE_V2_FROZEN_2026-08-30`
- Capacity: P80 / top20 T1
- Fallback: K=3
- Audit: READY / 0 blockers
- LLM: sampled Inventory/Catalog QA discovery only

Machine-readable packaging snapshot:

`source_snapshot.json`

## Important use distinction

- maximize scheduled-visit progression regardless of inventory → **Lead Quality**
- prioritize progression + serviceability → **Opportunity Score**

## Status

Prompt 13 deliverables are built and Prompt 14 final review is complete.

Submission authority:
- `FINAL_REVIEW.md`
- `SUBMISSION_STATE.json`

**READY TO SUBMIT**
