# Statistical Analysis Plan — E028

## 1. Estimand primario

Efecto causal de **asignar** un lead elegible al sistema dinámico completo frente al proceso actual:

```
ATE_30d = P(Y=1 | assigned Treatment) - P(Y=1 | assigned Control)
```

con:

`Y = lead_scheduled_visit_30d_from_assignment`.

La escala primaria es **puntos porcentuales absolutos**. Odds ratio y relative lift son complementarios y no sustituyen el estimand.

## 1.1 Assignment e identidad experimental

- `assignment_at` se persiste en UTC antes de scoring/routing experimental.
- La primera asignación por `experiment_id × lead_id` es inmutable.
- Reintentos técnicos recuperan el mismo brazo.
- Un lead con `scheduled_visit` ya observado antes de `assignment_at` no entra a la población elegible.
- La tabla de assignment debe imponer unicidad de `experiment_id × lead_id`; cualquier cross-arm assignment invalida el experimento.

## 2. Analysis population

Intention-to-treat:

- una fila por `lead_id`;
- incluye todos los leads randomizados elegibles;
- el brazo se toma de la asignación original;
- score failure, fallback failure o falta de acción del broker no permiten cambiar de brazo ni excluir al lead.

No se crea una población "exposed only" para el análisis primario.

## 3. Maduración

Un lead entra al análisis final sólo cuando han transcurrido 30×24 horas completas desde `assignment_at`.

No se compara un brazo con más días observables que el otro.

Tiempo canónico: UTC.

Ventana del evento: `(assignment_at, assignment_at + 30 days]`.

## 4. Outcome construction

Un lead es positivo si cualquier evento backend verificable cumple:

- `broker_response == scheduled_visit`;
- mismo `lead_id`;
- `response_event_at` dentro de la ventana.

Múltiples visitas cuentan una sola vez para el primary. Antes de agregar a lead-level, eventos backend duplicados se deduplican por el identificador técnico disponible; si ese identificador no existe, se documenta una clave determinista de deduplicación antes de abrir el experimento.

La construcción del outcome no puede usar ningún evento generado antes de `assignment_at`.

Si el pipeline de outcomes tiene pérdida de cobertura material, no se imputa silenciosamente: se activa un blocker de instrumentación.

## 5. Balance y SRM

Antes de mirar efecto:

1. verificar 50/50 global;
2. verificar asignación por estrato;
3. revisar covariables pre-treatment.

SRM:

- chi-square binomial allocation test;
- umbral de investigación: p < 0.001;
- un SRM no explicado invalida la lectura causal hasta resolver la causa.

Las diferencias de covariables no se usan para decidir "si la randomización funcionó" por p-values múltiples; se revisan magnitudes estandarizadas.

## 6. Primary analysis

Calcular por brazo:

- N randomizado y N maduro;
- positivos;
- tasa;
- Treatment − Control en pp;
- IC95% bilateral para diferencia de proporciones;
- p-value bilateral alpha=0.05.

La regla de producto sigue el intervalo y MDE pre-registrados, no sólo el p-value.

## 7. Sensitivity analysis pre-especificado

Modelo de probabilidad / GLM con:

- treatment assignment;
- search_sector;
- search_modality;
- user_type;
- assignment week.

Objetivo: precisión y robustez ante drift temporal concurrente.

El coeficiente marginal de Treatment se convierte nuevamente a diferencia absoluta de riesgo.

Si adjusted y unadjusted difieren materialmente, reportar ambos e investigar; no escoger retrospectivamente el más favorable.

## 8. Drift

Randomización concurrente protege la comparación A/B de un drift común, pero drift sigue importando para heterogeneidad y transportabilidad.

Pre-especificar:

- tasa primary por assignment week y brazo;
- delta por assignment week con intervalos descriptivos;
- distributions de features/OpportunityScore por semana;
- proporción de leads T0/T1/T2 por semana;
- availability freshness por semana.

No se interrumpe por una semana favorable/desfavorable salvo guardrail operacional.

## 9. Secondary metrics

Se reportan con IC95% y etiqueta **secondary/exploratory**.

No pueden transformar un primary INCONCLUSIVE/NO-SHIP en SHIP.

Si se hacen pruebas formales múltiples sobre secundarios, aplicar Holm para la familia declarada; por defecto se interpretan descriptivamente.

## 10. Time-to-event

Para `time_to_first_scheduled_visit`:

- Kaplan-Meier / cumulative incidence descriptiva por brazo;
- Cox o AFT sólo como sensibilidad;
- no sustituye el binary 30d primary.

## 11. Guardrails duros

Antes de SHIP deben cumplirse:

- cross-arm assignment: 0 casos;
- assignment/instrumentation completeness >=99.5%;
- scoring/ranking failure en Treatment <=1.0%;
- recommendation de Spot conocido como no disponible <=1.0%;
- Treatment − Control en no-result rate <= +2.0 pp;
- sin SRM no explicado.

Si un guardrail incumple por un bug de medición, el experimento se considera **INVALID / NEEDS_REPAIR**, no automáticamente evidencia de efecto negativo.

## 12. Operational monitors

No son por sí solos criterios de causal success/failure:

- p50/p95 time to broker response;
- broker workload concentration;
- fallback coverage;
- availability freshness;
- p95 ranking latency;
- queue size;
- distribución del Opportunity Score.

## 13. Missing data

Features faltantes se manejan según el modelo congelado.

Outcome primario no se imputa cuando falta por fallo del pipeline; se cuantifica cobertura por brazo y se bloquea la conclusión si la pérdida puede sesgar el contraste.

## 14. Heterogeneity

Cortes pre-especificados:

- sector;
- modalidad;
- user_type;
- assignment week;
- T0-only vs leads que alcanzaron T1/T2 (este último es post-treatment y por ello sólo descriptivo, nunca causal de subgrupo).

No se lanzan políticas segmentadas a partir de un subgrupo pequeño sin un experimento confirmatorio.

## 14.1 A/A dry run antes de launch

Antes del primer lead real en Treatment se ejecuta `validate_protocol.py` y/o un A/A equivalente en producción para comprobar:

- una fila por lead;
- assignment estable;
- ausencia de cross-arm contamination;
- SRM plumbing;
- maduración completa de 30 días en el backtest;
- target lead-level;
- cobertura de instrumentación.

El pseudo-delta A/A nunca se interpreta como efecto causal del sistema.

## 15. Stopping

- fixed sample;
- full 30-day maturation;
- no peeking del treatment effect;
- no optional stopping;
- si se necesita detener por seguridad/calidad, registrar fecha, motivo y población afectada.

## 16. Decision table

### SHIP

- delta primary >= +2.0 pp;
- IC95% lower bound >0;
- hard guardrails pass.

### NO-SHIP

- IC95% upper bound < +2.0 pp.

Esto significa que el experimento ha descartado el efecto mínimo que justificaba el cambio.

### INCONCLUSIVE

Cualquier otro resultado estadísticamente válido.

### INVALID / NEEDS_REPAIR

SRM no explicado, contaminación de brazos, pérdida material de outcomes o violación grave del protocolo.
