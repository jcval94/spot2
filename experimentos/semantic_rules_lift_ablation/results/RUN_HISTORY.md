# E018 run history

## Run 33297469160 — SUPERSEDED FOR CONCLUSION

The first successful E018 execution trained the intended baseline and semantic-rule CatBoost models, but its report concatenated raw probabilities from independently trained temporal folds before calculating OOF ranking metrics.

Inspection showed material fold-to-fold probability-scale differences. Ranking a row from fold 1 directly against a row from fold 4 is not a valid Lift calculation when each prediction comes from a different model/calibration scale.

The model predictions and within-fold metrics remain useful diagnostics, but the global OOF ranking conclusion from that run is discarded.

## Corrected evaluation

E018 was changed so that:

1. Lift/AP/AUC are computed inside each temporal test fold;
2. fold metrics are averaged;
3. paired bootstrap resamples `lead_id` within each fold;
4. each bootstrap metric delta is computed within fold before aggregation;
5. raw scores from different fitted models are never rank-mixed.

## Run 33297920881 — AUTHORITATIVE

Status: **SUCCESS**

Artifact: `9728035555`

Conclusion: **NOT_SUPPORTED**

Primary result:

- baseline macro Lift@10%: 1.267x;
- semantic Rules macro Lift@10%: 1.196x;
- point delta: -0.0716x;
- paired-bootstrap 95% CI: [-0.1438, +0.1251];
- P(delta > 0): 45.0%.

The CI includes zero, so E018 does not prove that semantic Rules harm lift. It does fail the pre-declared promotion gate and provides no evidence that they improve lift.

All final E018 documentation uses this corrected run.
