# HARD QUESTIONS — defensa Spot2

Las respuestas distinguen evidencia final (`codexway`), challengers (`experimentos`) y clean-room (`AssessmentSol1`). Hay exactamente 40 preguntas: cinco por categoría.

## Negocio

### 1. ¿Qué valor de negocio tiene un modelo con AUC 0.55?

**Respuesta ejecutiva — 20 segundos**

No lo vendo como un gran predictor universal. Lo uso para priorización limitada: en el holdout, el 10% superior concentró 16.98% de las visitas, Lift 1.689 con IC95% 1.381–1.982. El valor potencial está en ordenar una cola con capacidad escasa; debe confirmarse con piloto causal.

**Respuesta técnica — 60–90 segundos**

El AUC 0.5478 resume todos los pares positivo–negativo y el score final sólo tiene dos niveles, por lo que acumula muchos empates. Lift@10 mide otra decisión: el bolsillo alto tuvo 35.83% de visitas frente a 21.22% de baseline. En 1,000 leads y capacidad para 100, eso equivale históricamente a 35.83 vs 21.22 visitas, +14.61. No es uplift porque no hay asignación aleatoria; por eso la recomendación es shadow scoring y A/B guardado.

**Datos que la sustentan**

- AUC 0.547776, IC95% [0.527297, 0.568425].
- Lift@10 1.688794, IC95% [1.380730, 1.981679].
- Prevalencia holdout 21.2157%.

**Fuente**

- `codexway/outputs/metrics/t1_model_metrics.json`
- `codexway/outputs/metrics/t1_metric_intervals.csv`

**Error que debo evitar**

- Decir que +69% de lift es +69% de conversión causal.

### 2. ¿Por qué optimizar scheduled visit y no cierre o revenue?

**Respuesta ejecutiva — 20 segundos**

Porque scheduled visit es el outcome temprano observable y suficientemente frecuente: 1,001 positivos entre 4,898 maduros. Es un proxy de avance, no el objetivo económico final; cierre, ingreso y margen deben entrar como outcomes del piloto y del siguiente modelo.

**Respuesta técnica — 60–90 segundos**

El contrato T1 necesita una etiqueta que madure pronto y no mire más allá de siete días. Scheduled visit ofrece prevalencia 20.44%, mientras revenue/cierre no aparece con un contrato maduro y trazable en estos artefactos. Esa elección reduce latencia de aprendizaje, pero introduce riesgo de Goodhart: se podrían priorizar visitas que no cierran. Por eso la evaluación online debe medir visitas como métrica proximal y cierre, revenue, margen, cancelación y carga operativa como outcomes/guardrails downstream.

**Datos que la sustentan**

- 4,898 maduros; 1,001 positivos; prevalencia 20.4369%.
- Ventana de madurez 7 días.
- Outcome downstream de cierre/revenue: NO LOCALIZADO EN LOS ARTEFACTOS.

**Fuente**

- `codexway/outputs/tables/data_audit.json`
- `codexway/config/base.yaml`

**Error que debo evitar**

- Equiparar visita con venta o valor incremental.

### 3. ¿Qué pondrías realmente en producción mañana?

**Respuesta ejecutiva — 20 segundos**

Un sistema de decisión asistida, no auto-routing: score en shadow, bandas de calidad e inventario, verificación humana para unknown, fallback visible y piloto aleatorizado. Los gates permiten nueva validación forward, no despliegue autónomo.

**Respuesta técnica — 60–90 segundos**

Publicaría Lead Quality, serviceability lower/upper, gap, freshness y razones de fallback en una cola auditable. Mantendría control aleatorio y estratificación por capacidad/segmento; registraría exposición, acción, visita, cierre y SLA. Bloquearía snapshots futuros, monitorizaría drift, calibración, cobertura y unknown. Los campos de listing sin versionado se usarían sólo con estado capturado desde el lanzamiento; el histórico no justifica decisiones automáticas. La promoción exigiría mejora causal y guardrails estables.

**Datos que la sustentan**

- Decisión: `ELIGIBLE_FOR_NEW_FORWARD_VALIDATION_AND_GUARDED_RANDOMIZED_PILOT`.
- 44.30% exact unknown.
- Holdout procedimental, no virgen.

**Fuente**

- `codexway/outputs/metrics/deployment_readiness.json`
- `codexway/outputs/tables/online_ab_protocol.json`

**Error que debo evitar**

- Decir “production ready” sin calificar piloto y controles.

### 4. ¿Cómo traduces Lift@10 a capacidad comercial?

**Respuesta ejecutiva — 20 segundos**

Con 1,000 leads y capacidad para trabajar 100, el baseline histórico espera 21.22 visitas; el bolsillo alto tuvo 35.83, unas 14.61 adicionales. Es una expectativa de backtest, no una promesa causal.

**Respuesta técnica — 60–90 segundos**

Lift@10 es precision top 10 dividida por prevalencia: 0.358289/0.212157=1.688794. Para 100 de 1,000, azar produce 100×0.212157=21.22 positivos; el modelo 100×0.358289=35.83. En el holdout real se seleccionan 172 leads por discretización y los empates se prorratean: 61.63 vs 36.49 positivos esperados. El impacto real depende de que la priorización cambie acciones y de que las visitas no se desplacen desde el control.

**Datos que la sustentan**

- Precision top 10 35.8289%.
- Baseline 21.2157%.
- 172 leads discretos, 61.63 positivos tie-aware.

**Fuente**

- `codexway/outputs/tables/gains.csv`
- `codexway/outputs/abt/split_manifest.json`

**Error que debo evitar**

- Multiplicar el lift por la tasa y volver a sumar el baseline.

### 5. ¿Cuál es la recomendación de negocio final?

**Respuesta ejecutiva — 20 segundos**

Usar calidad para decidir prioridad e inventario para decidir cómo atender, manteniendo ambos ejes visibles. Probar en un piloto guardado si esa política genera más visitas útiles y cierres, con especial atención a unknown y fallback.

**Respuesta técnica — 60–90 segundos**

No recomiendo ordenar exclusivamente por el producto. Lead Quality conserva el mejor ranking de visitas; Inventory lower/upper evita tratar ausencia de información como cero y cambia la acción: trabajar, verificar o buscar alternativa. El score combinado reduce Lift@10, así que su caso económico debe venir de menor desperdicio operativo o mayor atendibilidad, métricas todavía sin gold. El experimento online debe comparar la política de dos ejes contra workflow actual y registrar por separado prioridad y serviceability.

**Datos que la sustentan**

- Lead Quality Lift@10 1.6888.
- Opportunity lower Lift@10 1.3702.
- 2.38% sin alternativa conocida; 0% sin potencial.

**Fuente**

- `codexway/outputs/metrics/system_score_metrics.csv`
- `codexway/outputs/metrics/inventory_audit.json`

**Error que debo evitar**

- Presentar el producto como superior en predicción de visitas.

## Data Science

### 6. ¿Por qué regresión logística si CatBoost es más potente?

**Respuesta ejecutiva — 20 segundos**

Porque potencia no compró generalización. En el mismo holdout, la logística estable tuvo AUC 0.5478, AP 0.2391 y Lift@10 1.6888; CatBoost 0.4922, 0.2086 y 0.8264, además de Brier 0.2423 vs 0.1658.

**Respuesta técnica — 60–90 segundos**

CatBoost sí pareció competitivo durante rolling: AUC media 0.5228 y AP 0.2448. Pero sólo ganó AP a la logística amplia en 2 de 4 folds y degradó Brier medio 0.0138, superando el gate 0.005. En el holdout comparable quedó por debajo del baseline en ranking. No puedo demostrar que “sobreajustó” como mecanismo; sí puedo demostrar que no generalizó bajo el contrato temporal y que su coste de complejidad no estaba respaldado por métricas.

**Datos que la sustentan**

- Diferencia final–CatBoost: +0.0556 AUC, +0.0305 AP, +0.8624 Lift@10.
- CatBoost rolling AP media 0.2448; 2/4 wins.
- Brier holdout 0.242269 vs 0.165771.

**Fuente**

- `codexway/outputs/metrics/t1_model_metrics.json`
- `codexway/outputs/metrics/rolling_model_comparison.csv`

**Error que debo evitar**

- Afirmar genéricamente que CatBoost sobreajusta o que logística siempre gana.

### 7. ¿No es sospechoso que el modelo final tenga una sola feature?

**Respuesta ejecutiva — 20 segundos**

Es deliberado: la única señal que sobrevivió la validación fue `Industrial AND (small OR paid)`. Compitió contra una logística amplia de 25 raw/105 dimensiones y contra CatBoost; simplificar fue resultado, no punto de partida.

**Respuesta técnica — 60–90 segundos**

La interacción cubre 514 de 4,898 maduros y su tasa es 30.16% vs 19.30% fuera. En holdout cubre 187 leads con 35.83% de positivos. El modelo estandariza esa bandera y aplica logística regularizada; el coeficiente es +0.1204. La contrapartida es baja resolución: sólo dos scores y poca discriminación fuera del bolsillo. Por eso se presenta como política de priorización acotada y se monitorea cobertura del segmento.

**Datos que la sustentan**

- 1 raw / 1 encoded final.
- Segmento maduro N=514, 155 positivos.
- Benchmark amplio 25 raw/105 encoded.

**Fuente**

- `codexway/outputs/tables/feature_importance.csv`
- `codexway/config/feature_policy.yaml`

**Error que debo evitar**

- Decir que es un “top feature” entre diez finales.

### 8. ¿`asked_visit` es leakage y domina el modelo?

**Respuesta ejecutiva — 20 segundos**

No domina y no está en el campeón. Si se conoce al cierre de la primera inquiry, no es leakage temporal literal; sí puede reflejar política del agente. Quitarla del challenger mejoró Lift@10 de 0.8495 a 0.9865.

**Respuesta técnica — 60–90 segundos**

Su validez depende del timestamp: sólo es admisible si se captura dentro de T1 antes de eventos posteriores. Incluso así puede crear feedback porque agentes que ya buscan visita la marcan. La ablación muestra AUC casi igual, AP casi igual, Brier ligeramente mejor y Lift bastante mejor sin ella. Además, la tasa descriptiva es 21.27% con la bandera vs 20.16% sin ella, una separación pequeña. La política prudente fue excluirla del campeón.

**Datos que la sustentan**

- Lift con/sin: 0.849526/0.986546.
- AUC con/sin: 0.488051/0.485178.
- Descriptivo: 258/1,213 vs 743/3,685.

**Fuente**

- `codexway/outputs/metrics/t1_model_metrics.json`
- `codexway/outputs/abt/abt_t1_first_inquiry.parquet`

**Error que debo evitar**

- Llamarla automáticamente leakage sin revisar el instante de captura.

### 9. ¿Por qué T1 y no T0 o T2?

**Respuesta ejecutiva — 20 segundos**

T1 es el compromiso entre acción temprana e intención observada. T0 no tuvo señal útil; T2 agrega trayectoria pero llega más tarde y usa otra población. El campeón T1 alcanzó Lift@10 1.689 frente a 1.023 en T0 y 1.137 en la sensibilidad T2, sin comparar esos números como leaderboard estricto.

**Respuesta técnica — 60–90 segundos**

T0 puntúa al crear el lead y conserva máxima anticipación, pero la sensibilidad reportó AUC 0.4665. T1 incorpora la primera necesidad explícita sin usar inquiry futura. T2 puede aprovechar evolución del proceso; experimentos históricos muestran algunas mejoras, pero cambia el grano a trayectorias y el momento de intervención. La elección es productiva: puntuar cuando todavía hay margen de acción y ya existe contexto mínimo. Las métricas de stages no son directamente comparables por targets y N distintos.

**Datos que la sustentan**

- T0 N=1,371, AUC .4665, Lift10 1.0231.
- T1 N=1,711, AUC .5478, Lift10 1.6888.
- T2 N=5,249, AUC .5057, Lift10 1.1375.

**Fuente**

- `codexway/outputs/metrics/t0_t2_sensitivity_metrics.json`

**Error que debo evitar**

- Tratar T0/T1/T2 como un benchmark sobre idéntica población.

### 10. ¿Por qué siete días de madurez?

**Respuesta ejecutiva — 20 segundos**

Porque da una etiqueta oportuna con casi toda la muestra madura. La tasa es estable: 20.4369% a 7d, 20.4301% a 14d y 20.4060% a 30d; no fue una ventana elegida para inflar la prevalencia.

**Respuesta técnica — 60–90 segundos**

A siete días hay 4,898 elegibles y 102 censurados; a 30 días quedan 4,680 y 320 censurados. Se pierden 218 observaciones maduras y 46 positivos por esperar más, mientras la tasa cambia apenas 0.031 puntos porcentuales. El target sigue siendo proximal: no captura ventas tardías. En producción revisaría la curva completa de tiempo-a-visita y usaría survival analysis si la censura o el timing fueran objetivos centrales.

**Datos que la sustentan**

- 7d: 4,898/1,001/20.4369%.
- 14d: 4,836/988/20.4301%.
- 30d: 4,680/955/20.4060%.

**Fuente**

- `codexway/outputs/tables/target_maturity_sensitivity.csv`

**Error que debo evitar**

- Afirmar que siete días cubre todo el ciclo comercial.

## Estadística

### 11. ¿La PR-AUC no está demasiado cerca de prevalence?

**Respuesta ejecutiva — 20 segundos**

La mejora es modesta: 0.2391 vs 0.2122, +0.027 absoluto y +12.7% relativo. No la exagero; la utilidad más clara aparece en la cola superior y su intervalo es 0.2145–0.2655.

**Respuesta técnica — 60–90 segundos**

AP debe compararse con la prevalencia del mismo holdout, no con 0.5. La razón AP/base es 1.127. El límite inferior bootstrap apenas supera el baseline puntual, por lo que la mejora global es pequeña. Esto es coherente con un modelo de dos niveles: logra una bolsa de alto riesgo pero ordena poco el resto. La decisión se apoya conjuntamente en AP, Lift@K, calibración y estabilidad, no en un único número.

**Datos que la sustentan**

- AP 0.239129, IC [0.214479, 0.265538].
- Prevalencia 0.212157.
- AP/prevalencia 1.12713.

**Fuente**

- `codexway/outputs/metrics/t1_model_metrics.json`
- `codexway/outputs/metrics/t1_metric_intervals.csv`

**Error que debo evitar**

- Comparar PR-AUC con 0.5 o llamarla +69%.

### 12. ¿Elegiste K=10 porque era donde se veía mejor?

**Respuesta ejecutiva — 20 segundos**

K=10 representa una capacidad operativa, y la conclusión no depende sólo de ese punto: Lift@5 también es 1.689 y Lift@20 es 1.337. Reporto los tres y sus límites cuando existen.

**Respuesta técnica — 60–90 segundos**

El score tiene un grupo alto mayor al 10%, por eso top 5 y top 10 comparten precision con prorrateo de empates. A 20%, el lift cae como cabría esperar al incorporar score bajo. Esto evita escoger sólo el máximo. El intervalo de Lift@10 es 1.381–1.982; para Lift@20 el intervalo no está guardado. En producción K debe fijarse antes del experimento según capacidad real y conservarse como contrato.

**Datos que la sustentan**

- Lift@5 1.688794.
- Lift@10 1.688794.
- Lift@20 1.337084.

**Fuente**

- `codexway/outputs/tables/gains.csv`
- `codexway/outputs/metrics/t1_metric_intervals.csv`

**Error que debo evitar**

- Inventar un IC para Lift@20.

### 13. ¿4,898 observaciones no es muy poco para ML?

**Respuesta ejecutiva — 20 segundos**

Es poco para modelos complejos, y el experimento lo confirmó. El campeón tiene una dimensión: train 2,191 y 443 positivos por feature. Regularización, splits temporales y bootstrap reducen riesgo; aun así, sólo recomiendo piloto.

**Respuesta técnica — 60–90 segundos**

El problema no es N aislado sino complejidad efectiva. La logística amplia tenía 105 dimensiones one-hot: 20.87 casos y 4.22 positivos por dimensión, una razón frágil. CatBoost tampoco generalizó. La interacción estable reduce varianza y permite estimar un bolsillo. Pero el holdout tiene sólo 363 positivos y los folds muestran dispersión de Lift 0.463; por eso los intervalos, el caveat de holdout procedimental y la validación forward son esenciales.

**Datos que la sustentan**

- Train 2,191, 443 positivos.
- Final 1D; amplio 105D.
- Rolling Lift SD 0.462668.

**Fuente**

- `codexway/outputs/abt/split_manifest.json`
- `codexway/outputs/metrics/rolling_model_comparison.csv`

**Error que debo evitar**

- Usar una regla universal de “10 eventos por variable” como prueba suficiente.

### 14. ¿Por qué calibrar si el caso principal es ranking?

**Respuesta ejecutiva — 20 segundos**

Porque la probabilidad se multiplica por serviceability y alimenta bandas; la escala sí importa. Platt mejoró validation mínimamente, aunque en holdout empeoró Brier 0.00027. Lo presento como calibración provisional.

**Respuesta técnica — 60–90 segundos**

Para AUC y lift, una transformación monotónica no cambia ranking. Para `Q×S`, sí cambia el nivel del Opportunity Score. El calibrador Platt se ajustó sólo en validation: Brier pasó 0.156111→0.156076 y LogLoss 0.490944→0.490803. En holdout, raw tuvo Brier 0.165501 y final 0.165771; la banda alta predijo 25.31% pero observó 35.83%. Esto obliga a recalibración forward y a no llamar perfectas las probabilidades.

**Datos que la sustentan**

- Mejora validation Brier 0.000034.
- Degradación holdout Brier 0.000270.
- High band: 25.31% predicho vs 35.83% observado.

**Fuente**

- `codexway/outputs/metrics/t1_model_metrics.json`
- `codexway/outputs/tables/calibration.csv`

**Error que debo evitar**

- Confundir parámetros del calibrador con calibration intercept/slope.

### 15. ¿Corregiste multiple testing en los pockets?

**Respuesta ejecutiva — 20 segundos**

Sí en la confirmación final: se evaluaron 19 celdas elegibles y ninguna pasó BH-FDR al 10%. El mejor pocket tuvo N=66, tasa 24.24%, lift 1.188 y p=0.164; no se promovió como regla.

**Respuesta técnica — 60–90 segundos**

Los pockets locales pueden mostrar lifts altos por azar, especialmente con N pequeños. La fase histórica descubrió un pocket N=60 con lift smoothed 1.51, pero su p-value/FDR exacto no quedó localizado. La confirmación canónica aplicó BH-FDR: 0 de 19 aprobó. La interacción final no se justifica con aquel p-value; se justifica por el proceso temporal de selección y su holdout, con el caveat de reutilización procedimental.

**Datos que la sustentan**

- 19 tests; 0 BH-FDR pass.
- Mejor confirmatorio N=66, 16 positivos, p=.1643.
- Histórico N=60, lift 1.510; FDR no localizado.

**Fuente**

- `codexway/outputs/tables/cluster_combinations.csv`
- `experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md`

**Error que debo evitar**

- Atribuir significancia al pocket histórico sin estadístico guardado.

## Data Leakage / Temporalidad

### 16. ¿Cuál fue el leakage más peligroso?

**Respuesta ejecutiva — 20 segundos**

Por daño observado, usar inquiries futuras: elevó AUC de 0.548 a 0.826 y Lift@10 de 1.689 a 2.985. Por facilidad de cometerlo, Availability: un join directo multiplicaba el grano 10× y nearest miraba al futuro.

**Respuesta técnica — 60–90 segundos**

El stress S002 agrega información posterior al primer contacto y produce una mejora implausible: AUC 0.8257, AP 0.5519, Lift@10 2.9846. S003 muestra que nearest snapshot tiene 43.54% de future use en el holdout. Sobre todas las inquiries, 7,758/22,576, 34.36%, elegirían futuro y un join por spot genera 226,151 filas. El pipeline final fija T1, usa agregación backward-as-of y verifica cero violations.

**Datos que la sustentan**

- S002 AUC .825725; Lift10 2.984648.
- Join 22,576→226,151, 10.017×.
- Final future violations 0.

**Fuente**

- `codexway/outputs/metrics/leakage_stress_test.json`
- `entregable/01_eda/EDA_FINAL.md`
- `codexway/outputs/metrics/inventory_audit.json`

**Error que debo evitar**

- Dar 34.36% y 43.54% sin sus poblaciones.

### 17. ¿Cómo resolviste Availability point-in-time?

**Respuesta ejecutiva — 20 segundos**

Con un as-of join estrictamente hacia atrás: para cada inquiry sólo el último snapshot con `snapshot_at <= inquiry_at`. La auditoría final reporta cero snapshots futuros.

**Respuesta técnica — 60–90 segundos**

No se une por `spot_id` a secas porque existen múltiples snapshots. Tampoco se usa nearest bidireccional. Se ordenan timestamps y se hace backward-as-of; después se vuelve al grano del lead. La cobertura histórica resultante es 92.38%, con lag mediano 6.61 días, p90 58.66 y p95 83.35. La cobertura no equivale a freshness: estados viejos se convierten en unknown según umbral, no en unavailable.

**Datos que la sustentan**

- Cobertura 92.38%.
- Lag mediano 6.61d; p90 58.66d; p95 83.35d.
- 0 violations finales.

**Fuente**

- `entregable/01_eda/EDA_FINAL.md`
- `codexway/outputs/metrics/inventory_audit.json`

**Error que debo evitar**

- Decir que cobertura alta significa dato fresco.

### 18. ¿Tu PIT es realmente PIT si price y attributes no estaban versionados?

**Respuesta ejecutiva — 20 segundos**

No completamente. Availability y existencia del listing sí respetan tiempo; price, area, attributes y copy son current-state sin historial. El backtest de fallback es condicional y necesita SCD2 más validación forward.

**Respuesta técnica — 60–90 segundos**

El candidate gate exige `created_at <= scoring_at`, y Availability toma el snapshot pasado. Eso elimina dos clases de time travel. Pero un precio o atributo leído hoy podría no ser el que existía en T1. Sin `effective_from/effective_to` no puedo demostrarlo. Por eso no uso esos campos para Lead Quality final y no presento el ranking de fallback histórico como estimación causal. En producción capturaría versiones al evento y reevaluaría desde una fecha limpia.

**Datos que la sustentan**

- Future snapshot violations 0.
- Listing-state mode: campos no versionados asumidos estáticos.
- Outcome downstream de fallback: no localizado.

**Fuente**

- `codexway/outputs/metrics/inventory_audit.json`
- `codexway/evidence/DECISIONS.md`

**Error que debo evitar**

- Afirmar “PIT completo” para Inventory.

### 19. ¿Por qué excluiste market context?

**Respuesta ejecutiva — 20 segundos**

Porque no bastaba con tener 500 filas: faltaba una semántica demostrable de publicación/effective time. Un experimento preliminar sugirió sólo ~0.005 AUC y 23% de cobertura exacta, insuficiente para asumir riesgo temporal.

**Respuesta técnica — 60–90 segundos**

El contexto externo puede haber sido revisado o publicado después del momento de scoring. Sin timestamp de disponibilidad real, un join por periodo puede filtrar futuro aunque la fecha nominal parezca anterior. EV-007 fue exploratorio, no un benchmark final. La política correcta es incorporarlo sólo cuando exista una tabla versionada con `published_at` o `effective_at`, medir cobertura por cohorte y repetir temporal CV.

**Datos que la sustentan**

- Market context 500 filas.
- Mejora preliminar ~0.005 AUC.
- Cobertura exacta ~23%.

**Fuente**

- `codexway/outputs/tables/data_audit.json`
- `experimentos/Evidencias/EV-007_geographic_enrichment.md`

**Error que debo evitar**

- Tratar la mejora preliminar como resultado holdout canónico.

### 20. ¿Cómo evitas que el pipeline cambie al recibir datos tardíos?

**Respuesta ejecutiva — 20 segundos**

Con `as_of` explícito, madurez de siete días, splits congelados, purge temporal y joins que sólo consumen registros disponibles al scoring. En producción añadiría snapshots inmutables y versionado de features.

**Respuesta técnica — 60–90 segundos**

El target sólo se etiqueta cuando su ventana cerró al 1 de julio de 2026; 102 leads quedan censurados, no negativos. Los buffers de purge excluyen 149 casos entre ventanas. Cada feature debe declarar event time y availability time. El repositorio todavía depende de campos de listing current-state, así que la invariancia completa ante backfills no está garantizada. La mitigación productiva es feature store con materialización point-in-time, hashes de fuente y tests de replay.

**Datos que la sustentan**

- `as_of` 2026-07-01 UTC.
- 102 censurados.
- 149 en purge.

**Fuente**

- `codexway/outputs/abt/split_manifest.json`
- `codexway/config/base.yaml`

**Error que debo evitar**

- Reetiquetar censurados como cero.

## ML Engineering / Producción

### 21. ¿Cómo empaquetaste y reproducirías el score?

**Respuesta ejecutiva — 20 segundos**

El bundle guarda transformador, logística y calibrador; el run manifest fija configuración y outputs. Reproduciría desde el commit congelado, validando schema, split, hashes y score distributions antes de servir.

**Respuesta técnica — 60–90 segundos**

`codexway/outputs/models/t1_model_bundle.joblib` contiene el pipeline y Platt; `codexway/config/base.yaml`, `codexway/config/feature_policy.yaml` y `codexway/outputs/run_manifest.json` fijan contratos. La inferencia debe recrear la interacción exactamente y nunca completar categorías con datos futuros. Añadiría firma de modelo, versión de sklearn, test golden-record y canary. Al inspeccionar el bundle apareció un warning por 1.7.2 vs 1.8.0, por lo que en producción se debe usar lockfile/container idéntico.

**Datos que la sustentan**

- Bundle `codexway/outputs/models/t1_model_bundle.joblib`.
- 1 feature, dos niveles de score.
- Warning de versión reconstruido al inspeccionar bundle.

**Fuente**

- `codexway/outputs/models/t1_model_bundle.joblib`
- `codexway/outputs/run_manifest.json`

**Error que debo evitar**

- Cargar artefactos pickle/joblib con librerías incompatibles sin validación.

### 22. ¿Cómo manejas los empates del score?

**Respuesta ejecutiva — 20 segundos**

Con evaluación tie-aware: si una frontera corta un grupo de score idéntico, prorrateo positivos y capacidad. En operación el desempate debe ser explícito, estable y no usar información posterior.

**Respuesta técnica — 60–90 segundos**

La logística final produce 0.187899 o 0.253098. El grupo alto tiene 187 leads, mayor que 10% del holdout. Seleccionar arbitrariamente 172 puede hacer que el lift dependa del orden de filas; por eso el backtest usa la tasa del grupo para una expectativa fraccional. En producción fijaría un tie-breaker pre-T1 —por ejemplo timestamp o asignación aleatoria auditada— y mediría tanto política esperada como realizada.

**Datos que la sustentan**

- Grupo alto holdout N=187, 67 positivos.
- Top10 discreto 172.
- Precision tie-aware 35.8289%.

**Fuente**

- `codexway/evidence/EV-116_TIE_AWARE_LIFT.md`
- `codexway/outputs/tables/gains.csv`

**Error que debo evitar**

- Presentar el orden dentro de empates como información del modelo.

### 23. ¿Qué monitorearías?

**Respuesta ejecutiva — 20 segundos**

Volumen y prevalencia madura, cobertura del pocket, PSI, AUC/AP/Lift una vez maduro, calibración, freshness, unknown, future violations, fallback acceptance y outcomes downstream.

**Respuesta técnica — 60–90 segundos**

Separaría salud de datos, modelo y política. Datos: schema, PK/FK, timestamps, lag y snapshots futuros. Modelo: share de interacción, dos scores, calibration bins, AP y lift por cohorte madura. Inventory: lower/upper, gap, candidatos, freshness y abstención. Política: asignación, SLA, visita, cierre, revenue y efectos por segmento. Alertas deben respetar retraso de siete días; no evaluar performance sobre cohortes inmaduras.

**Datos que la sustentan**

- Feature PSI final 0 en el corte.
- Gap medio 0.127682.
- Fresh lead coverage 98.34% a 30d.

**Fuente**

- `entregable/05_opportunity_produccion/03_MONITOREO_GOBIERNO_RUNBOOK.md`
- `codexway/outputs/tables/feature_drift.csv`

**Error que debo evitar**

- Monitorizar sólo AUC o usar targets aún no maduros.

### 24. ¿Cuándo reentrenarías o retirarías el modelo?

**Respuesta ejecutiva — 20 segundos**

No por calendario ciego: reentrenaría ante drift material, degradación sostenida de lift/calibración o cambio de proceso; lo retiraría si el intervalo online incluye daño o si falla el contrato temporal.

**Respuesta técnica — 60–90 segundos**

La señal está concentrada en una interacción que puede desaparecer si cambian campañas o mix sectorial. Exigiría varias cohortes maduras, comparación contra control y límites predefinidos. Un future-snapshot violation es gate duro. También vigilaría que el grupo alto no se vuelva demasiado pequeño o amplio. Reentrenar incluye repetir ablations y challenger benchmark; no se promueve automáticamente el modelo con mejor point estimate.

**Datos que la sustentan**

- Rolling Lift SD 0.4627.
- Monthly holdout Lift 1.207–2.554.
- Future violations finales 0.

**Fuente**

- `codexway/outputs/metrics/rolling_model_comparison.csv`
- `codexway/outputs/tables/monthly_model_stability.csv`

**Error que debo evitar**

- Fijar un umbral no documentado como si ya estuviera aprobado.

### 25. ¿Qué SLA y fallos contempla el fallback?

**Respuesta ejecutiva — 20 segundos**

El diseño se abstiene de afirmar disponibilidad cuando el dato está stale: lower=0, upper=1. Si no hay alternativa conocida, 2.38% de leads, exige sourcing/verificación; nunca se usa futuro para llenar el vacío.

**Respuesta técnica — 60–90 segundos**

El fallback aplica hard gates antes de ranking y muestra hasta cinco candidatos, mientras la serviceability agrega top tres con un factor de evidencia. Casos unknown conservan un rango amplio y action policy. No hay SLA operativo medido de latencia o uptime en los artefactos: **NO LOCALIZADO**. Antes de producción definiría timeout, fallback determinista, cache, observabilidad y comportamiento degradado cuando Availability no llegue.

**Datos que la sustentan**

- 119/5,000 sin alternativa conocida.
- 0/5,000 sin alternativa potencial.
- Hasta 5 mostradas; top 3 agregadas.

**Fuente**

- `codexway/src/spot2_codexway/inventory.py`
- `codexway/outputs/metrics/inventory_audit.json`

**Error que debo evitar**

- Inventar SLAs de producción no medidos.

## Product

### 26. ¿Por qué agregar Inventory si empeora Lift?

**Respuesta ejecutiva — 20 segundos**

Porque responde otra pregunta: no sólo quién visitará, sino si podemos atender su necesidad. El lower combinado baja Lift@10 de 1.689 a 1.370; por eso mantengo dos ejes visibles y no reemplazo Lead Quality.

**Respuesta técnica — 60–90 segundos**

La caída paired de Lift@10 es −0.3186, IC completamente negativa. Si el único KPI fuera scheduled visit, multiplicar no gana. El producto necesita además evitar un lead de alta intención cuyo spot está unavailable y sugerir alternativas. Como no existe gold de éxito del fallback, esa mejora operacional todavía es hipótesis. La interfaz debe mostrar calidad, lower/upper, gap y razón; el piloto debe medir si reduce intentos fallidos y mejora cierres.

**Datos que la sustentan**

- ΔLift10 −0.318591, IC [−0.625177, −0.012458].
- AP Opportunity lower 0.247703 vs 0.239129.
- Brier empeora +0.004944.

**Fuente**

- `codexway/outputs/metrics/system_score_paired_delta.csv`

**Error que debo evitar**

- Usar el AP mayor aislado para declarar ganador al combinado.

### 27. ¿Cómo decides con 44% de inventario exacto UNKNOWN?

**Respuesta ejecutiva — 20 segundos**

No fuerzo una certeza falsa: lower asume cero, upper asume potencial, el gap mide incertidumbre y la acción es verificar. Además, 98.34% de leads tiene al menos un candidato fresco a 30 días.

**Respuesta técnica — 60–90 segundos**

El 44.30% es al grano lead–spot exacto; no implica que 44% de todos los candidatos sea desconocido ni que el lead sea inatendible. En pares, 42.91% queda stale/unknown a 30 días, pero casi todos los leads conservan alguna opción fresca. La política lower/upper evita dos errores: optimismo sin evidencia y descarte por ausencia de observación. Los gaps altos deben disparar reconsulta o intervención humana.

**Datos que la sustentan**

- Exact unknown 2,215/5,000.
- Fresh candidates 57.09% de pares.
- Leads con ≥1 fresh 98.34%.

**Fuente**

- `codexway/outputs/metrics/inventory_audit.json`
- `codexway/outputs/tables/inventory_freshness_sensitivity.csv`

**Error que debo evitar**

- Restar 44.30% directamente de cobertura de fallback.

### 28. ¿45.64% exact attendable significa que sólo atiendes 45%?

**Respuesta ejecutiva — 20 segundos**

No. Es sólo el spot exacto en el momento T1. La serviceability incorpora alternativas: lower medio 0.6936, y sólo 2.38% no tiene alternativa con estado conocido.

**Respuesta técnica — 60–90 segundos**

De 5,000 leads, 2,282 tienen exacto atendible, 2,215 exacto unknown y 503 conocido no atendible. Para los dos últimos grupos se buscan alternativas compatibles por sector, estado y modalidad. Hay potencial para todos y alternativas conocidas para 97.62%. Eso tampoco significa 97.62% de éxito: serviceability es un score heurístico de oferta, no outcome observado. La conversión del fallback debe medirse online.

**Datos que la sustentan**

- Exact attendable 45.64%.
- Exact known unavailable 10.06%.
- No known alternative 2.38%.

**Fuente**

- `codexway/outputs/metrics/inventory_audit.json`

**Error que debo evitar**

- Llamar “atendidos” a leads sólo porque existe candidato.

### 29. ¿Cómo funciona la experiencia de fallback?

**Respuesta ejecutiva — 20 segundos**

Primero respeta sector, estado, modalidad y existencia temporal; luego ordena por geografía, área, precio y disponibilidad, muestra hasta cinco y se abstiene de afirmar known cuando no hay snapshot fresco.

**Respuesta técnica — 60–90 segundos**

Los hard gates evitan recomendaciones incompatibles. El soft score usa geografía 1/.85/.65 y similitud logarítmica simétrica de área/precio; la disponibilidad aporta lower/upper. Internamente se agregan las tres mejores alternativas con penalización por poca evidencia, pero la UI puede mostrar cinco con razones. En el caso lead 6, el exacto estaba unavailable y se ofrecieron cinco; lower 0.7386, upper 0.8029 y acción source_or_offer_fallback.

**Datos que la sustentan**

- 195,084 candidatos; mediana 33, p90 71.
- Caso lead 6: 48 candidatos, 19 known attendable.
- 4,636 leads muestran cinco IDs.

**Fuente**

- `codexway/src/spot2_codexway/inventory.py`
- `codexway/outputs/predictions/lead_opportunity_scores.csv`

**Error que debo evitar**

- Describir criterios soft como restricciones duras.

### 30. ¿Por qué multiplicar en lugar de entrenar un segundo modelo?

**Respuesta ejecutiva — 20 segundos**

Porque no existe una etiqueta downstream fiable de “lead atendido con éxito”. Multiplicar dos componentes auditables produce límites y una política provisional; un segundo modelo sin gold aprendería un proxy opaco.

**Respuesta técnica — 60–90 segundos**

`Q×S` supone separabilidad operacional y no modela interacción causal entre intención e inventario. Es una limitación, no una verdad. Su ventaja es trazabilidad: Q predice visita, S resume factibilidad lower/upper. Cuando exista historial de recomendaciones, aceptación, visita, cierre y no-contacto, entrenaría un modelo de outcome conjunto o uplift con exposición aleatoria, comparándolo contra la multiplicación y manteniendo constraints de inventory.

**Datos que la sustentan**

- Gold downstream de fallback: NO LOCALIZADO.
- Opportunity lower AUC 0.5119, Lift10 1.3702.
- Producto conserva `0≤lower≤upper≤100`.

**Fuente**

- `entregable/05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md`
- `codexway/src/spot2_codexway/inventory.py`

**Error que debo evitar**

- Interpretar el producto como probabilidad calibrada conjunta.

## IA

### 31. ¿Dónde está realmente la IA?

**Respuesta ejecutiva — 20 segundos**

En la exploración semántica de descripciones y QA, no en el score crítico. El modelo productivo propuesto es logística más reglas deterministas de inventario. El LLM ayudó a descubrir límites y no pasó el gate para automatización.

**Respuesta técnica — 60–90 segundos**

EV-017 ejecutó GPT-5 nano sobre 100 casos estratificados para buscar problemas residuales después de reglas. Encontró señales en estratos diseñados, pero cero hallazgos residuales accionables y cero reglas nuevas promovibles. El sidecar determinista cubrió 3,000 spots. La evaluación canónica actual no tiene gold humano natural; su prueba N=40 es sintética/cacheada. Por eso el LLM se mantiene offline, con salida estructurada y revisión humana.

**Datos que la sustentan**

- GPT-5 nano, N=100.
- 0/100 residual actionable.
- Canonical `n_gold=0`.

**Fuente**

- `experimentos/llm_semantic_feature_pilot/results/PILOT_REPORT.md`
- `codexway/outputs/metrics/llm_audit_evaluation.json`

**Error que debo evitar**

- Decir que el LLM decide prioridades o disponibilidad.

### 32. ¿Qué precisión y recall tuvo el LLM?

**Respuesta ejecutiva — 20 segundos**

Para datos naturales con gold humano: **NO LOCALIZADO EN LOS ARTEFACTOS**. Hay diagnósticos por estrato y una prueba sintética perfecta, pero no son precision/recall generalizables.

**Respuesta técnica — 60–90 segundos**

EV-015 preparó 240 casos y 100 challenge, pero `experimentos/llm_inventory_quality/E015_llm_inventory_semantic_audit/results/evaluation.json` no guarda labels humanos ni predicciones completas. El harness canónico reporta `n_gold=0`; su 100% en N=40 viene de respuestas sintéticas cacheadas y no acredita calidad real. Un resumen suplementario fuera de la autoridad final menciona sensibilidad/especificidad bajas, pero no debe sustituir el contrato final. Antes de promover exigiría doble etiquetado humano, acuerdo, precisión por issue y coste por hallazgo accionable.

**Datos que la sustentan**

- `n_gold=0` canónico.
- Synthetic N=40, cache hit.
- 340 casos preparados sin evaluación natural completa.

**Fuente**

- `codexway/outputs/metrics/llm_audit_evaluation.json`
- `experimentos/llm_inventory_quality/E015_llm_inventory_semantic_audit/results/evaluation.json`

**Error que debo evitar**

- Presentar 100% sintético como accuracy humana.

### 33. ¿El LLM sobre-marcaba problemas?

**Respuesta ejecutiva — 20 segundos**

La evidencia canónica no permite medir una tasa general de over-flagging. Sí muestra que en 100 casos no produjo nuevos hallazgos residuales accionables, por lo que no justificó ser gate.

**Respuesta técnica — 60–90 segundos**

Los estratos fueron intencionalmente enriquecidos: ambiguity dio 96% issues y clean 0%, de modo que no representan prevalencia poblacional. Las reglas deterministas ya cubrían gran parte del patrón; el LLM devolvió señales redundantes o no promovibles. Sin una muestra representativa con gold, “over-flagging” exacto es **NO LOCALIZADO**. La forma correcta de medirlo sería PPV por tipo, false-positive rate en controles y costo de revisión por verdadero positivo.

**Datos que la sustentan**

- 25 casos por estrato.
- Ambiguity 96%, clean 0%, land/rules 8%.
- 0 nuevas reglas promovibles.

**Fuente**

- `experimentos/llm_semantic_feature_pilot/results/pilot_segment_summary_v2.csv`

**Error que debo evitar**

- Extrapolar tasas estratificadas a los 3,000 spots.

### 34. ¿Cuánto costó la evaluación de IA?

**Respuesta ejecutiva — 20 segundos**

El piloto V2 de 100 casos reportó `$0.002579`, con 12,634 tokens de entrada y 4,869 de salida. Es coste de experimento, no TCO de producción.

**Respuesta técnica — 60–90 segundos**

V1 reportó 12,564 input, 6,767 output y `$0.003335`; V2 redujo output 28% y coste a `$0.002579`. Son cifras sorprendentemente bajas y dependen del pricing/configuración del momento; no las extrapolo sin validar tarifa, caching, reintentos, supervisión y volumen. El coste decisivo no fue tokens sino revisión y falta de señal incremental accionable.

**Datos que la sustentan**

- V1 `$0.003335`.
- V2 `$0.002579`.
- Output tokens −28%.

**Fuente**

- `experimentos/llm_semantic_feature_pilot/results/pilot_usage_summary_v2.csv`
- `experimentos/llm_semantic_feature_pilot/results/RUN_HISTORY.md`

**Error que debo evitar**

- Prometer ese coste unitario en producción futura.

### 35. ¿Qué tendría que pasar para promover el LLM?

**Respuesta ejecutiva — 20 segundos**

Demostrar hallazgos incrementales sobre reglas, con gold humano, precisión mínima, coste por hallazgo, estabilidad por sector y acción downstream segura. Hoy no cumple esos requisitos.

**Respuesta técnica — 60–90 segundos**

Congelaría taxonomía y prompt; construiría muestra representativa y challenge; doble etiquetado con adjudicación; mediría precision/recall por issue, cobertura, over-flagging, latencia y costo. Después haría shadow y revisión humana. Sólo una regla recurrente, interpretable y temporalmente válida pasaría al sistema determinista; un LLM como gate requeriría evidencia adicional de beneficio frente a esa baseline.

**Datos que la sustentan**

- Reglas: 322 spots/330 conflictos en EV-015.
- 0/100 hallazgos residuales accionables en EV-017.
- 84.4% de descripciones compartidas.

**Fuente**

- `experimentos/llm_inventory_quality/E015_llm_inventory_semantic_audit/results/rules_summary.json`
- `experimentos/llm_semantic_feature_pilot/results/PILOT_REPORT.md`

**Error que debo evitar**

- Promover por novedad tecnológica sin métrica incremental.

## Crítica metodológica

### 36. ¿El holdout quedó contaminado durante la recuperación?

**Respuesta ejecutiva — 20 segundos**

Sí, dejó de ser virgen: es un holdout temporal procedimental. Conservo sus cifras por ser el contrato final, pero reduzco la fuerza de la afirmación y exijo una cohorte forward nueva.

**Respuesta técnica — 60–90 segundos**

La separación cronológica sigue siendo real: train/validation 2025 y test enero–junio 2026. Sin embargo, el test fue observado al diagnosticar y recuperar la solución, de modo que decisiones posteriores pudieron adaptarse indirectamente. AssessmentSol1 documenta el incidente. Bootstrap no corrige selección adaptativa. La salida correcta es congelar ahora feature, pipeline y policy, y evaluar una cohorte nunca consultada o un piloto aleatorizado.

**Datos que la sustentan**

- Holdout N=1,711, 363 positivos.
- Periodo 2026-01-01–2026-06-23.
- Estado: procedural holdout.

**Fuente**

- `AssessmentSol1/models/lead_quality/PROCEDURAL_HOLDOUT.md`
- `codexway/outputs/abt/split_manifest.json`

**Error que debo evitar**

- Llamarlo validación externa o holdout prístino.

### 37. ¿La interacción final fue descubierta mirando demasiados segmentos?

**Respuesta ejecutiva — 20 segundos**

Existe riesgo de selección adaptativa y lo admito. La interacción pasó temporal CV y holdout procedimental, pero la evidencia definitiva debe venir de una cohorte congelada nueva.

**Respuesta técnica — 60–90 segundos**

La exploración de pockets y modelos aumenta el researcher degrees of freedom. La confirmación BH de 19 celdas no promovió ninguna; la interacción estable siguió otro camino de selección con criterios temporales. Aun así, como el holdout fue observado durante recuperación, no puedo tratar su IC bootstrap como si incorporara todo el proceso de búsqueda. La mitigación es pre-registrar el scorer exacto y evaluar forward sin cambios.

**Datos que la sustentan**

- 19 pockets confirmatorios, 0 FDR pass.
- 4 folds rolling; Lift media 1.2137.
- Holdout procedimental.

**Fuente**

- `codexway/evidence/EV-113_STABLE_SEGMENT.md`
- `AssessmentSol1/evidence/RESEARCH_CONTAMINATION.md`

**Error que debo evitar**

- Decir que el bootstrap corrige búsqueda de modelo.

### 38. ¿Los datos sintéticos limitan la conclusión?

**Respuesta ejecutiva — 20 segundos**

Sí. Permiten demostrar método, contratos y prevención de leakage, pero no garantizan magnitud ni transferibilidad al negocio real. La recomendación es piloto, no rollout.

**Respuesta técnica — 60–90 segundos**

Distribuciones, relaciones y ruido pueden ser artefactos del generador. Un pocket Industrial podría reflejar cómo se construyó la muestra. Por eso privilegio integridad temporal y trazabilidad, y evito causalidad. La siguiente fase debe validar definiciones con stakeholders, comparar prevalencia y mix reales, revisar missingness y ejecutar shadow/experimento en datos productivos. El valor del challenge está más en el sistema de decisión verificable que en un punto estimado.

**Datos que la sustentan**

- N maduro 4,898.
- Modelo final concentrado en un único pocket.
- Rolling con dispersión alta.

**Fuente**

- `entregable/REVISION_CRITICA_EVALUADOR.md`
- `codexway/outputs/MODEL_CARD.md`

**Error que debo evitar**

- Generalizar los porcentajes como SLA del negocio real.

### 39. ¿Por qué no usar el modelo histórico que reportó AUC 0.58?

**Respuesta ejecutiva — 20 segundos**

Porque no comparte target, stage ni población con el campeón. Los benchmarks históricos de modelo 3 son challengers útiles, no evidencia de que superen T1 bajo el contrato final.

**Respuesta técnica — 60–90 segundos**

En architecture OOF, specialist CatBoost obtuvo AUC 0.5820 y AP 0.4720 sobre N=7,980 y prevalencia 41.30%; esa base rate sola muestra que no es el mismo problema que scheduled visit T1 al 21.22%. T2 trajectory también puede usar información posterior. Para desplazar al campeón, habría que reimplementar la familia bajo la ABT, target, split, maturity y leakage gates canónicos y evaluarla en una cohorte nueva.

**Datos que la sustentan**

- Histórico N=7,980, prevalence 41.3002%, AUC .5820.
- Final holdout N=1,711, prevalence 21.2157%, AUC .5478.
- Comparabilidad: no.

**Fuente**

- `experimentos/modelo_3/architecture_cv/results/oof_model_ranking.csv`
- `codexway/outputs/metrics/t1_model_metrics.json`

**Error que debo evitar**

- Ordenar todos los AUC en un único leaderboard.

### 40. ¿Qué harías diferente con más datos?

**Respuesta ejecutiva — 20 segundos**

Congelaría una cohorte nueva, versionaría listings, capturaría cierre/revenue y éxito de fallback, y evaluaría modelos conjuntos o uplift. Mantendría el scorer simple como baseline fuerte.

**Respuesta técnica — 60–90 segundos**

Primero mejoraría observabilidad: event time/availability time, SCD2 de precio/atributos, exposición a recomendaciones, acciones del agente y outcomes tardíos. Después separaría tres modelos: propensión de visita, probabilidad de serviceability observada y efecto de intervención. Compararía logística, CatBoost y survival/uplift con nested temporal validation y calibración por cohorte. A nivel producto, probaría la política de dos ejes y fallback con randomización, heterogeneidad y guardrails de fairness/carga.

**Datos que la sustentan**

- 44.30% exact unknown.
- Listing fields no versionados.
- CatBoost histórico T2 mostró señales incrementales, pero no comparables.

**Fuente**

- `codexway/outputs/metrics/inventory_audit.json`
- `experimentos/Evidencias/EV-012_modelo_3_trajectory_cv.md`

**Error que debo evitar**

- Empezar por un modelo más complejo antes de reparar el contrato de datos.
