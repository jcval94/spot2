# T1 model card

## Intended use

Rank one lead at its first inquiry, before broker response. This is a first-contact
progress proxy, not true conversion probability.

## Model

Selected by the E113 rolling-CV/validation promotion gate:
**stable_segment_logistic**. Calibration decision:
`True`. The feature hypothesis is retrospective
because the historical holdout had already been globally consumed; E115 requires
new forward confirmation.

Offline ranking gate: **GO**. The score artifact is
generated for reproducibility, but must not automate routing when this gate fails.

## Procedural holdout

- ROC-AUC: 0.5478
- ROC-AUC bootstrap 95% CI: [0.5273, 0.5684]
- PR-AUC: 0.2391
- Log Loss: 0.5129
- Brier: 0.1658
- Recall@5/10/20%: 0.085 / 0.170 / 0.268
- Lift@5/10%: 1.689 / 1.689

## Non-negotiable exclusions

Broker response/time, internal score, future inquiries, mutable spot counters,
future/nearest snapshots, market context and LLM text features.

## System-level decision

Combined Opportunity gate: **GO**.
The conservative combination has AP 0.2477
versus 0.2391 for Lead Quality.
It remains diagnostic because the observed T1 target does not measure fallback success.

## Limitations

Synthetic/small data, imperfect outcome proxy, globally consumed historical
holdout, unversioned listing state and observational offline evaluation. A GO is
eligibility for new forward validation, not permission for automatic deployment.
