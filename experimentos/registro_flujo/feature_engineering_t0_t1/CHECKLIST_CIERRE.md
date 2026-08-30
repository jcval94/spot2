# Checklist de cierre — Feature Engineering T0/T1

## Resultado

**CLOSED / DECISION-READY**

Este checklist certifica que el cierre no depende de una conclusión verbal sino de artifacts reproducibles y decisiones trazables.

## 1. Problema y target

- [x] Pregunta de negocio explicitada.
- [x] Target offline congelada en E028.
- [x] Ventana temporal definida como `(score_time, score_time+30d]`.
- [x] Ambiguous y right-censored separados de negativos.
- [x] Outcome online del A/B definido a nivel lead/ITT.

## 2. ABT

- [x] E030 construida reproduciblemente.
- [x] Grain `lead_id × stage × score_time`.
- [x] Split por lead y temporal.
- [x] Model features separados de guardrails/audit-only.
- [x] Forbidden fields ausentes.
- [x] Governance de target y features validada.

## 3. Drift y leakage

- [x] Drift temporal evaluado.
- [x] Calendar/progress clocks retirados de LeadQuality.
- [x] Availability limitada a serviceability/freshness.
- [x] Market Context bloqueado sin effective/publication time.
- [x] Current-state Spot fields inseguros bloqueados.
- [x] prior_searches retirado.
- [x] Broker prior no promovido.

## 4. Feature Engineering T0/T1

- [x] Scale/log transforms.
- [x] Specificity/completeness.
- [x] Search Need.
- [x] Dynamic Need.
- [x] Soft clusters y centroid distances.
- [x] Physical/Location profiles.
- [x] Lead×Spot directional fit.
- [x] Semantic interactions.
- [x] Missingness patterns.
- [x] Category frequency.
- [x] Quantile bins.
- [x] Geo/inventory-relative.
- [x] Preferred-geo distance.
- [x] Temporally-smoothed target encoding.

## 5. Holdout governance

- [x] E031 seleccionó usando train/validation.
- [x] E032/E033 consumieron E030 test una sola vez.
- [x] Experimentos E035–E037 no reutilizaron E030 test como confirmación.
- [x] Nuevos challengers requieren nueva cohorte para confirmación.

## 6. Decisión por stage

- [x] T0 LeadQuality = `NEUTRAL_EVIDENCE_BACKED`.
- [x] T0 semantic representation permanece activa.
- [x] T1 LeadQuality = `NEUTRAL_EVIDENCE_BACKED`.
- [x] T1 semantic/matching representation permanece activa.
- [x] T2 = candidato E029 pendiente prospective gate.

## 7. LLM

- [x] Se verificó que no existe raw inquiry text.
- [x] E039 queda `BLOCKED_BY_DATA_GAP`, no FAILED.
- [x] No se simula texto desde campos estructurados.
- [x] Schema de salida estructurada definido.
- [x] Prompt contract definido.
- [x] Leakage contract definido.
- [x] LLM futuro = extractor semántico, no predictor de conversión.

## 8. Documentación

- [x] Descubrimientos D060–D091.
- [x] Evidencias EV-020–EV-040.
- [x] Cronología completa.
- [x] Decisiones.
- [x] Trazabilidad.
- [x] Arquitectura final.
- [x] Manifest final machine-readable.
- [x] Criterios explícitos de reapertura.

## 9. Pendientes de otra fase

No bloquean este cierre:

- [ ] E029 prospective post-freeze gate.
- [ ] E028 production A/A.
- [ ] backend event timestamp >=99.5%.
- [ ] E039 si aparece raw inquiry text.
- [ ] nueva target close/lease si negocio la entrega.

Estos elementos pertenecen a lanzamiento o a nuevas fuentes, no a la investigación offline T0/T1.

## 10. Regla final

Si una nueva propuesta de T0/T1 no introduce al menos uno de:

- nueva información;
- nueva target;
- nueva temporalidad point-in-time;
- nueva cohorte independiente;

entonces no constituye una reapertura confirmatoria de esta línea.

## Certificación

**La línea queda completamente cerrada con el dataset y target actuales.**
