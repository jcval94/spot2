# E025 - Deterministic price redundancy

**Conclusion: INCONCLUSIVE.**

Se eliminan solo spot_price_total_mxn_rent y spot_price_total_mxn_sale, porque E020 mostro que son practicamente area x price_per_sqm.

- No totals - full AP: +0.0023, IC95% [-0.0078, +0.0104].
- No totals - full AUC: -0.0028, IC95% [-0.0102, +0.0047].

| Variante | ROC-AUC | AP | Brier | Log loss | Lift@10% | Recall@20% |
|---|---:|---:|---:|---:|---:|---:|
| full | 0.556 | 0.517 | 0.245 | 0.684 | 1.12x | 0.220 |
| no_price_totals | 0.553 | 0.520 | 0.245 | 0.683 | 1.07x | 0.223 |
