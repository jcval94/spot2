# Decision log — Segmentación, perfiles y Matching

| Momento | Decisión | Evidencia disponible | Estado posterior |
|---|---|---|---|
| Inicio | Buscar perfiles interpretables, no sólo scores | estructura Lead/Spot/Broker | Se mantiene |
| Profile v2 | Seleccionar clusters sin outcome y con balance/estabilidad | benchmark multi-método | Se mantiene |
| Profile v2 | Separar Persona y Search Need | conceptos distintos | Refinada: Need sí; Persona source-dominated |
| Profile v2 | No usar Inquiry Intent | clusters ≈ weekday | **Final** |
| Profile v2 | Separar Spot físico/geografía | S1–S7 mezclan ambos | Confirmada por E006 |
| Auditoría | Availability sólo backward-as-of | join directo ~10x | **Final** |
| Auditoría | No usar response_hours como SLA | semántica inconsistente | **Final** |
| Auditoría | No usar total_inquiries como event count | no reconcilia | **Final** |
| Auditoría | Excluir Market Context histórico | PIT insuficiente | **Final hasta nueva fuente** |
| E006 | Conservar Physical+Location aunque lift sea inconcluso | mejor semántica | **Final de representación** |
| E007 | No declarar Compatibility Score global causal | bootstrap cruza cero | Se mantiene |
| E007 | Conservar E007 como benchmark global | mejor señal lead-level de esa fase | Se mantiene |
| E008 | No reemplazar Persona actual por BP | AP/lift empeoran | **Final** |
| E009 | Dynamic Need merece aislamiento | señal T1 | Confirmado por E012 |
| E010 | No confiar en Broker Supply v1 | 98.3% dominante | Confirmado por segundo intento |
| E011 | No promover primera jerarquía | no supera E007 | **Final para esa rama** |
| E012 | Mantener Dynamic Need como challenger T1 | lift/recall mejoran en punto | **Final** |
| E013 | No forzar Broker Supply | falla gate 5%–65% | **Final** |
| E015 | Conservar Broker Service como faceta auxiliar | balance/ARI fuerte; AP marginal≈0 | **Final** |
| E016 | No sustituir E007 globalmente | trade-off AP vs lift | **Final** |
| Cierre | DN4×LOC1×BSV1 sólo como hipótesis online/nueva cohorte | 1.510x exploratorio | **Final** |
| Cierre | No volver a optimizar pockets con el mismo future test | holdout ya inspeccionado | **Final** |
| Cierre | Persona actual + Need T0 + Dynamic Need T1 + PH + LOC + Broker legacy; BSV auxiliar | EV-006/010/013 | **CLOSED / DECISION-READY** |

## Hipótesis descartadas

### “Más clusters/facetas necesariamente mejoran el ranking”
Descartada: mejor semántica puede coexistir con peor AP/lift.

### “Persona sin source debe reemplazar P1–P7”
Descartada para scoring: BP1–BP3 pierde desempeño.

### “Broker Supply sólo necesitaba otro algoritmo/K”
Descartada: dos representaciones fallan balance.

### “Inquiry Intent representa intención comercial”
Descartada: representa weekday.

### “El mayor lift local debe convertirse en multiplicador”
Descartada: 1.510x es descriptivo/exploratorio, no uplift causal.

### “E016 es mejor porque tiene mayor Lift@10”
Descartada como decisión universal: E007 conserva mejor AP/Lead AP/Lead AUC.

## Regla para reabrir

Sólo nueva evidencia independiente: nueva cohorte, A/B online, target comercial real, información material nueva o un challenger equivalente que mueva la frontera actual.
