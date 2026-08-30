# Features

No feature engineering optimization is performed in PROMPT 0.

This phase defines only information eligibility:

- known at score time;
- conditionally known if source immutability/effective time is proven;
- known but audit-only;
- blocked because future;
- blocked because effective-time semantics are unknown.

Learned encodings, clusters, target encodings and fitted preprocessing will be created later inside training folds only.
