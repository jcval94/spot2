# P8_NUMERICAL_INCIDENT

The first execution bridge used a provisional diagonal Newton-style logistic optimizer. It produced proper scoring values that were incompatible with the near-random ranking metrics, indicating overly extreme probabilities and numerical instability.

That run was **discarded before stage decisions were documented**.

The frozen experiment design was not changed:
- same target definitions;
- same temporal folds;
- same T0 intake-only information set;
- same T2 baseline;
- same registered trajectory family;
- no new model family or feature search.

The exact same comparison was re-executed with a conservative fixed L2 FTRL logistic optimizer. Final persisted metrics come only from the stable run.

This is classified as a numerical implementation bug, not a performance-driven exception.
