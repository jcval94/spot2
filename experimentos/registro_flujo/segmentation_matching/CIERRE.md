# Cierre formal — Segmentación, perfiles y Matching

## Veredicto

**CLOSED / DECISION-READY**

La pregunta de investigación offline queda resuelta al estándar necesario para decidir qué perfiles conservar, cuáles descartar y qué hipótesis necesitan nueva evidencia.

## Checklist

- [x] Pregunta definida.
- [x] Calibration / train / future test congelados.
- [x] Clustering outcome-free.
- [x] Balance y estabilidad evaluados.
- [x] Persona auditada y rediseñada.
- [x] Search Need T0 definido.
- [x] Dynamic Need T1 definido.
- [x] Spot Physical / Location.
- [x] Broker Supply probado dos veces y rechazado.
- [x] Broker Service construido sin response_hours.
- [x] Inquiry Intent descartado.
- [x] Auditoría PK/FK/cardinalidad.
- [x] Availability backward-as-of.
- [x] Coverage drift documentado.
- [x] Market Context bloqueado por PIT.
- [x] total_inquiries bloqueado como event history.
- [x] Flat compatibility probado.
- [x] Jerarquías probadas.
- [x] Bootstrap por lead.
- [x] Negativos/inconclusos preservados.
- [x] A/B online pre-registrado y power analysis.
- [x] Interpretabilidad completa.
- [x] Mejor pocket documentado con caveat de multiple testing.
- [x] Decisión final explícita.
- [x] Future test marcado como consumido para discovery.
- [x] Governance y rerun final verdes.

## Decisión vigente

### Representación

**Lead:** Persona actual + Search Need T0 + Dynamic Need T1.  
**Spot:** Physical + Location.  
**Broker:** legacy para benchmark global + Broker Service auxiliar; no Supply clusters.  
**Context:** Availability backward-as-of.

### Ranking

- E007 = referencia global.
- E012 = challenger Dynamic Need.
- E016 = challenger de concentración/routing.

### Routing hypothesis

DN4 × LOC1 × BSV1 es la hipótesis prioritaria, no una regla.

## Por qué la falta de rolling CV de pockets no bloquea este cierre

No se concluye que 1.51x sea causal, estable ni desplegable.

La decisión cerrada es:

> con estos datos y este holdout, no existe justificación para seguir optimizando clusters/reglas offline ni para reemplazar globalmente E007.

La réplica temporal es requisito de **activación**, no de cierre de esta investigación.

## Blockers

### Para cerrar la línea offline
**Ninguno.**

### Para activar routing por pockets

1. nueva cohorte independiente o A/B online;
2. guardrails de capacidad/workload;
3. monitoreo no-result/availability;
4. outcome comercial cuando exista.

## Refinamiento opcional

- ablation de Dynamic Need;
- usar Supply como variables continuas;
- enriquecer inventario;
- nombres con stakeholders;
- threshold según objetivo operativo.

## Preguntas que requieren nueva fuente/target

- true sale/conversion;
- effective-time de Market Context;
- semántica contractual de response_hours;
- definición temporal de total_inquiries.

## Regla de no reutilización

El future test actual puede reproducir EV-010/EV-013, pero no confirmar una compatibilidad nueva descubierta después de este cierre.

## Regla de reapertura

Reabrir FL-003 sólo con **nueva evidencia independiente** que pueda cambiar la decisión.
