# Feature validation — E021 a E028

Esta línea convierte hallazgos del EDA profundo en pruebas controladas sobre el mismo sistema dinámico T0/T1/T2.

## Cadena de evidencia

- **E020 / EV-020:** EDA profundo que detecta drift, staleness, redundancias, outliers y restricciones point-in-time.
- **E021 / EV-021:** stress test de drift temporal por rolling cohorts — drift SUPPORTED.
- **E022 / EV-022:** ablación de clocks/calendario/progreso — dependencia temporal SUPPORTED; E005/T1 BLOCK.
- **E023 / EV-023:** Availability staleness — raw age fuera como predictor; freshness como guardrail.
- **E024 / EV-024:** outlier handling train-only — borrado automático NOT_SUPPORTED.
- **E025 / EV-025:** redundancias deterministas — formalmente INCONCLUSIVE bajo el margen pre-registrado.
- **E026 / EV-026:** prior_searches vs prior_inquiries — retirar prior_searches.
- **E027 / EV-027:** broker prior estrictamente point-in-time — no incluir en release.
- **E028 / EV-028:** target definitiva y A/B sistémico lead-level.

## Estado de evidencia

E021–E027 ya tienen ejecución reproducible completa en GitHub Actions run:
https://github.com/jcval94/spot2/actions/runs/33281869820

Los hallazgos promovidos son D069–D075 y su evidencia central EV-021–EV-027.

La conclusión dominante es que el **drift temporal/progreso es material**: el candidato E005/T1 no es aprobable tal cual para producción.

E028 tiene target/protocolo congelados, pero su launch permanece bloqueado hasta validar un release candidate drift-sanitized.

## Baseline experimental E021–E027

Los experimentos E022–E027 usan como referencia congelada el Random Forest especialista de E005. El runner primero exige reproducir numéricamente esa baseline antes de aceptar una comparación.

E021 cambia deliberadamente el esquema de validación para medir estabilidad temporal y por ello se interpreta como NON_EQUIVALENT.

## Target

Ver [E028/TARGET.md](E028_definitive_opportunity_score_abt/TARGET.md).

La etiqueta dinámica canónica es `target_scheduled_visit_30d`: al menos un scheduled_visit en los 30 días posteriores al scoring time, siempre que no haya ocurrido una visita previamente y exista maduración completa.

## Runner

```bash
pip install -r experimentos/feature_validation/requirements.txt
python experimentos/feature_validation/run_all.py
```

GitHub Actions ejecuta además validación de contratos, harness records y comprobación de outputs.

## Regla de promoción

Un resultado no entra a `conocimiento_agregado/DESCUBRIMIENTOS.md` como evidencia empírica hasta que:

1. el contrato esté fijado;
2. el leakage review pase;
3. la baseline se reconcilie;
4. la ejecución sea reproducible;
5. se hayan revisado métricas, intervalos y caveats;
6. exista EV central enlazada a los artifacts fuente.


## A/B definitivo E028

Ver:

- [TARGET.md](E028_definitive_opportunity_score_abt/TARGET.md)
- [OFFLINE_DECISIONS.md](E028_definitive_opportunity_score_abt/OFFLINE_DECISIONS.md)
- [TREATMENT_POLICY.md](E028_definitive_opportunity_score_abt/TREATMENT_POLICY.md)
- [ANALYSIS_PLAN.md](E028_definitive_opportunity_score_abt/ANALYSIS_PLAN.md)
- [RELEASE_MANIFEST_TEMPLATE.json](E028_definitive_opportunity_score_abt/RELEASE_MANIFEST_TEMPLATE.json)

El protocolo A/B se valida por separado en `.github/workflows/e028-definitive-abt.yml`.
