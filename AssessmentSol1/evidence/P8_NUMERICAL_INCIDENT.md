# P8_NUMERICAL_INCIDENT — optimizer QA

During the first P8 execution, a custom diagonal-Newton approximation produced implausibly extreme probabilities: Log Loss and Brier degraded sharply while ranking metrics stayed near random.

This was treated as an **implementation bug**, not evidence against the model hypothesis.

No target, feature set, split, model family or promotion rule changed.

The same frozen L2 Logistic comparisons were rerun with a stable fixed FTRL optimizer. Only the second execution is authoritative.

Authoritative solver settings:
- model family: Logistic;
- penalty: L2;
- regularization: fixed;
- optimizer: FTRL;
- optimizer settings chosen for numerical stability, not tuned on validation performance.

The stable rerun produced sane probability scores close to the base rates and is the source for all committed P8 metrics.
