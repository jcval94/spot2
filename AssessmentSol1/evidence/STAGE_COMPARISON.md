# STAGE_COMPARISON

| Stage | Scoring time | Question predicted | Target | Features available | Model / decision | Development performance | Operational use | Limitations |
|---|---|---|---|---|---|---|---|---|
| **T0** | `lead.created_at` | Will a lead generate a 30d inquiry that eventually becomes scheduled_visit? | `T0_30D_INQUIRY_INITIATION_PROGRESS_V1` | Intake only | **NEUTRAL_EVIDENCE_BACKED**; no discriminative model | Logistic AUC 0.495, AP 0.486 vs base AP 0.480 | Population planning prior only | Strong exposure drift; target depends on future opportunity to inquire |
| **T1 — PRINCIPAL** | deterministic first `inquiry_at` | Will this first inquiry eventually be recorded as scheduled_visit? | `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1` | Intake + current inquiry under frozen T1 information set | **BASE_RATE + RAW**, frozen | Learned challengers did not beat the simple prior defensibly | Principal Lead Quality contract; neutral probability prior | No individual ranking capability; scheduled_visit is a proxy |
| **T2** | current second+ `inquiry_at` | Will this current later inquiry eventually be recorded as scheduled_visit, conditional on valid stage membership? | `T2_CURRENT_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1` | Current request + strict-prior request trajectory | **FUTURE_EXTENSION** | Trajectory AP 0.190 vs baseline 0.186; ΔAP +0.0032, 2/4 positive folds | Do not deploy currently | Conditional population, cohort-gate ambiguity, incremental value unstable |

## Product hierarchy

**T1 remains the principal product contract.**

However, current evidence does not support a learned lead-level ranking model at any stage:

- **T0:** do not deploy a discriminative predictor.
- **T1:** retain the frozen base-rate prior; do not present it as ranking.
- **T2:** do not deploy trajectory re-scoring; keep as future extension.

T0, T1 and T2 are not averaged.

**T0 and T1 probabilities estimate different quantities.** T2 also conditions on reaching a later stage and therefore its probability is not directly comparable with the unconditional lead population.

The next assessment value should come from the independent Inventory / serviceability / Opportunity layer rather than continuing to search for hidden LeadQuality lift.
