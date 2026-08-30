# Treatment policy v1 — Dynamic Lead Opportunity

## 1. Principio

El A/B no debe confundir "mejor modelo" con una intervención indefinida. El brazo B usa una política congelada:

```
OpportunityScore(l,t) = LeadQuality(l,t) × InventoryServiceable(l,t)
```

donde:

- `LeadQuality(l,t)` es la probabilidad calibrada de `target_scheduled_visit_30d=1` usando únicamente información disponible en `t`;
- `InventoryServiceable(l,t)` es un indicador 0/1 de que existe al menos un Spot viable y suficientemente fresco para atender al lead ahora o dentro de su urgencia conocida.

No se convierte una heurística de inventario en una "probabilidad" artificial. En esta primera versión, serviceability es una regla de negocio auditable.

## 2. Lead Quality

### Decisión posterior a E021–E027

La versión E005 no puede entrar intacta al A/B.

Quedan bloqueados como inputs predictivos del release actual:
`score_weekday`, `score_hour`, `score_month`, `days_from_lead_creation`, `inquiry_number`, `days_since_first_inquiry` y `prior_searches`.

También quedan fuera el broker prior y la edad cruda del snapshot de availability.

**Stage policy de lanzamiento:**

- T0: **LeadQuality neutral, evidence-backed por E032/E035/E037**. Search Need y specificity siguen activas como representación explicativa/operativa, no como propensity ranking.
- T1: **LeadQuality neutral, evidence-backed por E033/E035/E036/E037**. Dynamic Need, Need transition, Physical/Location y Lead×Spot fit siguen disponibles para matching/routing experimental; serviceability/fallback permanece activo.
- T2: usa el artifact congelado E029 **sólo si el prospective gate post-freeze pasa**; antes de ese PASS permanece neutral.

Si un stage no pasa el gate, su LeadQuality se trata como neutral para ordenamiento; no se fabrica una probabilidad discriminante.

Ver [OFFLINE_DECISIONS.md](OFFLINE_DECISIONS.md).

## 2.1 Lead Quality

El release candidate E029 ya está congelado; E028 sólo puede iniciar después de que ese artifact pase su prospective gate y el A/A productivo.

Reglas:

1. modelo y feature list versionados por commit/hash;
2. calibración congelada;
3. no hay retraining durante el A/B;
4. T0/T1/T2 comparten la misma target futura de 30 días;
5. el score se recalcula en cada stage elegible;
6. una visita ya ocurrida saca al lead del universo de scoring posterior.

Si el modelo no produce score, el lead permanece en Treatment por ITT y el fallo entra a guardrails.

## 3. InventoryServiceable

Para un lead en tiempo `t`, primero se genera el conjunto de spots elegibles.

### Restricciones duras

Un Spot puede ser candidato sólo si:

1. `sector_name == search_sector`;
2. modalidad compatible:
   - rent → rent/both;
   - sale → sale/both;
   - both → cualquier modalidad compatible con al menos una intención;
3. geografía:
   - si existe `preferred_corridor`, mismo corredor;
   - si no existe corredor pero sí municipio, mismo municipio;
4. disponibilidad:
   - en producción se consulta el estado actual del inventario;
   - en backtest se usa exclusivamente el último snapshot con `snapshot_date <= t`;
   - si el estado histórico tiene >90 días de antigüedad se considera **desconocido**, no disponible;
   - si `is_available=true`, pasa;
   - si no está disponible pero existe `urgency_days`, pasa sólo cuando `days_until_available <= urgency_days`;
5. presupuesto:
   - renta: `price_total_mxn_rent <= max_budget_mxn_rent_monthly` cuando ambos existen;
   - venta: `price_total_mxn_sale <= max_budget_mxn_sale_total` cuando ambos existen;
   - presupuesto faltante no se transforma en rechazo automático.

No se usa `days_on_market`, `total_views`, `total_inquiries` ni `is_active` histórico sin reconstrucción point-in-time.

### Definición

```
InventoryServiceable(l,t) = 1  si candidate_spots(l,t) no está vacío
                           = 0  en otro caso
```

Esto evita inventar precisión estadística donde los datos sólo justifican una regla de elegibilidad.

## 4. Requested Spot y fallback

Si la inquiry refiere a un Spot específico:

1. si el Spot solicitado pertenece a `candidate_spots`, se conserva como primera opción;
2. si no, se activa fallback;
3. el fallback sólo puede elegir dentro de `candidate_spots`.

Para ordenar los alternativos se usa una distancia simple, reproducible y libre de outcome:

```
area_distance   = abs(log(spot_area / requested_or_target_area))
budget_distance = abs(log(spot_total_price / max_budget))
fallback_distance = mean(componentes disponibles)
```

Menor distancia = mejor alternativa.

- Si falta área, se omite ese componente.
- Si falta presupuesto, se omite ese componente.
- Empates: `spot_id` ascendente para determinismo.
- Se sirven máximo 5 alternativas.

El ranking no usa `scheduled_visit` histórico, broker performance ni celdas de compatibilidad outcome-derived. Eso mantiene el primer A/B causal centrado en **priorización + serviceability**, no en un ranker offline todavía inconcluso.

## 5. Cómo actúa Growth

Treatment no es sólo un número mostrado.

- `InventoryServiceable=1`: ordenar la cola de acción por OpportunityScore descendente.
- Ties: score anterior/created_at más antiguo primero.
- T1/T2 reemplazan el score previo del mismo lead; no crean nuevos "leads" en el denominador.
- `InventoryServiceable=0`: mover a cola "inventory constrained"; no desaparece del experimento ni del análisis ITT.
- Si aparece inventario nuevo durante los 30 días, el lead puede volver a ser serviceable y reingresar a la cola Treatment con su score vigente.

## 6. Qué NO cambia durante E028

Una vez empieza la randomización quedan congelados:

- feature set;
- modelos por stage;
- calibradores;
- serviceability rules;
- cutoff de staleness;
- fórmula del Opportunity Score;
- fallback constraints y ranking;
- UI/routing behavior del brazo Treatment;
- primary target y MDE.

Los cambios urgentes de seguridad/calidad requieren detener el experimento; no se parchea silenciosamente un solo brazo.

## 7. Por qué esta política

Es intencionalmente conservadora:

- convierte Lead Quality en una probabilidad calibrada;
- trata inventario como una restricción operacional observable;
- evita presentar un heuristic score como P(disponibilidad);
- mantiene fallback explicable;
- reduce grados de libertad antes de un RCT;
- permite que una versión posterior pruebe un Inventory/Matching model separado si E028 demuestra valor del sistema.


## Feature policy v2

La separación entre LeadQuality y capas semánticas/routing se congela en [E038](../E038_stage_aware_feature_policy/README.md). Neutralidad de LeadQuality no significa que T0/T1 estén apagados.
