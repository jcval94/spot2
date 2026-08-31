# Splits

No final test is opened in PROMPT 0.

Rules for later phases:

- split by lead/entity where repeated snapshots exist;
- preserve temporal order;
- fit learned transformations only on training folds;
- do not mix probabilities from independently trained folds into a single global rank unless calibration/metric semantics justify it;
- label already-inspected historical slices as development or **procedural final holdout**, not pristine unseen;
- true confirmation requires new/hidden data.
