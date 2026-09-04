# DEFENSE NUMBERS MASTER — Tech Challenge Spot2

Este compendio sirve para defensa oral. No cambia el modelo, la política ni los artefactos de la entrega. Jerarquía aplicada: `entregable/**` para narrativa; `codexway/**` para cifras finales y método; `experimentos/**` para challengers; `AssessmentSol1/**` sólo como auditoría clean-room complementaria.

**Snapshot analizado:** commit `7d4e90df6d7e7340f3963128089bd303e8993e52`, datos con `as_of = 2026-07-01 00:00:00 UTC`.

# ⚠️ INCONSISTENCIAS QUE DEBO CONOCER ANTES DE PRESENTAR

| Cifra A | Cifra B | Origen | Explicación | Cuál usar oralmente |
|---|---|---|---|---|
| 1 feature | 26 en allowlist; 25 raw en benchmark | `codexway/outputs/tables/feature_importance.csv`; `codexway/config/feature_policy.yaml`; `codexway/src/spot2_codexway/modeling.py` | El campeón estable sólo usa la interacción promovida. La allowlist mezcla 25 inputs amplios más esa interacción. | **1 feature final**; mencionar 25/105 sólo al hablar del challenger amplio. |
| 34.36% future | 43.5418% future | `entregable/01_eda/EDA_FINAL.md`; `codexway/outputs/metrics/leakage_stress_test.json` | 34.36% = 7,758 de 22,576 inquiries bajo nearest; 43.54% = S003 sobre holdout T1. | “34.36% en todas las inquiries; 43.54% en el stress de holdout; final 0.” |
| Brier raw 0.165501 | calibrado 0.165771 | `codexway/outputs/metrics/t1_model_metrics.json` | Platt mejoró validation mínimamente, pero empeoró holdout en 0.000270. AUC, AP y lift no cambian. | Reportar **0.165771** como final y admitir el matiz. |
| Mediana 29 | Mediana 33 | `entregable/01_eda/tablas/01_metricas_eda_clave.csv`; reconstrucción de `codexway/outputs/predictions/lead_opportunity_scores.csv` | 29 corresponde al corte/desarrollo del EDA; 33 al output final de los 5,000 leads. | **33 en output final**; 29 sólo como historia de desarrollo. |
| UNKNOWN 44.30% | UNKNOWN/stale 42.91% | `codexway/outputs/metrics/inventory_audit.json`; `codexway/outputs/tables/inventory_freshness_sensitivity.csv` | El primero usa leads y el spot exacto; el segundo usa 195,084 pares lead–candidato a freshness 30d. | Dar ambos con denominador explícito. |
| “holdout” | “procedural holdout” | `codexway/outputs/abt/split_manifest.json`; `AssessmentSol1/models/lead_quality/PROCEDURAL_HOLDOUT.md` | Es temporal y posterior a train/validation, pero fue consultado durante recuperación. | “Holdout temporal procedimental”, no “prístino”. |
| GPT-5 nano real | gpt-5.6-luna cached/synthetic | `experimentos/Evidencias/EV-017_llm_semantic_feature_pilot.md`; `codexway/outputs/metrics/llm_audit_evaluation.json` | El piloto real de 100 casos usó nano; la validación canonical actual tiene 0 gold natural y prueba sintética cacheada. | La evidencia real es **GPT-5 nano, N=100**; no afirmar accuracy natural. |
| “deployment GO” | no producción automática | `codexway/outputs/metrics/deployment_readiness.json`; `codexway/outputs/tables/online_ab_protocol.json` | El gate habilita forward validation y piloto aleatorizado guardado. | “Elegible para piloto”, no “listo para auto-routing”. |

## 1. Dataset, grano y target

### 1.1 Inventario de fuentes

| Tabla | Filas | Columnas | Grano / rol | Fuente |
|---|---:|---:|---|---|
| leads | 5,000 | 20 | Un lead | `codexway/outputs/tables/data_audit.json` → `tables.leads` |
| inquiries | 22,576 | 13 | Una consulta | mismo → `tables.inquiries` |
| spots | 3,000 | 25 | Un listing | mismo → `tables.spots` |
| spot_attributes | 3,000 | 12 | Un set de atributos por spot | mismo → `tables.spot_attributes` |
| availability_snapshot | 30,000 | 6 | Un estado por spot y fecha | mismo → `tables.availability_snapshot` |
| market_context | 500 | 10 | Contexto externo | mismo → `tables.market_context` |
| **Total raw** | **64,076** | — | Suma reproducida; no son unidades independientes | suma exacta de los seis `rows` anteriores |

Controles: PKs únicas, 0 FKs huérfanas, 0 inquiries anteriores a creación del lead y 0 spots creados después de la inquiry. Fuente: `codexway/outputs/tables/data_audit.json`.

### 1.2 Definición final

- **Momento T1:** instante de la primera inquiry del lead.
- **Target:** `scheduled_visit_7d = 1` si existe una visita agendada dentro de los siete días posteriores a T1; si el horizonte no ha cerrado al `as_of`, queda censurado.
- **Población:** 5,000 T1; 4,898 maduros, 102 censurados.
- **Clases:** 1,001 positivos + 3,897 negativos = 4,898.
- **Prevalencia:** `1,001 / 4,898 = 0.2043691303 = 20.4369%`.
- **Limitación:** scheduled visit es proxy de avance comercial, no cierre, revenue, margen ni valor incremental causal.

Fuentes: `codexway/outputs/tables/data_audit.json` → `t1_contract`; `codexway/config/base.yaml`; `codexway/src/spot2_codexway/targets.py`. Los negativos son `rows_mature − positives`, reconstrucción exacta.

### 1.3 Sensibilidad de madurez

| Ventana | Elegibles | Censurados | Positivos | Negativos | Prevalencia |
|---:|---:|---:|---:|---:|---:|
| 7d | 4,898 | 102 | 1,001 | 3,897 | 20.4369% |
| 14d | 4,836 | 164 | 988 | 3,848 | 20.4301% |
| 30d | 4,680 | 320 | 955 | 3,725 | 20.4060% |

La tasa cambia sólo `0.0309` puntos porcentuales entre 7d y 30d. Esto contradice la hipótesis de que 7d fue elegido para fabricar una tasa; la elección gana recencia y tamaño elegible. Fuente: `codexway/outputs/tables/target_maturity_sensitivity.csv`.

## 2. Splits temporales

| Split | N | Positivos | Negativos | Prevalencia | Periodo UTC |
|---|---:|---:|---:|---:|---|
| Train | 2,191 | 443 | 1,748 | 20.2191% | 2025-01-01 10:21:59 a 2025-09-23 16:35:41 |
| Validation | 847 | 165 | 682 | 19.4805% | 2025-10-01 07:07:23 a 2025-12-23 16:47:07 |
| Test / holdout temporal | 1,711 | 363 | 1,348 | 21.2157% | 2026-01-01 07:12:40 a 2026-06-23 17:58:56 |
| Purge | 149 | 30 | 119 | 20.1342% | 2025-09-24 a 2025-12-31, en buffers |
| Censurado | 102 | NA | NA | NA | Horizonte 7d no cerrado |

Comprobaciones: train + validation + test = `4,749`, positivos `971`; más purge = `4,898`, positivos `1,001`. Los 102 censurados no son negativos. Fuente: `codexway/outputs/abt/split_manifest.json`.

### 2.1 Rolling temporal CV

Los folds se reconstruyeron de manera reproducible ejecutando `rolling_folds` sobre `codexway/outputs/abt/abt_t1_first_inquiry.parquet`; las métricas guardadas están en `codexway/outputs/metrics/rolling_model_comparison.csv`.

| Fold | Train N / pos | Train termina | Val N / pos | Validation |
|---:|---:|---|---:|---|
| 1 | 876 / 174 | 2025-05-07 | 258 / 47 | 2025-05-14–2025-06-11 |
| 2 | 1,204 / 235 | 2025-06-11 | 249 / 51 | 2025-06-18–2025-07-15 |
| 3 | 1,533 / 307 | 2025-07-15 | 255 / 40 | 2025-07-22–2025-08-19 |
| 4 | 1,861 / 365 | 2025-08-18 | 272 / 64 | 2025-08-26–2025-09-23 |

| Modelo rolling | AUC media | AP media | Brier medio | LogLoss medio | Lift@10 media | Mediana | SD | Folds Lift>1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Stable logistic | 0.512695 | 0.203179 | 0.157108 | 0.493746 | 1.213713 | 1.159051 | 0.462668 | 2/4 |
| Logistic amplia | 0.498592 | 0.217593 | 0.166723 | 0.524916 | 0.846428 | 0.700550 | 0.523885 | 1/4 |
| CatBoost | 0.522795 | 0.244760 | 0.180488 | 0.547954 | 1.186308 | 1.214779 | 0.286332 | 3/4 |

CatBoost ganó AP a la logística amplia en sólo 2/4 folds, por debajo del gate de 3/4, y empeoró Brier medio en `0.013765`, más que el máximo tolerado `0.005`. La señal estable tampoco es uniforme: sus Lift@10 por fold fueron `0.7842`, `1.4431`, `1.7526`, `0.8750`. Debe defenderse como señal candidata con incertidumbre, no como desempeño homogéneo.

## 3. Ficha del modelo final — Lead Quality

| Campo | Valor | Fuente |
|---|---|---|
| Modelo | `stable_segment_logistic` | `codexway/outputs/MODEL_CARD.md` |
| Algoritmo | `sklearn.linear_model.LogisticRegression` | `codexway/src/spot2_codexway/modeling.py` |
| Hiperparámetros | `C=1.0`, `max_iter=2000`, `random_state=42`; regularización L2 default | `codexway/config/base.yaml`; código |
| Calibración | Platt logistic fit en validation | `codexway/src/spot2_codexway/modeling.py`; `codexway/outputs/models/t1_model_bundle.joblib` |
| Momento | T1, primera inquiry | `codexway/config/base.yaml` |
| Target | scheduled visit a 7d | `codexway/config/base.yaml`; `codexway/src/spot2_codexway/targets.py` |
| Train/validation/test | 2,191 / 847 / 1,711 | `codexway/outputs/abt/split_manifest.json` |
| Variables finales | 1 raw y 1 dimensión encoded | `codexway/outputs/tables/feature_importance.csv`; `codexway/outputs/models/t1_model_bundle.joblib` |
| Score raw | 0.187899 o 0.253098 tras calibrar | reconstruido desde `codexway/outputs/models/t1_model_bundle.joblib`; validado en `codexway/outputs/predictions/t1_holdout_predictions.parquet` |

### 3.1 Raw, transformada y final

| Feature | Tipo | Transformación | Disponible en T1 | Coeficiente | Dirección | Comentario |
|---|---|---|---|---:|---|---|
| `search_sector` | raw categórica | condición `== Industrial` | Sí | no aplica por separado | — | No entra sola al campeón. |
| `company_size` | raw categórica | condición `== small` | Sí | no aplica por separado | — | Observable antes del outcome. |
| `source` | raw categórica | condición `== paid` | Sí | no aplica por separado | — | Fuente de adquisición, no outcome. |
| `industrial_small_or_paid_interaction` | final binaria | `Industrial AND (small OR paid)`; StandardScaler | Sí | **+0.120427** estandarizado | Positiva | Una asociación de bolsillo; no causal. |

No existen diez importancias finales: existe una. Inventar un top 10 sería mezclar el benchmark amplio con el campeón. La distribución madura fue: interacción 0, `4,384` leads/`846` positivos/`19.2974%`; interacción 1, `514`/`155`/`30.1556%`. En holdout: 187/1,711 en el grupo alto, 67/187 positivos (`35.8289%`). Fuente de coeficiente: `codexway/outputs/tables/feature_importance.csv`; distribuciones reconstruidas de `codexway/outputs/abt/abt_t1_first_inquiry.parquet`.

**Interpretación correcta:** el coeficiente estandarizado equivale a OR `exp(0.120427)=1.128` por una desviación estándar. La diferencia entre los dos scores calibrados es `6.5199` pp y el odds ratio entre scores es `1.465`. Ninguna de esas cifras prueba que ser Industrial, small o paid cause visitas.

### 3.2 Dimensionalidad y `asked_visit`

- Benchmark amplio: 25 variables raw y 105 columnas después del one-hot; la allowlist de política tiene 26 al incluir la interacción estable.
- Razones en train del benchmark: `2,191/25=87.64` casos y `443/25=17.72` positivos por raw; después de encoding, `20.87` casos y `4.22` positivos por dimensión.
- Campeón: `2,191` casos y `443` positivos por única dimensión.
- Con `asked_visit`: AUC `0.488051`, AP `0.215650`, Brier `0.174441`, Lift@10 `0.849526`.
- Sin `asked_visit`: AUC `0.485178`, AP `0.215159`, Brier `0.174283`, Lift@10 `0.986546`.
- Diferencia sin menos con: AUC `-0.002873`, AP `-0.000491`, Brier `-0.000158` —mejora—, Lift@10 `+0.137020`.

Conclusión: `asked_visit` no domina y no aparece en el campeón. Es observable en T1, pero puede codificar intención del agente/cliente y debe tratarse con cautela causal. Fuentes: `codexway/outputs/metrics/t1_model_metrics.json`; `codexway/config/feature_policy.yaml`.

## 4. Comparación canónica de modelos

Todos los renglones siguientes usan el mismo holdout T1 de 1,711, salvo donde se marque otra población.

| Modelo | AUC | AP | Brier | LogLoss | Lift@5 | Lift@10 | Lift@20 | Resultado |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Base rate | 0.500000 | 0.212157 | 0.167246 | 0.517104 | 1.000000 | 1.000000 | 1.000000 | Baseline |
| Business rule | 0.515687 | 0.216487 | 0.250076 | 0.898215 | 0.946789 | 0.986262 | 1.035952 | Pierde calibración/ranking |
| Logistic lead-only | 0.482327 | 0.209836 | 0.173312 | 0.538006 | — | 0.931738 | — | Rechazada |
| Logistic amplia | 0.488051 | 0.215650 | 0.174441 | 0.541507 | 1.096163 | 0.849526 | 0.920713 | Rechazada |
| Logistic sin `asked_visit` | 0.485178 | 0.215159 | 0.174283 | 0.541190 | 0.986546 | 0.986546 | 0.920713 | Sensibilidad |
| CatBoost | 0.492213 | 0.208591 | 0.242269 | 0.677682 | 0.651867 | 0.826371 | 0.931215 | Rechazado |
| Stable logistic raw | 0.547776 | 0.239129 | **0.165501** | **0.512146** | 1.688794 | 1.688794 | 1.337084 | Ganador pre-calibración |
| **Stable logistic + Platt** | **0.547776** | **0.239129** | 0.165771 | 0.512874 | **1.688794** | **1.688794** | **1.337084** | **Final** |

Fuente: `codexway/outputs/metrics/t1_model_metrics.json`. El CatBoost canónico usa 500 iteraciones, depth 6, learning rate 0.04, L2 leaf reg 5, early stopping 50, métrica PR-AUC, seed 42 y un thread; fuente: `codexway/config/base.yaml` y `codexway/src/spot2_codexway/modeling.py`.

### ¿Por qué ganó logística?

Contra CatBoost, el campeón ganó `+0.055563` AUC, `+0.030538` AP y `+0.862422` Lift@10; redujo Brier `0.076499` y LogLoss `0.164808`. CatBoost sí fue `+0.004162` mejor que la logística amplia en AUC, pero perdió `0.007059` AP, `0.067829` Brier, `0.136175` LogLoss y `0.023155` Lift@10. En rolling, CatBoost tuvo mejor AUC/AP medios que la logística amplia, pero falló los gates de consistencia AP y degradación Brier. La decisión no fue “logística siempre es mejor”; fue “esta señal simple generalizó mejor bajo este contrato”.

## 5. Métricas finales

### 5.1 Globales

| Métrica | Valor holdout | IC95% bootstrap | Baseline / nota |
|---|---:|---:|---|
| ROC-AUC | 0.547776 | [0.527297, 0.568425] | Random 0.5 |
| PR-AUC / AP | 0.239129 | [0.214479, 0.265538] | Prevalencia 0.212157 |
| Brier | 0.165771 | [0.154543, 0.177226] | Base rate 0.167246 |
| LogLoss | 0.512874 | [0.486925, 0.539434] | Base rate 0.517104 |
| Accuracy a threshold 0.253098 | 0.756867 | NO LOCALIZADO | Reconstruido; threshold exacto de validation |
| Precision | 0.358289 | NO LOCALIZADO | 67 TP de 187 score alto |
| Recall | 0.184573 | NO LOCALIZADO | 67/363, clasificación por score alto completo |
| F1 | 0.243636 | NO LOCALIZADO | Reconstruido |
| Calibration intercept / slope | **NO LOCALIZADO EN LOS ARTEFACTOS** | — | No confundir con parámetros del Platt |
| ECE | **NO LOCALIZADO EN LOS ARTEFACTOS** | — | — |
| Lift@1 | **NO LOCALIZADO EN LOS ARTEFACTOS** | — | El artefacto comienza en 5% |

Confusion matrix reconstruida al threshold de validation: TN 1,228; FP 120; FN 296; TP 67. Fuente canónica de las primeras cuatro: `codexway/outputs/metrics/t1_model_metrics.json`, intervalos `codexway/outputs/metrics/t1_metric_intervals.csv`; reconstrucción desde `codexway/outputs/predictions/t1_holdout_predictions.parquet`.

### 5.2 Ranking operativo, tie-aware

| Capacidad | Leads discretos | Precision | Recall/capture | IC95% Recall | Positivos esperados | Lift | IC95% Lift |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5% | 86 | 0.358289 | 0.084884 | NO LOCALIZADO | 30.81 | 1.688794 | [1.380730, 1.982620] |
| 10% | 172 | 0.358289 | 0.169768 | [0.138799, 0.199210] | 61.63 | 1.688794 | [1.380730, 1.981679] |
| 20% | 343 | 0.283671 | 0.268042 | [0.239114, 0.297570] | 97.30 | 1.337084 | NO LOCALIZADO |

`Lift@K = Precision@K / prevalence`, equivalente a `Recall@K / share_seleccionado_real`. Como `ceil(K×N)` y el prorrateo de empates cambian el share real ligeramente, no se debe calcular como `Recall/0.10` redondeado. Fuentes: `codexway/outputs/tables/gains.csv`; `codexway/outputs/metrics/t1_metric_intervals.csv`; conteos reconstruidos.

**AUC y Lift no se contradicen.** AUC promedia el orden de todos los pares positivo–negativo. Este modelo produce sólo dos niveles de score y muchos empates, por lo que gran parte del universo no queda ordenada. Lift@10 pregunta algo más local: qué tasa tiene el bolsillo superior. Un bolsillo de 187 leads con 35.83% de visitas puede producir Lift@10 1.69 aunque el resto esté casi sin ranking.

## 6. T0, T1 y T2

| Stage / target | N test | Prevalencia | AUC | AP | Brier | LogLoss | Lift@10 | Comparabilidad |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| T0 logistic, any scheduled inquiry 30d | 1,371 | 53.8293% | 0.466506 | 0.522793 | 0.296258 | 0.794946 | 1.023090 | Target y exposición distintos |
| **T1 final, scheduled visit 7d** | **1,711** | **21.2157%** | **0.547776** | **0.239129** | **0.165771** | **0.512874** | **1.688794** | Campeón |
| T2 trajectory | 5,249 | 19.9276% | 0.505721 | 0.206862 | 0.160493 | 0.502534 | 1.137451 | Filas trayectoria; 0 overlap entidad train/test |

Fuente: `codexway/outputs/metrics/t0_t2_sensitivity_metrics.json`. No hacer leaderboard entre stages: cambian instante, población y target/exposición. T1 ganó como punto operativo porque agrega intención de primera inquiry sin usar información posterior a ella.

Targets alternativos, sólo sensibilidad: `accepted_or_scheduled` en el holdout T1, N 1,711, prevalencia 65.6341%, AUC 0.500351, AP 0.657115, Lift@10 0.938961; `any_scheduled_inquiry_30d`, N 1,493, prevalencia 51.7080%, AUC 0.552534, AP 0.562277, Lift@10 1.121684. Fuente: `codexway/outputs/metrics/target_sensitivity_metrics.csv`.

## 7. Leakage y contrato temporal

| Riesgo | Evidencia | Solución final | Severidad / defensa |
|---|---|---|---|
| Join Availability por `spot_id` | 22,576 inquiries → 226,151 filas = 10.017× | Agregación backward-as-of al grano inquiry/lead | Crítico: duplica outcomes y mezcla tiempos. |
| Nearest snapshot | 7,758/22,576 = 34.36% usarían futuro | `snapshot_at <= inquiry_at`; 0 violations | Crítico: time travel silencioso. |
| Inquiry futura | S002 AUC 0.825725, AP 0.551904, Lift@10 2.984648 | Cortar en primera inquiry | Es el leakage con mayor inflación observada. |
| Nearest en stress holdout | S003 future rate 43.5418%; AUC 0.510237 | Nunca nearest sin dirección | Denominador distinto del 34.36%. |
| `asked_visit` | Disponible en T1, pero sensible a comportamiento del agente | Ablation y exclusión del campeón | No es leakage literal si nace en T1; sí riesgo de policy feedback. |
| Market context | Publicación/effective-time no demostrados | Sólo EDA | Evita pseudo-PIT. |
| Prices/attributes/listing copy | No versionados históricamente | Inventario etiquetado como condicional | La Availability sí es PIT; el fallback histórico completo no está probado PIT. |

La respuesta rigurosa sobre listings históricos: `created_at` evita candidatos que aún no existían y Availability usa backward-as-of. Sin embargo, precio, área, atributos y copy son estado actual sin `effective_from/effective_to`; podrían haber cambiado. Por tanto, el backtest de fallback es **condicional a campos estáticos**, no un PIT completo. En producción se requieren SCD2/event sourcing y forward shadow validation.

Fuentes: `entregable/01_eda/EDA_FINAL.md`; `codexway/outputs/metrics/leakage_stress_test.json`; `codexway/outputs/metrics/inventory_audit.json`; `codexway/evidence/DECISIONS.md`.

## 8. Inventory

### 8.1 Estado exacto y serviceability

| Métrica | Valor | Numerador/denominador | Fuente |
|---|---:|---:|---|
| Exact attendable | 45.64% | 2,282/5,000 leads | `codexway/outputs/metrics/inventory_audit.json` |
| Exact unknown | 44.30% | 2,215/5,000 | mismo |
| Exact conocido no atendible | 10.06% | 503/5,000, reconstruido | `1 − 0.4564 − 0.4430` |
| Sin alternativa conocida | 2.38% | 119/5,000 | `codexway/outputs/metrics/inventory_audit.json` |
| Sin alternativa potencial | 0.00% | 0/5,000 | mismo |
| Serviceability lower media | 0.693569 | 5,000 leads | mismo |
| Serviceability upper media | 0.821251 | 5,000 | mismo |
| Gap medio | 0.127682 | 5,000 | mismo |
| Confidence media | 0.521694 | 5,000 | mismo |

Distribución final reconstruida desde `codexway/outputs/predictions/lead_opportunity_scores.csv`: lower mediana 0.754254, p90 0.934889, max 0.998768; upper mediana 0.875624, p90 0.966199, max 0.999332; gap mediana 0.057318, p90 0.369695, p95 0.533399, max 0.978201; confidence mediana 0.555556, p90 0.729223, p95 0.758621, max 0.95.

### 8.2 Profundidad y evolución

En 5,000 leads se generaron 195,084 pares elegibles: media 39.0168 candidatos, p10 14, p25 21, mediana 33, p75 52, p90 71, p95 86, máximo 152 y mínimo 3. La mediana mensual sube de 16 en enero/febrero de 2025 a 40 en diciembre de 2025, 44 en enero de 2026 y 56 en junio de 2026; julio 2026 tiene mediana 61.5 pero sólo 30 censurados, por lo que no es comparable. Fuente reconstruida: `codexway/outputs/predictions/lead_opportunity_scores.csv`.

### 8.3 Freshness

| Umbral | Pares frescos | Pares unknown/stale | Leads con ≥1 fresco |
|---:|---:|---:|---:|
| 7d | 19.1635% | 80.8365% | 93.46% |
| 30d | 57.0898% | 42.9102% | 98.34% |
| 90d | 86.0291% | 13.9709% | 98.52% |

Población: 195,084 pares lead–candidato. Fuente: `codexway/outputs/tables/inventory_freshness_sensitivity.csv`.

**Por qué UNKNOWN ≠ UNAVAILABLE:** a 30d, 42.91% de pares no tiene estado suficientemente fresco, pero 98.34% de leads conserva al menos una opción fresca y 100% conserva alguna opción potencial. Colapsar unknown a 0 confundiría ausencia de observación con evidencia de no disponibilidad y cerraría artificialmente el upper bound.

## 9. Fallback

### 9.1 Reglas

- **Hard gates:** `candidate.created_at <= scoring_at`; mismo `search_sector` y `desired_state`; modalidad compatible; ningún snapshot futuro.
- **Soft fit:** geografía `1.00` mismo corredor, `0.85` municipio, `0.65` estado; área y precio usan `exp(-abs(log(candidate/desired)))`; Availability aporta lower/upper; el fit es media geométrica.
- **Unknown/stale:** disponibilidad lower 0, upper 1.
- **Known available:** lower=upper=1. Unavailable con `days_until_available <= urgency_days` recibe `max(0, 1-days/urgency)`; si no, 0.
- **Agregación interna:** top 3 alternativas y factor de evidencia `1-exp(-n_known_alts/3)`; `serviceability = max(exact, fallback)`.
- **Presentación:** hasta 5 alternativas.

Fuente: `codexway/src/spot2_codexway/inventory.py`.

### 9.2 Cobertura y abstención

Todos los 5,000 leads reciben una lista potencial: 2 IDs en 5 casos, 3 en 178, 4 en 181 y 5 en 4,636. Esto no significa que todos necesiten fallback. El exacto no es atendible y existe alternativa conocida en 2,607 leads (`52.14%`); con alternativa potencial, 2,718 (`54.36%`). Hay 119 leads (`2.38%`) sin alternativa conocida: banda `low_serviceability` y verificación/abstención. No hay casos sin alternativa potencial en la muestra.

Bandas: serviceable 1,982; uncertain 1,970; potential fallback 929; low 119. Fuente y reconstrucción: `codexway/outputs/metrics/inventory_audit.json`; `codexway/outputs/predictions/lead_opportunity_scores.csv`.

Los cortes de serviceability son explícitos: `Uncertain` si confidence < 0.50 o gap > 0.20; en caso contrario, `Serviceable` si lower ≥ 0.75; `Potential fallback` si upper ≥ 0.50; si no, `Low serviceability`. Las bandas Opportunity se fijan con cuantiles de validation: q30 `0.131803`, q70 `0.168166`, q90 `0.178977`, que producen en la población completa 1,949 Low, 1,747 Medium, 807 High y 497 Priority. Quality usa q70 `0.187899` y q90 `0.253098`; por empates quedan 4,473 Standard y 527 High, sin Priority. Fuente: `codexway/src/spot2_codexway/inventory.py`; cortes reconstruidos desde `codexway/outputs/predictions/lead_opportunity_scores.csv`.

### 9.3 Caso reproducible

`lead_id=6`, `inquiry_id=15`, scoring `2025-10-06`: Lead Quality `0.253098` (High); exacto known unavailable; 48 candidatos, 19 alternativas atendibles y 42 potenciales; lower `0.738602`, upper `0.802915`, gap `0.064313`, confidence `0.520833`; cinco fallbacks `[756,2687,439,1605,1999]`; Opportunity `18.6939–20.3216`; acción `source_or_offer_fallback`. Fuente: fila del lead en `codexway/outputs/predictions/lead_opportunity_scores.csv`.

### 9.4 Sensibilidad histórica de K — no mezclar con el output final

E020 evaluó 598 casos de fallback bajo otro contrato. En fold 4, K=1/3/5 logró al menos lista completa de `75.92%/62.37%/55.69%`; el no-result fue `24.08%` para los tres. Con K=3, `70.90%` tuvo al menos una alternativa actualmente disponible; mediana de candidatos válidos 6. Esto respalda top 3 para agregación, pero **no** contradice el 0% sin alternativa potencial del output final porque las poblaciones y reglas difieren. Fuente: `experimentos/E020_lead_opportunity_fallback_e2e/results/fallback_k_selection.csv`; `experimentos/E020_lead_opportunity_fallback_e2e/results/fallback_fold4_summary.csv`.

## 10. Opportunity Score

### 10.1 Fórmula y política

\[
Q_i = P(Y_i=1\mid X_{i,T1}),\qquad
O_i^L = 100\,Q_i S_i^L,\qquad
O_i^U = 100\,Q_i S_i^U
\]

Con `0≤S^L≤S^U≤1`, entonces `0≤O^L≤O^U≤100`. El score publicado es `O^L`; el upper y el gap expresan incertidumbre de inventario. No es probabilidad calibrada de cierre ni uplift. Fuente: `codexway/src/spot2_codexway/inventory.py`; `entregable/05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md`.

Política: calidad alta + serviceable → trabajar si pasa gate; calidad alta + uncertain → verificar; calidad alta + low → buscar/ofrecer fallback; calidad standard → workflow estándar. Los límites funcionan como banda de decisión, no como una etiqueta binaria falsa.

### 10.2 Lead Quality vs Inventory vs Opportunity

| Score, holdout N=1,711 | AUC | AP | Brier | LogLoss | Lift@5 | Lift@10 | Recall@10 | Lift@20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Lead Quality | 0.547776 | 0.239129 | 0.165771 | 0.512874 | 1.688794 | 1.688794 | 0.169768 | 1.337084 |
| Inventory lower | 0.472903 | 0.206752 | 0.537677 | 1.576530 | 1.150971 | 0.876930 | 0.088154 | 0.934455 |
| Inventory upper | 0.480117 | 0.211222 | 0.582617 | 1.820740 | 1.260587 | 1.123567 | 0.112948 | 0.948197 |
| Opportunity lower | 0.511881 | 0.247703 | 0.170715 | 0.531798 | 1.589436 | 1.370203 | 0.137741 | 1.085616 |
| Opportunity upper | 0.523496 | 0.261279 | 0.169455 | 0.526644 | 1.808668 | 1.507223 | 0.151515 | 1.223036 |

Fuente: `codexway/outputs/metrics/system_score_metrics.csv`.

| Score | K | Leads | Precision | Recall | Positivos capturados | Lift | IC95% Lift |
|---|---:|---:|---:|---:|---:|---:|---:|
| Lead Quality | 5% | 86 | 0.358289 | 0.084884 | 30.81 | 1.688794 | [1.380730,1.982619] |
| Opportunity lower | 5% | 86 | 0.337209 | 0.079890 | 29.00 | 1.589436 | [1.117560,2.079578] |
| Opportunity upper | 5% | 86 | 0.383721 | 0.090909 | 33.00 | 1.808668 | [1.281732,2.250100] |
| Lead Quality | 10% | 172 | 0.358289 | 0.169768 | 61.63 | 1.688794 | [1.380730,1.981679] |
| Opportunity lower | 10% | 172 | 0.290698 | 0.137741 | 50.00 | 1.370203 | [1.077626,1.689829] |
| Opportunity upper | 10% | 172 | 0.319767 | 0.151515 | 55.00 | 1.507223 | [1.157331,1.774394] |
| Lead Quality | 20% | 343 | 0.283671 | 0.268042 | 97.30 | 1.337084 | NO LOCALIZADO |
| Opportunity lower | 20% | 343 | 0.230321 | 0.217631 | 79.00 | 1.085616 | NO LOCALIZADO |
| Opportunity upper | 20% | 343 | 0.259475 | 0.245179 | 89.00 | 1.223036 | NO LOCALIZADO |

Los positivos de Lead Quality son expectativas fraccionales por empates; Opportunity lower/upper producen conteos enteros en estas fronteras. Fuentes: `codexway/outputs/metrics/system_score_metrics.csv`; `codexway/outputs/metrics/system_score_intervals.csv`.

Opportunity lower Lift@10 IC95% `[1.077626,1.689829]`; upper `[1.157331,1.774394]`. Paired lower vs Lead Quality: ΔAUC `-0.035895` IC `[-0.069591,-0.001053]`; ΔAP `+0.008575` `[-0.016075,0.039635]`; ΔBrier `+0.004944` `[0.002784,0.006928]`; ΔLift@10 `-0.318591` `[-0.625177,-0.012458]`; ΔRecall@10 `-0.032027` `[-0.062847,-0.001252]`. Fuentes: `codexway/outputs/metrics/system_score_intervals.csv`; `codexway/outputs/metrics/system_score_paired_delta.csv`.

**Defensa:** Opportunity lower es peor para predecir scheduled visit; no se oculta. La caída relativa de Lift@10 es `18.87%`. Se mantiene Inventory porque el objetivo operacional es no enviar esfuerzo hacia inventario no servible y ofrecer fallback. No existe gold downstream de éxito de fallback; por eso su valor causal debe probarse con piloto.

## 11. Interpretabilidad — variables que preguntarán

| Variable | Definición / distribución | Papel final | Riesgo |
|---|---|---|---|
| sector | Sector solicitado; Industrial activa la interacción | Raw precursor | Segmentos pueden cambiar; no causal. |
| modality | rent/sale/both | Sólo benchmark/fallback hard gate | Política comercial, no predictor final. |
| user_type | Tipo de usuario | Challenger amplio | Categorías y missingness; importancia final no localizada. |
| company_size | `small` activa interacción Industrial | Raw precursor | Proxy de madurez/mercado; no causal. |
| source | `paid` activa interacción Industrial | Raw precursor | Feedback de campañas; monitorear drift. |
| channel | Canal de inquiry | Challenger amplio | Diagnóstico: Lift varía, pero no entra final. |
| requested_area / target_area | Necesidad declarada y objetivo | Benchmark/fallback soft fit | Unidades y missingness. |
| area ratio | Cociente candidato/deseado | Inventory `exp(-|log ratio|)` | No es modelo de conversión. |
| urgency | Días tolerados | Inventory availability decay | Valor declarado; puede faltar. |
| asked_visit | Intención explícita en primera inquiry | Ablation; excluida del final | Policy feedback; no dominó. |
| budget | Presupuesto / relación con precio | Benchmark/fallback soft fit | Moneda y datos actuales no versionados. |
| geografía | corredor/municipio/estado | Fallback 1/.85/.65 | Jerarquía heurística, no causal. |
| missingness | Imputación por mediana/moda; no hay flags explícitas finales | Benchmark amplio | Un cambio de instrumentación puede alterar la señal; flags finales: NO LOCALIZADO. |

Importancias de estas variables en el **modelo final**: no aplican, porque sólo entra la interacción. Coeficientes del benchmark amplio no se guardaron: **NO LOCALIZADO EN LOS ARTEFACTOS**. Segmentos del score final en holdout: Industrial N=434, AUC 0.616, AP 0.318, Lift@10 1.401; Land/Office/Retail AUC 0.5 por score constante dentro del segmento. Fuente: `codexway/outputs/tables/segment_metrics.csv`.

## 12. Resultados negativos y experimentación

| Experimento | Hipótesis | Resultado cuantitativo | Por qué no pasó | Aprendizaje / fuente |
|---|---|---|---|---|
| CatBoost canónico | No linealidad mejora T1 | Holdout AUC .4922, AP .2086, Lift10 .8264 | Peor que final y mala calibración | Potencia no sustituye estabilidad; `codexway/outputs/metrics/t1_model_metrics.json` |
| Random Forest histórico | Especialistas por etapa | OOF macro AUC .5711, AP .4699, Lift10 1.2288 | Otro target/contrato, no comparable | Challenger prometedor para T2; `experimentos/modelo_3/architecture_cv/results/oof_model_ranking.csv` |
| LightGBM histórico | Boosting alternativo | OOF macro AUC .5589, AP .4595, Lift10 1.2192 | Otro universo y sin promoción | Familia no ignorada; mismo path de benchmark |
| Logistic separada histórica | Modelo interpretable por stage | OOF macro AUC .4994, AP .4147, Lift10 .9938 | Sin señal | La segmentación por stage no basta; mismo path |
| Clustering E001 | Perfiles agregados añaden señal | AUC .5129, AP .2123, Lift10 1.0332 | Ganancia pequeña/inestable | Segmentación sirve para diagnóstico; `experimentos/profile_clustering_v2/results/model_metrics.csv` |
| Clustering E002/E003 | Más granularidad/intención | E002 AP .2054; E003 .2060; deltas con CI cruzan 0 | No mejora incremental | Resultado negativo útil; `experimentos/profile_clustering_v2/results/bootstrap_deltas.csv` |
| Interaction pockets | Celdas locales capturan lift | Confirmación final: 19 celdas elegibles, 0 pasan BH-FDR 10%; mejor N=66, tasa 24.24%, lift 1.1876, p=.1643 | Multiple testing | Lift raw local no basta; `codexway/outputs/tables/cluster_combinations.csv` |
| Response time RF EV-002 | Menor respuesta causa más conversión | Base AUC ~.516, +response ~.526; permutation ~0; contrafactual +0.33 pp | Variable post-T1/confundida | Diagnóstico, no score causal; `experimentos/Evidencias/EV-002_response_time_random_forest.md` |
| Geo EV-007 | Market context mejora T0 | ~+0.005 AUC; cobertura exacta ~23% | Sin publication/effective time | No sacrificar PIT por enriquecimiento; `experimentos/Evidencias/EV-007_geographic_enrichment.md` |
| ABT EV-016 | Más features listas para modelar | 86/86 campos en manifest; 9 tests pasan; 673 visits sin response time | No se benchmarkeó predictivamente | Infraestructura no es evidencia de lift; `experimentos/Evidencias/EV-016_abt_feature_engineering.md` |
| Semantic rules EV-018 | QA semántica mejora score | N=5,499 OOF; Lift10 1.2674→1.1958, Δ−.0716 CI [−.1438,.1251]; AP Δ+.0019 CI cruza 0 | No soportado | Útil como sidecar de QA, no ranking; `experimentos/Evidencias/EV-018_semantic_rules_lift_ablation.md` |
| T2 trajectory EV-012 | Trayectoria agrega señal | pooled CB ΔAP +.0161 CI [.0003,.0322]; multihead +.0155 [.0013,.0303] | T2 y contrato distinto | Línea futura real, no reemplazo T1; `experimentos/Evidencias/EV-012_modelo_3_trajectory_cv.md` |
| Availability threshold EV-019 | Fijar gates por capacidad | T1 top15 Lift medio 1.1223; T2 top15 1.4571; T0 sin gate | Otro target/stage y política histórica | Los cortes raw son diagnósticos; `experimentos/E019_operational_threshold_availability/results/threshold_frontier.csv` |
| Fallback K EV-020 | K=3 balancea cobertura y lista | Fold4 N=598; full list K1/K3/K5 75.92/62.37/55.69%; no-result 24.08% | Contrato distinto del output final | K operativo es trade-off; `experimentos/E020_lead_opportunity_fallback_e2e/results/fallback_k_selection.csv` |

El pocket histórico `DN4×LOC1×BSV1` tuvo N=60, tasa raw 36.67%, smoothed 31.37% y lift 1.510. Su p-value/FDR exacto **NO LOCALIZADO EN LOS ARTEFACTOS**; no atribuirle significancia. Fuente: `experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md`.

**Fracaso vs resultado negativo útil:** un experimento es un fracaso metodológico si rompe grano, usa futuro o carece de target comparable; no puede informar performance. Un experimento limpio cuyo intervalo cruza cero o cuya métrica empeora es un resultado negativo útil: descarta complejidad y delimita la siguiente hipótesis. Clustering y reglas semánticas pertenecen al segundo grupo; los stress tests leaky son controles deliberadamente inválidos, no challengers.

## 13. IA / LLM

**Dónde estuvo:** auditoría semántica de descripciones y descubrimiento de reglas, fuera del camino crítico de Lead Quality y del gate de inventario.

- Piloto real EV-017: GPT-5 nano, 100 casos estratificados. V2 usó 12,634 tokens input y 4,869 output; coste reportado `$0.002579`; 28% menos tokens de salida que V1. En estratos de 25: ambiguity tuvo issue en 96%; clean 0%; land residual 8%; rules-positive 8%. Resultado decisivo: `0/100` residual actionable y `0/100` nuevas reglas promovibles.
- Sidecar determinista sobre 3,000 spots: direct 322, Land-copy 230, ambiguity 327, Retail-adaptive 109; 890 con al menos una señal, 91 con dos.
- EV-015 original: 3,000 descripciones pero sólo 856 textos únicos; 84.4% compartidos y 12 oraciones dominantes; reglas marcaron 322 spots/330 conflictos. `experimentos/llm_inventory_quality/E015_llm_inventory_semantic_audit/results/evaluation.json` no contiene gold humano ni predicciones LLM: precision/recall natural **NO LOCALIZADO**.
- Evaluación canonical actual: 340 filas, `n_gold=0`; la corrida no se envió por opt-in de privacidad. La prueba controlada N=40 usa respuestas sintéticas cacheadas y no acredita performance natural.

Conclusión honesta: el LLM fue mediocre para generar señal incremental accionable y no se promovió como gate. La buena decisión de IA fue limitarlo a discovery/QA y conservar reglas deterministas auditables. Fuentes: `experimentos/llm_semantic_feature_pilot/results/PILOT_REPORT.md`, `experimentos/llm_semantic_feature_pilot/results/pilot_usage_summary_v2.csv`; `experimentos/llm_inventory_quality/E015_llm_inventory_semantic_audit/results/`; `codexway/outputs/metrics/llm_audit_evaluation.json`.

## 14. Robustez

| Prueba | Resultado | Qué habría invalidado | Conclusión |
|---|---|---|---|
| Holdout temporal | AUC .5478, Lift10 1.6888 | Rendimiento ≤ baseline | Señal modesta pero útil localmente. |
| Bootstrap 1,000 | AUC CI [.5273,.5684]; Lift10 [1.3807,1.9817] | CI cruzando baseline | Incertidumbre cuantificada; no implica causalidad. |
| Rolling 4 folds | Lift10 media 1.2137, SD .4627; 2/4 >1 | Inestabilidad extrema sin pocket reproducible | Señal variable; piloto guardado. |
| Madurez 7/14/30 | 20.4369/20.4301/20.4060% | Cambio material de base rate | Ventana 7d no infla tasa. |
| With/without asked | Lift10 .8495/.9865 | Caída grave sin variable | No domina y se excluye. |
| Monthly holdout | Lift10 1.207, 1.281, 2.554, 1.432, 1.650, 1.823 Jan–Jun | Meses consistentemente <1 | Positivo en 6/6 meses, magnitud variable. |
| Feature PSI | 0 para la feature final | Drift relevante | Sin drift detectado en ese corte; baja cardinalidad limita sensibilidad. |
| Freshness 7/30/90 | Leads con opción fresca 93.46/98.34/98.52% | Colapso de cobertura | 30d ofrece compromiso razonable. |
| Opportunity paired | ΔLift10 −.3186 CI enteramente <0 | Que se afirmara mejora predictiva | Separa visita de atendibilidad. |
| Leakage stress | Future inquiry AUC .8257/Lift2.9846 | Que score final se acercara por información futura | Stress detecta inflación esperada; final usa contrato T1. |
| Segmentos | Industrial AUC .616; otros .5 | Afirmar generalización uniforme | Beneficio concentrado en un bolsillo. |

Fuentes: `codexway/outputs/metrics/t1_metric_intervals.csv`, `codexway/outputs/metrics/rolling_model_comparison.csv`, `codexway/outputs/tables/target_maturity_sensitivity.csv`, `codexway/outputs/tables/monthly_model_stability.csv`, `codexway/outputs/tables/feature_drift.csv`, `codexway/outputs/tables/inventory_freshness_sensitivity.csv`, `codexway/outputs/metrics/system_score_paired_delta.csv`, `codexway/outputs/metrics/leakage_stress_test.json`, `codexway/outputs/tables/segment_metrics.csv`.

## 15. Los números peligrosos

| Número | Por qué genera dudas | Pregunta probable | Respuesta corta | Evidencia cuantitativa | Qué NO debo decir |
|---|---|---|---|---|---|
| AUC 0.5478 | Cerca de 0.5 | “¿Es random?” | Señal global débil, pero IC sobre .5 y pocket top útil. | IC [.5273,.5684], Lift10 1.6888 | “Es un gran predictor.” |
| AP 0.2391 vs 0.2122 | Mejora absoluta pequeña | “¿Valor mínimo?” | +2.70 pp, +12.7% relativo, con concentración top. | AP CI [.2145,.2655] | “AP subió 69%.” |
| Lift10 1.6888 | Riesgo de cherry-pick | “¿Elegiste K?” | K=5 igual y K=20=1.337; K representa capacidad. | CI10 [1.3807,1.9817] | “Conversion sube 69% causalmente.” |
| Opportunity Lift10 1.3702 | Inferior a quality | “¿Por qué agregar?” | Optimiza acción servible, no sólo visita. | Δ−.3186 CI [−.6252,−.0125] | “Inventory mejora la predicción.” |
| 44.30% exact unknown | Mucha incertidumbre | “¿Cómo decides?” | Uso lower/upper y verificación; 98.34% tiene algún candidato fresco. | gap medio .1277 | “Unknown es unavailable.” |
| 45.64% exact attendable | Parece cobertura máxima | “¿Sólo atiendes 45%?” | Es el spot exacto; alternativas elevan serviceability lower media a .6936. | 2.38% sin alternativa conocida | “Sólo 45% es atendible.” |
| N=4,898 | ML pequeño | “¿Sobreajuste?” | Modelo final 1D, 2,191 train/443 positivos por feature, regularizado. | Bootstrap, temporal split | “N es suficiente para cualquier ML.” |
| 1 feature | Puede parecer trivial | “¿Dónde está el modelado?” | Fue promovida tras competir contra 25 raw/105 encoded. | Final supera CatBoost por .0556 AUC | “Una variable explica el negocio.” |
| CatBoost .4922 | Sorprende | “¿Sobreajustó?” | No afirmo mecanismo; sí evidencia de mala generalización/calibración. | Brier .2423 vs .1658 | “CatBoost siempre sobreajusta.” |
| Platt | Ranking no cambia | “¿Para qué calibrar?” | Opportunity multiplica probabilidades; escala importa. | Validation Brier mejora .000034; holdout empeora .000270 | “Calibración quedó perfecta.” |
| Producto `Q×S` | Heurístico | “¿Por qué no segundo modelo?” | No hay gold de serviceability downstream; bounds preservan incertidumbre. | lower/upper y paired deltas | “Es probabilidad de cierre.” |
| Proxy scheduled visit | Puede desalinear revenue | “¿Genera baja calidad?” | Sí es riesgo; piloto debe medir cierre/revenue y guardrails. | No hay outcome downstream | “Visita equivale a venta.” |
| PIT listing | Campos current-state | “¿PIT real?” | Availability sí; price/attributes no están versionados. | 0 future snapshots, pero SCD2 ausente | “Todo el backtest es totalmente PIT.” |
| 34.36% vs 43.54% | Parece contradicción | “¿Cuál es correcto?” | Ambos, con poblaciones distintas. | 7,758/22,576 vs stress holdout | Mezclarlos en una frase sin denominador. |
| 33 vs 29 candidates | Distintos cortes | “¿Cambió la data?” | 33 es final full-pop; 29 fue desarrollo EDA. | 195,084 candidatos final | Elegir el que suena mejor. |

## 16. Comparaciones matemáticas rápidas

### 16.1 CatBoost vs final

- AUC: `0.547776−0.492213 = +0.055563` absoluto; `+11.29%` relativo a CatBoost.
- AP: `+0.030538`; `+14.64%` relativo.
- Brier: `−0.076499`; `31.58%` menor.
- Lift@10: `+0.862422`; `104.36%` mayor.

### 16.2 Top 10 del holdout

Con N=1,711 se seleccionan `ceil(.10×1,711)=172` leads. Baseline esperado: `172×.2121566=36.49` positivos. Por empates, el artefacto prorratea el grupo alto: `61.63` positivos esperados. Diferencia histórica: `+25.13`.

Por 1,000 leads y capacidad 100: azar `21.22`; Lead Quality `35.83`; Opportunity lower `29.07`. Diferencias: Lead Quality `+14.61` vs azar; Opportunity `+7.85`; Quality vs Opportunity `+6.76`. Son asociaciones de backtest, no uplift causal.

### 16.3 Complejidad

- Campeón: N/feature `2,191`; positivos/feature `443`.
- Challenger amplio raw: `87.64` y `17.72`.
- Challenger amplio encoded 105D: `20.87` y `4.22`.

### 16.4 Inventory

- Exact known: `100−44.30=55.70%`; dentro de lo known, attendable `45.64/55.70=81.94%`.
- Exact known unavailable: `10.06% = 503 leads`.
- Gap serviceability medio: `0.821251−0.693569=0.127682`.
- Pérdida relativa de Lift por Opportunity lower: `(1.688794−1.370203)/1.688794=18.87%`.

## 17. Auditoría final de consistencia

- [x] `1,001 + 3,897 = 4,898`; censurados separados.
- [x] Train, validation, test y purge suman población madura.
- [x] Prevalencias recalculadas con su denominador.
- [x] Lift se describe como concentración histórica, nunca uplift.
- [x] Development/rolling, procedural holdout y experimentos históricos están etiquetados.
- [x] CatBoost canónico se compara sobre el mismo holdout; los CatBoost históricos no.
- [x] Métricas Opportunity no se atribuyen a Lead Quality.
- [x] AssessmentSol1 se trata como clean-room complementario, no como campeón.
- [x] T0/T1/T2 no se mezclan.
- [x] `asked_visit` con/sin está etiquetado y fuera del final.
- [x] Puntuales e intervalos aparecen separados.
- [x] Accuracy/precision/recall/F1 reconstruidos están marcados como tales.
- [x] Ausencias se reportan como **NO LOCALIZADO EN LOS ARTEFACTOS**.

**Evaluación de confianza:** compartir con caveats. Lead Quality está suficientemente trazado para un piloto guardado; Inventory requiere versionado histórico de listing fields y un outcome downstream antes de justificar automatización.
