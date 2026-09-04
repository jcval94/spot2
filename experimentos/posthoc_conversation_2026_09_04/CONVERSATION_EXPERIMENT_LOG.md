# Spot2 — bitácora de experimentos post-hoc de la conversación

Fecha: 2026-09-04  
Rama: `analysis/user-requested-separate-features-clusters`  
Estado: exploratorio / post-hoc. No modifica la solución final de `main` ni GitHub Pages.

---

## 1. Objetivo de esta bitácora

Este documento conserva, en un solo lugar, los challengers y diagnósticos adicionales ejecutados durante la conversación posterior al cierre de la solución principal de Spot2.

El propósito no es reescribir la solución oficial ni reemplazar automáticamente el modelo final. El objetivo fue responder preguntas concretas:

1. ¿El modelo final de una sola feature era un accidente de preprocessing?
2. ¿Las variables se estaban moviendo demasiado en el tiempo?
3. ¿`days_from_lead_creation` estaba dañando la generalización?
4. ¿Separar `Industrial`, `small` y `paid` funcionaba mejor que su interacción?
5. ¿Los clusters estables podían aportar señal predictiva?
6. ¿Una logística o Random Forest multivariable, con datos estandarizados, podía recuperar Lift?
7. ¿Existían reglas simples de máximo 3 variables con Lift mensual persistentemente > 1?
8. ¿Era preferible una policy layer jerárquica a seguir forzando modelos más complejos?

---

## 2. Autoridad y protocolo

La solución final oficial sigue siendo `codexway/**` en `main`.

Todos los challengers de esta bitácora se ejecutaron en una rama aislada para no sustituir targets, features, thresholds o arquitectura final.

### Split temporal utilizado

Se conservó exactamente el contrato temporal original:

- Train: `2025-01-01` inclusive a `2025-09-24` exclusivo.
- Validation: `2025-10-01` inclusive a `2025-12-24` exclusivo.
- Test: `2026-01-01` inclusive a `2026-06-24` exclusivo.
- Purge/maturity: 7 días.
- `prediction_timestamp` define el split.
- Solo observaciones maduras (`target_t1` no nulo).

Tamaños:

- Train: 2,191.
- Validation: 847.
- Test: 1,711.
- Prevalencia test: ~0.2122.

### Regla metodológica importante

El holdout 2026 ya había sido abierto en el trabajo original y fue consultado varias veces durante estos diagnósticos. Por ello, estos experimentos deben considerarse **post-hoc**. Ninguna nueva regla o modelo puede reclamar confirmación mediante un holdout realmente intacto.

La forma correcta de promover una hipótesis nueva sería validarla sobre datos futuros/frescos o mediante un experimento prospectivo.

---

## 3. Modelo final de referencia

La solución final de Lead Quality es una logística con una sola interacción binaria:

```text
industrial_small_or_paid =
    (search_sector == "Industrial")
    AND
    (company_size == "small" OR source == "paid")
```

Holdout 2026 aproximado:

- ROC AUC: 0.5478.
- Average Precision: 0.2391.
- Lift@5: 1.6888.
- Lift@10: 1.6888.
- Lift@20: 1.3371.

Lift@10 mensual 2026:

| Mes | Lift@10 |
|---|---:|
| Ene | 1.207 |
| Feb | 1.281 |
| Mar | 2.553 |
| Abr | 1.432 |
| May | 1.650 |
| Jun | 1.823 |

Lectura: discriminación global débil, pero concentración útil y consistentemente >1 en el top decile mensual del holdout.

---

## 4. Descomposición de la interacción ganadora

Archivo principal:

`codexway/tests/test_user_requested_challengers.py`

Run exitoso: `33885390709`.

Se probaron las piezas de la interacción por separado y en combinaciones pequeñas.

### Resultados holdout

| Challenger | Lift@5 | Lift@10 | Lift@20 |
|---|---:|---:|---:|
| Ganador reconstruido | 1.689 | 1.689 | 1.337 |
| `industrial_small` + `industrial_paid` | 1.540 | 1.669 | 1.337 |
| `is_industrial` + `is_small` + `is_paid` | 1.433 | 1.254 | 1.047 |
| Industrial only | 1.206 | 1.206 | 1.206 |
| Small only | 0.899 | 0.899 | 0.899 |
| Paid only | 1.051 | 1.051 | 1.051 |
| Industrial + small only | 1.903 | 1.550 | 1.245 |
| Industrial + paid only | 1.512 | 1.302 | 1.135 |
| 3 categóricas raw con OHE | 0.887 | 0.997 | 1.111 |

### Interpretación

- `small` sola no aporta señal útil.
- `paid` sola es casi aleatoria.
- `Industrial` tiene señal modesta.
- La señal depende de la **interacción condicionada a Industrial**.
- Separar las tres variables como main effects pierde gran parte de la estructura.
- `industrial_small_only` tuvo Lift@5 más alto en test, pero validation no justificaba seleccionarla; promoverla usando test sería cherry-picking.

Conclusión: la interacción simple no parece ser un capricho arbitrario de feature engineering.

---

## 5. Clusters como challengers predictivos

Archivo:

`codexway/src/spot2_codexway/profiles.py`

Familias estables preexistentes:

- `physical_profile`: ARI = 1.0.
- `location_profile`: ARI = 1.0.
- `broker_service_profile`: ARI ≈ 0.9304.

Drift temporal train→test aproximado:

- Physical PSI ≈ 0.0035.
- Location PSI ≈ 0.0077.
- Broker service PSI ≈ 0.0313.

Familias rechazadas por balance:

- `need_profile`.
- `dynamic_need_profile`.

### Cluster-only seleccionado por validation

El mejor subset por Lift@10 de validation fue `location_profile`.

Validation:

- AUC ≈ 0.5038.
- Lift@5 ≈ 1.458.
- Lift@10 ≈ 1.431.
- Lift@20 ≈ 1.159.

Test:

- AUC ≈ 0.4852.
- Lift@5 ≈ 0.981.
- Lift@10 ≈ 0.981.
- Lift@20 ≈ 0.971.

### Aprendizaje

La pertenencia a clusters puede ser temporalmente estable y, aun así, la relación cluster→target no ser estable.

Por ello, los clusters quedaron mejor justificados como:

- segmentación descriptiva;
- perfiles de negocio;
- posible modificador de reglas;

pero no como scorer independiente.

---

## 6. Auditoría completa de drift temporal de features

Archivo:

`scratch/user_requested_temporal_drift_audit.py`

Workflow run exitoso: `33886280818`.

Se auditó el conjunto amplio de features del modelo mediante PSI categórico/numerico y desplazamientos estandarizados.

### Train → validation

Ninguna variable tuvo PSI moderado/alto.

Máximo:

- `days_from_lead_creation`: PSI ≈ 0.0751.

### Train → test

Solo una variable fue realmente notable:

- `days_from_lead_creation`: PSI ≈ **0.1536** (moderado).
- Mediana train: **4.61 días**.
- Mediana test: **2.76 días**.
- Shift medio: ~0.37 desviaciones estándar.

El resto fue bajo. Ejemplos:

- `sale_request_to_lead_budget_ratio`: 0.0296.
- `max_budget_mxn_sale_total`: 0.0290.
- `preferred_corridor`: 0.0172.
- `requested_area_sqm`: 0.0159.
- `message_length`: 0.0144.
- `area_request_to_target_ratio`: 0.0143.
- `industry`: 0.0094.
- `company_size`: 0.0048.
- `search_sector`: 0.0041.
- `source`: 0.0031.

### Aprendizaje

La hipótesis de “el ABT completo se mueve muchísimo en el tiempo” **no quedó respaldada**.

Además, las tres variables que forman la interacción final son especialmente estables.

---

## 7. Estandarización

El pipeline logístico amplio original ya aplicaba:

- imputación mediana en numéricas;
- `StandardScaler` en numéricas;
- imputación + OneHotEncoder en categóricas;
- fitting del preprocessing exclusivamente sobre train.

Durante los challengers posteriores se adoptó como regla adicional que los inputs numéricos se mantuvieran estandarizados con parámetros de train.

En el experimento RF/logística sin `days_from_lead_creation`, incluso los one-hot se variance-scaled para homogeneizar la representación entre modelos.

Punto conceptual: `StandardScaler` resuelve escala/condicionamiento, pero **no elimina drift temporal**. Si la distribución cambia, el cambio sigue existiendo en unidades estandarizadas.

---

## 8. Logística y Random Forest sin `days_from_lead_creation`

Archivo:

`codexway/analysis/user_requested_no_days_standardized.py`

Workflow run: `33887245733`.

Cambios:

- Se eliminó `days_from_lead_creation`.
- Se mantuvieron todas las demás features limpias.
- Se conservó `industrial_small_or_paid_interaction`.
- Estandarización aprendida solo en train.
- RF fijado a priori: 800 árboles, profundidad 6, `min_samples_leaf=20`, `max_features=sqrt`.
- No hubo tuning contra test.

### Resultado global holdout

| Modelo | AUC | Lift@5 | Lift@10 | Lift@20 |
|---|---:|---:|---:|---:|
| Logística sin days | 0.494 | 0.877 | 0.959 | 0.948 |
| Random Forest sin days | 0.505 | 0.877 | 1.041 | 1.099 |
| Ganador final | 0.548 | 1.689 | 1.689 | 1.337 |

### Lift mensual RF

| Mes | Lift@5 | Lift@10 | Lift@20 |
|---|---:|---:|---:|
| Ene | 0.950 | 1.144 | 1.246 |
| Feb | 0.332 | 0.663 | 0.760 |
| Mar | 0.527 | 1.185 | 1.053 |
| Abr | 0.660 | 0.683 | 0.938 |
| May | 1.800 | 1.350 | 1.371 |
| Jun | 1.292 | 1.508 | 1.508 |

### Lift mensual logística

| Mes | Lift@5 | Lift@10 | Lift@20 |
|---|---:|---:|---:|
| Ene | 1.267 | 1.308 | 1.329 |
| Feb | 0.332 | 0.995 | 0.844 |
| Mar | 0.790 | 1.053 | 0.856 |
| Abr | 0.330 | 0.853 | 0.768 |
| May | 1.200 | 1.350 | 0.990 |
| Jun | 0.862 | 0.646 | 1.077 |

Validation tampoco justificaba promoción:

- Logística Lift@10 validation ≈ 0.845.
- RF Lift@10 validation ≈ 0.966.

### Aprendizaje

Eliminar la variable con mayor drift temporal **no recuperó generalización**.

Esto debilitó dos explicaciones alternativas:

1. que `days_from_lead_creation` fuera el principal causante del fracaso;
2. que el modelo amplio fallara por un problema básico de escalamiento.

---

## 9. Búsqueda exhaustiva de reglas tipo pivot

Archivo:

`codexway/analysis/user_requested_rule_search_300.py`

Workflow run: `33889549137`.

Objetivo: dejar de forzar clasificadores y buscar reglas simples de máximo tres variables que pudieran expresarse como filtros/pivot tables.

### Metodología

- RF permutation importance se utilizó **solo como heurística para priorizar variables**.
- Las numéricas se discretizaron usando z-score con parámetros de train.
- Se permitieron ANDs de máximo 3 condiciones.
- Se incorporaron clusters estables (`PH`, `LOC`, `BSV`).
- Soporte mínimo: 10 observaciones por mes evaluado.
- Ranking principal: validation → histórico → soporte/importancia.
- Test 2026 no entró al ordenamiento.

### Importancia RF usada como punto de partida

Primeras variables aproximadas:

1. `preferred_corridor`.
2. `requested_area_sqm`.
3. `industrial_small_or_paid_interaction`.
4. `search_sector`.
5. `target_area_sqm`.
6. `preferred_municipality`.
7. `preferred_state`.
8. `industry`.
9. `requested_budget_mxn_sale_total`.
10. `source`.
11. `rent_request_to_lead_budget_ratio`.
12. `requested_budget_mxn_rent_monthly`.

Importante: el RF global tenía AUC ~0.505; por lo tanto esta importancia no se interpreta como causal ni como evidencia fuerte por sí sola.

### Volumen de búsqueda

- Combinaciones brutas evaluadas: **60,648**.
- Reglas con soporte suficiente: **637**.
- Reglas con Lift >1 en todos los meses de validation: **61**.
- Reglas con Lift >1 en los 6 meses de test 2026: **13**.
- Reglas con Lift >1 en validation y los 6 meses de 2026: **6**.
- Reglas >1 en absolutamente todos los meses 2025+2026: **0**.

### Reglas más interesantes

#### A. Industrial + retail

```text
search_sector = Industrial
AND industry = retail
```

Lift 2026 por mes:

- Ene 2.09.
- Feb 1.16.
- Mar 1.24.
- Abr 1.06.
- May 1.40.
- Jun 1.82.

Mínimo 2026: ~1.060.  
N test: 101.

#### B. Ganador + PH1

```text
industrial_small_or_paid = 1
AND physical_profile = PH1
```

Lift 2026:

- 1.15 / 1.22 / 2.70 / 1.52 / 1.31 / 2.37.

Mínimo: ~1.152.  
N test: 134.

Interpretación: PH1 puede refinar descriptivamente al ganador, pero no resultó conveniente usarlo para romper prioridad operativa, como se explica más adelante.

#### C. Industrial + banda de presupuesto de renta estandarizado

```text
search_sector = Industrial
AND -0.239 <= z(requested_budget_mxn_rent_monthly) < 0.181
```

Lift 2026:

- 1.04 / 1.16 / 1.40 / 1.20 / 1.12 / 1.19.

Mínimo: ~1.043.  
N test: 196 antes de aplicar exclusiones jerárquicas.

### Reglas atractivas solo en test que NO deberían promocionarse

Ejemplos:

- Bandas combinadas de `target_area` y presupuesto de renta con mínimo test ~1.14, pero validation mínimo ~0.72.
- Industrial + banda de sale budget con mínimo test ~1.09, pero validation mínimo ~0.83.

Aprendizaje: la minería de reglas puede producir fácilmente segmentos aparentemente excelentes en test; validation sigue siendo crucial para distinguir señal de cherry-picking.

---

## 10. Primera matriz jerárquica de 5 niveles

Archivo:

`codexway/analysis/user_requested_priority_matrix.py`

Runs relevantes:

- `33891009579`.
- Corrección ordinal: `33891158004`.

Primera propuesta:

1. P1 Industrial + retail.
2. P2 ganador + PH1.
3. P3 resto del ganador.
4. P4 Industrial + banda central de rent budget.
5. P5 resto.

### Bug técnico detectado y corregido

En la primera ejecución, `priority_score` usó valores ordinales 1–5 directamente. La función `binary_metrics` recorta scores a [1e-8, 1-1e-8] porque normalmente recibe probabilidades. Eso colapsaba los niveles >1 y podía destruir el orden.

Se corrigió transformando el ordinal a un score válido dentro de (0,1), preservando exactamente el ranking.

Los lifts de segmentos acumulados de la primera versión no dependían de ese score y sí eran correctos; únicamente Lift@5/@10/@20 requería la corrección.

### Resultado conceptual

Usar PH1 para romper empates dentro del ganador empeoró la estabilidad de la policy a capacidad 10%; febrero quedó alrededor de 0.97 en una de las configuraciones.

Aprendizaje: PH1 aporta descripción, pero no conviene forzarlo como prioridad separada.

---

## 11. Matriz simplificada recomendada

Archivo:

`codexway/analysis/user_requested_priority_matrix_collapsed.py`

Workflow run: `33891319724`.

Se simplificó la jerarquía a:

### P1 — Muy alta

```text
search_sector = Industrial
AND industry = retail
```

### P2 — Alta

```text
industrial_small_or_paid = 1
excluyendo P1
```

### P3 — Media

```text
search_sector = Industrial
AND -0.239 <= z(requested_budget_mxn_rent_monthly) < 0.181
excluyendo P1/P2
```

### P4 — Base

Resto.

PH1 queda como etiqueta descriptiva dentro de P2, no como nivel.

### Cobertura test aproximada

- P1: 101 leads (5.9%).
- P2: 146 (8.5%).
- P3: 28 (1.6%).
- P4: 1,436 (83.9%).
- P1–P3: ~16.1% del holdout.

### Lift@k mensual de la policy completa · test 2026

| Mes | Lift@5 | Lift@10 | Lift@20 |
|---|---:|---:|---:|
| Ene | 2.086 | 1.362 | 1.057 |
| Feb | 1.161 | 1.137 | 1.093 |
| Mar | 1.239 | 1.798 | 1.571 |
| Abr | 1.082 | 1.232 | 1.254 |
| May | 1.400 | 1.434 | 1.290 |
| Jun | 1.823 | 1.723 | 1.480 |
| Peor mes | **1.082** | **1.137** | **1.057** |
| Promedio | **1.465** | **1.448** | **1.291** |

Resultado: **todos los meses permanecen >1 en 5%, 10% y 20% de capacidad.**

### Validation 2025

| Mes | Lift@5 | Lift@10 | Lift@20 |
|---|---:|---:|---:|
| Oct | 1.894 | 1.475 | 1.261 |
| Nov | 1.533 | 1.493 | 1.384 |
| Dic | 1.571 | 1.402 | 1.170 |

También todos >1.

### Lectura acumulativa

#### Solo P1

2026: 2.086 / 1.161 / 1.239 / 1.060 / 1.400 / 1.823.

#### P1 + P2

2026: 1.200 / 1.130 / 1.960 / 1.291 / 1.469 / 1.673.

#### P1 + P2 + P3

2026: 1.078 / 1.133 / 1.873 / 1.313 / 1.358 / 1.540.

La lectura correcta es **acumulativa**. No es necesario que cada nivel exclusivo tenga lift >1 todos los meses. Lo importante para la operación es que, al consumir capacidad desde P1 hacia abajo, la población seleccionada siga superando la prevalencia mensual.

---

## 12. Comparación matriz vs modelo final

Lift@10 mensual aproximado:

| Mes | Regla final | Matriz |
|---|---:|---:|
| Ene | 1.21 | 1.36 |
| Feb | 1.28 | 1.14 |
| Mar | 2.55 | 1.80 |
| Abr | 1.43 | 1.23 |
| May | 1.65 | 1.43 |
| Jun | 1.82 | 1.72 |

La regla final sigue siendo más fuerte en Lift@10 en la mayoría de los meses.

Por ello, la matriz **no reemplaza automáticamente** al modelo final.

Su valor es diferente:

- varios niveles de prioridad;
- mayor cobertura operativa;
- explicación inmediata;
- una extensión controlada fuera de `small/paid`;
- posibilidad de usar clusters como metadata descriptiva;
- menor presión por forzar un clasificador multivariable sin señal generalizable.

La interpretación propuesta es una **policy layer exploratoria**.

---

## 13. Qué aprendimos sobre el problema

### 13.1 El problema no parece ser simplemente scaling

La logística amplia ya escalaba numéricas y los challengers adicionales estandarizaron consistentemente. El rendimiento no se recuperó.

### 13.2 El problema no parece ser drift masivo del ABT

Salvo `days_from_lead_creation`, los PSI fueron bajos. Y eliminar esa variable no ayudó.

### 13.3 La señal parece local y condicional

La interacción Industrial × (small OR paid) se sostuvo mejor que los main effects.

Además aparecieron microsegmentos sencillos, especialmente Industrial + retail y bandas específicas de presupuesto.

### 13.4 Los clusters tienen valor, pero no necesariamente como score

Las familias físicas, geográficas y de servicio fueron temporalmente estables, pero los clusters solos no generalizaron. PH1 sí apareció como refinamiento descriptivo de una regla ya útil.

### 13.5 Forzar complejidad puede ser contraproducente

RF y logística multivariables amplias quedaron alrededor del azar fuera del tiempo. Una política explícita de segmentación puede ser más honesta y operacionalmente útil que un modelo complejo sin señal estable.

---

## 14. Qué NO debe afirmarse

No afirmar:

- que la nueva matriz es superior al modelo final;
- que 2026 es un holdout limpio para estas nuevas reglas;
- que los clusters demostraron causalidad;
- que las reglas encontradas son universalmente estables;
- que AUC ~0.55 es un modelo predictivo fuerte.

Sí se puede afirmar:

- que múltiples familias de modelos y transformaciones fueron probadas;
- que el preprocessing básico no explica el fracaso;
- que el drift general de features es bajo;
- que la señal final es pequeña pero persistente en algunos segmentos;
- que una policy layer simple puede sostener Lift >1 mes a mes en validation y en el periodo de test observado;
- que su promoción formal requiere datos frescos.

---

## 15. Archivos y runs reproducibles

### Scripts / pruebas

- `codexway/tests/test_user_requested_challengers.py`
- `scratch/user_requested_temporal_drift_audit.py`
- `codexway/analysis/user_requested_no_days_standardized.py`
- `codexway/analysis/user_requested_rule_search_300.py`
- `codexway/analysis/user_requested_priority_matrix.py`
- `codexway/analysis/user_requested_priority_matrix_collapsed.py`

### Workflows

- `.github/workflows/user-requested-challengers-fast.yml`
- `.github/workflows/user-requested-temporal-drift.yml`
- `.github/workflows/user-requested-no-days-standardized.yml`
- `.github/workflows/user-requested-rule-search-300.yml`
- `.github/workflows/user-requested-priority-matrix.yml`
- `.github/workflows/user-requested-priority-matrix-collapsed.yml`

### Runs principales

- Decomposición + clusters: `33885390709`.
- Drift audit: `33886280818`.
- No-days standardized logistic/RF: `33887245733`.
- Regla-search 60k: `33889549137`.
- Matriz 5 niveles: `33891009579`.
- Fix score ordinal: `33891158004`.
- Matriz simplificada: `33891319724`.

---

## 16. Próximo experimento correcto

La mejor continuación metodológica no es seguir optimizando contra el mismo test.

Opciones válidas:

1. **Fresh cohort:** aplicar de forma congelada la regla final y la matriz a leads posteriores a junio de 2026.
2. **Shadow mode:** calcular prioridades sin cambiar operación y observar Lift/coverage mensualmente.
3. **Experimento controlado:** comparar proceso actual vs priorización basada en la policy.
4. Mantener PH1 y otros clusters como metadata analítica, no como score, hasta que exista evidencia prospectiva.

---

## 17. Conclusión

Después de revisar interacciones, clusters, drift, escalamiento, eliminación de la feature más desplazada, logística, Random Forest y más de 60 mil reglas simples, la evidencia apunta a que el problema contiene **señal débil pero localizada**, no a un fallo obvio de StandardScaler o a un drift masivo de la ABT.

La solución oficial de una interacción sigue teniendo el mejor argumento de parsimonia y ranking top-decile. La matriz de prioridad es una extensión exploratoria interesante porque transforma esa señal en niveles operativos interpretables y mantiene Lift >1 mes a mes en validation y en el holdout observado. Sin embargo, debido al carácter post-hoc del análisis, debe confirmarse con datos frescos antes de cualquier promoción formal.
