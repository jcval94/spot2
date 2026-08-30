# LLM Feature Analysis — variables donde sí puede aportar

## Conclusión

Un LLM **no es un tratamiento general de datos** para Spot2. La gran mayoría de las 86 columnas se resuelve mejor con reglas determinísticas, semántica de unidades, point-in-time joins y transforms tabulares. El LLM tiene valor donde existe **lenguaje o coherencia semántica entre campos**, no para “rellenar” números.

## 1. `spots.title` + `spots.description` — ALTA prioridad LLM

El copy puede ser incoherente con `sector_name` o `spot_attributes`. E015 ya demostró que hay patrones cross-field que reglas simples no habían representado inicialmente, especialmente `Land × lenguaje de edificio/interiores`.

Un output estructurado por `spot_id` podría producir:

- `semantic_issue_count`
- `semantic_high_severity_flag`
- `cross_field_mismatch_flag`
- `copy_structured_consistency_score` [0,1]
- `claim_natural_light`
- `claim_security`
- `claim_parking`
- `claim_readiness`
- `claim_accessibility`
- `claim_use_case`
- `unverifiable_claim_count`
- `llm_confidence`

**Uso primario:** Catalog QA / Inventory Quality. Como feature predictiva en T1/T2 debe probarse como challenger separado; no se asume que un listing semánticamente limpio convierta mejor.

El copy actual es extremadamente templated: 12 oraciones componen todo el catálogo. La arquitectura preferida sigue siendo:

`Rules conocidas -> LLM para discovery de long-tail -> revisión humana -> promoción de patrones estables a Rules`.

## 2. `inquiries.message_length` — el LLM NO puede ayudar con el dato actual

`message_length` es sólo longitud. No contiene el mensaje.

No es posible derivar honestamente intent, constraints o sentiment mediante LLM a partir de un entero.

### Si Spot2 entrega raw inquiry text

Entonces sí propondría:

- `intent_stage`: exploratory / comparing / ready_to_visit / ready_to_transact
- `intent_strength`: 0–1
- `urgency_explicit`
- `requested_area_extracted`
- `requested_budget_extracted`
- `location_flexibility`
- `area_flexibility`
- `budget_flexibility`
- `must_have_constraints_count`
- `use_case`
- `decision_timeline`
- `missing_information_count`
- `semantic_completeness_score`
- `extraction_confidence`

Serían elegibles **desde T1**, porque el texto ya existe al llegar la inquiry. Nunca deberían incluir la respuesta posterior del broker.

## 3. `spot_attributes` — LLM sólo como auditor, no como imputador

`natural_light`, `security_type`, `parking_spaces` y `building_status` pueden compararse contra copy.

El LLM puede detectar contradicciones o ambigüedad, pero **no debe reemplazar el dato estructurado con una inferencia inventada**. Si existe conflicto:

- conservar ambas fuentes;
- crear flag de discrepancia;
- mandar a QA cuando severidad/confianza lo amerite.

## 4. `industry`, `company_size`, geografía, precios, área — LLM NO recomendado

Son variables estructuradas. No hay beneficio justificable frente a normalización determinística. Usar un LLM para imputarlas añadiría costo, variabilidad y riesgo de alucinación.

## 5. `broker_response` / `broker_response_hours` — LLM NO recomendado

La inconsistencia es de semántica de evento, no de lenguaje. La corrección es determinística:

- respuesta realizada sólo si status ∈ {accepted, rejected, scheduled_visit};
- `broker_response_hours` debe existir para reconstruir `response_event_at`;
- `no_response + hours` se marca como inconsistencia y no se convierte en respuesta.

## 6. `market_context` — LLM NO resuelve el problema

La limitación es que falta `published_at/effective_from`. Un LLM no puede inventar disponibilidad histórica. Se necesita metadata o una política de publicación verificable.

## Hook recomendado para una iteración posterior

No se conecta la API en E016. Si se decide probar features LLM, el pipeline debe consumir un sidecar versionado por `spot_id`, con schema estricto y prompt/model/version registrados.

Primera prueba incremental:

1. ABT base E016 sin LLM.
2. + Rules semantic flags.
3. + LLM incremental semantic flags.
4. Validación temporal y ablación.

Sólo promover una feature LLM si aporta señal incremental o valor operacional demostrable y mantiene trazabilidad.
