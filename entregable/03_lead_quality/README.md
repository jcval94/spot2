# Entregable 3 — Modelo de Calidad del Lead

Este directorio contiene la versión final en español del **Entregable 3 — Lead Quality Model** del assessment de Spot2.

## Documento principal

- [Modelo de Calidad del Lead — documento autocontenido](MODELO_CALIDAD_LEAD.md)

## Autoridad metodológica

La autoridad final de este entregable es **[Codexway](../../codexway/)**.

En particular, se conservan como definición final de Lead Quality:

- el scoring moment T1;
- el target de la primera inquiry;
- el buffer de madurez de 7 días;
- la ABT point-in-time;
- la allowlist de features;
- el modelo `stable_segment_logistic`;
- la calibración Platt;
- la validación temporal;
- el tratamiento tie-aware de métricas de capacidad;
- el cutoff de prioridad validado;
- la política operativa de shadow validation + piloto aleatorizado.

La evidencia de **[experimentos](../../experimentos/)** y **[AssessmentSol1](../../AssessmentSol1/)** se usa como investigación complementaria: challengers, ablations, resultados negativos, auditorías temporales y aprendizaje metodológico.

**No se mezclan métricas entre líneas que utilicen distinto target, población, madurez, grano, split o information set.**

## Respuesta corta

Lead Quality estima, en T1, la probabilidad de que la **primera inquiry** de un lead termine registrada como `scheduled_visit`, usando únicamente información disponible después de persistir esa inquiry y antes de conocer la respuesta del broker.

El modelo final de Codexway es una **Regresión Logística de segmento estable** basada en una interacción T0-safe:

`Industrial AND (company_size = small OR source = paid)`

con calibración Platt.

En el holdout procedimental:

- ROC-AUC: **0.5478**;
- PR-AUC: **0.2391** frente a prevalencia **0.2122**;
- Lift@5%: **1.689x**;
- Lift@10%: **1.689x**;
- Recall@10%: **16.98%**;
- Lift@10% IC95% bootstrap: **[1.381x, 1.982x]**.

La recomendación no es automatizar inmediatamente: el resultado es retrospectivo porque el holdout histórico ya había sido consumido globalmente durante investigación previa. La salida queda **elegible para una nueva validación forward en shadow mode** y, si se confirma, para un A/B sticky por `lead_id`.

## Evidencia canónica

### Codexway

- [README](../../codexway/README.md)
- [Model Card](../../codexway/outputs/MODEL_CARD.md)
- [Decisiones congeladas](../../codexway/evidence/DECISIONS.md)
- [Leakage Matrix](../../codexway/evidence/LEAKAGE_MATRIX.md)
- [Feature policy](../../codexway/config/feature_policy.yaml)
- [Métricas T1](../../codexway/outputs/metrics/t1_model_metrics.json)
- [Intervalos bootstrap](../../codexway/outputs/metrics/t1_metric_intervals.csv)
- [Rolling temporal CV](../../codexway/outputs/metrics/rolling_model_comparison.csv)
- [Segment metrics](../../codexway/outputs/tables/segment_metrics.csv)
- [Deployment readiness](../../codexway/outputs/metrics/deployment_readiness.json)

### Evidencia complementaria

- [AssessmentSol1 — target contract](../../AssessmentSol1/target/TARGET_CONTRACT.md)
- [AssessmentSol1 — temporal semantics](../../AssessmentSol1/evidence/TEMPORAL_SEMANTICS.md)
- [AssessmentSol1 — feature engineering decisions](../../AssessmentSol1/evidence/FEATURE_ENGINEERING_DECISIONS.md)
- [AssessmentSol1 — recovery decision](../../AssessmentSol1/models/lead_quality_recovery/RECOVERY_DECISION.md)
- [Experimentos — arquitectura Modelo 3](../../experimentos/modelo_3/DECISION_ARQUITECTURA.md)
- [Experimentos — Semantic Rules ablation](../../experimentos/Evidencias/EV-018_semantic_rules_lift_ablation.md)
- [Experimentos — Dynamic Need / Matching](../../experimentos/Evidencias/EV-013_matching_profiles_v4.md)
