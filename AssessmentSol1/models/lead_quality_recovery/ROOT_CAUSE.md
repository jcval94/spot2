# Lead Quality recovery — root cause

## Conclusion

The previous `BASE_RATE + RAW` champion was not caused by an inverted target, Lift bug, prediction/label misalignment or cross-fold leakage.

The main issue was an **objective / information-set mismatch**:

1. P7 correctly optimized a probability-quality promotion rule dominated by AP uncertainty and Brier. Under that rule the learned models were not defensibly better than Base Rate.
2. Prompt 11.5 changes the operational gate: a Lead Quality model must provide useful **ranking concentration** at top 10% / 20%.
3. Lead-only and broad Lead+Inquiry sets are weak and temporally unstable. Adding more of them frequently dilutes ranking.
4. The original selected-Spot challenger E contained backward Availability. It showed some ranking signal, but Availability is explicitly forbidden in this recovery Lead Quality construct.
5. Rebuilding the selected-Spot challenger using only static/PIT-defensible matching information preserves signal without Availability.
6. Inverse ablation shows `sector_match` hurts ranking generalization and `modality_match` is constant (=1) for the selected T1 Spot and therefore redundant.

## Recovered signal

The smallest stable candidate uses only:

- `selected_spot_area_closeness`;
- `selected_spot_geographic_fit`;
- `selected_spot_attribute_completeness`.

All derive from the current inquiry's selected Spot, which is known at T1, subject to the existing Spot-existence and attribute-immutability contracts.

No Availability, current-state Spot field, current/unversioned price, future event, Market Context or internal score is used.

## Why the sign can look counter-intuitive

The recovered full-development coefficients are negative for these three compatibility descriptors. That does **not** mean poor fit causes conversion. The target is the `scheduled_visit` proxy, not commercial conversion, and the coefficients are predictive associations conditional on this data. A plausible process explanation is that imperfect fit can trigger broker follow-up / visit scheduling, but that explanation is **not proven** and is not used to justify the model.

## FEATURE_FAMILY_HURTING_GENERALIZATION

`selected_spot_sector_match` is explicitly classified:

**FEATURE_FAMILY_HURTING_GENERALIZATION**

Removing it changes macro Lift@10 from 1.0374 to 1.0754 and produces Lift@10 > 1 in 4/4 folds. AP decreases only from 0.22038 to 0.21861 and remains above the macro base-rate AP benchmark 0.20833.

`modality_match` is not classified as harmful; it is simply constant and redundant.

## Target decision

The frozen target remains methodologically coherent enough for ranking recovery. No target reopening is needed because R4 passes the recovery gate using temporally valid information.
