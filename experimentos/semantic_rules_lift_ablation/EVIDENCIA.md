# Evidencia

Evidencia canónica: [EV-018 — Semantic Rules Lift Ablation](../Evidencias/EV-018_semantic_rules_lift_ablation.md).

## Estado

**EXECUTED / NOT_SUPPORTED for Lift@10% promotion**

Corrida autoritativa: `33297920881`.

Artifact: `9728035555`.

Resultados principales:

- baseline macro Lift@10%: **1.267x**;
- semantic Rules macro Lift@10%: **1.196x**;
- delta: **-0.0716x**;
- bootstrap 95% CI: **[-0.1438, +0.1251]**;
- P(delta > 0): **45.0%**;
- macro AP delta: **+0.0019**.

La evidencia completa está en:

- [REPORT.md](results/REPORT.md)
- [cv_mean_metrics.csv](results/cv_mean_metrics.csv)
- [paired_bootstrap.csv](results/paired_bootstrap.csv)
- [fold_metrics.csv](results/fold_metrics.csv)
- [semantic_coverage.csv](results/semantic_coverage.csv)
- [RUN_HISTORY.md](results/RUN_HISTORY.md)

No se promueven estas variables al ABT de scoring. Se conservan como sidecar de Inventory QA.
