# Accepted decisions

These decisions survive the clean-room review as principles, not copied fitted state.

1. **Scoring is dynamic.** T0, T1 and T2 have different information sets and exact score times.
2. **Point-in-time joins are mandatory.** Availability uses only snapshots dated at or before scoring.
3. **Mutable current-state fields are unsafe historically.** Reconstruct them from event history or block them.
4. **Current broker response is future information.** Only previously realized response events can enter historical summaries.
5. **Unknown event timing stays unknown.** Ambiguous scheduled visits are not negatives; immature windows are right-censored.
6. **Market Context is blocked until an effective/publication time is defensible.**
7. **Known does not mean model-eligible.** Calendar/progress clocks can be known at score time and still remain audit-only because of synthetic drift/proxy behavior.
8. **Availability is primarily serviceability/freshness context**, not automatically a LeadQuality feature.
9. **Research history is contaminated by iterative inspection.** Historical tests can support engineering decisions but are not pristine unseen confirmation.
10. **Rules before LLM.** Structured/deterministic signals should not incur LLM cost or nondeterminism.
11. **Spot Attributes immutability assumption.** For the definitive assessment, `spot_attributes` values are explicitly assumed immutable over the life of a Spot and may be used at T1/T2 when `spots.created_at <= score_time`. This is a declared AssessmentSol1 modeling assumption, not a guarantee stated in the original assessment and not a timestamp inferred from raw data.

All accepted logic must be reimplemented inside AssessmentSol1 and rerun from raw data when its phase arrives.
