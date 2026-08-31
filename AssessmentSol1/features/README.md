# Feature Engineering — current status

P5–6 is complete.

Authoritative feature governance:
- `FEATURE_REGISTRY.csv` — 129 registered entries;
- `feature_groups.json`;
- `ablation_plan.json`;
- `FEATURE_POLICY.md`;
- `STAGE_POLICY.md`.

T1 core is intake + current inquiry + deterministic refinement only. Matching/Inventory stay separate except the pre-registered E challenger. T2 trajectory contains strict-prior request history only.

Any learned transform must fit inside TRAIN folds. `llm_*`, response fields, Market Context, unproven historical counters and other forbidden fields cannot enter modeling.

See `evidence/PRE_P8_AUDIT.md` for the latest reconciliation.
