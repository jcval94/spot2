# PROCEDURAL_HOLDOUT — diagnostic only, non-pristine

**Integrity status:** `CONSUMED_BY_METHOD_INCIDENT_BEFORE_FREEZE`.

The frozen champion was not changed after this diagnostic.

Mature June rows: **273** (17 additional June rows were censored by the frozen maturity rule).

Diagnostic metrics:
- prevalence: 0.19414
- predicted probability: 0.20375 for every row
- ROC AUC: 0.5000
- Average Precision: 0.19414
- Log Loss: 0.49246
- Brier: 0.15654

Lift@5/10/20 and Precision/Recall@top-k are stored for completeness, but because all probabilities tie, their values depend on deterministic row tie-breaking and **must not be interpreted as ranking performance**.

This slice cannot support a pristine procedural-final claim. True confirmation requires new or externally hidden data.
