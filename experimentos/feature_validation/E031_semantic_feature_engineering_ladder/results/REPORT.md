# E031 — Semantic Feature Engineering ladder

**Important:** selection uses only E030 train/validation. E030 test is not used by this ladder.

## T0_cold

| variant               |   roc_auc |   average_precision |   ap_over_prevalence |   lift_top_10pct |   recall_top_20pct |    brier |   n_cat |   n_num |
|:----------------------|----------:|--------------------:|---------------------:|-----------------:|-------------------:|---------:|--------:|--------:|
| atomic                |  0.47224  |            0.494367 |             0.994466 |         0.890849 |           0.191304 | 0.255413 |       9 |       7 |
| scale_specificity     |  0.463411 |            0.487143 |             0.979935 |         0.97706  |           0.194203 | 0.257021 |       9 |      46 |
| semantic_need         |  0.45783  |            0.487343 |             0.980335 |         0.890849 |           0.191304 | 0.256937 |      15 |      46 |
| soft_profiles         |  0.467755 |            0.500368 |             1.00654  |         1.09201  |           0.194203 | 0.256879 |      16 |      51 |
| semantic_interactions |  0.464748 |            0.495459 |             0.996662 |         1.03453  |           0.188406 | 0.257671 |      20 |      51 |

Selected on validation: **soft_profiles**. Qualified gate: **False**.
## T1_first_inquiry

| variant               |   roc_auc |   average_precision |   ap_over_prevalence |   lift_top_10pct |   recall_top_20pct |    brier |   n_cat |   n_num |
|:----------------------|----------:|--------------------:|---------------------:|-----------------:|-------------------:|---------:|--------:|--------:|
| atomic                |  0.501978 |            0.516177 |             1.01618  |         1.01245  |           0.202279 | 0.254014 |      27 |      36 |
| scale_specificity     |  0.485118 |            0.507134 |             0.998375 |         0.98433  |           0.19943  | 0.255744 |      27 |      75 |
| semantic_need         |  0.488051 |            0.506679 |             0.997479 |         0.98433  |           0.193732 | 0.25529  |      33 |      75 |
| soft_profiles         |  0.494386 |            0.508881 |             1.00182  |         0.956207 |           0.202279 | 0.255837 |      36 |      97 |
| semantic_interactions |  0.500989 |            0.51953  |             1.02278  |         1.09683  |           0.205128 | 0.254238 |      42 |      97 |

Selected on validation: **semantic_interactions**. Qualified gate: **False**.
