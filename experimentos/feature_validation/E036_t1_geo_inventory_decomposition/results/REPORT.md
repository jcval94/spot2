# E036 — T1 geo/inventory decomposition

**Development only.**

| stage            | variant                 |   folds |   mean_auc |   min_auc |   mean_ap_over_prevalence |   min_ap_over_prevalence |   mean_lift10 |   min_lift10 |   folds_auc_gt_05 | status        |
|:-----------------|:------------------------|--------:|-----------:|----------:|--------------------------:|-------------------------:|--------------:|-------------:|------------------:|:--------------|
| T1_first_inquiry | atomic                  |       3 |   0.489648 |  0.482714 |                  0.991413 |                 0.94797  |      0.964161 |     0.780488 |                 0 | NO_DEV_SIGNAL |
| T1_first_inquiry | geo_distance            |       3 |   0.484225 |  0.465366 |                  1.00342  |                 0.929042 |      1.07194  |     0.926829 |                 0 | NO_DEV_SIGNAL |
| T1_first_inquiry | inventory_geo_frequency |       3 |   0.482039 |  0.470137 |                  0.994405 |                 0.936775 |      0.998133 |     0.878049 |                 0 | NO_DEV_SIGNAL |
| T1_first_inquiry | inventory_plus_geo      |       3 |   0.488691 |  0.486971 |                  1.00526  |                 0.957704 |      0.996181 |     0.852273 |                 0 | NO_DEV_SIGNAL |
| T1_first_inquiry | inventory_relative      |       3 |   0.481838 |  0.480816 |                  0.994276 |                 0.964028 |      0.940932 |     0.795455 |                 0 | NO_DEV_SIGNAL |

Selected exploratory component: **inventory_plus_geo** (NO_DEV_SIGNAL).
