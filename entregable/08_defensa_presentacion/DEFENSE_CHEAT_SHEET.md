# CHEAT SHEET — números que debo memorizar

**Corte de evidencia:** commit `7d4e90df6d7e7340f3963128089bd303e8993e52`; datos `as_of = 2026-07-01 UTC`. **Campeón:** `stable_segment_logistic` de `codexway`; los challengers no sustituyen estas cifras.

## ⚠️ Inconsistencias que debo conocer antes de presentar

- **1 feature final, no 26.** La logística estable usa una sola interacción binaria. La allowlist amplia enumera 26 campos, de los cuales 25 son inputs raw del benchmark amplio y el vigesimosexto es la interacción promovida.
- **34.36% ≠ 43.54%.** `7,758/22,576 = 34.36%` es el riesgo de nearest-snapshot sobre todas las inquiries; `43.54%` es el stress test S003 sobre el holdout T1. La solución final tiene **0** snapshots futuros.
- **Holdout temporal, pero procedimental.** Test tiene 1,711 leads de enero–junio de 2026, pero fue observado durante el proceso de recuperación; no venderlo como holdout virgen.
- **Calibración marginal.** Platt mejoró validation en Brier de `0.156111` a `0.156076`, pero en holdout el score raw fue ligeramente mejor (`0.165501` vs `0.165771`).
- **Inventory UNKNOWN usa dos denominadores.** `44.30%` son leads cuyo spot exacto queda unknown; `42.91%` son pares lead–candidato con snapshot de más de 30 días.

## 36 números para responder sin buscar

| Prioridad | Pregunta | Número | Qué significa | Cómo decirlo oralmente | Fuente exacta |
|---|---|---:|---|---|---|
| P0 | ¿Cuántos leads? | 5,000 | Grano principal lead | “Partí de cinco mil leads.” | `codexway/outputs/tables/data_audit.json` → `tables.leads.rows` |
| P0 | ¿Cuántas inquiries? | 22,576 | Eventos de consulta | “Había 22,576 consultas, 4.52 por lead en promedio.” | `codexway/outputs/tables/data_audit.json` → `tables.inquiries.rows` |
| P1 | ¿Cuántos spots? | 3,000 | Inventario de listings | “El universo tenía tres mil spots.” | `codexway/outputs/tables/data_audit.json` → `tables.spots.rows` |
| P1 | ¿Spot attributes? | 3,000 | Una fila por spot | “Attributes preserva grano uno-a-uno.” | `codexway/outputs/tables/data_audit.json` → `tables.spot_attributes.rows` |
| P1 | ¿Snapshots? | 30,000 | Historial de Availability | “Diez snapshots por spot en mediana.” | `codexway/outputs/tables/data_audit.json`; `entregable/01_eda/EDA_FINAL.md` |
| P1 | ¿Market context? | 500 | Observaciones externas | “Market context tenía 500 filas y se dejó fuera del score por semántica temporal.” | `codexway/outputs/tables/data_audit.json` |
| P2 | ¿Filas raw totales? | 64,076 | Suma reproducida de seis tablas | “Son 64,076 filas raw; no son observaciones independientes.” | Reconstruido: suma de `tables.*.rows` en `codexway/outputs/tables/data_audit.json` |
| P0 | ¿T1 total/maduro? | 5,000 / 4,898 | 102 censurados por madurez | “El modelado usa 4,898 T1 maduros de 5,000.” | `codexway/outputs/tables/data_audit.json` → `t1_contract` |
| P0 | ¿Positivos/negativos? | 1,001 / 3,897 | Scheduled visit a 7 días | “Hay 1,001 positivos y 3,897 negativos.” | `codexway/outputs/tables/data_audit.json` → `t1_contract.positives`; negativos reconstruidos |
| P0 | ¿Prevalencia? | 20.4369% | `1,001/4,898` | “El baseline de clase es 20.44%.” | `codexway/outputs/tables/data_audit.json` → `t1_contract.positive_rate` |
| P0 | ¿Madurez? | 7 días | Ventana posterior a T1 | “Espero siete días para declarar el proxy.” | `codexway/config/base.yaml`; `codexway/outputs/tables/target_maturity_sensitivity.csv` |
| P0 | ¿Train? | 2,191; 443 positivos; 20.2191% | 2025-01-01–2025-09-23 | “Train son 2,191 leads, 443 positivos.” | `codexway/outputs/abt/split_manifest.json` |
| P0 | ¿Validation? | 847; 165; 19.4805% | 2025-10-01–2025-12-23 | “Validation son 847 y 165 positivos.” | `codexway/outputs/abt/split_manifest.json` |
| P0 | ¿Holdout? | 1,711; 363; 21.2157% | 2026-01-01–2026-06-23 | “Holdout temporal son 1,711, con 363 visitas.” | `codexway/outputs/abt/split_manifest.json` |
| P1 | ¿Purga temporal? | 149; 30; 20.1342% | Buffers excluidos entre ventanas | “Purgué 149 casos para separar ventanas.” | `codexway/outputs/abt/split_manifest.json` |
| P0 | ¿Modelo final? | Logistic Regression `C=1` + Platt | Interacción estable y regularización L2 default | “Elegí la logística estable, calibrada en validation.” | `codexway/config/base.yaml`; `codexway/outputs/MODEL_CARD.md` |
| P0 | ¿Features finales? | 1 raw / 1 encoded | `industrial_small_or_paid_interaction` | “El campeón deliberadamente tiene una sola señal.” | `codexway/outputs/tables/feature_importance.csv` |
| P0 | ¿Coeficiente? | +0.120427 estandarizado | OR por 1 SD = 1.128 | “Es una asociación positiva, no causal.” | `codexway/outputs/tables/feature_importance.csv`; `codexway/outputs/models/t1_model_bundle.joblib` |
| P1 | ¿Tamaño del segmento? | 514/4,898; 155 positivos; 30.1556% | Industrial y small o paid | “La señal cubre 10.49% del maduro y tiene 30.16% de tasa.” | Reconstruido desde `codexway/outputs/abt/abt_t1_first_inquiry.parquet` |
| P0 | ¿ROC-AUC final? | 0.547776; IC95% [0.527297, 0.568425] | Discriminación global holdout | “Es modesta, pero el intervalo queda sobre 0.5.” | `codexway/outputs/metrics/t1_model_metrics.json`; `codexway/outputs/metrics/t1_metric_intervals.csv` |
| P0 | ¿PR-AUC? | 0.239129; IC95% [0.214479, 0.265538] | Baseline holdout 0.212157 | “Es 2.70 puntos absolutos y 12.7% relativo sobre prevalencia.” | `codexway/outputs/metrics/t1_model_metrics.json`; `codexway/outputs/metrics/t1_metric_intervals.csv` |
| P1 | ¿Brier/LogLoss? | 0.165771 / 0.512874 | Probabilidades Platt, holdout | “La calidad probabilística supera el constant-rate en Brier.” | `codexway/outputs/metrics/t1_model_metrics.json` |
| P0 | ¿Lift@10? | 1.688794; IC95% [1.380730, 1.981679] | 16.9768% de positivos capturados en 10% de capacidad | “Top 10 concentra 69% más visitas históricas que azar.” | `codexway/outputs/metrics/t1_model_metrics.json`; `codexway/outputs/metrics/t1_metric_intervals.csv` |
| P1 | ¿Lift@5/@20? | 1.688794 / 1.337084 | Robustez por capacidad | “La señal no depende sólo de K=10.” | `codexway/outputs/metrics/t1_model_metrics.json` |
| P1 | ¿Top 10 en números? | 61.63 vs 36.49 positivos esperados | Frontera tie-aware; 172 leads discretos | “Son 25.13 visitas históricas adicionales en este holdout.” | Reconstruido de `codexway/outputs/tables/gains.csv` y `codexway/outputs/abt/split_manifest.json` |
| P0 | ¿CatBoost? | AUC 0.492213; AP 0.208591; Lift@10 0.826371 | Holdout, mismas features amplias | “No sólo no ganó: perdió ranking y calibración contra el campeón.” | `codexway/outputs/metrics/t1_model_metrics.json` |
| P1 | ¿asked_visit domina? | No; Lift@10 0.849526 con vs 0.986546 sin | Challenger amplio, no campeón | “Quitarla mejoró Lift 0.137x; no está en el modelo final.” | `codexway/outputs/metrics/t1_model_metrics.json` |
| P0 | ¿Leakage de Availability? | 22,576 → 226,151 filas; 10.017× | Join directo por spot rompe el grano | “Era el riesgo de ingeniería más sutil.” | `entregable/01_eda/EDA_FINAL.md` |
| P0 | ¿Snapshots futuros? | 7,758/22,576 = 34.36%; final 0 | Nearest incorrecto vs backward-as-of | “Un nearest inocente mira al futuro en un tercio de las consultas.” | `entregable/01_eda/EDA_FINAL.md`; `codexway/outputs/metrics/inventory_audit.json` |
| P1 | ¿Cobertura/lag backward? | 92.38%; mediana 6.61d; p90 58.66d; p95 83.35d | Todas las inquiries | “PIT correcto no implica dato fresco.” | `entregable/01_eda/EDA_FINAL.md` |
| P0 | ¿Exact attendable/unknown? | 45.64% / 44.30% | 2,282 y 2,215 de 5,000 leads | “Unknown no significa unavailable.” | `codexway/outputs/metrics/inventory_audit.json` |
| P1 | ¿Sin alternativa conocida/potencial? | 2.38% / 0% | 119/5,000 vs 0/5,000 | “Sólo 2.38% queda sin alternativa respaldada por estado conocido.” | `codexway/outputs/metrics/inventory_audit.json` |
| P1 | ¿Freshness 30 días? | 57.0898% de candidatos; 98.34% de leads con ≥1 | 195,084 pares lead–candidato | “Aunque 42.91% de pares es stale/unknown, casi todos los leads tienen alguna opción fresca.” | `codexway/outputs/tables/inventory_freshness_sensitivity.csv` |
| P1 | ¿Candidate depth? | mediana 33; p90 71; máximo 152 | 5,000 leads; 195,084 candidatos | “La profundidad es suficiente, con cola larga.” | Reconstruido desde `codexway/outputs/predictions/lead_opportunity_scores.csv` |
| P0 | ¿Opportunity Lift@10? | Lower 1.370203; IC95% [1.077626, 1.689829] | Visita predicha por `p×serviceability_lower` | “Pierde 18.9% de lift predictivo frente a Lead Quality, pero decide atendibilidad.” | `codexway/outputs/metrics/system_score_metrics.csv`; `codexway/outputs/metrics/system_score_intervals.csv` |
| P1 | ¿Upper bound? | Lift@10 1.507223 | Inventario desconocido tratado como potencial | “La incertidumbre se conserva como rango, no como cero.” | `codexway/outputs/metrics/system_score_metrics.csv` |
| P0 | ¿Producción mañana? | Piloto aleatorizado y guardado | No auto-enrutamiento | “Forward validation, shadow scoring, fallback humano y monitoreo.” | `codexway/outputs/metrics/deployment_readiness.json`; `codexway/outputs/tables/online_ab_protocol.json` |

## Respuestas de 20 segundos

**¿Por qué logística y no CatBoost?** En el holdout comparable, la logística estable tuvo AUC `0.5478`, AP `0.2391` y Lift@10 `1.6888`; CatBoost tuvo `0.4922`, `0.2086` y `0.8264`. Además, en rolling CV CatBoost empeoró Brier medio `0.0138` frente a la logística amplia y sólo ganó AP en 2 de 4 folds. La complejidad no compró generalización.

**¿AUC 0.55 no es random?** Globalmente es una señal débil, no la vendo como gran predictor. Pero el scorer es binario y genera muchos empates: AUC resume todo el ranking; Lift@10 mide la concentración del bolsillo superior. En holdout ese bolsillo capturó `16.98%` de las visitas usando `10%` de capacidad, Lift `1.69x`, IC95% `[1.38,1.98]`.

**¿Cuál fue el leakage más peligroso?** El de mayor daño fue usar inquiries futuras: en el stress S002 infló AUC de `0.548` a `0.826` y Lift@10 de `1.689` a `2.985`. El más fácil de introducir fue Availability: join directo multiplicaba filas `10.017×` y nearest podía usar futuro en `34.36%`; el backward-as-of final deja `0` violaciones.

**¿Por qué Inventory si baja Lift?** Porque visita y atendibilidad son objetivos distintos. Lead Quality optimiza visitas (`Lift@10 1.689`); Opportunity lower baja a `1.370`, pero evita priorizar un lead cuyo spot no se puede servir. La política usa dos ejes y un rango lower–upper; no afirma que multiplicar mejore el target de visita.

**¿UNKNOWN = UNAVAILABLE?** No. Con freshness de 30 días, `42.91%` de pares candidato queda unknown/stale, pero `98.34%` de los leads tiene al menos un candidato fresco y no hay leads sin alternativa potencial. Convertir unknown a cero descartaría oferta plausible sin evidencia.

## Fórmulas rápidas

- `Lift@K = Precision@K / prevalence`. Para K=10: `0.358289 / 0.212157 = 1.688794`. Es equivalente a `Recall/share seleccionado real`; aquí se usan 172 leads y prorrateo de empates.
- Por **1,000 leads** y capacidad 100: azar ≈ `21.22` visitas; Lead Quality ≈ `35.83`; diferencia histórica ≈ **+14.61**. Opportunity lower ≈ `29.07`; diferencia vs azar ≈ **+7.85**. Es backtest, no uplift causal.
- Pérdida de Lift al agregar Inventory: `1.688794 − 1.370203 = 0.318591`, o `18.87%` relativo.
- AP/prevalence: `0.239129 / 0.212157 = 1.127`; mejora absoluta `+0.026972`.
- N por feature final: `2,191/1 = 2,191`; positivos por feature `443/1 = 443`. El benchmark amplio tiene 25 raw/105 encoded: `20.87` train rows y `4.22` positivos por dimensión, razón para regularizar y no promoverlo.

## Si sólo recuerdo 15 cosas

| # | Número / hecho | Frase de memoria |
|---:|---|---|
| 1 | 5,000 leads; 22,576 inquiries; 3,000 spots | “Cinco mil leads y 22.6 mil consultas sobre tres mil spots.” |
| 2 | 4,898 T1 maduros | “Ciento dos quedaron censurados por la ventana de siete días.” |
| 3 | 1,001 positivos; 3,897 negativos | “El proxy es scheduled visit a siete días.” |
| 4 | 20.4369% prevalencia | “Éste es el baseline de clase global madura.” |
| 5 | Train 2,191; 443 positivos | “Entrené temporalmente en enero–septiembre de 2025.” |
| 6 | Validation 847; holdout 1,711 | “Calibré en Q4-2025 y evalué enero–junio de 2026.” |
| 7 | 1 feature final | “No son 26: el campeón usa una interacción binaria.” |
| 8 | Logistic C=1 + Platt | “Modelo estable, regularizado y calibrado en validation.” |
| 9 | CatBoost AUC 0.4922; Lift@10 0.8264 | “El challenger potente no generalizó en el holdout comparable.” |
| 10 | AUC 0.5478 [0.5273, 0.5684] | “Discriminación global modesta pero estadísticamente sobre 0.5.” |
| 11 | Lead Quality Lift@10 1.6888 [1.3807, 1.9817] | “Top 10 concentra 69% más positivos históricos que azar.” |
| 12 | Opportunity lower Lift@10 1.3702 [1.0776, 1.6898] | “Sacrifica ranking de visitas para incorporar atendibilidad.” |
| 13 | Join 10.017×; nearest futuro 34.36%; final 0 | “Availability fue el principal riesgo de time travel.” |
| 14 | Exact 45.64% attendable; 44.30% unknown | “Unknown conserva potencial y no se convierte en unavailable.” |
| 15 | Piloto guardado, no auto-enrutamiento | “Pondría shadow scoring, verificación humana y experimento causal.” |
