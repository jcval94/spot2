# EV-117 — Forward-candidate gate under temporal variance

## Decision

The stable-segment Logistic may enter a new forward shadow cohort when all of
the following hold on train/validation evidence:

- mean rolling Lift@10 is above 1;
- median rolling Lift@10 is above 1;
- at least two of four rolling folds are above 1;
- fixed-validation Lift@10 is above 1;
- validation Brier stays within the configured tolerance of the constant model.

This is a candidate-selection gate, not a deployment gate. Two rolling folds are
below random and the historical holdout was globally consumed. Only new forward
data can confirm temporal persistence.

## Why not add more features

The bounded train/validation search tested small additions to the clean segment
(current inquiry intent, urgency, source, modality and timing). None raised the
fold-count stability beyond two of four. The solution therefore keeps the single
interpretable T0-safe interaction instead of promoting extra variance.
