# T0 Cold Start — PROMPT 8

Decision: **NEUTRAL_EVIDENCE_BACKED**.

T0 scores at `leads.created_at` and predicts `T0_30D_INQUIRY_INITIATION_PROGRESS_V1`.

**T0 and T1 probabilities estimate different quantities.**

Only intake-time lead information was allowed. Inquiry payload, requested Spot, Availability, outcomes, current-state Spot fields, `lead_score_internal`, and unproven historical counters were not predictors.

The fixed L2 Logistic does not beat the fold-specific Base Rate defensibly:
- macro AP: 0.4803 → 0.4831 (+0.0028);
- macro AUC: 0.5000 → 0.4934;
- Brier: 0.2631 → 0.2665;
- Log Loss: 0.7207 → 0.7294.

No T0 discriminative model is recommended. T0 can provide only a cold-start prior / uncertainty state until better intake information exists.

See `../../evidence/T0_EXPOSURE_DRIFT.md`.
