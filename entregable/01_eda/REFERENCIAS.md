# Referencias y trazabilidad — EDA

Este anexo explica **de dónde sale cada afirmación importante del EDA**. No es necesario abrir documentación histórica para entender la entrega final.

La jerarquía utilizada fue:

1. **Codexway:** define la solución final.
2. **AssessmentSol1:** funciona como auditoría metodológica complementaria.
3. **experimentos:** conserva pruebas alternativas, resultados negativos y aprendizajes.

Cuando dos líneas de investigación usan poblaciones, variables objetivo o reglas temporales distintas, **sus métricas no se mezclan**.

## A. Evidencia que define la solución final

| ID | Evidencia | Para qué se utilizó |
|---|---|---|
| C01 | Contrato de producto de Codexway | Momento T1, arquitectura general y limitaciones |
| C02 | Decisiones finales | Reglas de temporalidad, inventario, segmentación y validación |
| C03 | Matriz de fuga de información futura | Qué familias de variables están permitidas y cuáles se bloquean |
| C04 | Mapa de fuentes | Clasificación de la evidencia heredada |
| C05 | Resumen del EDA | Conteos, madurez y prevalencia de la visita agendada |
| C06 | Composición de leads | Mezcla de sector y modalidad |
| C07 | Tasa por segmento | Asociaciones descriptivas con la visita agendada |
| C08 | Contexto de mercado | Dinámica sectorial utilizada sólo para análisis descriptivo |
| C09 | Vigencia del inventario | Sensibilidad a ventanas de 7, 30 y 90 días |
| C10 | Auditoría de inventario | Estados desconocidos, rangos de incertidumbre y limitaciones |
| C11 | Hallazgos de segmentación | Confirmación o rechazo de patrones locales |
| C12 | Sensibilidad T0/T2 | Papel secundario de momentos anteriores y posteriores a T1 |
| C13 | Sensibilidad de madurez | Estabilidad de la variable de éxito con ventanas de 7/14/30 días |
| C14 | Cronología de decisiones | Evolución de correcciones y decisiones finales |

## B. Auditoría metodológica complementaria

| ID | Evidencia | Para qué se utilizó |
|---|---|---|
| A01 | Auditoría de datos | Integridad de relaciones, datos faltantes, valores extremos y uniones temporales |
| A02 | Hallazgos del EDA | Demanda/oferta, área solicitada, urgencia y profundidad de alternativas |
| A03 | Cambios temporales | Separar cambios de población de cambios en cobertura o instrumentación |
| A04 | Decisiones sobre variables | Significado de datos faltantes y refinamiento de la necesidad T0→T1 |
| A05 | Semántica temporal | Qué información es observable en cada momento |
| A06 | Demanda frente a oferta | Brecha sectorial en la muestra de desarrollo |
| A07 | Resumen numérico | Área, urgencia, exposición y antigüedad del inventario |
| A08 | Serie mensual T1 | Evolución de cobertura y cantidad de candidatos |
| A09 | Resumen de inventario | Profundidad y ausencia de información |
| A10 | Hallazgos de mercado | Ejemplos geográficos y sectoriales |
| A11 | Cambio de exposición en T0 | Evidencia alternativa sobre cambios temporales |
| A12 | Trayectoria T2 | Evidencia sobre el valor adicional, pero inestable, de interacciones posteriores |

> Algunas decisiones de esta auditoría usan contratos distintos de los de Codexway. Se utilizaron para **cuestionar y validar** la solución, no para sustituirla.

## C. Investigación experimental

| ID | Evidencia | Para qué se utilizó |
|---|---|---|
| E01 | [profile_clustering_v2](../../experimentos/profile_clustering_v2/README.md) + resultados de clusterers/perfiles/combinaciones | Clustering resultado-free por Lead, Persona, Search Need, Spot, Broker e Inquiry Intent; balance, estabilidad, interpretación y primeras interacciones Lead × Spot × Broker |
| E02 | [matching_profiles_v4](../../experimentos/matching_profiles_v4/INTERPRETABILIDAD.md) + [decisión final](../../experimentos/matching_profiles_v4/DECISION_SEGMENTACION.md) | Behavioral Persona, Dynamic Need, Physical/Location, Broker Service/Supply, transición T0→T1 y pockets locales como DN4 × LOC1 × BSV1 |
| E03 | Tratamiento de variables | Documentar cuándo un dato faltante tiene significado estructural |
| E04 | Conocimiento agregado | Síntesis de descubrimientos experimentales |
| E05 | Piloto semántico con IA | Evaluar si un LLM aportaba información nueva al modelo |
| E06 | Prueba de reglas semánticas | Confirmar que mejorar el control de catálogo no implicaba mejorar el ranking |
| E07 | Pruebas de compatibilidad y disponibilidad | Auditar relaciones, temporalidad del inventario y alternativas |

### Archivos experimentales usados directamente para la sincronización de clustering

- [Clusterers seleccionados v2](../../experimentos/profile_clustering_v2/results/selected_clusterers.csv)
- [Interpretabilidad de perfiles v2](../../experimentos/profile_clustering_v2/results/profile_interpretability.csv)
- [Combinaciones Lead × Spot × Broker v2](../../experimentos/profile_clustering_v2/results/top_3entity_combinations.csv)
- [Clusterers seleccionados v4](../../experimentos/matching_profiles_v4/results/selected_clusterers.csv)
- [Interpretabilidad de perfiles v4](../../experimentos/matching_profiles_v4/results/profile_interpretability.csv)
- [Transición Need T0→T1](../../experimentos/matching_profiles_v4/results/need_t0_t1_transition_matrix.csv)
- [Pockets con Broker Service](../../experimentos/matching_profiles_v4/results/top_service_compatibility_cells.csv)

## D. Tablas finales utilizadas en el EDA

- [Resumen de fuentes](tablas/00_resumen_fuentes.csv)
- [Métricas principales](tablas/01_metricas_eda_clave.csv)
- [Hallazgos y decisiones](tablas/02_hallazgos_decisiones.csv)
- [Fuentes integradas](tablas/03_fuentes_integradas.csv)

## Regla de interpretación

Una cifra histórica se utiliza sólo si es compatible con la población y el momento que se están describiendo. Si una fuente usa otra definición de éxito o una ventana temporal distinta, se presenta como evidencia complementaria y se etiqueta como tal.

El objetivo de este anexo es que el evaluador pueda distinguir con claridad **qué define la solución final, qué la audita y qué simplemente documenta caminos explorados**.
