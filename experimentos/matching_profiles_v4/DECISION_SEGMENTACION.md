# Decisión final — Segmentación y Matching

**Estado:** **CLOSED / DECISION-READY**

Esta decisión congela la representación recomendada al cierre de la línea de clustering, perfiles y matching.

## Representación recomendada

### Lead

1. **Persona actual P1–P7** se conserva como feature de referencia para el scoring global.
   - No interpretarla como persona comercial pura.
   - Principalmente representa canal de adquisición + historia.

2. **Search Need T0 N1–N3** se conserva:
   - N1 renta;
   - N2 venta;
   - N3 flexible/both.

3. **Dynamic Need T1 DN1–DN5** se incorpora como challenger/capa semántica en T1.
   - Especialmente útil para N2/N3.
   - DN4 (*stretch-space*) es el régimen más interesante para hipótesis de routing.
   - No sustituye automáticamente Need T0: representa su actualización.

### Spot

Usar la descomposición:

- **Physical Space PH1–PH4**;
- **Location LOC1–LOC7**.

No volver al Spot unificado como representación conceptual por defecto.

### Broker

1. **Broker legacy B1–B7** se conserva para el benchmark global actual, con cautela sobre cualquier interpretación de velocidad.
2. **Broker Service BSV1–BSV3** se conserva como dimensión auxiliar/experimental.
3. **Broker Supply clusters BS/BSP no se usan.**
   - dos representaciones fallaron el gate de balance;
   - no seguir ajustando K para fabricar grupos.

### Contexto point-in-time

- Availability sólo con **backward as-of**.
- No usar `market_context` históricamente hasta tener effective/publication time.
- No tratar `spots.total_inquiries` como conteo de eventos.
- No tratar `broker_response_hours` como SLA limpio.

## Política de matching

### Referencia global

**E007 old compatibility** se mantiene como referencia global offline porque conserva el mejor AP global, Lead AP y Lead AUC de esta línea.

### Challengers

- **E012 Dynamic Need:** challenger simple para T1.
- **E016 Dynamic Need × Physical/Location × Broker Service:** challenger orientado a top-decile/routing.

No hay evidencia robusta de que sustituyan universalmente a E007.

## Hipótesis prioritaria para nueva evidencia

### DN4 × LOC1 × BSV1

- N=60;
- scheduled_visit raw 36.67%;
- smoothed 31.37%;
- lift suavizado **1.510x**.

Esta celda es **hipótesis**, no regla.

No:

- multiplicar el score por 1.51;
- convertirla en hard routing;
- volver a optimizarla contra el mismo future test.

El siguiente test debe ser nueva cohorte temporal independiente o A/B online sticky por `lead_id`.

## Perfiles explícitamente descartados

- Inquiry Intent I1–I7: aprende weekday.
- Behavioral Persona BP1–BP3 como reemplazo del scoring: mejor semántica, peor AP/lift.
- Broker Supply BS/BSP: no clusterizable bajo el gate definido.
- Market Context histórico actual: no point-in-time defendible.
- response_hours como explicación de SLA.
- total_inquiries como historial de events.

## Regla de congelamiento

El future test usado por EV-010/EV-013 ya fue inspeccionado repetidamente para descubrir celdas locales.

> Desde este cierre no puede usarse como conjunto independiente para confirmar nuevas reglas de compatibilidad.

Puede seguir usándose para reproducir resultados ya registrados.

## Regla de reapertura

Reabrir la decisión sólo si ocurre al menos uno:

1. nueva cohorte temporal contradice la arquitectura;
2. A/B online confirma o refuta materialmente routing por perfiles;
3. aparece target comercial superior a `scheduled_visit`;
4. nuevas variables cambian materialmente Persona/Broker Supply;
5. una alternativa supera E007/E012/E016 con comparación equivalente y nueva evidencia independiente.

Fuentes: [EV-006](../Evidencias/EV-006_profile_clustering_v2.md), [EV-010](../Evidencias/EV-010_matching_ab_v3.md), [EV-013](../Evidencias/EV-013_matching_profiles_v4.md).
