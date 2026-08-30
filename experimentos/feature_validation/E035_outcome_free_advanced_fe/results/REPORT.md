# E035 — Outcome-free advanced Feature Engineering

**Development only. E030 validation/test are not used.**

| stage            | variant                |   folds |   mean_auc |   min_auc |   mean_ap |   mean_ap_over_prevalence |   min_ap_over_prevalence |   mean_lift10 |   min_lift10 |   folds_auc_gt_05 | status          |
|:-----------------|:-----------------------|--------:|-----------:|----------:|----------:|--------------------------:|-------------------------:|--------------:|-------------:|------------------:|:----------------|
| T0_cold          | atomic                 |       3 |   0.488814 |  0.459936 |  0.377228 |                  0.980863 |                 0.904143 |      0.956721 |     0.740741 |                 1 | NO_DEV_SIGNAL   |
| T0_cold          | combined_v2            |       3 |   0.494921 |  0.469249 |  0.378146 |                  0.980892 |                 0.924915 |      0.897914 |     0.77037  |                 1 | NO_DEV_SIGNAL   |
| T0_cold          | geo_inventory_relative |       3 |   0.493947 |  0.474288 |  0.379694 |                  0.984534 |                 0.93556  |      0.921737 |     0.740741 |                 1 | NO_DEV_SIGNAL   |
| T0_cold          | missingness_frequency  |       3 |   0.497878 |  0.474145 |  0.38097  |                  0.986527 |                 0.933349 |      0.87014  |     0.707692 |                 1 | NO_DEV_SIGNAL   |
| T0_cold          | robust_bins            |       3 |   0.493947 |  0.474288 |  0.379694 |                  0.984534 |                 0.93556  |      0.921737 |     0.740741 |                 1 | NO_DEV_SIGNAL   |
| T1_first_inquiry | atomic                 |       3 |   0.489648 |  0.482714 |  0.402043 |                  0.991413 |                 0.94797  |      0.964161 |     0.780488 |                 0 | NO_DEV_SIGNAL   |
| T1_first_inquiry | combined_v2            |       3 |   0.491    |  0.487621 |  0.409364 |                  1.0092   |                 0.944385 |      0.932024 |     0.536585 |                 0 | NO_DEV_SIGNAL   |
| T1_first_inquiry | geo_inventory_relative |       3 |   0.500079 |  0.493309 |  0.417236 |                  1.02829  |                 0.975387 |      1.0587   |     0.97561  |                 1 | WEAK_DEV_SIGNAL |
| T1_first_inquiry | missingness_frequency  |       3 |   0.497224 |  0.486049 |  0.408714 |                  1.00991  |                 0.947738 |      0.99098  |     0.829268 |                 1 | NO_DEV_SIGNAL   |
| T1_first_inquiry | robust_bins            |       3 |   0.493961 |  0.483654 |  0.402976 |                  0.99445  |                 0.949054 |      0.893761 |     0.682927 |                 1 | NO_DEV_SIGNAL   |

## Selected development challengers

- T0_cold: **missingness_frequency** — NO_DEV_SIGNAL; mean AUC 0.498, AP/prevalence 0.987x, min Lift@10 0.708x.
- T1_first_inquiry: **geo_inventory_relative** — WEAK_DEV_SIGNAL; mean AUC 0.500, AP/prevalence 1.028x, min Lift@10 0.976x.
