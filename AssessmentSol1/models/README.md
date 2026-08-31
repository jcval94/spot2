# Models — current status after Lead Quality recovery

## T1 — principal Lead Quality

Current frozen champion: **`LQ_RECOVERY_R4_STATIC_MATCH_V1`**.

It is a small regularized Logistic ranking model with selected-Spot area closeness, geographic fit and attribute completeness. Calibration is RAW and Availability is excluded.

The original `models/lead_quality/**` Base-Rate champion is retained as historical Prompt-7 evidence. Current authority is `models/lead_quality_recovery/**`.

## T0 — cold start

Decision remains **NEUTRAL_EVIDENCE_BACKED**. No T0 predictive ranking model is promoted.

## T2 — re-scoring

Decision remains **FUTURE_EXTENSION**. No T2 predictive model is promoted.

## Product implication

T1 now has modest but usable ranking signal under the frozen recovery gate. It is not a high-separation classifier:
- top 5% remains weak;
- uncertainty is wide;
- June is not a pristine confirmation set.

Downstream integration is frozen in `../opportunity_score/` and `../recovery_downstream/`.
