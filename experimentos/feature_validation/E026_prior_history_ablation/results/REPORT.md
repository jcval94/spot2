# E026 - prior_searches vs prior_inquiries

**Conclusion: NOT_SUPPORTED.**

La pregunta no es si ambas variables estan correlacionadas - E020 mostro que no - sino si cada una aporta senal incremental distinta.

- Full - drop prior_searches AP: -0.0101, IC95% [-0.0183, -0.0010].
- Full - drop prior_inquiries AP: -0.0061, IC95% [-0.0152, +0.0025].

| Variante | ROC-AUC | AP | Brier | Log loss | Lift@10% | Recall@20% |
|---|---:|---:|---:|---:|---:|---:|
| full | 0.556 | 0.517 | 0.245 | 0.684 | 1.12x | 0.220 |
| drop_prior_searches | 0.561 | 0.528 | 0.245 | 0.682 | 1.12x | 0.219 |
| drop_prior_inquiries | 0.563 | 0.524 | 0.244 | 0.682 | 1.14x | 0.224 |
| drop_both | 0.563 | 0.524 | 0.245 | 0.683 | 1.12x | 0.231 |
