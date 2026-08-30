# EV-019 — Operational threshold and explicit availability probability

**Estado de evidencia:** SUPPORTED / DECISION-READY para los tres gaps solicitados.

**Experimento:** [E019_operational_threshold_availability](../E019_operational_threshold_availability/)

## Evidencia fuente

- [Operational report](../E019_operational_threshold_availability/results/REPORT.md)
- [Threshold frontier](../E019_operational_threshold_availability/results/threshold_frontier.csv)
- [Availability temporal CV](../E019_operational_threshold_availability/results/availability_cv_metrics.csv)
- [Availability delay diagnostic](../E019_operational_threshold_availability/results/availability_delay_buckets.csv)
- [Decision summary](../E019_operational_threshold_availability/results/summary.json)
- [Runner](../E019_operational_threshold_availability/run_experiment.py)
- Upstream Lead Quality OOF predictions: [trajectory CV](../modelo_3/trajectory_cv/results/oof_predictions.csv)

## Threshold / capacity

Using pooled CatBoost + trajectory OOF scores, with ranking computed independently inside fold and stage:

### T1

- top 10%: Lift 1.126x; Recall 11.4%;
- **top 15%: Lift 1.122x; Recall 17.0%**;
- top 20%: Lift 1.094x; Recall 22.0%.

### T2

- top 10%: Lift 1.457x; Recall 14.6%;
- **top 15%: Lift 1.457x; Recall 21.9%**;
- top 20%: Lift 1.428x; Recall 28.6%.

### T0

Lift remains approximately 1.0 across the capacity frontier. No high-priority gate is justified at T0.

## Frozen operational policy

- T0: no high-priority threshold; standard queue / monitoring score.
- T1: prioritize top 15% within stage.
- T2: prioritize top 15% within stage.
- final threshold representation: **stage-relative P85**, not a fixed raw probability.

Indicative median raw P85 cutoffs are 0.488 for T1 and 0.456 for T2, but fold ranges are wide enough that these values are not frozen for deployment.

## Explicit P(availability)

Candidate-level definition:

1. use the latest availability snapshot at or before score time;
2. if currently available, probability is 1;
3. if currently unavailable, use the historically observed 30-day transition probability for unavailable spots in the same sector, estimated only from matured past labels and shrunk toward the global historical rate;
4. missing as-of snapshots use only a low-confidence historical prior and are never represented as confirmed available.

Lead-level serviceability:

`P_availability(lead,t) = max p_spot_available_30d`

over the compatible fallback pool.

The max operator is used to avoid an unsupported independence assumption across listings.

## Availability validation

Target: spot is available at score time or observed available in a future snapshot within 30 days.

Currently unavailable rows without any future snapshot in the 30-day window are censored.

4-fold expanding temporal validation uses `label_mature_at < test_start`, creating the required 30-day maturation purge.

- observable events: 17,323;
- macro AUC: **0.8827**;
- macro Brier: **0.06687**;
- macro log-loss: **0.19195**;
- backward-as-of coverage: **92.38%**;
- coverage with lag <=90 days: **88.51%**.

## Negative result retained

For currently unavailable spots, observed 30-day availability is roughly flat across `days_until_available` buckets:

- 1–7: 66.5%;
- 8–14: 67.0%;
- 15–30: 64.3%;
- 31–60: 69.3%;
- >60: 67.7%.

Therefore the final probability does not impose an artificial monotonic decay from this field.

## Leakage

- Lead Quality ranking is within temporal fold and stage.
- Availability feature state is backward-as-of only.
- Future snapshots define y only.
- Availability calibration history is purged until the 30-day label is mature.
- Current `is_active` is not used.

**LEAKAGE_CHECK = PASS**

## What this proves

- the operational capacity/threshold question is decision-ready;
- the final threshold is top 15% at T1/T2;
- Inventory Availability now has an explicit, temporally validated probability definition.

## What this does not prove

- that 15% is the only valid staffing capacity if Growth later provides a hard operational limit;
- that the availability probability is causal;
- that the complete Lead Opportunity Score formula or fallback @K performance is already closed.

Related discoveries: D062 and D063 in [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
