# Freshness Policy

Freshness answers **how much confidence to place in the last known observation**. It does not redefine whether that observation was historically known.

A backward snapshot remains `availability_known=true` even when old. Only absence of a prior snapshot produces `UNKNOWN`. This corrects the superseded P3 behavior that treated >90-day observations as unknown.

## Frozen confidence mapping

| Snapshot age | Confidence |
|---|---:|
| no prior snapshot | 0.00 |
| <=7 days | 1.00 |
| <=30 days | 0.80 |
| <=90 days | 0.55 |
| >90 days | 0.30 |

The 30-day value is the default reporting lens, not a cutoff that turns older snapshots into unknown.

## DEVELOPMENT sensitivity

| Freshness view | Candidate coverage | Exact serviceability | Same-sector fallback | Tier-3-only | Leads with no fresh observation |
|---|---:|---:|---:|---:|---:|
| 7d | 19.94% | 37.16% | 14.17% | 30.93% | 1.01% |
| 30d | 54.97% | 61.42% | 13.30% | 20.44% | 0.43% |
| 90d | 83.84% | 69.18% | 11.93% | 15.32% | 0.43% |

Using every valid backward snapshot, regardless of age, 90.45% of DEVELOPMENT candidate rows have a prior snapshot. Exact serviceability is 70.47%, same-sector fallback 11.45%, Tier-3-only serviceability 14.54%, and 3.39% of leads have only viable candidates whose availability requires verification.

The strong temporal coverage growth is an inventory/instrumentation regime effect. It is a reason to expose confidence, not to leak later observations backward.

## Same-day caveat

`snapshot_date` is date-only. Same-day use follows the already documented business-date assumption. The earlier strict-previous-day sensitivity showed mild impact, but production should require an ingestion timestamp or documented publication SLA.
