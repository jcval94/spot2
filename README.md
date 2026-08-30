# Spot2 — Lead Opportunity Score

Repositorio de trabajo para la evaluación técnica de Data Science de Spot2. El objetivo es construir y justificar un **Lead Opportunity Score** que combine calidad del lead, capacidad real del inventario para atenderlo y una estrategia de fallback cuando el inmueble ideal no está disponible.

## Navegación rápida

- [Assessment original](assessment.md)
- [README del candidato](README-candidate.md)
- [Diccionario de variables](feature_dictionary.md)
- [Sandbox de experimentos](experimentos/)
- [Descubrimientos acumulados](experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md)
- [Evidencias](experimentos/Evidencias/)

## Modelo entidad–relación

El siguiente diagrama contiene **todas las variables de las seis tablas entregadas**, su tipo lógico y un **ejemplo real no nulo observado en los CSV del repositorio**. Los ejemplos son ilustrativos por columna y pueden provenir de filas distintas; esto es especialmente importante en campos de renta/venta cuya nulabilidad depende de la modalidad.

```mermaid
erDiagram
    LEADS ||--o{ INQUIRIES : "genera"
    SPOTS ||--o{ INQUIRIES : "recibe"
    SPOTS ||--|| SPOT_ATTRIBUTES : "tiene"
    SPOTS ||--o{ AVAILABILITY_SNAPSHOT : "registra"
    INQUIRIES }o..o| AVAILABILITY_SNAPSHOT : "backward as-of"
    INQUIRIES }o..o| MARKET_CONTEXT : "contexto geo-sector-mes"

    LEADS {
        int lead_id PK "ej: 1"
        string user_type "ej: investor"
        string company_size "ej: small"
        string industry "ej: financial"
        string search_sector "ej: Office"
        string search_modality "ej: sale"
        float target_area_sqm "ej: 690.3"
        float min_budget_mxn_rent_monthly "ej: 36459.82"
        float max_budget_mxn_rent_monthly "ej: 43916.05"
        float min_budget_mxn_sale_total "ej: 38085531.84"
        float max_budget_mxn_sale_total "ej: 56159661.88"
        string preferred_state "ej: Jalisco"
        string preferred_municipality "ej: Zapopan"
        string preferred_corridor "ej: andares-puerta-hierro"
        string source "ej: event"
        int prior_searches "ej: 7"
        int prior_inquiries "ej: 5"
        boolean has_converted_before "ej: false"
        float lead_score_internal "ej: 0.6562"
        datetime created_at "ej: 2025-05-09T00:00:00.000000"
    }

    SPOTS {
        int spot_id PK "ej: 1"
        int broker_id "ej: 238"
        string sector_name "ej: Retail"
        string type_name "ej: Subspace"
        string state "ej: CDMX"
        string municipality "ej: Cuauhtémoc"
        string settlement "ej: Roma Norte"
        string corridor "ej: roma-condesa"
        string region "ej: centro"
        float lat "ej: 19.425615"
        float lon "ej: -99.169211"
        string title "ej: Subspace en Retail - roma-condesa, Cuauhtémoc"
        string description "ej: Amplio espacio con buena iluminación natural. Recién remodelado con acabados modernos. Fácil acceso a transporte público y avenidas principales."
        float area_sqm "ej: 1015.9"
        float price_sqm_mxn_rent "ej: 285.9"
        float price_sqm_mxn_sale "ej: 31411.35"
        float price_total_mxn_rent "ej: 290445.81"
        float price_total_mxn_sale "ej: 23624476.34"
        float maintenance_cost_mxn "ej: 39681.59"
        string modality "ej: rent"
        int days_on_market "ej: 118"
        int total_inquiries "ej: 4"
        int total_views "ej: 47"
        boolean is_active "ej: false"
        datetime created_at "ej: 2026-05-30T00:00:00.000000"
    }

    SPOT_ATTRIBUTES {
        int spot_id PK, FK "ej: 1"
        boolean natural_light "ej: false"
        int luminaires "ej: 0"
        int charging_ports "ej: 0"
        string security_type "ej: full"
        int floor_level "ej: 0"
        int elevators "ej: 7"
        float vertical_height_m "ej: 2.3"
        int parking_spaces "ej: 35"
        string building_status "ej: new"
        string floor_material "ej: ceramic"
        string[] amenities "ej: rooftop, cafeteria, gym, meeting_rooms"
    }

    INQUIRIES {
        int inquiry_id PK "ej: 1"
        int lead_id FK "ej: 1"
        int spot_id FK "ej: 1483"
        datetime inquiry_at "ej: 2025-05-16T20:03:15.000000"
        string channel "ej: email"
        int message_length "ej: 136"
        float requested_area_sqm "ej: 796.3"
        float requested_budget_mxn_rent_monthly "ej: 39529.47"
        float requested_budget_mxn_sale_total "ej: 56159661.88"
        int urgency_days "ej: 134"
        boolean asked_visit "ej: false"
        string broker_response "ej: rejected"
        float broker_response_hours "ej: 19.2"
    }

    AVAILABILITY_SNAPSHOT {
        int snapshot_id PK "ej: 1"
        int spot_id FK "ej: 323"
        date snapshot_date "ej: 2026-06-13"
        boolean is_available "ej: true"
        int days_until_available "ej: 0"
        int competing_inquiries_30d "ej: 8"
    }

    MARKET_CONTEXT {
        string state PK "ej: Nuevo León"
        string municipality PK "ej: San Pedro Garza García"
        string corridor PK "ej: vasconcelos-calzada"
        string sector PK "ej: Land"
        date month PK "ej: 2026-02-01"
        int similar_available_spots "ej: 9"
        float avg_price_sqm_mxn "ej: 48.46"
        float recent_occupancy_rate "ej: 0.669"
        float absorption_velocity_days "ej: 323.3"
        int recent_inquiry_volume "ej: 419"
    }
```

### Convención de tipos

Los tipos del diagrama representan el **tipo lógico de negocio/dato**:

- `int`: entero.
- `float`: número decimal.
- `boolean`: verdadero/falso.
- `string`: texto o categoría.
- `date`: fecha sin componente horario.
- `datetime`: timestamp.
- `string[]`: colección de strings; en el CSV se encuentra serializada como una lista de texto y aplica a `spot_attributes.amenities`.

Los ejemplos fueron tomados de valores **realmente presentes y no nulos** en los archivos de `data/candidate/csv/`. Un ejemplo de una columna no implica que pertenezca a la misma fila que los ejemplos de las demás columnas.

### Reglas de unión importantes

| Relación | Cardinalidad / regla | Uso correcto |
|---|---|---|
| `leads → inquiries` | 1:N por `lead_id` | Historial de interacción de cada lead. |
| `spots → inquiries` | 1:N por `spot_id` | Inmueble consultado en cada interacción. |
| `spots → spot_attributes` | 1:1 por `spot_id` | Enriquecimiento estático del inmueble. |
| `spots → availability_snapshot` | 1:N temporal | Historial de disponibilidad del inmueble. |
| `inquiries → availability_snapshot` | N:0..1 analítica | Usar el último `snapshot_date <= inquiry_at`; **no** hacer un join directo solamente por `spot_id`. |
| `inquiries → market_context` | N:0..1 contextual | Resolver mediante geografía y sector del spot + mes de `inquiry_at`: `(state, municipality, corridor, sector, month)`. |

> **Nota temporal:** la auditoría relacional mostró que un join directo entre `inquiries` y `availability_snapshot` por `spot_id` expande las filas aproximadamente **10.02×**. La construcción correcta usa un backward as-of join (`latest snapshot_date <= inquiry_at`), evitando información futura. Ver [D025](experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md#d025--la-estructura-relacional-está-limpia-availability-exige-un-join-as-of) y [EV-010](experimentos/Evidencias/EV-010_matching_ab_v3.md).

> **Nota semántica:** `spots.total_inquiries` no debe asumirse equivalente al conteo histórico de la tabla `inquiries`; ambos fueron reconciliados y no representan la misma definición de evento.

## Convención de trabajo

Todo análisis experimental vive por defecto dentro de `experimentos/`. La trazabilidad mínima esperada es:

`experimento → EVIDENCIA.md → Evidencias/EV-... → resultado fuente`

y cada descubrimiento consolidado debe poder recorrerse desde:

`conocimiento_agregado/DESCUBRIMIENTOS.md → EV-... → experimento/resultados`

Esto permite conservar resultados positivos, negativos e inconclusos sin contaminar las entradas canónicas del reto.


## Estado de investigación

### Feature Engineering / recuperación T0-T1

**CLOSED / DECISION-READY.**

Punto de entrada oficial:

- [Resumen del flujo](experimentos/registro_flujo/feature_engineering_t0_t1/README.md)
- [Arquitectura final](experimentos/registro_flujo/feature_engineering_t0_t1/ARQUITECTURA_FINAL.md)
- [Cierre](experimentos/registro_flujo/feature_engineering_t0_t1/CIERRE.md)
- [Checklist de cierre](experimentos/registro_flujo/feature_engineering_t0_t1/CHECKLIST_CIERRE.md)
- [Estado final machine-readable](experimentos/registro_flujo/feature_engineering_t0_t1/FINAL_STATE.json)

Decisión resumida:

- T0 LeadQuality: `NEUTRAL_EVIDENCE_BACKED`;
- T1 LeadQuality: `NEUTRAL_EVIDENCE_BACKED`;
- T0/T1 mantienen capas semánticas para explicación, matching y routing;
- T2 conserva el candidato E029 pendiente de validación prospectiva;
- E039 documenta el extractor semántico LLM futuro y queda bloqueado únicamente porque no existe raw inquiry text.

Los pendientes de prospective gate y A/A productivo pertenecen a la fase de lanzamiento y no reabren la investigación offline T0/T1.
