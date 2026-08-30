# Rejected decisions

## Runtime reuse

Reject direct use of any historical ABT, OOF prediction, model, preprocessor, scaler, calibrator, clusterer, target encoder or fitted artifact.

## Leakage / temporal semantics

Reject:

- current `broker_response` or `broker_response_hours` as predictors;
- `lead_score_internal`;
- raw historical `days_on_market`, `total_inquiries`, `total_views`, `is_active`;
- forward/nearest Availability joins that can select a future snapshot;
- Market Context joins without a defensible publication/effective-time contract;
- treating missing scheduled-visit event time as a negative label.

## Research conclusions not promoted

Reject as default LeadQuality features:

- `prior_searches`;
- broker prior/rate;
- Behavioral Persona replacement;
- Broker Supply clusters;
- Inquiry Intent v1;
- deterministic semantic listing Rules after E018 failed the Lift@10% promotion gate;
- any `llm_*` listing-copy feature from E017.

These negative decisions are evidence-backed for the current data/research history. A materially new information source or truly new cohort can justify a new hypothesis later.
