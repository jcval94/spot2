> **ARCHIVO HISTÓRICO / NO USAR COMO ENTRY POINT.** La versión vigente del Entregable 1 es [entregable/01_eda/README.md](01_eda/README.md). Este archivo se conserva únicamente por trazabilidad y no redefine decisiones canónicas.\n\n# Entregable 1 — Análisis exploratorio de datos (EDA)

## Resumen ejecutivo

El mercado de Spot2 no tiene un único cuello de botella. El EDA muestra tres fenómenos distintos que deben mantenerse separados desde el inicio:

1. **La demanda es amplia y relativamente estable**, pero cambia de composición por sector, modalidad y tipo de usuario.
2. **La propensión de progreso comercial varía por segmento**, aunque ninguna variable aislada explica por sí sola la conversión.
3. **La capacidad de atender la demanda cambia mucho más que la calidad del lead**, porque la cobertura histórica del inventario y de Availability evoluciona fuertemente en el tiempo.

Esta distinción es la principal conclusión del análisis. Un lead puede tener buena propensión a avanzar y, al mismo tiempo, no contar con inventario observable o compatible. Por eso el EDA ya anticipa una arquitectura en la que **Lead Quality** e **Inventory Serviceability** se modelan como componentes relacionados, pero conceptualmente distintos.

La autoridad principal de este entregable es [Codexway](../codexway/). Los hallazgos de [AssessmentSol1](../AssessmentSol1/) y [experimentos](../experimentos/) se incorporan como evidencia complementaria, pruebas de robustez y resultados negativos. Cuando esas líneas utilizan targets o poblaciones distintas, sus métricas se presentan por separado y nunca se mezclan.

---

## 1. Alcance analítico y contrato temporal

La unidad primaria de análisis de Codexway es **T1: un score por lead en su primera inquiry**, después de que la solicitud actual ya fue persistida y antes de conocer cualquier respuesta del broker.

El proxy principal de progreso comercial es:

**primera inquiry con broker_response = scheduled_visit**

con:

- fecha de corte de datos: 1 de julio de 2026;
- buffer de madurez: 7 días;
- 4,898 leads maduros;
- 1,001 positivos;
- prevalencia del proxy: **20.44%**;
- 102 leads recientes censurados por derecha y, por tanto, scoreables pero no evaluables.

Este proxy no es un cierre, ingreso ni conversión comercial oculta. Es una señal observable de avance en el funnel y debe interpretarse como tal.

Una segunda línea clean-room, AssessmentSol1, utiliza un proxy T1 ligeramente diferente —eventual scheduled visit posterior a la primera inquiry— y una ventana de desarrollo más restringida. Sus tasas no se mezclan con Codexway; se usan únicamente para verificar si determinados patrones descriptivos sobreviven a otra definición razonable del problema.

**Consecuencia:** toda asociación que se presenta más adelante debe responder primero a una pregunta temporal: ¿esa información era observable en el instante de scoring?

Fuentes:
- [Codexway README](../codexway/README.md)
- [Decisiones congeladas de Codexway](../codexway/evidence/DECISIONS.md)
- [EDA clean-room de AssessmentSol1](../AssessmentSol1/evidence/EDA_FINDINGS.md)

---

## 2. La base de datos es relacionalmente sólida; la dificultad real es temporal

El paquete contiene seis fuentes canónicas:

| Tabla | Filas | Papel principal |
|---|---:|---|
| leads | 5,000 | necesidad inicial, perfil y origen del lead |
| inquiries | 22,576 | interacciones lead–spot |
| spots | 3,000 | catálogo inmobiliario |
| spot_attributes | 3,000 | atributos físicos del inmueble |
| availability_snapshot | 30,000 | estado histórico de disponibilidad |
| market_context | 500 | contexto agregado de mercado |

La auditoría independiente de AssessmentSol1 confirma:

- 0 duplicados de llave primaria;
- 0 huérfanos en Inquiry→Lead;
- 0 huérfanos en Inquiry→Spot;
- 0 huérfanos en SpotAttributes→Spot;
- 0 huérfanos en Availability→Spot;
- 0 inquiries anteriores a la creación del lead;
- 0 inquiries anteriores a la creación del spot;
- 0 snapshots anteriores a la creación del spot;
- 0 duplicados spot_id × snapshot_date.

Por tanto, **el problema no es una base relacional rota**. El riesgo está en unir correctamente fuentes cuya información cambia con el tiempo.

El ejemplo más importante es Availability. Un join tradicional por spot_id expande las 22,576 inquiries a **226,151 filas, 10.017 veces el volumen original**. Todavía peor, una estrategia de “snapshot más cercano” utilizaría un snapshot futuro en **7,758 inquiries, 34.36% del total**.

La única política histórica defendible es:

**último snapshot con snapshot_date <= prediction_timestamp**

Codexway implementa esta política mediante backward as-of y la protege con tests.

### Hallazgo

Availability es una relación **1:N temporal**, no una dimensión estática.

### Implicación

La disciplina point-in-time no es un detalle de ingeniería; forma parte de la definición estadística del problema.

Fuentes:
- [Data audit de AssessmentSol1](../AssessmentSol1/evidence/DATA_AUDIT.md)
- [Leakage Matrix de Codexway](../codexway/evidence/LEAKAGE_MATRIX.md)
- [EV-010 Matching A/B](../experimentos/Evidencias/EV-010_matching_ab_v3.md)

---

## 3. ¿Quién llega a Spot2? Composición de la demanda

### 3.1 Por sector

Sobre los 5,000 leads:

| Sector | Leads | Participación |
|---|---:|---:|
| Retail | 1,528 | **30.56%** |
| Office | 1,450 | **29.00%** |
| Industrial | 1,249 | **24.98%** |
| Land | 773 | **15.46%** |

La demanda está diversificada: ningún sector domina por sí solo, aunque Retail y Office concentran cerca de 60% de los leads.

La combinación sector × modalidad muestra que las celdas más grandes son:

- Retail + renta: **15.16%** de todos los leads;
- Office + renta: **14.76%**;
- Industrial + renta: **12.22%**;
- Retail + venta: **9.38%**;
- Office + venta: **8.60%**.

Tabla base:
[lead_mix.csv](../codexway/outputs/tables/lead_mix.csv)

Evidencia visual:
[eda_lead_mix.png](../codexway/outputs/figures/eda_lead_mix.png)

### 3.2 Por modalidad

| Modalidad | Leads | Participación |
|---|---:|---:|
| rent | 2,503 | **50.06%** |
| sale | 1,490 | **29.80%** |
| both | 1,007 | **20.14%** |

Spot2 es, en primer lugar, un marketplace de demanda de **renta**, pero casi la mitad del universo requiere venta o flexibilidad entre ambas modalidades.

Este punto resulta relevante más adelante: la investigación experimental muestra que la necesidad de renta tiende a permanecer relativamente estable entre T0 y T1, mientras que las necesidades de venta o modalidad flexible se refinan con mucha mayor intensidad cuando llega la primera inquiry.

### 3.3 Por tipo de usuario

| Tipo de usuario | Leads | Participación |
|---|---:|---:|
| tenant_direct | 1,956 | **39.12%** |
| broker | 1,804 | **36.08%** |
| investor | 997 | **19.94%** |
| developer | 243 | **4.86%** |

No hay una única “persona” dominante. Tenant direct y brokers representan tres cuartas partes del flujo, mientras que inversionistas aportan aproximadamente una quinta parte.

### 3.4 Por fuente de adquisición

| Fuente | Participación |
|---|---:|
| organic | **29.26%** |
| paid | **24.92%** |
| referral | **20.34%** |
| social | **10.48%** |
| email | **9.92%** |
| event | **5.08%** |

La adquisición tampoco está concentrada en un solo canal, lo que reduce el riesgo de construir un sistema que en realidad sólo aprenda un único funnel comercial.

---

## 4. Demanda vs. oferta: Retail merece atención

AssessmentSol1 reconstruyó, únicamente dentro de DEVELOPMENT y respetando existencia del inventario al corte, la relación entre demanda e inventario histórico observable.

El hallazgo más claro es Retail:

- participación de Retail en demanda: **30.40%**;
- participación de Retail en catálogo histórico: **24.51%**;
- brecha demanda–oferta: **+5.89 puntos porcentuales**;
- índice demanda/oferta: **1.24x**.

Office, en contraste, estaba prácticamente equilibrado:

- demanda: **29.35%**;
- oferta: **29.56%**.

Este resultado es consistente con Codexway, donde Retail representa 30.56% de todos los leads.

### Interpretación de negocio

Retail no sólo es el sector con mayor participación de demanda; también muestra una presión relativa mayor frente a su peso en el catálogo histórico.

### Lo que NO significa

No significa que 24.51% del inventario sea realmente atendible para esos leads. Share de catálogo no incorpora todavía:

- disponibilidad as-of;
- frescura del snapshot;
- área compatible;
- precio compatible;
- ubicación;
- modalidad;
- calidad temporal de los atributos.

Es una señal de presión relativa, no una probabilidad de serviceability.

Fuente:
[EDA_FINDINGS — EDA-01](../AssessmentSol1/evidence/EDA_FINDINGS.md)

---

## 5. El proxy de progreso comercial sí cambia por segmento, pero no existe un “segmento mágico”

Sobre los 4,898 T1 maduros de Codexway:

### 5.1 Por sector

| Sector | N | Tasa del proxy scheduled_visit |
|---|---:|---:|
| Industrial | 1,220 | **24.34%** |
| Land | 764 | **21.07%** |
| Retail | 1,497 | **19.04%** |
| Office | 1,417 | **18.21%** |

Industrial supera a Office por aproximadamente **6.1 pp**.

Este es el contraste descriptivo más fuerte de los segmentos básicos.

AssessmentSol1, usando un proxy T1 distinto y sólo DEVELOPMENT, reproduce el mismo orden cualitativo:

**Industrial > Land > Retail > Office**

con 24.35%, 21.07%, 19.35% y 17.71%, respectivamente.

La similitud de orden bajo dos definiciones de target distintas incrementa la confianza en que el sector contiene información real, aunque las tasas exactas no deben fusionarse.

### 5.2 Por tipo de usuario

| Tipo | Tasa |
|---|---:|
| developer | **21.49%** |
| tenant_direct | **21.24%** |
| broker | **20.08%** |
| investor | **19.24%** |

La dispersión es mucho menor que por sector. No hay evidencia descriptiva para pensar que “ser broker” o “ser inversionista” determine el outcome.

### 5.3 Por fuente

| Fuente | Tasa |
|---|---:|
| social | **22.48%** |
| paid | **21.13%** |
| email | **20.29%** |
| organic | **20.18%** |
| event | **19.44%** |
| referral | **19.22%** |

Hay señal, pero las diferencias son moderadas.

### 5.4 Por canal de inquiry

| Canal | Tasa |
|---|---:|
| app | **21.55%** |
| web | **21.28%** |
| email | **19.57%** |
| whatsapp | **19.43%** |
| phone | **17.69%** |

La lectura correcta no es “usar web y evitar phone”; estos son canales elegidos por usuarios y procesos distintos. El EDA identifica una asociación, no causalidad.

AssessmentSol1 también analizó asked_visit y encontró una diferencia mucho menor de lo que su nombre podría sugerir:

- asked_visit=true: **21.33%**;
- asked_visit=false: **20.07%**;
- diferencia: **+1.26 pp**.

Esto convierte a asked_visit en una variable legítima para sensibilidad, no en una etiqueta encubierta.

Fuentes:
- [target_rate_by_segment.csv](../codexway/outputs/tables/target_rate_by_segment.csv)
- [eda_target_segments.png](../codexway/outputs/figures/eda_target_segments.png)
- [AssessmentSol1 EDA-03 y EDA-12](../AssessmentSol1/evidence/EDA_FINDINGS.md)

---

## 6. Temporalidad: hay no estacionariedad, pero no evidencia suficiente para vender “estacionalidad”

Los leads nuevos por mes son relativamente estables.

En 2025–junio 2026, el volumen mensual se mueve aproximadamente entre **237 y 315 leads**.

En cambio, las inquiries observadas crecen de forma muy marcada:

- ene-2025: 263;
- jun-2025: 947;
- dic-2025: 1,594;
- mar-2026: 1,941;
- jun-2026: 2,104.

El número de leads no muestra un crecimiento comparable.

### Interpretación

El crecimiento de inquiries no debe leerse inmediatamente como explosión de demanda. Puede reflejar:

- maduración de cohortes;
- mayor número de interacciones por lead;
- cambios del proceso;
- mayor cobertura observacional;
- acumulación de inventario;
- generación sintética del dataset.

AssessmentSol1 confirma la necesidad de cautela: en DEVELOPMENT, los primeros contactos mensuales varían entre aproximadamente 166 y 325, pero el horizonte de ~16 meses es demasiado corto y está demasiado mezclado con cambios de cobertura como para identificar un ciclo anual estable.

### Un detalle importante

Julio de 2026 muestra 0 nuevos leads y 269 inquiries en la tabla de volumen. Esto es un artefacto natural de las distintas fechas máximas de cada fuente y del data-as-of, no una “caída de demanda”.

### Conclusión

El hallazgo defendible es **no estacionariedad temporal**, especialmente en inventario y cobertura. No una ley estacional.

Fuentes:
- [monthly_volume.csv](../codexway/outputs/tables/monthly_volume.csv)
- [eda_monthly_volume.png](../codexway/outputs/figures/eda_monthly_volume.png)
- [AssessmentSol1 EDA-14](../AssessmentSol1/evidence/EDA_FINDINGS.md)

---

## 7. Dinámica de mercado: sectores con economías inmobiliarias distintas

Codexway mantiene market_context fuera del modelo histórico por no contar con publication/effective timestamp. Aun así, es una fuente válida para EDA descriptivo.

Resumen sectorial:

| Sector | Spots similares mediana | Precio/m² mediano | Ocupación mediana | Absorción mediana | Inquiry volume mediano |
|---|---:|---:|---:|---:|---:|
| Industrial | 15 | **$140.56** | **87.7%** | **169.8 días** | 238 |
| Land | 16 | **$45.00** | **59.7%** | **236.9 días** | 256 |
| Office | 17 | **$357.96** | **83.0%** | **118.85 días** | 264 |
| Retail | 15 | **$288.49** | **77.3%** | **92.3 días** | **278** |

### Lectura

- **Retail** combina la absorción más rápida y el mayor inquiry volume mediano de los cuatro sectores.
- **Office** es el sector con precio/m² mediano más alto, pero con absorción más rápida que Industrial.
- **Industrial** tiene la mayor ocupación mediana, aunque no la mayor velocidad de absorción.
- **Land** es un mercado claramente distinto: precio/m² muy inferior, ocupación menor y absorción mucho más lenta.

Esta heterogeneidad justifica evitar una única interpretación del “mercado inmobiliario” para todos los sectores.

### Ejemplos por corredor y municipio

El clean-room de AssessmentSol1 encontró, dentro del periodo DEVELOPMENT:

- Retail en centro-chihuahua: absorción media ~**74 días**;
- Retail en lomas-verdes-satelite: ~**82 días**;
- Retail en del-valle-narvarte: ~**84 días**;
- Industrial en varios corredores con ocupación alrededor de **0.88–0.90**, pero absorciones de **150–185 días**.

Es una diferencia de negocio importante: **alta ocupación no implica necesariamente rotación rápida**.

### Guardrail temporal

Market Context sólo tiene un campo month. No existe timestamp de publicación o disponibilidad del dato.

El matching exacto geografía × sector × mes cubre apenas **23.84%** de las inquiries.

Por ello, market_context se conserva como:

**EDA_ONLY**

y no como feature histórica.

Fuentes:
- [market_context_eda.csv](../codexway/outputs/tables/market_context_eda.csv)
- [eda_market_context.png](../codexway/outputs/figures/eda_market_context.png)
- [market_context_highlights.csv](../AssessmentSol1/outputs/eda/market_context_highlights.csv)
- [D031](../experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md)

---

## 8. La primera inquiry no sólo registra contacto: refina materialmente la necesidad

El análisis Lead→Inquiry de experimentos encontró:

- **81.53%** de los requested rent budgets cae dentro del rango inicial del lead;
- **81.04%** de los requested sale budgets cae dentro del rango inicial;
- mediana requested_area / target_area = **1.053x**;
- sólo **62.16%** de las inquiries mantiene el área solicitada entre 0.5x y 2.0x del target_area inicial.

AssessmentSol1 reproduce la misma historia desde otro ángulo:

- target_area inicial mediana: **395.05 m²**;
- requested_area primera inquiry mediana: **480.9 m²**;
- p90 requested_area: **2,561.1 m²**;
- máximo: **40,920.9 m²**.

### Interpretación

T1 contiene información nueva. La inquiry no es únicamente una repetición de los datos de intake.

Esto respalda features de:

- ratio de área T1/T0;
- gap absoluto y relativo;
- consistencia de presupuesto;
- cambio de modalidad o necesidad;
- missingness explícito;
- grado de refinamiento de la búsqueda.

### Evidencia experimental adicional: Dynamic Need

Los experimentos posteriores encontraron que la actualización T0→T1 es especialmente informativa para venta y modalidad flexible:

- Need de renta → Dynamic Need estable en **99.82%** de un perfil;
- venta y both se distribuyen entre varios perfiles de necesidad dinámica.

Sin embargo, Codexway volvió a probar la segmentación con controles más estrictos y **Dynamic Need no pasó el gate de balance**. Por tanto:

- el concepto “la necesidad se refina” sí queda soportado;
- un ID concreto de cluster Dynamic Need **no** se promueve como verdad de producción.

Esta distinción entre hallazgo de negocio y representación algorítmica es importante.

Fuentes:
- [D027 y D048](../experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md)
- [FEATURE_ENGINEERING_DECISIONS](../AssessmentSol1/evidence/FEATURE_ENGINEERING_DECISIONS.md)
- [CLUSTER_FINDINGS de Codexway](../codexway/outputs/CLUSTER_FINDINGS.md)

---

## 9. Availability: el mayor drift no está en el target, está en la observabilidad del inventario

La cobertura backward-as-of sobre todas las inquiries es **92.38%**.

Pero esta cifra agregada esconde un cambio temporal extremo:

- ene-2025: **6.46%**;
- jun-2025: **84.69%**;
- sep-2025: **96.57%**;
- dic-2025: **99.9%**;
- desde ene-2026: **100%**.

Además:

- mediana del lag del snapshot: **6.61 días**;
- p90: **58.66 días**;
- p95: **83.35 días**;
- 4.20% de las inquiries cubiertas tiene lag >90 días.

Codexway complementa este análisis con sensibilidad de frescura a nivel candidato:

| Ventana de frescura | % candidatos frescos | % leads con al menos un candidato fresco |
|---|---:|---:|
| <=7 días | **19.16%** | **93.46%** |
| <=30 días | **57.09%** | **98.34%** |
| <=90 días | **86.03%** | **98.52%** |

### Hallazgo central

“Existe un snapshot” y “el snapshot es reciente” son dos cosas distintas.

Un lead puede tener al menos una alternativa con evidencia fresca aunque una gran parte del pool tenga snapshots viejos.

### UNKNOWN no es UNAVAILABLE

La ausencia de un snapshot anterior al score time no demuestra que el inmueble estuviera no disponible. Sólo demuestra que **no podemos conocer su estado con la información entregada**.

Esta diferencia es decisiva para no penalizar injustamente cohortes antiguas.

### Separación arquitectónica sugerida por el EDA

Mientras la prevalencia del target T1 se mantiene aproximadamente alrededor de 20%, la observabilidad y profundidad del inventario cambia radicalmente.

AssessmentSol1 encontró además que la mediana de candidate depth crece de **16** en ene-2025 a **49** en abr-2026.

Por ello, introducir directamente candidate depth o Availability coverage dentro de Lead Quality permitiría que el modelo aprenda una era de instrumentación en lugar de calidad intrínseca del lead.

Fuentes:
- [inventory_freshness_sensitivity.csv](../codexway/outputs/tables/inventory_freshness_sensitivity.csv)
- [availability_coverage.png](../codexway/outputs/figures/availability_coverage.png)
- [AssessmentSol1 EDA-07 y EDA-08](../AssessmentSol1/evidence/EDA_FINDINGS.md)
- [D030](../experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md)

---

## 10. Missingness: gran parte no es mala calidad, sino estructura del negocio

La tabla cruda de missingness puede ser engañosa.

Los mayores faltantes son:

| Campo | Missing global |
|---|---:|
| lead.min_budget_mxn_sale_total | **51.86%** |
| lead.max_budget_mxn_sale_total | **50.06%** |
| inquiry.requested_budget_mxn_sale_total | **49.90%** |
| spot.price_sqm_mxn_sale | **39.73%** |
| lead.min_budget_mxn_rent_monthly | **32.16%** |
| inquiry.urgency_days | **30.64%** |
| lead.max_budget_mxn_rent_monthly | **29.80%** |
| inquiry.requested_budget_mxn_rent_monthly | **29.55%** |
| spot_attributes.charging_ports | **20.20%** |
| spot_attributes.vertical_height_m | **15.23%** |
| preferred_corridor | **7.60%** |
| company_size | **5.14%** |

Sin contexto, podría concluirse que el dataset tiene problemas graves de presupuestos y precios.

La reconciliación por modalidad cambia esa lectura:

- Lead min rent, cuando aplica: **96.64% completo**;
- Lead max rent, cuando aplica: **100%**;
- Lead min sale, cuando aplica: **96.40%**;
- Lead max sale, cuando aplica: **100%**;
- precios de Spot rent/sale, cuando la modalidad aplica: **100% completos**;
- 0 casos de min_budget > max_budget;
- price_total ≈ price_sqm × area dentro de 1% en **100%** de listings comparables.

### Conclusión

Los nulls de renta/venta representan en gran medida estados de **NOT_APPLICABLE**, no valores desconocidos.

### Urgency es diferente

urgency_days tiene ~30.6% missing y no existe una modalidad que explique mecánicamente ese faltante.

AssessmentSol1 lo interpreta correctamente como:

**urgencia no declarada**

y no como cero días o urgencia promedio.

Fuente:
- [data_quality_missingness.csv](../codexway/outputs/tables/data_quality_missingness.csv)
- [D028](../experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md)

---

## 11. Outliers: son reales para el negocio hasta demostrar lo contrario

La distribución inmobiliaria es fuertemente heavy-tailed.

Ejemplos de la auditoría:

- spots.area_sqm: 11.83% fuera de 1.5×IQR; máximo **136,403 m²**;
- maintenance_cost_mxn: 12.59% fuera de IQR; máximo **$1,665,495**;
- inquiry.requested_area_sqm: 11.57% fuera de IQR; máximo **40,920.9 m²**;
- lead.prior_searches: máximo 60;
- lead.prior_inquiries: máximo 199.

El error sería aplicar winsorization o eliminación automática sólo por exceder una regla estadística.

Un terreno industrial, un gran inmueble logístico o una transacción enterprise pueden ser auténticamente extremos.

### Decisión EDA

- identificar;
- revisar semántica;
- usar transformaciones robustas cuando corresponda;
- no eliminar de forma global sin evidencia.

Fuente:
[DATA_AUDIT](../AssessmentSol1/evidence/DATA_AUDIT.md)

---

## 12. Hay variables cuyo nombre parece confiable, pero su semántica no lo es

Dos hallazgos cambiaron directamente la política de variables.

### 12.1 spots.total_inquiries no es el conteo de inquiries observado

Al reconciliar el campo con la tabla de eventos:

- exact match: **7.07%**;
- total_inquiries >= conteo de eventos: 37.43%;
- correlación: **-0.051**;
- diferencia mediana: -2.

No existe evidencia para usar este campo como “histórico de consultas”.

### 12.2 broker_response_hours no es un SLA limpio

Se observaron:

- 3,786 no_response con response_hours poblado;
- 2,701 accepted/rejected/scheduled_visit sin response_hours;
- medianas por outcome prácticamente iguales, alrededor de 8.1–8.5 horas.

Esto contradice una interpretación simple del nombre de la variable.

### Implicación

El EDA no sólo estudia distribuciones. También valida si la semántica del dato permite convertir una columna en una feature.

Fuentes:
- [D029 y D033](../experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md)
- [AssessmentSol1 DATA_AUDIT](../AssessmentSol1/evidence/DATA_AUDIT.md)

---

## 13. Modalidad sí parece una restricción dura; sector y geografía se comportan como preferencias

Sobre las 22,576 inquiries:

- compatibilidad de modalidad Lead↔Spot: **100.0%**;
- sector exacto: **70.35%**;
- municipio preferido exacto: **19.80%**;
- corredor exacto cuando se declara: **18.60%**.

### Interpretación

La conducta observada del marketplace dice:

- modalidad = restricción estructural;
- sector = preferencia fuerte, pero no absoluta;
- municipio/corredor = preferencias blandas.

Esto es muy relevante para fallback. Convertir municipio o corredor en hard filters produciría una política mucho más rígida que el comportamiento observado de los usuarios.

Fuente:
[D026](../experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md)

---

## 14. Segmentación: existen pockets interesantes, pero no hay evidencia para “multiplicadores mágicos”

Durante la exploración se probaron múltiples familias de clustering y matching:

- Search Need;
- Dynamic Need;
- Physical;
- Location;
- Broker Supply;
- Broker Service;
- combinaciones jerárquicas.

Uno de los pockets exploratorios más llamativos fue:

**DN4 × LOC1 × BSV1**

con:

- N=60;
- scheduled_visit raw: **36.67%**;
- tasa suavizada: **31.37%**;
- lift suavizado: **1.510x**.

Sin embargo, ese resultado fue descubierto después de inspeccionar múltiples combinaciones y no constituye validación confirmatoria.

Codexway volvió a imponer gates de estabilidad, balance, N mínimo, shrinkage, Wilson intervals y Benjamini–Hochberg FDR.

Resultado actual de Codexway:

- perfiles que pasan balance/ARI: Physical, Location, Broker Service;
- Need y Dynamic Need rechazados en el gate actual;
- 19 celdas elegibles;
- **0 pasan BH-FDR al 10%**.

### Conclusión final del EDA

Los clusters son útiles para:

- describir perfiles;
- construir hipótesis de routing;
- entender interacciones locales;
- diseñar experimentos online.

No son evidencia suficiente para multiplicar el score por un lift observado offline.

Fuentes:
- [CLUSTER_FINDINGS de Codexway](../codexway/outputs/CLUSTER_FINDINGS.md)
- [D039–D049](../experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md)

---

## 15. La calidad semántica del inventario es un problema real y distinto del scoring

La revisión de title + description contra atributos estructurados encontró señales de calidad de catálogo que no aparecen en un EDA puramente tabular.

El sidecar determinístico derivado de la exploración semántica detectó sobre 3,000 spots:

- direct conflict: **322 spots, 10.73%**;
- Land × lenguaje de edificio/interiores: **230, 7.67%**;
- security ambiguity: **327, 10.90%**;
- Retail adaptive-use language: **109, 3.63%**;
- alguna ambigüedad semántica: **429, 14.30%**;
- al menos una señal semántica: **890 spots**.

Un ejemplo especialmente interesante fue:

**sector=Land + lenguaje propio de un edificio terminado**, como “recién remodelado”, “acabados modernos” o “listo para ocupar”.

### Importante

Estas filas son **candidatos de QA**, no errores confirmados.

No existe human gold suficiente para llamar a cada flag una inconsistencia verdadera.

### ¿Predice mejor la conversión?

Se probó explícitamente.

Agregar Semantic Rules al ABT:

- Macro Lift@10: **1.267x → 1.196x**;
- delta: **-0.0716x**;
- IC95%: [-0.1438, +0.1251].

No pasó el gate de promoción.

### Hallazgo senior

**La calidad del catálogo y la calidad del lead son problemas distintos.**

Una regla puede ser muy útil para limpiar inventario y, aun así, no mejorar el ranking de scheduled visits.

Fuentes:
- [D055–D061](../experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md)
- [AI_USAGE de AssessmentSol1](../AssessmentSol1/llm/AI_USAGE.md)
- [EV-018](../experimentos/Evidencias/EV-018_semantic_rules_lift_ablation.md)

---

## 16. Hipótesis que generó el EDA y qué ocurrió después

Una fortaleza de este análisis es que varias hipótesis no se quedaron como intuiciones: fueron sometidas a experimentos posteriores.

| Hipótesis nacida del EDA | Evidencia posterior | Estado |
|---|---|---|
| Industrial debería mostrar mayor propensión de progreso | Mayor tasa descriptiva bajo Codexway y AssessmentSol1 | **Soportada descriptivamente** |
| La primera inquiry refina la necesidad inicial | Ratios T0→T1, gaps de área, Dynamic Need | **Soportada** |
| asked_visit podría ser una señal casi determinante | Sólo +1.26 pp en clean-room | **Señal modesta; requiere ablación** |
| Dynamic Need podría mejorar scoring | Mejora puntual de Lift@10, pero intervalos cruzan cero y falla gate actual de clustering | **Inconclusa como feature global** |
| Ciertas combinaciones Need×Location×Broker podrían ser muy potentes | Pocket 1.51x, no confirmatorio; Codexway 0 celdas FDR | **Hipótesis para A/B, no regla** |
| Availability faltante significa poca oferta | Coverage drift muestra que mucha ausencia es observabilidad | **Rechazada** |
| Market Context debería ayudar al modelo histórico | Falta effective/publication time y coverage exacta baja | **EDA-only** |
| Las inconsistencias semánticas del catálogo pueden predecir Lead Quality | Ablación de Semantic Rules no mejora Lift@10 | **Rechazada para scoring; útil para QA** |
| total_inquiries puede representar popularidad histórica | Reconciliación con eventos falla | **Rechazada** |
| response_hours mide SLA del broker | Semántica inconsistente con outcomes | **Rechazada para interpretación causal/SLA** |

Este recorrido EDA → hipótesis → experimento → decisión es más valioso que presentar únicamente correlaciones que nunca fueron desafiadas.

---

## 17. Principales hipótesis predictivas que sí merece evaluar Lead Quality

Después de todos los hallazgos, las familias más defendibles para el modelo son:

### H1. Sector

Industrial presenta una tasa de scheduled_visit superior a Office y Retail en dos reconstrucciones independientes del target.

**Esperanza:** señal moderada, no suficiente por sí sola.

### H2. Refinamiento T0→T1

La diferencia entre necesidad inicial y solicitud actual parece contener más información que el valor absoluto aislado.

Ejemplos:

- requested_area / target_area;
- gap de área;
- presupuesto solicitado vs rango original;
- modalidad consistente;
- cantidad de dimensiones modificadas.

### H3. Intención actual

asked_visit, channel, urgency y completitud de la inquiry son observables en T1.

**Riesgo:** confundir intención con leakage. Se requiere evidencia de que el campo es conocido antes de la respuesta.

### H4. Interacciones simples y estables

La evidencia posterior de Codexway favorece representaciones de baja cardinalidad y estabilidad temporal sobre una gran colección de perfiles.

### H5. Historial dinámico, sólo cuando existe de forma point-in-time

Para T2, la trayectoria previa puede aportar señal, siempre que todo se construya mediante shift estricto y no se utilice ninguna respuesta futura.

### Lo que deliberadamente queda fuera de Lead Quality

- Availability;
- candidate depth;
- broker response;
- response hours;
- raw current spot counters;
- market_context sin publication time;
- precios actuales usados como si fueran históricos;
- LLM semantic flags;
- clusters inestables;
- variables outcome-derived.

---

## 18. Riesgos de sesgo y contaminación temporal detectados

El EDA identifica varios mecanismos capaces de generar resultados artificialmente buenos.

### 18.1 Era de instrumentación

Las cohortes antiguas tienen peor Availability coverage. Un modelo que consume esa cobertura puede aprender “año 2025 vs 2026” en lugar de comportamiento comercial.

### 18.2 Exposición futura

El número total de inquiries de un lead no existe en T1. AssessmentSol1 encuentra media 4.58, mediana 5 y máximo 8, pero ese número sólo es válido para entender exposición retrospectiva.

### 18.3 Estado actual del listing

days_on_market, total_views, total_inquiries e is_active no tienen historial versionado.

Usarlos retrospectivamente equivale a mirar el futuro.

### 18.4 Precios históricos

Los precios actuales son informativos para narrativa, pero el dataset no demuestra que fueran los mismos al score time.

Por tanto, un “budget fit histórico” exacto sería falsa precisión.

### 18.5 Contexto de mercado

month no equivale a publication timestamp.

### 18.6 Clusters

Un cluster entrenado sobre todo el dataset introduce fit leakage; cualquier perfil usado en validación debe ser refit exclusivamente en train.

Fuente principal:
[Leakage Matrix de Codexway](../codexway/evidence/LEAKAGE_MATRIX.md)

---

## 19. Qué aprendimos del mercado, en lenguaje de negocio

### 1. No todos los leads valen lo mismo

Industrial muestra mayor propensión observada a scheduled_visit que Office y Retail.

### 2. Pero la oportunidad no depende sólo del lead

El inventario observable cambia radicalmente entre cohortes.

### 3. Retail tiene una tensión especialmente interesante

Es el sector con mayor demanda y, en el clean-room, con una participación de demanda superior a su share de catálogo histórico.

### 4. La primera conversación importa

La inquiry refina el área, presupuesto y necesidad inicial, especialmente en venta y búsquedas flexibles.

### 5. Los usuarios son flexibles geográficamente

La modalidad se respeta de forma casi absoluta; municipio y corredor no.

Esto abre espacio para fallback inteligente.

### 6. “Más datos” no siempre significa “mejores features”

Hay columnas cuyo nombre parece útil pero cuya semántica no soporta el uso histórico.

### 7. El inventario tiene un problema de observabilidad, no sólo de disponibilidad

Una ausencia temprana de snapshot es desconocimiento, no ausencia de oferta.

### 8. El catálogo también tiene una dimensión de calidad semántica

Las contradicciones de copy merecen un sistema de QA, pero no deben confundirse con propensión de conversión.

---

## 20. Decisiones que este EDA deja preparadas para los siguientes entregables

El EDA sugiere las siguientes decisiones de diseño:

1. **T1 debe ser el momento principal de scoring**, porque incorpora la necesidad refinada de la primera inquiry.
2. **Lead Quality e Inventory deben mantenerse separados** durante el modelado.
3. **Availability debe reconstruirse backward-as-of**, nunca mediante nearest o estado actual.
4. **UNKNOWN debe preservarse explícitamente**.
5. **Los faltantes deben modelarse por semántica**, especialmente NOT_APPLICABLE vs NOT_STATED.
6. **No se deben eliminar outliers globalmente** sin justificación de negocio.
7. **Market Context es descriptivo hasta contar con effective time**.
8. **Clusters son herramientas de interpretación e hipótesis**, no multiplicadores automáticos.
9. **La calidad semántica del inventario pertenece a QA**, no al scorer de Lead Quality salvo evidencia incremental.
10. **Toda selección posterior debe ser temporal**, con métricas de ranking y no sólo AUC.

---

## 21. Conclusión

El hallazgo más importante de este EDA no es una correlación aislada.

Es que Spot2 contiene **tres procesos superpuestos**:

**demanda del lead → progreso comercial → capacidad del inventario para atenderlo**

La demanda es relativamente amplia y estable; la propensión observada al scheduled_visit cambia de forma moderada entre segmentos; y la disponibilidad/observabilidad del inventario cambia de forma mucho más agresiva con el tiempo.

Eso obliga a diseñar el sistema con disciplina temporal.

El análisis también muestra que varias aparentes “señales” eran en realidad trampas:

- Availability unida sin as-of;
- total_inquiries tratado como evento histórico;
- broker_response_hours interpretado como SLA;
- missing presupuestario tratado como mala calidad;
- market_context usado sin tiempo de publicación;
- clusters exploratorios convertidos en reglas;
- inconsistencias semánticas convertidas en features sin demostrar lift.

Detectar estas trampas cambia más la calidad de la solución que agregar un algoritmo adicional.

El resultado es un EDA que no sólo describe el dataset: **define qué puede creerse, qué puede modelarse y qué debe permanecer como hipótesis**.

---

## 22. Trazabilidad de evidencia

### Base autoritativa — Codexway

- [README general](../codexway/README.md)
- [Lead mix](../codexway/outputs/tables/lead_mix.csv)
- [Tasa del target por segmento](../codexway/outputs/tables/target_rate_by_segment.csv)
- [Volumen mensual](../codexway/outputs/tables/monthly_volume.csv)
- [Market context EDA](../codexway/outputs/tables/market_context_eda.csv)
- [Missingness](../codexway/outputs/tables/data_quality_missingness.csv)
- [Inventory freshness](../codexway/outputs/tables/inventory_freshness_sensitivity.csv)
- [Cluster findings](../codexway/outputs/CLUSTER_FINDINGS.md)
- [Leakage Matrix](../codexway/evidence/LEAKAGE_MATRIX.md)
- [Decisiones metodológicas](../codexway/evidence/DECISIONS.md)

### Robustez clean-room — AssessmentSol1

- [EDA Findings](../AssessmentSol1/evidence/EDA_FINDINGS.md)
- [Data Audit](../AssessmentSol1/evidence/DATA_AUDIT.md)
- [Feature Engineering Decisions](../AssessmentSol1/evidence/FEATURE_ENGINEERING_DECISIONS.md)
- [Market Context Highlights](../AssessmentSol1/outputs/eda/market_context_highlights.csv)

### Investigación experimental

- [Descubrimientos acumulados](../experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md)
- [EV-010 Matching A/B](../experimentos/Evidencias/EV-010_matching_ab_v3.md)
- [EV-013 Matching Profiles](../experimentos/Evidencias/EV-013_matching_profiles_v4.md)
- [EV-017 LLM Semantic Pilot](../experimentos/Evidencias/EV-017_llm_semantic_feature_pilot.md)
- [EV-018 Semantic Rules Ablation](../experimentos/Evidencias/EV-018_semantic_rules_lift_ablation.md)

---

## 23. Cobertura contra el assessment

| Requerimiento oficial de EDA | Cobertura |
|---|---|
| Distribución por sector | ✅ Sección 3 |
| Distribución por modalidad | ✅ Sección 3 |
| Distribución por tipo de usuario | ✅ Sección 3 |
| Tasas de conversión/proxy por segmento | ✅ Sección 5 |
| Estacionalidad y patrones temporales | ✅ Sección 6, con cautela metodológica |
| Dinámica por corredor/municipio | ✅ Sección 7 |
| Precios y absorción | ✅ Sección 7 |
| Calidad de datos y missingness | ✅ Secciones 10–12 |
| Outliers | ✅ Sección 11 |
| Sesgos y riesgos | ✅ Sección 18 |
| Hipótesis sobre predictores | ✅ Secciones 16–17 |
| Narrativa de negocio | ✅ Secciones 19–21 |

**Estado del Entregable 1: COMPLETO.**
