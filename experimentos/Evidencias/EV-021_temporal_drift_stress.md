# EV-021 — Stress test de drift temporal

**Estado:** evidencia empírica reproducible.

**Experimento:** [E021](../feature_validation/E021_temporal_drift_stress/)

**GitHub Actions fuente:** https://github.com/jcval94/spot2/actions/runs/33281869820

## Pregunta

¿El target y el modelo mantienen un régimen suficientemente estable entre cohortes futuras como para confiar en una única evaluación temporal?

## Resultado

**SUPPORTED: existe drift temporal material.**

En cuatro folds expanding-time:

- positive rate macro mínimo: **35.40%**;
- máximo: **47.80%**;
- rango: **12.41 pp**;
- ROC-AUC macro: **0.553–0.572**;
- AP/prevalence: **1.069–1.156**.

El drift no es uniforme entre variables. Los PSI early-vs-late más altos son:

- T2 `days_from_lead_creation`: **2.824**;
- T2 `days_since_first_inquiry`: **2.043**;
- T2 `availability_snapshot_age_days`: **0.763**;
- T1 `days_from_lead_creation`: **0.390**;
- T1 `availability_snapshot_age_days`: **0.265**.

Como referencia usual, PSI >0.25 ya representa un cambio de distribución fuerte; aquí algunos clocks de T2 están muy por encima.

## Interpretación

La principal inestabilidad está concentrada en **tiempo/progreso del funnel**, no en todas las variables del lead. Esto es consistente con el EDA: el generador comprime las interacciones hacia la creación del lead conforme avanza el calendario.

El modelo puede seguir discriminando algo en folds futuros, especialmente T2, pero su baseline y distribución de features cambian. Por ello una única métrica holdout no es suficiente para aprobar un release candidate.

## No demuestra

- no prueba causalidad;
- no convierte toda variable temporal en leakage;
- no significa que el producto real necesariamente tendrá el mismo drift sintético;
- no permite atribuir el cambio del positive rate a una sola feature.

## Decisión

Todo release candidate debe:

1. validarse en más de una cohorte futura;
2. reportar performance por assignment/scoring week;
3. monitorizar clocks/progreso y freshness;
4. evitar interpretar señal temporal como intención comercial.

## Evidencia fuente

- `E021_temporal_drift_stress/results/fold_metrics.csv`
- `E021_temporal_drift_stress/results/feature_psi_early_vs_late.csv`
- `E021_temporal_drift_stress/results/drift_summary.json`
- harness record E021.


## Descubrimientos relacionados

- [D060](../conocimiento_agregado/DESCUBRIMIENTOS.md#d060--)
- [D069](../conocimiento_agregado/DESCUBRIMIENTOS.md#d069--)
