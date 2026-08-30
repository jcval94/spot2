# E037 — Temporal smoothed categorical priors

**Development only; target encoding is fit strictly on prior fold train.**

| stage            | variant         |   folds |   mean_auc |   min_auc |   mean_ap_over_prevalence |   min_ap_over_prevalence |   mean_lift10 |   min_lift10 |   folds_auc_gt_05 | status          |
|:-----------------|:----------------|--------:|-----------:|----------:|--------------------------:|-------------------------:|--------------:|-------------:|------------------:|:----------------|
| T0_cold          | atomic          |       3 |   0.488814 |  0.459936 |                  0.980863 |                 0.904143 |      0.956721 |     0.740741 |                 1 | NO_DEV_SIGNAL   |
| T0_cold          | te_interactions |       3 |   0.497702 |  0.486204 |                  0.9948   |                 0.952464 |      0.97519  |     0.8      |                 1 | NO_DEV_SIGNAL   |
| T0_cold          | te_marginals    |       3 |   0.498236 |  0.477564 |                  0.995084 |                 0.962175 |      0.94149  |     0.8      |                 1 | NO_DEV_SIGNAL   |
| T1_first_inquiry | atomic          |       3 |   0.489648 |  0.482714 |                  0.991413 |                 0.94797  |      0.964161 |     0.780488 |                 0 | NO_DEV_SIGNAL   |
| T1_first_inquiry | te_interactions |       3 |   0.505224 |  0.496617 |                  1.02001  |                 1.0017   |      0.958076 |     0.878049 |                 2 | WEAK_DEV_SIGNAL |
| T1_first_inquiry | te_marginals    |       3 |   0.49629  |  0.473188 |                  1.02212  |                 0.961628 |      1.02958  |     0.829268 |                 2 | NO_DEV_SIGNAL   |
- T0_cold: **te_marginals** — NO_DEV_SIGNAL.

- T1_first_inquiry: **te_marginals** — NO_DEV_SIGNAL.
