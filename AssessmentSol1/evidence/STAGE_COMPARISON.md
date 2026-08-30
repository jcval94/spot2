# STAGE_COMPARISON — T0 vs T1 vs T2

The three stages answer different questions and must never be averaged as interchangeable probabilities.

| Stage | Scoring time | Question predicted | Target | Features available | Frozen model / decision | Performance summary | Operational use | Main limitation |
|---|---|---|---|---|---|---|---|---|
| T0 | `lead.created_at` | Will the lead initiate a successful inquiry within the next 30d? | `T0_30D_INQUIRY_INITIATION_PROGRESS_V1` | Intake only | **NEUTRAL_EVIDENCE_BACKED**; Base Rate preferred to intake Logistic | Logistic macro AUC 0.493, AP 0.483 vs Base Rate AP 0.480 | Cold-start prior / uncertainty state only | Target strongly moves with future inquiry exposure; different estimand from T1 |
| T1 | deterministic first `inquiry_at` | Will this first inquiry eventually be recorded as scheduled_visit? | `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1` | Intake + current request are observable, but learned ranking was rejected | **Principal product: BASE_RATE + RAW**, p=0.2037546 | Learned challengers failed frozen promotion; champion AUC=0.5 and no ranking | Main Lead Quality probability prior; combine later with independent Inventory serviceability | Proxy outcome; no individual ranking signal; June holdout non-pristine |
| T2 | current second-or-later `inquiry_at` | Will this current T2 inquiry eventually be recorded as scheduled_visit, conditional on valid stage membership? | `T2_CURRENT_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1` | Current payload + strict-prior request trajectory | **FUTURE_EXTENSION** | AP 0.1807 baseline → 0.1857 trajectory (+0.0050); 3/4 folds positive but below gate | Do not deploy now; retain for future re-scoring research | Conditional population, cohort gate ambiguity, small unstable incremental value |

## Product conclusion

**T1 remains the principal Lead Quality product.**

That does not mean T1 currently provides ranking. Its evidence-backed output is a neutral probability prior. The eventual business prioritization must come from the separate Inventory Serviceability / Matching / Opportunity layer rather than manufacturing lead-level discrimination.

### What T0 adds
A legitimate score at lead creation, but currently only as a cold-start prior. It should **not** deploy a discriminative model.

### What T2 adds
A temporally valid framework for later re-scoring and weak evidence that request trajectory can matter. The incremental value is too small for deployment today.

### Stages that should not deploy a predictive ranking model
- **T0:** no;
- **T1:** no ranking model — only the frozen prior;
- **T2:** no, FUTURE_EXTENSION.

T0/T1 probabilities are explicitly non-equivalent because their targets differ. T1/T2 share the current-inquiry outcome definition but condition on different stage populations, so their probabilities are also not interchangeable.
