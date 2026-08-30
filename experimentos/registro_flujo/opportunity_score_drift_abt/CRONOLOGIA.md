# Cronología

## E020 — EDA profundo

**Pregunta:** ¿qué distribuciones, drift, clipping, staleness y rareza condicionan el feature engineering?

**Resultado:** se detecta compresión temporal de interacción, clipping sintético, current-state Spot inconsistente, Availability dinámica/stale y heterogeneidad de broker no causal.

**Decisión de ese momento:** no limpiar outliers mecánicamente; abrir experimentos específicos para drift, staleness, redundancia, historial y broker.

**Nueva incertidumbre:** cuánto del rendimiento offline depende realmente de clocks temporales.

## E021 — Temporal drift stress

**Cambio:** rolling cohorts + PSI.

**Resultado:** positive rate macro cambia ~12.4 pp; PSI T2 de `days_from_lead_creation` 2.824 y `days_since_first_inquiry` 2.043.

**Decisión:** una sola partición temporal no basta; toda release requiere validación multi-cohorte.

## E022 — Temporal feature ablation

**Cambio:** retirar calendario/progreso manteniendo target/modelo.

**Resultado:** T1 RF AUC ~0.588→0.504 y AP ~0.563→0.510; time-proxy-only supera al RF completo macro.

**Decisión:** bloquear E005/T1 con clocks crudos; construir candidato drift-sanitized.

## E023 — Availability staleness

**Resultado:** edad cruda no aporta lift robusto; representación protegida es no-inferior.

**Decisión:** freshness como guardrail, >90d unknown.

## E024 — Outlier handling

**Resultado:** borrar anomalies de train mejora el punto pero IC cruza cero.

**Decisión:** no borrar automáticamente.

## E025 — Redundancy ablation

**Resultado:** price totals parecen prescindibles, pero la no-inferioridad AUC falla por margen mínimo.

**Decisión:** conservar en v1 o confirmar en nueva cohorte; no declarar éxito retrospectivamente.

## E026 — Prior-history ablation

**Resultado:** retirar `prior_searches` mejora macro AP robustamente.

**Decisión:** excluir `prior_searches`; `prior_inquiries` queda opcional/no demostrada.

## E027 — Broker prior PIT

**Resultado:** ΔAP +0.0015, IC cruza cero; T2 incluso negativo en punto.

**Decisión:** no incluir broker prior ni cambiar routing por esa señal.

## E028 — Target definitiva + A/B sistémico

**Cambio:** separar target predictiva de primary outcome causal.

**Resultado:** protocolo lead-level pre-registrado; A/A retrospectivo pasa SRM, pero el histórico tiene 4.81% de outcomes ambiguos y sólo 24.68% del tamaño requerido.

**Decisión:** protocolo listo; launch bloqueado hasta candidato drift-sanitized + A/A productivo + freeze.


## E029 — Drift-sanitized release candidate

**Motivación:** E022 demostró que T1 dependía fuertemente de clocks/progreso y E026/E027 resolvieron señales adicionales que no deben entrar al release.

**Cambio pre-registrado:** LeadQuality T2-only con target canónica corregida, sin clocks/progreso, sin prior_searches, sin Availability dentro del modelo y sin broker prior. T0/T1 quedan neutrales.

**Regla de honestidad:** el histórico sólo puede producir diagnóstico post-selección. El artifact se congela y el PASS real requiere una cohorte creada después del freeze.

**Gate prospectivo:** primera T2 por lead; 8 semanas completas, extensible sólo por N hasta >=500 leads o 16 semanas. AUC >=0.55 con lower CI >0.50, AP/prevalencia >=1.05, Lift@10 >=1.10 y timestamp de outcome >=99.5%.

**Estado:** ejecución/build-and-freeze en curso; E028 sigue bloqueado hasta gate prospectivo + A/A productivo.
