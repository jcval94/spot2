# Leakage stress tests

This directory is deliberately unsafe research evidence. Nothing here is deployable and nothing here may be imported by the product pipeline.

The clean harness in `../harness.py` rejects all three specs in product mode.

- **S001:** raw `lead_score_internal`; unknown generation time/inputs.
- **S002:** pre-registered future-inquiry score `future_inquiry_count + 2*any_future_asked_visit`. It deliberately uses only later inquiries; no future response outcome is needed to create leakage.
- **S003:** nearest Availability snapshot instead of backward-as-of; equal-distance ties prefer the later snapshot.

All use the frozen T1 DEVELOPMENT population and the same capacity evaluation. Results are pedagogical only and are forbidden from feature engineering, model selection, calibration, Inventory policy or Opportunity Score tuning.

The exact metrics frozen for Prompt 11 are in `stress_metrics.csv`.
