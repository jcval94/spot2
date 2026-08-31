# Matriz final de cobertura del reto

Esta tabla permite verificar, en una sola vista, qué parte de la entrega responde a cada requisito.

> **Cómo leerla:** **COMPLETO** significa que existe una respuesta y evidencia suficiente dentro del paquete final. **PARCIAL** significa que existe trabajo sólido, pero todavía falta evidencia que sólo puede obtenerse con nuevos datos o una prueba en operación. No hay requisitos técnicos principales marcados como FALTANTE.
>
> Cuando aparece **Lift@10**, significa cuánto mejora el 10% mejor priorizado frente a elegir al azar el mismo número de casos. Los nombres de variables como `scheduled_visit` se conservan porque son necesarios para reproducir la solución.

| Requisito | Dónde se responde | Evidencia principal | Estado |
|---|---|---|---|
| Entender la distribución de leads por sector, modalidad y tipo de usuario | [EDA](01_eda/README.md) | 5,000 leads y análisis de composición | **COMPLETO** |
| Analizar tasas de avance comercial por segmento | [EDA final](01_eda/EDA_FINAL.md) | Visita agendada en T1 y segmentación descriptiva | **COMPLETO** |
| Considerar temporalidad y cambios en el tiempo | [EDA final](01_eda/EDA_FINAL.md) | Cohortes, T0/T1/T2 y cambios en cobertura de inventario | **COMPLETO** |
| Analizar contexto de mercado y geografía | [EDA final](01_eda/EDA_FINAL.md) | Contexto por sector y geografía, usado con cautela temporal | **COMPLETO** |
| Revisar datos faltantes, valores extremos y sesgos | [EDA final](01_eda/EDA_FINAL.md) | Calidad de datos y significado de la ausencia de información | **COMPLETO** |
| Presentar hipótesis de negocio y qué ocurrió con ellas | [EDA final](01_eda/EDA_FINAL.md) | Hipótesis soportadas, inconclusas y descartadas | **COMPLETO** |
| Resumir problema, enfoque, resultado e impacto | [Resumen ejecutivo](02_one_pager/README.md) | Síntesis de la solución final | **COMPLETO** |
| Contar con una pieza visual ejecutiva | [Resumen visual](02_one_pager/ONE_PAGER_SPOT2_AESTHETIC.html) | Flujo Lead → Calidad → Oportunidad ← Inventario | **COMPLETO** |
| Justificar las variables del modelo de Calidad del lead | [Modelo de Calidad](03_lead_quality/MODELO_CALIDAD_LEAD.md) | Variables permitidas en T1 y controles temporales | **COMPLETO** |
| Comparar y seleccionar modelos | [Modelo de Calidad](03_lead_quality/MODELO_CALIDAD_LEAD.md) | Se evaluaron alternativas simples y complejas; se retuvo la solución más estable | **COMPLETO** |
| Reportar métricas de desempeño | [Modelo de Calidad](03_lead_quality/MODELO_CALIDAD_LEAD.md) | ROC-AUC 0.5478, PR-AUC 0.2391, Brier 0.1658 y Lift@10 1.689x | **COMPLETO** |
| Validar el modelo respetando el tiempo | [Modelo de Calidad](03_lead_quality/MODELO_CALIDAD_LEAD.md) | Separaciones temporales y muestra histórica de evaluación | **COMPLETO** |
| Definir una política compatible con capacidad operativa | [Calidad del lead](03_lead_quality/README.md) | Prioridad base sobre el 10% superior; escenarios 5/10/20% | **COMPLETO** |
| Analizar errores, segmentos y estabilidad | [Modelo de Calidad](03_lead_quality/MODELO_CALIDAD_LEAD.md) | Análisis de errores y estabilidad temporal | **COMPLETO** |
| Definir qué significa inventario atendible | [Inventario](04_inventory_fallback/README.md) | Compatibilidad, disponibilidad conocida e incertidumbre | **COMPLETO** |
| Evitar utilizar estados futuros del inventario | [Inventario](04_inventory_fallback/README.md) | Último estado conocido hasta el momento de decisión | **COMPLETO** |
| Resolver falta de inventario | [Inventario](04_inventory_fallback/README.md) | Alternativas, hasta 5 visibles y abstención si ninguna es defendible | **COMPLETO** |
| Distinguir “desconocido” de “no disponible” | [Inventario](04_inventory_fallback/README.md) | Incertidumbre explícita y vigencia de 30 días | **COMPLETO** |
| Combinar Calidad del lead e Inventario | [Puntaje de oportunidad](05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md) | `p_quality × inventory_serviceability_lower` y cota superior | **COMPLETO** |
| Evaluar el puntaje combinado | [Puntaje de oportunidad](05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md) | Lift@10 conservador 1.370x | **COMPLETO** |
| Demostrar que Inventario incrementa la conversión T1 | [Puntaje de oportunidad](05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md) | El resultado T1 no mide directamente el éxito de alternativas | **PARCIAL** |
| Diseñar una arquitectura para operación real | [Arquitectura](05_opportunity_produccion/02_ARQUITECTURA_PRODUCCION.md) | Componentes separados, versionados y auditables | **COMPLETO** |
| Definir monitoreo y manejo de fallos | [Guía operativa](05_opportunity_produccion/03_MONITOREO_GOBIERNO_RUNBOOK.md) | Datos, modelo, inventario, operación y resultados | **COMPLETO** |
| Definir cuándo reentrenar o volver a una versión anterior | [Guía operativa](05_opportunity_produccion/03_MONITOREO_GOBIERNO_RUNBOOK.md) | Controles de reentrenamiento y reversión | **COMPLETO** |
| Usar IA de forma real y justificar su papel | [Uso de IA](07_ia_product_vision/01_USO_OBLIGATORIO_IA.md) | Piloto real con GPT-5 nano, costos y resultados | **COMPLETO** |
| Documentar qué funcionó y qué no con IA | [Uso de IA](07_ia_product_vision/01_USO_OBLIGATORIO_IA.md) | Útil para descubrir problemas semánticos; no promovida al predictor | **COMPLETO** |
| Proponer una visión de producto a tres meses | [Visión ejecutiva](07_ia_product_vision/04_PRODUCT_VISION_EJECUTIVA.md) | Instrumentación → validación → experimento controlado | **COMPLETO** |
| Definir qué datos adicionales pedir | [Visión ejecutiva](07_ia_product_vision/04_PRODUCT_VISION_EJECUTIVA.md) | Historial de inmuebles, recomendaciones, visitas, cierres y valor | **COMPLETO** |
| Definir cómo medir impacto real | [Diseño experimental](07_ia_product_vision/03_EXPERIMENTACION_CAUSAL.md) | Comparación controlada contra la política actual | **COMPLETO** |

## Qué queda deliberadamente abierto

Hay un punto principal que no puede resolverse sólo con los datos históricos disponibles:

**el valor causal e incremental de incorporar Inventario al proceso de priorización.**

La entrega demuestra que el componente puede construirse sin usar información futura y que el Puntaje de oportunidad supera una selección aleatoria. Sin embargo, el resultado actual —visita agendada en la primera consulta— no registra si una alternativa recomendada fue aceptada ni si produjo una venta.

Por eso este punto se mantiene **PARCIAL** y la siguiente etapa propuesta es una validación con datos nuevos seguida de un experimento controlado. Esta limitación se presenta de forma explícita en lugar de convertir evidencia histórica en una afirmación causal.
