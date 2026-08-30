# Target definitiva v1 — Lead Opportunity

## Decisión de producto

El sistema debe priorizar leads que puedan avanzar comercialmente dentro de un horizonte útil para Growth. El evento proxy elegido es **agendar una visita**, porque es observable en los datos entregados, representa avance comercial material y ocurre antes que el cierre final.

No se usa `accepted`, respuesta genérica del broker ni número de inquiries como éxito.

## Target dinámica de entrenamiento

Para un lead `l` evaluado en el scoring time `t`:

```
target_scheduled_visit_30d(l,t) = 1
si existe al menos un evento broker_response == "scheduled_visit"
con response_event_at > t y response_event_at <= t + 30 días.
En cualquier otro caso maduro = 0.
```

### Elegibilidad de un snapshot

Un snapshot entra al dataset supervisado sólo si:

1. no existe un `scheduled_visit` del lead con `response_event_at <= t`;
2. `t <= observable_end - 30 días`;
3. toda feature usada era observable en o antes de `t`;
4. T0 usa `leads.created_at`;
5. T1 usa el `inquiry_at` de la primera inquiry;
6. T2 usa cada `inquiry_at` posterior mientras el lead siga pre-visita.

### Observabilidad del timestamp del outcome

En producción E028, `response_event_at` debe ser el **timestamp real del evento backend**.

En el paquete candidato no existe ese timestamp de forma directa; se aproxima como:

`inquiry_at + broker_response_hours`.

El EDA encontró que **14.97% de las filas scheduled_visit tienen broker_response_hours faltante**. Por tanto, cuando una visita con hora desconocida podría caer dentro de la ventana de 30 días, el label retrospectivo es:

`AMBIGUOUS_UNKNOWN_EVENT_TIME`

y se excluye del entrenamiento/evaluación binaria. **Nunca se convierte silenciosamente en 0.**

La semántica canónica está congelada en [target_contract.json](target_contract.json) y la implementación ejecutable en [target_contract.py](target_contract.py). Los casos de frontera están cubiertos por [test_target_contract.py](test_target_contract.py).

Este problema es retrospectivo. Para abrir el A/B productivo se exige >=99.5% de completitud del timestamp real de scheduled_visit; una pérdida material/asimétrica invalida la lectura causal.

## Censoring

Los snapshots con menos de 30 días completos hacia el fin observable **no se etiquetan como negativos**: se excluyen como right-censored.

También se excluyen como ambiguos los snapshots cuyo outcome exacto no puede determinarse por falta del timestamp del evento.

### Múltiples snapshots del mismo lead

Un mismo lead puede tener varios T2 positivos antes de una misma visita. Eso es correcto para un modelo de re-scoring porque responde a preguntas distintas en tiempos distintos.

Pero:

- train/validation/test se particionan por `lead_id`, nunca por snapshot;
- bootstrap se hace por lead;
- la métrica causal online se mide una sola vez por lead.

## Assignment canónico

`assignment_at` es el timestamp UTC persistido por el servicio de randomización **antes** de calcular cualquier score o modificar routing.

Un lead es elegible sólo si:

1. entra por primera vez a la población de Growth definida antes del experimento;
2. no tiene un `scheduled_visit` ya observado antes de `assignment_at`;
3. no es test/interno/duplicado bajo reglas congeladas pre-randomización.

La primera asignación gana y es inmutable. Reintentos técnicos nunca crean una segunda asignación.

## Target primaria del A/B

Para un lead randomizado en `assignment_at`:

```
AB_primary(l) = 1
si existe al menos un scheduled_visit
con response_event_at > assignment_at
y response_event_at <= assignment_at + 30 días.
```

Una fila por lead. Múltiples eventos `scheduled_visit` cuentan una sola vez mediante `MAX(event_indicator)`; duplicados técnicos del mismo evento deben deduplicarse por el identificador backend disponible antes de construir el outcome.

El denominador son **todos los leads elegibles randomizados**, aunque el tratamiento no consiga score, fallback o broker disponible.

Eso implementa intention-to-treat y evita sesgo por exposición posterior.

## Por qué 30 días

- es suficientemente corto para que Growth pueda actuar y aprender;
- coincide con el proxy ya usado en la evaluación;
- reduce mezcla con cambios de mercado muy posteriores;
- permite comparar cohortes con una ventana fija;
- evita definir éxito según cuánto tiempo estuvo observado cada lead.

Dado el drift temporal detectado, el horizonte fijo es además indispensable para que las cohortes sean comparables.

## Limitaciones

`scheduled_visit` es un **proxy de progreso comercial**, no el outcome oculto de conversión final ni un contrato firmado.

En producción, si Spot2 dispone de cierre/lease/venta de calidad suficiente, se recomienda:

- mantener scheduled_visit_30d como target operacional de corto plazo;
- añadir close_90d o revenue_90d como outcome de negocio secundario/north-star;
- no reemplazar la target de 30 días por cierre hasta demostrar cobertura y latencia suficientes.

## Variables explícitamente prohibidas

Para cualquier score histórico quedan bloqueadas:

- respuesta de la inquiry actual o futura;
- `broker_response_hours` de la inquiry actual;
- cualquier visita ocurrida después del scoring time como feature; la visita futura sólo puede aparecer en el label;
- `lead_score_internal`;
- current-state Spot fields no reconstruidos as-of como `days_on_market`, `total_views`, `total_inquiries`, `is_active`;
- Market Context sin semántica de publicación/effective time defendible.

## Nombre canónico

**Offline/model training:** `target_scheduled_visit_30d`.

**Online A/B primary outcome:** `lead_scheduled_visit_30d_from_assignment`.
