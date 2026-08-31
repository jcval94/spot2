# Lead Opportunity Score — frozen Prompt 10

The final T1 product score is now constructed from the two independently frozen components:

```
OpportunityScore = P(LeadQuality) × InventoryServiceability
PublishedScore = 100 × OpportunityScore
```

The frozen Lead Quality champion is `BASE_RATE + RAW` with probability `0.20375457875457875` and no model features. The selected-Spot-context Ablation E remains challenger-only and is not used, so the primary score does not double count Inventory/Matching information.

The frozen Inventory authority is `INV_SERVICEABILITY_V1_FROZEN_2026-08-30`.

## Important interpretation

Because Lead Quality is a positive constant, Opportunity Score and Inventory Serviceability have identical ranking order. The multiplicative score preserves the requested product decomposition but does not create additional ranking power.

DEVELOPMENT does not demonstrate enrichment of observed positives:

- top 5%: 39 / 890 positives captured; Recall 4.38%; Lift 0.87x;
- top 10%: 87 / 890; Recall 9.78%; Lift 0.98x;
- top 20%: 179 / 890; Recall 20.11%; Lift 1.01x.

The default top-10% capacity is an explicit operational assumption, not an optimum.

The post-freeze June diagnostic is also negative and is documented in `POST_FREEZE_HOLDOUT.md`. It did not change formula, thresholds, bands, model, Inventory or fallback policy.

## Canonical files

- `SCORE_CONTRACT.md`
- `DECISION_POLICY.md`
- `frozen_score_config.json`
- `build_score.py`
- `evaluate_score.py`
- `POST_FREEZE_HOLDOUT.md`
- `outputs/`
- `examples/`
- `figures/`

The main product table is available as both `outputs/scored_population.csv` and `outputs/scored_population.parquet`, one T1 row per lead. Product rows contain no target or broker-response field.

`priority_leads.csv` contains PRIORITY + HIGH under the frozen DEVELOPMENT+CALIBRATION thresholds. `capacity_metrics.csv` and `gains_curve.csv` contain the capacity evaluation.

The score configuration was frozen before the procedural-holdout diagnostic and must not be changed because of June results.
