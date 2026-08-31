# Metric definitions and edge cases

AssessmentSol1 reports model metrics using temporal folds and preserves population labels.

## Ranking

- **ROC AUC:** pairwise ranking metric; a constant score is 0.5.
- **Average Precision (AP):** primary precision-recall summary used for model comparison.
- **PR-AUC:** trapezoidal area of the empirical PR curve only when at least two score values exist. For a constant score it is reported as undefined because linear interpolation can produce a misleading value near `(1 + prevalence)/2`.
- **Lift/Precision/Recall@k:** reported only when the score defines an ordering. They are undefined for Base Rate because all probabilities tie.

## Probability quality

- **Brier Score** and **Log Loss** remain fully valid for constant probabilities.
- **Calibration intercept:** for a constant score, reported as calibration-in-the-large correction.
- **Calibration slope:** undefined for a constant score because there is no score variation.

## Selection authority

AP, Brier/Log Loss and the pre-registered temporal protocol carry the T1 decision. Undefined tied-score ranking metrics never act as promotion gates.
