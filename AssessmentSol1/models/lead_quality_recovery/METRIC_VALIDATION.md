# Metric and pipeline validation

## Result

**No ranking-metric bug found.**

The recovery did not modify Feature Engineering until these checks passed.

## Checks

| Check | Result | Evidence |
|---|---|---|
| higher score = higher predicted positive probability | PASS | Logistic score is sigmoid(logit); ranking sorts probability descending |
| Lift@5/10/20 formula | PASS | top ceil(N×X), precision in top-X divided by same-fold positive rate |
| base-rate denominator | PASS | computed separately inside each validation fold |
| target orientation | PASS | `scheduled_visit = 1`; every other observed response including `no_response = 0` |
| descending sorting | PASS | existing `evaluate.py` uses `np.argsort(-p, kind="mergesort")` |
| prediction/label alignment | PASS | one validation prediction per row; paired comparisons validate fold+lead one-to-one |
| duplicates | PASS | T1 modeling frame remains one row per lead |
| sample weights | PASS / NONE | Logistic and CatBoost P7 fits use no sample weights |
| calibration | PASS for ranking | prior RAW calibration is monotonic/no-op; recovered ranking uses RAW logistic output and does not reuse the old base-rate calibrator |
| split assignment | PASS | frozen calendar split and fold roles reused unchanged |
| OOF concatenation | PASS | selection authority is macro within-fold; no global cross-fold rank mixing |
| Logistic positive class | PASS | `predict_proba(...)[:, 1]` |
| CatBoost positive class | PASS | `predict_proba(...)[:, 1]` |
| CatBoost class weights / loss | PASS | no class weights; `loss_function=Logloss` |
| train/evaluation population | PASS | both use mature T1 DEVELOPMENT rows and identical fold roles |
| procedural holdout | NOT USED | recovery never opens June |

## Synthetic direction test

A synthetic 10-row population with two positives was used to validate directionality.

- perfect ranking at top 20%: **Lift = 5.0**
- inverted ranking at top 20%: **Lift = 0.0**

This confirms that the implementation produces >1 for concentration and <1 for inversion.

## Reconstruction correction during review

The first independent reconstruction temporarily omitted raw response category `no_response`. That was a reviewer-side reconstruction error, not a repository bug. The target contract treats any observed non-`scheduled_visit` response as negative. After restoring `no_response`, DEVELOPMENT returns to 4,368 rows and prevalence 0.20375458, matching the frozen pipeline.

## Ties

Discrete single-feature audits can have many ties and therefore are diagnostic only. Champion selection uses a multi-valued continuous score and fold-level metrics, not a tie-heavy single-feature ranking.
