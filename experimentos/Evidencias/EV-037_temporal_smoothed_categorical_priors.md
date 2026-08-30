# EV-037 — Temporal smoothed categorical priors

**Estado:** sin recovery robusto.

[E037](../feature_validation/E037_temporal_smoothed_categorical_priors/)

Target encoding centrado y suavizado (alpha=50) fue ajustado sólo con cada fold train y aplicado a cohortes futuras.

### T0

- te_marginals mean AUC **0.4982**;
- AP/prevalence **0.995x**;
- Lift@10 **0.941x**.

NO_DEV_SIGNAL.

### T1

te_interactions:
- mean AUC **0.5052**;
- min AUC **0.4966**;
- mean AP/prevalence **1.020x**;
- min AP/prevalence **1.002x**;
- mean Lift@10 **0.958x**;
- 2/3 folds AUC >0.50.

Clasifica como señal débil por AUC/AP, pero no concentra positivos en top-decile y no pasa el gate robusto.

**Conclusión:** historical categorical priors pueden conservarse como línea futura con nueva cohorte, pero no justifican activar T0/T1 LeadQuality.

Fuente: [summary.csv](../feature_validation/E037_temporal_smoothed_categorical_priors/results/summary.csv).


## Conocimiento acumulado

Hallazgos promovidos: [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
