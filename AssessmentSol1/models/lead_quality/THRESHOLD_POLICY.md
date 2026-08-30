# THRESHOLD_POLICY — T1 Lead Quality

Frozen champion: **BASE_RATE + RAW**.

Every T1 row receives the same probability:

`p = 0.2037545788`.

## Threshold analysis

A scalar cutoff cannot rank or selectively prioritize leads:

- threshold < 0.2037546 → effectively all leads pass;
- threshold > 0.2037546 → no leads pass;
- threshold == 0.2037546 → outcome depends only on the comparison operator, not on lead quality.

Therefore there is **no evidence-backed LeadQuality cutoff** in AssessmentSol1.

This is the correct threshold-analysis conclusion for a constant champion. Creating an arbitrary 0.5, 0.2 or top-k cutoff would manufacture discrimination that the model does not possess.

## Operational implication

If Growth has finite capacity before a stronger lead-level signal exists:

1. do not use arbitrary row-order tie-breaking;
2. use the later Inventory/Opportunity layer to distinguish serviceable opportunities when defensible;
3. otherwise use a transparent non-model policy such as FIFO/randomized allocation or explicit business constraints.

Any future threshold must be justified from business costs/capacity and validated on genuinely new/hidden evidence.
