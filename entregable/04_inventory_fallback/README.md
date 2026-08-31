# Entregable 4 — Inventory Availability Model + política operativa de Fallback

> **Autoridad metodológica:** `codexway/**`.  
> **Evidencia complementaria:** `experimentos/**` y `AssessmentSol1/**`.  
> **Alcance de este documento:** Inventory Availability / Inventory Serviceability y Fallback.  
> **Fuera de alcance por instrucción:** no se define ni se modifica todavía el Opportunity Score.

---

## 1. Resumen ejecutivo

El problema de inventario es distinto del problema de calidad del lead.

**Lead Quality** responde:

> ¿Qué tan probable es que el lead progrese al outcome comercial definido, usando únicamente información permitida en el momento T1?

**Inventory Serviceability** responde:

> ¿Existe, con la información de inventario que realmente era conocible en `score_time`, un Spot que pueda atender razonablemente la necesidad del lead?

Estas dos preguntas deben mantenerse separadas. Un lead puede ser excelente y no tener inventario servible; también puede existir un Spot perfecto para un lead con baja propensión comercial.

La solución final conserva la arquitectura de `codexway`:

1. construir el universo de Spots que **ya existían** en `score_time`;
2. aplicar compatibilidad obligatoria de modalidad;
3. recuperar Availability con un **strict backward as-of**: último `snapshot_date <= score_time`;
4. distinguir disponibilidad conocida de incertidumbre;
5. calcular compatibilidad de área, precio y geografía;
6. construir cotas inferior/superior de matching cuando Availability es desconocida o stale;
7. ordenar candidatos de manera determinista;
8. utilizar los mejores **3** candidatos alternativos para el componente agregado de fallback/serviceability;
9. exponer **hasta 5** recomendaciones de fallback, porque ése es el límite canónico congelado en `codexway/config/base.yaml`;
10. devolver `NO_RESULT` antes que fabricar una recomendación que viole restricciones o dependa de información futura.

La evidencia complementaria aporta dos conclusiones especialmente valiosas:

- Availability presenta un fuerte **coverage drift temporal**; no puede tratarse como una fuente estacionaria.
- El Spot históricamente visitado **no es un gold label limpio de recommendation relevance**. Por tanto, Hit@K histórico es diagnóstico, no el gate principal del fallback.

La conclusión metodológica más importante es:

> **Availability point-in-time está bien defendida; el matching histórico completo sigue siendo condicional porque varios atributos del listing, especialmente precios, no tienen versionado temporal.**

---

## 2. Modelo conceptual

El subsistema puede pensarse como cinco capas independientes:

    Lead en T1
       |
       | necesidad expresada en la primera inquiry
       v
    [1] Candidate universe
       |-- Spot existía en score_time
       |-- modalidad compatible
       |-- sector/estado permitido por la política final
       v
    [2] Availability PIT
       |-- último snapshot_date <= score_time
       |-- nunca snapshot futuro
       v
    [3] Compatibility
       |-- area_fit
       |-- price_fit
       |-- geo_fit
       |-- availability bounds
       v
    [4] Inventory Serviceability
       |-- exact component
       |-- fallback component top-3
       |-- lower / upper bound
       |-- confidence / uncertainty
       v
    [5] Fallback presentation
       |-- ranking determinista
       |-- hasta 5 recomendaciones
       |-- reason codes
       '-- NO_RESULT si no hay alternativa válida

La separación entre capas es deliberada. En particular, **Lead Quality no entra en Candidate Generation, Availability ni ranking de fallback**. Esto evita que una señal comercial contamine una pregunta de factibilidad de inventario.

---

## 3. Lead Quality vs Inventory Serviceability

| Dimensión | Lead Quality | Inventory Serviceability |
|---|---|---|
| Pregunta | ¿El lead progresará al target? | ¿El inventario conocido puede atenderlo? |
| Unidad principal | Lead / primera inquiry T1 | Lead × candidate Spot en `score_time` |
| Outcome | `scheduled_visit` de la primera inquiry | No usa el target comercial para construir candidatos |
| Información temporal | Sólo features permitidas en T1 | Spot existente + Availability as-of |
| Availability | **No entra** al modelo de Lead Quality | Es una señal central |
| Ranking | Probabilidad/calidad comercial | Compatibilidad + disponibilidad + fallback |
| Incertidumbre | Calibración/model uncertainty | Missing/stale snapshot y atributos no versionados |
| Uso | Priorizar propensión | Determinar si el lead es atendible y con qué alternativas |

**Regla de diseño:** no interpretar Inventory Serviceability como otra versión de Lead Quality, ni Lead Quality como evidencia de disponibilidad.

---

## 4. Momento de decisión y contrato point-in-time

El momento operativo principal sigue siendo **T1: primera inquiry**, después de que el request existe y antes de conocer la respuesta del broker.

Para cada candidato, el sistema sólo puede usar información que habría estado disponible en ese instante.

### 4.1 Existencia del Spot

Un Spot sólo puede entrar al universo si:

`spot.created_at <= score_time`

Un Spot creado después de `score_time` es futuro y debe excluirse aunque más adelante resulte ser una excelente alternativa.

### 4.2 Availability

Para cada `spot_id` se busca:

`max(snapshot_date) tal que snapshot_date <= score_time`

Éste es un **backward as-of join**.

No se permite:

- nearest snapshot si puede seleccionar una observación futura;
- forward fill desde una fecha posterior;
- unir todos los snapshots por `spot_id` y decidir después;
- usar el snapshot "más cercano" sin imponer dirección backward.

### 4.3 Por qué un join convencional introduce leakage

Un join directo `Inquiry × Availability` por `spot_id` produce múltiples filas por inquiry y mezcla pasado con futuro. La auditoría experimental observó una expansión aproximada de **10.02x**.

Si después se elige, por ejemplo, el snapshot de menor distancia temporal, el algoritmo puede terminar usando una observación posterior al score. Eso introduce **look-ahead leakage**: el modelo conoce un estado de inventario que el sistema real todavía no conocía.

La evidencia de `codexway` es fuerte en este punto:

- join de Availability: `STRICT_BACKWARD_ASOF`;
- violaciones por snapshot futuro: **0**.

---

## 5. Definición de Availability

### 5.1 Estados operativos de `codexway`

La implementación ganadora materializa cuatro comportamientos:

| Estado lógico | Condición | Cota inferior | Cota superior | Interpretación |
|---|---|---:|---:|---|
| Disponible ahora | snapshot fresco + `is_available=true` | 1 | 1 | atendible ahora |
| Disponible dentro de urgencia | snapshot fresco, hoy no disponible, pero `days_until_available <= urgency` | valor entre 0 y 1 | igual | parcialmente atendible dentro de la ventana |
| No atendible | snapshot fresco y no entra en urgencia | 0 | 0 | disponibilidad conocida insuficiente |
| Desconocido / stale | no hay snapshot previo **o** el último snapshot excede freshness | 0 | 1 | no afirmar disponible ni no disponible |

En el código, el último caso aparece como:

`unknown_missing_or_stale`

Esto es conservador: la cota inferior asume que no puede contarse como disponibilidad confirmada y la cota superior conserva la posibilidad de que sí pueda servir.

### 5.2 `UNKNOWN != UNAVAILABLE`

Ésta es una regla crítica.

**UNAVAILABLE / fresh_not_attendable** significa que existe una observación válida y suficientemente fresca que dice que el Spot no puede atender la urgencia del lead.

**UNKNOWN** significa que la evidencia histórica disponible no permite afirmar el estado actual.

Por tanto:

- `UNAVAILABLE` puede excluirse como alternativa confirmada;
- `UNKNOWN` requiere verificación y no debe convertirse silenciosamente en cero factual;
- una ausencia de datos no es evidencia de ausencia de inventario.

### 5.3 Missing histórico vs snapshot stale

Aunque `codexway` agrupa ambos en el mismo estado operacional de incertidumbre, conceptualmente no son lo mismo:

**Sin observación histórica previa**
- no existe ningún `snapshot_date <= score_time`;
- no sabemos cuál era el último estado conocido;
- incertidumbre epistemológica máxima.

**Snapshot stale**
- sí existe una observación histórica previa;
- sabemos qué decía;
- pero tiene demasiada antigüedad para afirmar que sigue describiendo el estado operativo actual.

AssessmentSol1 hizo explícita esta distinción y propuso que stale reduzca confidence sin borrar el hecho de que alguna observación fue conocida. Esa semántica es una mejora de auditoría útil, pero **no sustituye la implementación final de `codexway`**. Para esta entrega:

- la **decisión canónica** sigue usando las cotas de `codexway` para missing/stale;
- el reporte debe conservar un reason/audit subtype que distinga `NO_PRIOR_SNAPSHOT` de `STALE_SNAPSHOT`.

Así se evita la confusión sin cambiar el comportamiento ganador.

---

## 6. Freshness y coverage drift

`codexway` congela un lens operativo de **30 días** para freshness.

Sensibilidad del mismo candidate universe:

| Freshness | Candidate rows frescos | Unknown/stale | Leads con al menos un candidato fresco |
|---:|---:|---:|---:|
| 7 días | 19.16% | 80.84% | 93.46% |
| 30 días | 57.09% | 42.91% | 98.34% |
| 90 días | 86.03% | 13.97% | 98.52% |

Esto demuestra que la elección de freshness cambia radicalmente la **certeza**, aunque la mayoría de leads tenga al menos alguna alternativa con observación fresca.

La investigación histórica también encontró un fuerte régimen temporal de cobertura:

- ~6.5% en enero de 2025;
- ~84.7% en junio de 2025;
- ~96.6% en septiembre de 2025;
- 100% desde enero de 2026 en el audit citado.

Por eso la cobertura de Availability debe monitorearse por cohorte y mes. Un modelo puede parecer mejor simplemente porque en períodos tardíos tiene más inventario observado.

**Consecuencia:** nunca evaluar un ranking de inventario sin reportar simultáneamente freshness/coverage.

---

## 7. Candidate Generation

### 7.1 Restricciones duras

En la solución final de `codexway`:

1. el Spot debe existir en `score_time`;
2. la modalidad debe ser compatible;
3. el pool principal conserva el mismo `search_sector` y estado deseado;
4. el Spot originalmente solicitado se reincorpora explícitamente al pool para poder evaluar el exact match;
5. no se usa un snapshot futuro.

La modalidad es una restricción dura:

- rent sólo contra rent/both;
- sale sólo contra sale/both;
- both puede aceptar ambas modalidades compatibles.

### 7.2 Geografía

La relajación geográfica se representa explícitamente:

1. mismo corredor;
2. mismo municipio;
3. mismo estado.

En `codexway` se asignan fits:

- corredor: 1.00;
- municipio: 0.85;
- estado: 0.65.

No conviene ocultar esta relajación. Un fallback de mismo estado no debe presentarse como equivalente a un exact corridor match.

### 7.3 Área

El matching de área usa una función simétrica en escala logarítmica:

`exp(-abs(log(candidate_area / desired_area)))`

La función vale 1 en match exacto y cae suavemente cuando el Spot es demasiado grande o pequeño.

AssessmentSol1 comparó una forma de gap relativo contra log-ratio y encontró **94.85% de overlap Top-5**. Esa evidencia confirma que la decisión de área no depende de una fórmula exótica; diferentes funciones razonables producen ordenamientos locales muy parecidos.

### 7.4 Precio: limitación PIT importante

`codexway` calcula un `price_fit` con precios del Spot. Sin embargo, el propio champion declara que los atributos del listing —incluyendo precio— **no están versionados históricamente**.

Por tanto:

> el Availability join es estrictamente PIT, pero el **full historical matching score es condicional**.

`spot.created_at <= score_time` prueba que el listing ya existía; no prueba que el precio almacenado hoy sea exactamente el que estaba vigente en `score_time`.

AssessmentSol1 llevó esta cautela al extremo y bloqueó el historical budget fit, marcándolo `UNKNOWN_PRICE_NOT_PIT`. No se adopta esa sustitución como política final porque `codexway` conserva autoridad, pero sí se incorpora su auditoría como limitación explícita.

**Requisito de producción:** versionar precios y demás atributos mutables con `effective_from/effective_to` o un snapshot/CDC equivalente.

---

## 8. Matching y ranking

Para un candidato, `codexway` calcula:

- `area_fit`;
- `price_fit`;
- `geo_fit`;
- `availability_fit_lower`;
- `availability_fit_upper`.

La compatibilidad sin Availability es una media geométrica de área, precio y geografía.

Después construye:

`candidate_match_lower = geometric_mean(area, price, geo, availability_lower)`

`candidate_match_upper = geometric_mean(area, price, geo, availability_upper)`

Esta construcción tiene una propiedad útil: cuando Availability es desconocida, el candidato no desaparece. Queda representado como un intervalo.

### Ranking canónico

Los candidatos se ordenan por:

1. mayor `candidate_match_lower`;
2. mayor `candidate_match_upper`;
3. menor `candidate_spot_id` como desempate determinista.

El primer criterio favorece opciones defendibles sin depender de la interpretación optimista. El segundo permite ordenar empates conservadores por potencial. El tercero garantiza reproducibilidad.

### Evidencia sobre ranking alternativo

AssessmentSol1 comparó un ranking tiered lexicographic contra un score continuo:

- overlap Top-5: **60.11%**;
- el continuo relajaba tier aun existiendo Tier-0 en **11.56%**;
- seleccionaba una relajación de sector pese a existir inventario same-sector en **5.72%**.

La conclusión complementaria es útil: los pesos continuos pueden optimizar un score y al mismo tiempo violar expectativas de producto. Aunque `codexway` usa su propio geometric matching, la interfaz debe seguir mostrando la relajación geográfica y los reason codes para que el usuario operativo entienda qué se sacrificó.

---

## 9. Inventory Serviceability

La solución final no convierte Inventory en un simple booleano.

Para el Spot exacto se calcula un componente lower/upper. Para alternativas se toman los mejores candidatos y se construye un componente de fallback.

### 9.1 K interno del componente de fallback

Aquí existe una distinción que debe quedar completamente explícita:

- **K de agregación de serviceability = 3**;
- **K máximo de recomendaciones visibles = 5**.

En el código de `codexway`:

- se toman los `top_lower[:3]` y `top_upper[:3]` para construir el componente agregado;
- se aplica una penalización de profundidad `1 - exp(-n_alternatives/3)`;
- `serviceability = max(exact_component, fallback_component)`.

Por tanto, la señal de serviceability no crece indefinidamente por tener cientos de listings. El valor depende principalmente de la calidad de las mejores alternativas y de si existe profundidad suficiente.

### 9.2 Auditoría final de `codexway`

| Métrica | Resultado |
|---|---:|
| Mean serviceability lower | 0.6936 |
| Mean serviceability upper | 0.8213 |
| Mean uncertainty width | 0.1277 |
| Mean inventory confidence | 0.5217 |
| Exact spot attendable | 45.64% |
| Exact spot unknown | 44.30% |
| Sin alternativa conocida | 2.38% |
| Sin alternativa potencial | 0.00% |
| Future snapshot violations | 0 |

La amplitud media del intervalo, ~0.128, es una señal importante: parte relevante del score de inventario depende de incertidumbre, no de un estado perfectamente observado.

---

## 10. Fallback operativo

### 10.1 Cuándo entra

El fallback se activa cuando el Spot solicitado no proporciona una opción suficientemente atendible o cuando se requiere mostrar alternativas servibles.

No debe entenderse como "buscar cualquier Spot parecido". Es una búsqueda gobernada dentro del candidate universe PIT.

### 10.2 Restricciones obligatorias

Como mínimo:

- Spot existente en `score_time`;
- modalidad compatible;
- sector/estado conforme al universo final de `codexway`;
- no usar Availability futura;
- no recomendar como confirmada una opción conocida como no atendible;
- conservar reason codes de relajación y estado.

Las restricciones duras se aplican **antes** del ranking.

### 10.3 Ordenamiento

El orden canónico es el ranking lower/upper de `codexway`.

En presentación se debe exponer, para cada recomendación:

- `spot_id`;
- rank;
- exact/fallback;
- relaxation tier;
- `area_fit`;
- `price_fit`;
- `geo_fit`;
- Availability state;
- `snapshot_date`;
- `snapshot_age_days`;
- confidence/uncertainty;
- reason codes.

### 10.4 Cuántos candidatos se devuelven: K=5 final

La configuración canónica de `codexway` congela:

`max_fallback_recommendations: 5`

y el test de inventario exige que ninguna lista supere 5 elementos.

Por tanto, **la entrega final conserva K=5 como máximo visible**.

### 10.5 ¿Entonces qué significa la evidencia K=3?

E020 y AssessmentSol1 encontraron evidencia favorable a K=3:

- E020, folds de diseño: lista completa >=3 en 60.8% vs >=5 en 50.3%;
- E020, fold final: >=3 en 62.4% vs >=5 en 55.7%;
- AssessmentSol1 DEVELOPMENT: al menos 3 recomendaciones en 92.74% vs al menos 5 en 84.62%.

Esto es una sensibilidad importante, pero no reemplaza la decisión final de `codexway`.

La reconciliación correcta es:

- **top-3** ya es la profundidad que gobierna el componente de serviceability en `codexway`;
- **hasta 5** es la profundidad de presentación/fallback final;
- K=3 permanece como challenger de UX/operación para un futuro piloto.

No se debe reescribir la solución ganadora sólo porque otras ramas usan K=3.

### 10.6 UNKNOWN en fallback

Cuando un candidato tiene Availability desconocida/stale:

- no se vende como `AVAILABLE`;
- puede aparecer como alternativa potencial si la política necesita completar la lista;
- debe llevar un estado equivalente a `VERIFY_AVAILABILITY` en la capa operativa;
- su cota inferior permanece conservadora.

### 10.7 NO_RESULT

Si no existe ningún candidato que pase las restricciones obligatorias, el comportamiento esperado es:

`NO_RESULT`

Esto es preferible a:

- cambiar de modalidad;
- inventar un sector;
- usar un Spot creado en el futuro;
- usar un snapshot futuro;
- relajar geografía sin límite;
- recomendar una opción conocida como no atendible.

**NO_RESULT es una decisión válida**, no un error del sistema. Protege precision operativa y evita convertir coverage en una métrica manipulable mediante relajaciones incorrectas.

---

## 11. Evaluación del fallback

### 11.1 Por qué el Spot histórico elegido no es un gold label limpio

El dataset registra lo que ocurrió, no un log de recomendaciones contrafactuales.

Una futura visita puede estar influida por:

- disponibilidad que cambió después del score;
- intervención del broker;
- nueva información del lead;
- exposición a inventario no presente en el candidate set original;
- decisiones humanas no registradas;
- cambios de preferencia;
- listings futuros.

E020 encontró que, entre futuras visitas alternativas observadas:

- 67.4% coincide con el sector declarado;
- 16.5% coincide con corredor preferido;
- sólo 1.0% cumple simultáneamente sector + corredor + restricciones estrictas;
- sólo 1.75% cumple la política bounded completa usada por ese experimento.

Por eso optimizar el recomendador para copiar el Spot finalmente visitado puede **premiar violaciones de la política**.

### 11.2 Hit@K

En E020, como diagnóstico:

- Hit@1: 0%;
- Hit@3: 0%;
- Hit@5: 0.52%.

Estos números no prueban que el fallback sea inútil. Prueban que el histórico no es un gold de recommendation relevance adecuado para esa política.

Por tanto, Hit@K debe reportarse con la etiqueta:

**DIAGNÓSTICO / GOLD LABEL NO ALINEADO**

y nunca como métrica principal de promoción.

### 11.3 Métricas primarias de fallback

La evaluación correcta debe incluir:

**Coverage@K**
- proporción de casos de fallback con al menos una recomendación válida;
- proporción con lista completa de K;
- distribución de candidate depth.

**Constraint precision**
- % de recomendaciones que cumplen todas las hard constraints;
- idealmente 100%.

**As-of availability**
- % confirmado disponible/attendable con el snapshot PIT;
- % UNKNOWN/VERIFY;
- % conocido no disponible recomendado, cuyo objetivo debe ser 0%.

**Freshness**
- edad del snapshot de cada recomendación;
- porcentaje por buckets;
- coverage por período.

**No-result rate**
- frecuencia de `NO_RESULT`;
- razón: sin inventario, restricciones, Availability conocida negativa, etc.

**Utilidad operativa online**
- contacto efectivo;
- aceptación del fallback;
- visita agendada tras recomendación;
- tiempo hasta encontrar opción servible;
- carga del broker;
- concentración por Spot;
- tasa de verificación de UNKNOWN.

---

## 12. Coverage@K y candidate depth

Coverage debe medirse por cohorte temporal y no sólo globalmente.

Definiciones sugeridas:

`Coverage@K_any = leads con >=1 recomendación válida / leads que requieren fallback`

`Coverage@K_full = leads con >=K recomendaciones válidas / leads que requieren fallback`

Además:

- mediana y percentiles de candidate depth;
- coverage por sector;
- coverage por modalidad;
- coverage por estado/municipio/corredor;
- coverage por freshness bucket;
- coverage con Availability conocida vs desconocida.

E020 aporta una sensibilidad histórica útil para K=3:

- casos fallback en fold final: 598;
- ≥1 alternativa top-3 válida: 75.9%;
- lista completa de 3: 62.4%;
- no-result: 24.1%;
- ≥1 alternativa actualmente disponible top-3: 70.9%;
- mediana de candidatos válidos: 6.

Estas cifras **no se copian como performance de `codexway`** porque provienen de otra política. Se conservan como evidencia de diseño y de la necesidad de reportar profundidad real.

---

## 13. P(availability): evidencia complementaria, no sustitución del champion

E019 construyó un challenger probabilístico explícito:

`P(spot disponible ahora o observado disponible dentro de 30d | estado PIT + transiciones históricas maduras)`

y agregó a nivel lead mediante máximo sobre candidatos compatibles.

Resultados macro de cuatro folds temporales:

- AUC: **0.883**;
- Brier: **0.0669**;
- Log Loss: **0.192**;
- backward-asof coverage: **92.38%**.

Además, mostró que `days_until_available` no tenía una relación monotónica suficientemente limpia como para justificar un decay artesanal.

Este resultado es valioso porque demuestra que es posible modelar Availability de manera temporalmente correcta. Sin embargo, **no reemplaza el Inventory Serviceability final de `codexway`**, que utiliza estados, fits y cotas lower/upper.

Uso correcto de E019 en esta entrega:

- evidencia de que una futura V2 probabilística es viable;
- benchmark de calibración;
- no sustituir la semántica final ni sus restricciones.

---

## 14. Brokers, clusters y pockets locales

La investigación de matching encontró segmentos locales y perfiles de broker con señales interesantes, pero no robustas como score global.

Ejemplos:

- Broker Service produjo una segmentación balanceada e interpretable;
- algunas celdas locales alcanzaron lift elevado;
- los deltas globales quedaron inconclusos bajo bootstrap;
- el mismo future test fue reutilizado para discovery, por lo que nuevas reglas no son confirmatorias.

Por ello:

- broker profiles pueden servir para **routing auxiliar**;
- pockets locales pueden generar hipótesis de operación/A-B;
- **no deben convertirse en hard constraints ni score multipliers del fallback final** sin nueva evidencia;
- nunca usar outcomes posteriores para crear el candidate set del mismo período evaluado.

---

## 15. Leakage y gold-label governance

### Permitido

- `spot.created_at <= score_time`;
- último `snapshot_date <= score_time`;
- current inquiry fields conocidos en T1;
- Availability futura sólo para construir un target futuro en un experimento específicamente diseñado y madurado, nunca como feature.

### Bloqueado / condicional

- snapshot futuro;
- nearest snapshot sin dirección backward;
- `is_active` actual como proxy histórico;
- `competing_inquiries_30d` si su effective-time no está probado;
- market context sin publication/effective time;
- atributos mutables actuales presentados como si fueran históricos;
- histórico del Spot visitado como gold automático del recomendador.

### Estado final de la evidencia

`codexway` reporta:

- future snapshot violations = **0**;
- Availability temporal = **POINT_IN_TIME_BACKWARD_ASOF**;
- listing state temporal = **CONDITIONAL_UNVERSIONED_ASSUMED_STATIC_SINCE_CREATION**.

Esta última etiqueta no es un detalle menor. Es el límite exacto de la afirmación metodológica.

---

## 16. Casos límite

### Caso A — Spot exacto disponible

- existe al score;
- snapshot backward fresco;
- disponible ahora;
- exact component alto.

**Acción:** mantener Spot exacto; fallback puede existir como respaldo, no como sustitución obligatoria.

### Caso B — Spot exacto no disponible, alternativas conocidas

- exact = no atendible;
- existen candidatos compatibles con `candidate_match_lower > 0`.

**Acción:** ordenar fallback y devolver hasta 5.

### Caso C — Sin snapshot previo

- no existe Availability histórica antes del score.

**Acción:** estado UNKNOWN; lower=0, upper=1; no declarar "no disponible"; reason de verificación.

### Caso D — Snapshot stale

- hay observación histórica, pero excede freshness.

**Acción final `codexway`:** tratarla conservadoramente dentro de la banda de incertidumbre; marcar explícitamente stale para auditoría y verificación. No reinterpretar como una observación futura ni como UNAVAILABLE.

### Caso E — Spot futuro muy compatible

- gran match físico/geográfico;
- `created_at > score_time`.

**Acción:** excluirlo por completo.

### Caso F — Precio actual parece perfecto, pero no tiene versión histórica

**Acción:** el cálculo histórico completo queda marcado como condicional. No afirmar PIT estricto para precio hasta versionarlo.

### Caso G — Todos los candidatos conocidos están no atendibles

**Acción:** no recomendar ninguno como disponible. Si existen candidatos UNKNOWN con potencial, `VERIFY_AVAILABILITY`; si no, `NO_RESULT`.

### Caso H — No existe candidato que pase hard constraints

**Acción:** `NO_RESULT`.

---

## 17. Ejemplos concretos de decisión

### Ejemplo 1 — AVAILABLE_NOW

Lead busca Industrial renta en un corredor específico.

- Spot A ya existía.
- Último snapshot 3 días antes del score.
- `is_available=true`.
- Área y precio compatibles.

Resultado:

- Availability lower=upper=1;
- candidato defendible;
- puede ser exact o primer fallback.

### Ejemplo 2 — UNAVAILABLE

- snapshot 5 días antes;
- no disponible;
- `days_until_available` excede urgencia.

Resultado:

- lower=upper=0;
- no se recomienda como opción confirmada.

### Ejemplo 3 — UNKNOWN por missing history

- Spot existía;
- no hay ningún snapshot previo.

Resultado:

- lower=0;
- upper=1;
- estado operacional `VERIFY_AVAILABILITY`;
- no confundir con "no disponible".

### Ejemplo 4 — stale

- último snapshot existe, pero tiene >30 días bajo el lens canónico.

Resultado `codexway`:

- entra al bucket de incertidumbre;
- lower=0, upper=1;
- reason subtype `STALE_SNAPSHOT` recomendado para observabilidad;
- requiere verificación si se muestra.

### Ejemplo 5 — NO_RESULT

- no existe alternativa que respete existencia PIT + modalidad + candidate universe.

Resultado:

- lista vacía;
- `NO_RESULT`;
- no ampliar reglas silenciosamente.

---

## 18. Riesgos y limitaciones

1. **Coverage drift:** Availability es mucho más completa en períodos tardíos.
2. **Freshness sensitivity:** el porcentaje de candidatos frescos cambia drásticamente entre 7/30/90 días.
3. **Listing fields no versionados:** price/area/geography pueden no representar exactamente el valor histórico.
4. **Gold label incompleto:** historical chosen Spot no es recomendación observada ni contrafactual válido.
5. **Proxy comercial no alineado:** el target T1 no observa explícitamente éxito del fallback.
6. **Unknown/stale:** una parte relevante del inventario necesita verificación, no clasificación binaria.
7. **K:** K=5 es canónico de presentación, aunque K=3 tenga evidencia secundaria favorable.
8. **Local pockets:** segmentos/brokers interesantes son auxiliares, no pruebas suficientes para alterar la política final.
9. **Same-day timestamps:** si `snapshot_date` carece de hora de ingestión, producción debe documentar SLA/publication semantics.
10. **Precision operativa:** aumentar coverage relajando constraints puede empeorar la calidad real; por eso `NO_RESULT` es guardrail.

---

## 19. Monitoring recomendado

### Availability

- snapshot coverage;
- stale rate;
- unknown-no-history;
- unknown-stale;
- available-now;
- available-within-urgency;
- unavailable;
- snapshot age p50/p90/p95;
- violations de `snapshot_date > score_time` = 0.

### Candidate Generation

- candidatos por lead;
- leads con 0 candidatos;
- distribución por corridor/municipality/state;
- modalidad mismatch attempts;
- future-spot rejections;
- candidate depth.

### Fallback

- Coverage@1, @3, @5;
- full-list coverage @3 y @5;
- `NO_RESULT` rate;
- `VERIFY_AVAILABILITY` rate;
- known-unavailable recommendation rate = 0;
- freshness de recomendaciones;
- exact vs fallback;
- reason-code mix;
- concentración de recomendaciones por Spot.

### Evaluación online

Una prueba futura debe usar asignación sticky por `lead_id` y medir:

- aceptación del fallback;
- scheduled visit después de recomendación;
- tiempo a primera opción servible;
- workload de broker;
- no-result;
- availability verification success;
- SRM y estabilidad por sector/modalidad.

El offline actual no permite una afirmación causal.

---

## 20. Trazabilidad de decisiones

| Decisión | Autoridad final | Evidencia complementaria | Estado |
|---|---|---|---|
| Availability backward-as-of | [`codexway/inventory.py`](../../codexway/src/spot2_codexway/inventory.py) | EV-010, AssessmentSol1 serviceability | **Final** |
| No future snapshots | [`inventory_audit.json`](../../codexway/outputs/metrics/inventory_audit.json) | tests de ambas ramas | **Final / 0 violaciones** |
| UNKNOWN no equivale a UNAVAILABLE | [`DECISIONS.md`](../../codexway/evidence/DECISIONS.md) + E111 | AssessmentSol1 temporal correction | **Final** |
| Freshness default 30d | [`base.yaml`](../../codexway/config/base.yaml) | sensibilidad 7/30/90 | **Final con sensitivity** |
| Missing/stale con cotas [0,1] | [`inventory.py`](../../codexway/src/spot2_codexway/inventory.py) | Assessment distingue stale vs missing | **Final; reason subtype recomendado** |
| Candidate existence gate | [`inventory.py`](../../codexway/src/spot2_codexway/inventory.py) | E020 / Assessment | **Final** |
| Modalidad como hard constraint | [`inventory.py`](../../codexway/src/spot2_codexway/inventory.py) | EV-010 | **Final** |
| Geografía corredor→municipio→estado | [`inventory.py`](../../codexway/src/spot2_codexway/inventory.py) | E020 / Assessment | **Final** |
| Matching lower/upper | [`inventory.py`](../../codexway/src/spot2_codexway/inventory.py) | E111 | **Final** |
| Top-3 para componente fallback | [`inventory.py`](../../codexway/src/spot2_codexway/inventory.py) | E020 K=3 | **Final interno** |
| Hasta K=5 recomendaciones | [`base.yaml`](../../codexway/config/base.yaml) + [test](../../codexway/tests/test_inventory.py) | E020 y Assessment favorecen K=3 | **Final de presentación; K=3 challenger** |
| Historical chosen Spot no es gold limpio | limitación reconocida por `codexway` | [E020](../../experimentos/E020_lead_opportunity_fallback_e2e/results/REPORT.md) | **Final como caveat** |
| Hit@K no es gate primario | target alignment parcial en `system_evaluation` | E020 Hit@K negativo | **Final** |
| Full historical matching es condicional | [`inventory_audit.json`](../../codexway/outputs/metrics/inventory_audit.json) | Assessment bloquea price no PIT | **Final caveat** |
| P(availability) calibrada | no promovida por `codexway` | [E019](../../experimentos/E019_operational_threshold_availability/results/REPORT.md) | **Challenger futuro** |
| Brokers/local pockets | no entran en fallback final | EV-013 | **Auxiliar / hypothesis only** |

### Fuentes directas principales

- [Codexway README](../../codexway/README.md)
- [Codexway Inventory implementation](../../codexway/src/spot2_codexway/inventory.py)
- [Codexway frozen config](../../codexway/config/base.yaml)
- [Codexway frozen decisions](../../codexway/evidence/DECISIONS.md)
- [Codexway Inventory audit](../../codexway/outputs/metrics/inventory_audit.json)
- [Codexway freshness sensitivity](../../codexway/outputs/tables/inventory_freshness_sensitivity.csv)
- [Codexway system evaluation](../../codexway/outputs/metrics/system_evaluation.json)
- [E019 — Availability probability](../../experimentos/E019_operational_threshold_availability/results/REPORT.md)
- [E020 — Fallback end-to-end](../../experimentos/E020_lead_opportunity_fallback_e2e/results/REPORT.md)
- [EV-010 — Matching / relational audit](../../experimentos/Evidencias/EV-010_matching_ab_v3.md)
- [EV-013 — Profiles / matching](../../experimentos/Evidencias/EV-013_matching_profiles_v4.md)
- [AssessmentSol1 Inventory contract](../../AssessmentSol1/inventory/SERVICEABILITY_CONTRACT.md)
- [AssessmentSol1 Freshness](../../AssessmentSol1/inventory/FRESHNESS_POLICY.md)
- [AssessmentSol1 Fallback](../../AssessmentSol1/inventory/FALLBACK_POLICY.md)
- [AssessmentSol1 Temporal correction](../../AssessmentSol1/inventory/TEMPORAL_CORRECTION.md)

---

## 21. Decisión operativa final

La política final de este entregable queda así:

1. **Separar Lead Quality de Inventory Serviceability.**
2. Construir inventario con existencia PIT.
3. Resolver Availability exclusivamente mediante backward as-of.
4. No usar snapshots futuros.
5. Mantener `UNKNOWN != UNAVAILABLE`.
6. Tratar missing/stale de forma conservadora con cotas de incertidumbre de `codexway` y distinguir la causa en auditoría.
7. Aplicar hard constraints antes del ranking.
8. Ordenar por matching conservador lower, luego upper y desempate estable.
9. Construir el componente de fallback con top-3.
10. Exponer hasta **5** recomendaciones, conforme al config final de `codexway`.
11. Marcar UNKNOWN como `VERIFY_AVAILABILITY` en operación.
12. Emitir `NO_RESULT` cuando no exista una alternativa válida.
13. Evaluar fallback principalmente con constraint-valid Coverage@K, Availability as-of, freshness y no-result.
14. Conservar Hit@K histórico únicamente como diagnóstico porque el Spot observado no es gold limpio.
15. Versionar precio y demás atributos mutables antes de afirmar PIT completo del matching histórico.

---

## 22. Tabla de decisión por problema

| Problema | Señal utilizada | Decisión |
|---|---|---|
| ¿El Spot existía? | `spot.created_at <= score_time` | excluir Spots futuros |
| ¿Qué Availability conocíamos? | último `snapshot_date <= score_time` | strict backward as-of |
| ¿Está disponible ahora? | snapshot fresco + `is_available` | AVAILABLE_NOW |
| ¿Puede estar dentro de la urgencia? | `days_until_available` vs `urgency_days` en snapshot fresco | AVAILABLE_WITHIN_URGENCY / no atendible |
| ¿No existe snapshot previo? | ausencia de backward snapshot | UNKNOWN, verificar |
| ¿El snapshot es stale? | `snapshot_age_days > freshness` | incertidumbre conservadora; no UNAVAILABLE |
| ¿Es compatible por modalidad? | lead modality vs Spot modality | hard gate |
| ¿Es buen match? | area + price + geography + Availability bounds | ranking lower/upper |
| ¿El exact Spot no sirve? | exact component vs alternativas | activar fallback |
| ¿Cuántos candidatos influyen en serviceability? | top alternativas | top-3 interno |
| ¿Cuántos fallbacks se muestran? | config final `max_fallback_recommendations` | hasta K=5 |
| ¿No hay candidato válido? | candidate depth = 0 bajo hard constraints | NO_RESULT |
| ¿Cómo evaluar fallback? | constraints, as-of Availability, freshness, Coverage@K | no optimizar contra historical chosen Spot |

---

## 23. Comportamiento esperado por caso

| Caso | Comportamiento esperado |
|---|---|
| Disponible | usar como candidato confirmado; lower=upper positivo |
| No disponible | no recomendar como alternativa confirmada; lower=upper=0 si no entra en urgencia |
| Estado desconocido | `UNKNOWN / VERIFY_AVAILABILITY`; nunca reinterpretar como UNAVAILABLE |
| Snapshot stale | mantener incertidumbre explícita; `codexway` usa bounds conservadores y exige verificación |
| Sin candidato válido | `NO_RESULT` |

---

## Cierre

El Inventory Availability Model queda metodológicamente defendido en su parte más sensible: **la selección de Availability es point-in-time y no usa snapshots futuros**.

El documento evita una afirmación más fuerte de la que permiten los datos. La disponibilidad histórica sí está temporalmente controlada; el matching completo aún hereda riesgo por atributos de Spot no versionados.

La política de fallback privilegia precision operativa y trazabilidad sobre coverage artificial. Un `NO_RESULT` explícito es mejor que una recomendación incorrecta, y un `UNKNOWN` verificable es mejor que convertir una ausencia de evidencia en un falso `UNAVAILABLE`.

**No se avanza en este entregable a Opportunity Score.**
