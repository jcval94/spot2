# Opportunity Score outputs

Canonical product outputs:

- `scored_population.csv` — 5,000 T1 product rows, no target/outcome columns.
- `scored_population.parquet` — same 5,000-row product table, Parquet PLAIN/uncompressed materialization.
- `priority_leads.csv` — rows assigned PRIORITY or HIGH under frozen thresholds.
- `capacity_metrics.csv` — DEVELOPMENT and post-freeze June diagnostic Top 5/10/20 metrics for Lead Quality, Inventory, Opportunity and the non-deployable internal reference.
- `gains_curve.csv` — cumulative gains data from 1–100% capacity for Inventory and Opportunity.
- `score_distribution_summary.csv` and `score_distribution_bins.csv` — distribution evidence.

The product scoring tables never contain `broker_response`, target labels or hidden outcomes.

The Parquet file is intentionally simple: one row group, PLAIN encoding, no compression. The canonical executable `build_score.py` also writes both CSV and Parquet when run in the project environment.
