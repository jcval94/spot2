# Leakage matrix

The executable policy is `config/feature_policy.yaml`; this table explains it.

| Feature/family | Source | Known at T1? | Risk | Clean action |
|---|---|---:|---:|---|
| Lead intake demographics, sector, modality, budgets, geography, source | leads | Yes | Low/drift | Allow |
| Prior counters/conversion | leads | Not demonstrated | Mutable aggregate | Conditional ablation only |
| `lead_score_internal` | leads | Unknown construction | Very high | Benchmark/stress only |
| Current inquiry payload | first inquiry | Yes | Low | Allow; ablate `asked_visit` |
| `Industrial AND (company_size=small OR source=paid)` | leads | Yes, all inputs at lead creation | Retrospective hypothesis / model-selection overfit | Allow for E113; promotion gate excludes holdout, but E115 requires forward confirmation |
| `broker_response`, `broker_response_hours` | inquiries | No | Direct leakage/broken clock | Block |
| Later inquiries/aggregates | inquiries | No | Direct future leakage | Block |
| Price, area, location and other listing fields | spots | Existence only is proven | No versioned updates | Conditional inventory analysis; strict PIT claim withheld |
| Mutable spot counters/status | spots | No | Current snapshot | Block |
| Physical attributes | attributes | Conditional on spot creation | No effective time | Inventory only |
| Availability state | snapshots | Yes if past | Temporal join | Backward as-of only; missing/stale becomes an uncertainty interval |
| Snapshot age | derived | Yes | Coverage-era proxy | Confidence/monitoring only |
| `competing_inquiries_30d` | snapshots | Unknown | Ambiguous window | Block |
| Market context | market panel | Publication unknown | High | EDA only |
| Clusters | derived | If fit in train | Fit leakage | Challenger/analysis only |
| LLM copy features | spot text | No historical versions | Look-ahead | Cross-sectional QA only |
