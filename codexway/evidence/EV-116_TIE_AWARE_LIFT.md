# EV-116 — Tie-aware capacity Lift

## Question

Does the Lift > 1 conclusion survive when a capacity boundary cuts through a
group of leads with identical scores?

## Method

Capacity metrics select every row strictly above the score boundary and assign
the remaining slots fractionally across all rows tied at the boundary. Reported
precision, recall and Lift are therefore expected values under a fair random
tie-break and are invariant to input row order.

This changes evaluation only. The T1 contract, feature, model, target, temporal
split and strict backward as-of inventory join are unchanged.

On the retrospectively consumed procedural holdout, row-order-invariant Quality
Lift@10 is 1.689x with bootstrap IC95% [1.381, 1.982]. Conservative Opportunity
Lift@10 remains 1.370x [1.078, 1.690].

## Claim boundary

E116 removes arbitrary row order from the ranking metric. It does not restore a
pristine holdout: the data were already consumed globally. The result remains
retrospective and requires a new forward shadow cohort.
