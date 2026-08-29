# Qué está dando señal en T2

## Resumen ejecutivo

La familia con mayor dependencia predictiva es **comportamiento acumulado y respuestas históricas ya observadas**. Al romper conjuntamente esa información, Average Precision cae +0.064.
La variable individual más influyente para el head es **mediana histórica de horas de respuesta** (ΔAP +0.010; ΔAUC +0.005).
El análisis usa 1,297 snapshots T2 de test temporal, con tasa positiva de 43.2%.

T2 no mejora simplemente porque el modelo conoce la etapa. Mejora porque a esa altura del funnel existe información que no estaba disponible en T0/T1: comportamiento acumulado, intención actual, encaje con el inmueble y disponibilidad observable.

## Fidelidad del análisis

- Head T2 reentrenado: ROC-AUC **0.595**, AP **0.515**.
- Head T2 original: ROC-AUC **0.595**, AP **0.515**.
- Random Forest diagnóstico: ROC-AUC **0.609**, AP **0.524**.

El ranking principal de variables viene del head T2 reentrenado. El Random Forest se usa como segunda opinión, no como sustituto del Modelo 3.

## Variables con mayor poder predictivo

| Rank | Variable | Familia | ΔAP | ΔAUC | Perfil descriptivo |
|---:|---|---|---:|---:|---|
| 1 | mediana histórica de horas de respuesta | interaction_history | +0.0097 | +0.0053 | <=Q25 (4.4): 40.7% vs >=Q75 (13.3): 41.4% (+0.7 pp) |
| 2 | respuestas históricas ya observadas | interaction_history | +0.0078 | +0.0086 | <=Q25 (1): 49.2% vs >=Q75 (2): 36.2% (-13.0 pp) |
| 3 | antigüedad del snapshot de disponibilidad | availability_asof | +0.0070 | +0.0056 | <=Q25 (5.792): 36.3% vs >=Q75 (32.53): 48.0% (+11.7 pp) |
| 4 | min budget mxn sale total | lead_intake | +0.0056 | +0.0016 | <=Q25 (6.132e+06): 31.7% vs >=Q75 (2.068e+07): 45.3% (+13.6 pp) |
| 5 | respuestas históricas aceptadas | interaction_history | +0.0039 | +0.0050 | <=Q25 (0): 51.4% vs >=Q75 (1): 37.8% (-13.6 pp) |
| 6 | spot floor level | spot_static | +0.0037 | +0.0004 | <=Q25 (0): 41.9% vs >=Q75 (3): 42.6% (+0.7 pp) |
| 7 | spot maintenance cost mxn | spot_static | +0.0037 | +0.0014 | <=Q25 (2968): 44.6% vs >=Q75 (3.168e+04): 44.8% (+0.2 pp) |
| 8 | tasa histórica de aceptación | interaction_history | +0.0036 | +0.0011 | <=Q25 (0): 45.7% vs >=Q75 (1): 41.2% (-4.5 pp) |
| 9 | spot price sqm mxn rent | spot_static | +0.0034 | +0.0023 | <=Q25 (121.5): 37.8% vs >=Q75 (331.4): 42.2% (+4.3 pp) |
| 10 | spot lat | spot_static | +0.0033 | +0.0008 | <=Q25 (19.43): 45.5% vs >=Q75 (25.64): 40.8% (-4.7 pp) |

### Cómo leer la importancia

Una caída positiva significa que al destruir esa información en test el ranking empeora. Una importancia cercana a cero puede significar poca señal incremental o que otras variables correlacionadas pueden sustituirla.

## Importancia por familia

| Familia | ΔAP | ΔAUC | Qué representa |
|---|---:|---:|---|
| interaction_history | +0.0638 | +0.0720 | comportamiento acumulado y respuestas históricas ya observadas |
| spot_static | +0.0098 | +0.0031 | características estructurales del inmueble consultado |
| availability_asof | +0.0074 | +0.0058 | capacidad de atender la demanda con inventario observable |
| lead_intake | +0.0064 | +0.0074 | perfil conocido desde la creación del lead |
| context_flags | +0.0000 | +0.0000 | presencia o ausencia de contexto utilizable |
| lead_spot_match | -0.0012 | -0.0009 | compatibilidad entre lo que busca el lead y el inmueble |
| current_inquiry | -0.0024 | +0.0019 | intención y restricciones de la inquiry actual |

## Robustez: una sola observación T2 por lead

Para comprobar que el resultado no sea sólo consecuencia de que los leads más activos generan más snapshots, repetimos la permutación por familia usando el primer y el último T2 de cada lead.

| Cohorte | Familia dominante | ΔAP | ΔAUC |
|---|---|---:|---:|
| all_t2 | interaction_history | +0.0638 | +0.0720 |
| first_t2_per_lead | interaction_history | +0.0471 | +0.0472 |
| last_t2_per_lead | interaction_history | +0.0757 | +0.0870 |

## ¿Coincide el Random Forest?

- Spearman head vs RF permutation: **0.245**.
- Spearman head vs RF impurity importance: **0.259**.

El permutation importance es más confiable aquí que la importancia MDI del Random Forest, porque MDI puede favorecer variables continuas o de alta cardinalidad.

## Qué significa para Spot2

1. **Lead Quality debe seguir siendo dinámico.** El incremento de información aparece cuando ya existe comportamiento real.
2. **El siguiente feature engineering debería concentrarse en las familias dinámicas que más ΔAP generan**, no en agregar más variables estáticas indiscriminadamente.
3. **Compatibilidad lead↔spot y disponibilidad deben evaluarse como bloques.** Variables correlacionadas pueden repartirse señal y parecer débiles por separado.
4. **No convertir importancia en causalidad.** Una variable puede ser un excelente marcador de intención sin ser una palanca causal de conversión.

## Limitaciones

- El target es scheduled_visit, no cierre.
- Los datos son sintéticos.
- Permutation importance mide dependencia predictiva, no efecto causal.
- Variables correlacionadas pueden ocultarse entre sí.
- Los perfiles de dirección son descriptivos y univariados.

## Recomendación

Usaría este ranking para diseñar el siguiente experimento de feature engineering: profundizar primero en las dos familias con mayor caída conjunta y validar el lift incremental con el mismo split temporal y controles de leakage.
