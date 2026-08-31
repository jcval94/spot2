# Procedural holdout governance after Lead Quality recovery

## Status: SUPERSEDED AS CURRENT SCORE EVIDENCE

The old Prompt-10 June diagnostic belonged to the Base-Rate / multiplicative V1 architecture. Its numeric results are historical only and **must not be interpreted as post-recovery V2 performance**.

Prompt 11.6 deliberately did **not** reopen or reuse June to select:

- `LQ_RECOVERY_R4_STATIC_MATCH_V1`;
- Opportunity Score V2;
- P80 / top-20 capacity;
- K=3 fallback.

June remains `DIAGNOSTIC_ONLY_NON_PRISTINE` because of the previously documented procedural-holdout incident. Re-consuming it while rebuilding downstream would create a second policy-selection path through a contaminated holdout.

The authoritative post-recovery evidence is DEVELOPMENT temporal OOF under `AssessmentSol1/recovery_downstream/`.

Any future post-recovery confirmation must use genuinely new/hidden data. No post-recovery formula, capacity or fallback change may be justified from the old June diagnostic.
