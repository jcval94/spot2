# Opportunity Score outputs — post-recovery V2

Canonical committed product output:

- `scored_population.csv` — 5,000 T1 rows, recovered probabilities, V2 actionability gate, K=3 fallbacks, no outcomes.
- `priority_leads.csv` — exact top 20% of the current 5,000-row scoring batch using score-desc / lead_id-asc.
- `capacity_metrics.csv` — macro DEVELOPMENT temporal-OOF reevaluation for 5/10/15/20 and separated objectives.
- `gains_curve.csv` — macro fold-relative gains for recovered Lead Quality, V2 and the rejected raw multiplicative diagnostic.
- `score_distribution.csv`, `score_distribution_bins.csv`, `score_distribution_summary.csv` — rebuilt V2 distribution evidence.

The stale committed V1 Parquet materialization was removed deliberately. Running `build_score.py` in a project environment with Polars regenerates a V2 Parquet file from raw inputs; the committed CSV is the post-recovery product authority.

No product scoring table contains `broker_response`, target labels, `lead_score_internal` or other outcome-only fields.
