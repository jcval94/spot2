# E019 — Operational threshold + explicit Inventory Availability probability

## Decision

This experiment closes three assessment gaps:

1. operational capacity / threshold analysis;
2. final Lead Quality threshold policy;
3. an explicit, point-in-time `P(availability)` component.

The experiment does **not** change the frozen Lead Quality architecture. It consumes the OOF predictions from `modelo_3/trajectory_cv` and the candidate inventory tables.

## Final operational threshold

The final default capacity is **top 15% within stage** for T1 and T2.

Why:

- T1: Lift falls only from 1.126x at 10% to 1.122x at 15%, while recall increases from 11.4% to 17.0%.
- T2: Lift is effectively unchanged (1.457x at both 10% and 15%), while recall rises from 14.6% to 21.9%.
- T0 does not show useful ranking lift. It remains a monitoring score / standard queue, not a high-priority routing gate.

The threshold is a **stage-relative percentile**, not one raw probability constant. Raw-score cutoffs moved materially across temporal folds, so a fixed absolute threshold would be less robust.

Indicative median raw cutoffs corresponding to top 15%:

- T1: 0.488 (fold range 0.426–0.542).
- T2: 0.456 (fold range 0.376–0.533).

These raw values are diagnostic only. The production policy is P85 / top-15% within stage.

## Explicit P(availability)

At score time t, use only the latest availability snapshot with `snapshot_date <= t`.

For each spot:

- if it is available now: `p_spot_available_30d = 1`;
- if it is unavailable now: estimate the probability that it becomes available within 30 days from historical, already-matured unavailable observations in the same sector, shrunk toward the historical global unavailable-to-available transition rate;
- if no as-of snapshot exists: use the historical sector prior only as a low-confidence fallback and never represent the spot as confirmed available.

For a lead, build a point-in-time compatible candidate pool using the existing matching/fallback policy. Then:

`P(availability | lead, inventory_t) = max(p_spot_available_30d)`

over compatible candidates.

This max aggregation is deliberately conservative and does not assume independence between listings. A single strong compatible option is enough to make the lead serviceable.

## Availability validation

Availability is evaluated against an observable 30-day inventory target:

- success = spot is available at score time, or an observed future snapshot within 30 days is available;
- unavailable rows without a future snapshot inside the horizon are censored;
- training rows must have their 30-day label matured before the next test window begins.

4-fold expanding temporal validation:

- observable events: 17,323;
- macro AUC: **0.883**;
- macro Brier: **0.0669**;
- macro log-loss: **0.192**.

The high positive rate (~90%) is intrinsic to this synthetic inventory target and must be stated with the metrics.

## Important negative result

`days_until_available` was checked as a probability-shaping variable. Among currently unavailable spots, the observed 30-day availability rate stayed roughly flat across delay buckets. It is therefore not used to manufacture false probability precision in the final policy.

## Leakage

- OOF Lead Quality thresholds are computed inside temporal folds.
- Availability features use only backward-as-of snapshots.
- Future availability snapshots are used only to construct the evaluation label.
- Training availability labels are purged until their 30-day horizon has matured before each test window.
- No current `is_active` or future snapshot is used as a feature.

See `results/REPORT.md` and `EVIDENCIA.md`.
