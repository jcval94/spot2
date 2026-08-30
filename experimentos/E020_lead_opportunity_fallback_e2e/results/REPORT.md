# E020 — Lead Opportunity Score + Fallback end-to-end

**Conclusión: SUPPORTED / DECISION-READY.**

E020 cierra la integración que faltaba entre Lead Quality, Inventory Availability y fallback.

## 1. Fallback final

### Política congelada

Cuando el spot solicitado no está confirmado como disponible en el último snapshot conocido:

1. mismo sector;
2. modalidad compatible;
3. spot creado antes o en el score;
4. snapshot de availability conocido al score;
5. área entre 0.5x y 2.0x de la necesidad;
6. precio total <=1.5x del presupuesto relevante;
7. preferencia geográfica por:
   - corredor;
   - municipio;
   - estado;
8. ranking por:
   - tier geográfico;
   - disponible ahora primero;
   - distancia logarítmica de área + precio/m².

Se devuelven **hasta K=3** alternativas.

No se relaja más allá del estado ni se violan sector/modalidad. Si no existen candidatos válidos, se devuelve `NO_RESULT`.

### Por qué K=3

En los folds 1-3 usados para escoger K:

- lista completa de 3: **60.8%**;
- lista completa de 5: **50.3%**.

K=3 gana ~10.5 pp de cobertura completa frente a K=5 y produce un shortlist operativamente manejable.

Fold 4 confirma el patrón:

- casos que requieren fallback: **598**;
- al menos una recomendación válida dentro del top-3: **75.9%**;
- lista completa de 3: **62.4%**;
- lista completa de 5: **55.7%**;
- no-result: **24.1%**;
- al menos una alternativa actualmente disponible en top-3: **70.9%**;
- mediana de candidatos válidos: **6**;
- de las listas completas de 3, **82.6%** permanecen enteramente en el corredor;
- **86.1%** de las recomendaciones devueltas están disponibles en el snapshot as-of;
- **63.4%** además cumplen el criterio estricto: corredor + área 0.5-1.5x + precio <=1.15x presupuesto.

### Por qué Hit@K histórico NO es el gate principal

El historial de inquiries no es un log de recomendaciones.

Entre 801 spots de futuras visitas alternativas observadas:

- sólo **67.4%** coincide con el sector declarado del lead;
- sólo **16.5%** coincide con su corredor preferido;
- apenas **1.0%** cumple simultáneamente sector + corredor + restricciones estrictas;
- sólo **1.75%** cumple la política bounded completa usada por el fallback.

Por eso optimizar el recomendador para reproducir el spot histórico rompería las reglas de negocio que pide el assessment.

Como diagnóstico, en fold 4:

- Hit@1: 0%;
- Hit@3: 0%;
- Hit@5: 0.52%.

Esto se conserva como resultado negativo y como evidencia de que el dataset no contiene un gold standard de recommendation relevance.

La evaluación primaria del fallback es por **constraint-valid Coverage@K**, availability as-of y no-result rate.

## 2. Lead Opportunity Score final

La fórmula queda congelada como:

`Lead Opportunity Score = P_quality × P_inventory_top3`

donde:

- `P_quality` es la probabilidad OOF de `pooled_catboost_trajectory`;
- `P_inventory_top3` es el máximo entre:
  - P(availability) del spot solicitado;
  - P(availability) de las alternativas top-3.

La multiplicación tiene una interpretación simple: una oportunidad sólo es alta si tiene calidad de lead y capacidad de servicio.

**No se declara como probabilidad conjunta perfectamente calibrada.** Lead Quality e Inventory Availability no han demostrado independencia condicional.

## 3. Proxy operativo conjunto

Para evaluar el sistema completo se define:

`joint_success = scheduled_visit_30d AND confirmed_serviceable`

donde `confirmed_serviceable=1` si el spot actual o al menos una alternativa top-3 está disponible en el snapshot as-of.

Este proxy mide el objetivo del sistema combinado: conversión potencial **y** capacidad inmediata de atenderla.

No reemplaza el target de Lead Quality; es una métrica de decisión end-to-end.

## 4. Métricas end-to-end

Las métricas se calculan dentro de fold y stage y después se promedian.

| Stage | Variante | AUC | AP | Brier | Log loss | Lift@10% | Recall@20% |
|---|---|---:|---:|---:|---:|---:|---:|
| T1 | Quality only | 0.561 | 0.430 | 0.237 | 0.667 | 1.192x | 0.217 |
| T1 | **Opportunity Score** | **0.652** | **0.487** | **0.223** | **0.636** | **1.281x** | **0.252** |
| T2 | Quality only | 0.623 | 0.394 | 0.205 | 0.597 | 1.432x | 0.278 |
| T2 | **Opportunity Score** | **0.669** | **0.437** | **0.197** | **0.577** | **1.619x** | **0.321** |
| MACRO | Quality only | 0.592 | 0.412 | 0.221 | 0.632 | 1.312x | 0.247 |
| MACRO | **Opportunity Score** | **0.660** | **0.462** | **0.210** | **0.607** | **1.450x** | **0.287** |

La mejora sobre el proxy conjunto aparece en **los cuatro folds** para T2 y en 3/4 folds con un empate en T1.

## 5. Evaluación a la capacidad final P85

Fold 4, usando **top 15% dentro de cada etapa**:

### T1

- Quality-only:
  - 73 seleccionados;
  - 41 joint positives;
  - confirmed serviceable 94.5%.
- Opportunity Score:
  - 73 seleccionados;
  - 41 joint positives;
  - confirmed serviceable **100%**.

### T2

- Quality-only:
  - 146 seleccionados;
  - 65 joint positives;
  - confirmed serviceable 86.3%.
- Opportunity Score:
  - 146 seleccionados;
  - **73 joint positives**;
  - confirmed serviceable **100%**.

### Total

Misma capacidad operativa:

- seleccionados: **219**;
- joint positives quality-only: **106**;
- joint positives Opportunity Score: **114**;
- ganancia: **+8 leads**, equivalente a **+7.5%** sobre el baseline de oportunidades atendibles seleccionadas.

Además, dentro del top-15% de Quality en fold 4 había **83** casos cuyo spot solicitado no estaba disponible; el fallback recupera **59** de ellos con una alternativa actualmente disponible, ~**71.1%**.

## 6. Guardrail: conversión pura

La integración no mejora `scheduled_visit` si ignoramos inventario.

Fold 4, P85 por etapa:

- Quality-only conversion positives: **124**;
- Opportunity Score conversion positives: **114**;
- delta: **-10**.

Esto no se oculta.

Interpretación:

- si el objetivo fuera sólo “quién probablemente visitará”, usaríamos Lead Quality;
- si el objetivo es “quién probablemente visitará **y además puedo atender ahora**”, el Opportunity Score es la decisión correcta.

El assessment pide explícitamente lo segundo.

## 7. Distribución del score

Fold 4, T1+T2:

| Percentil | Lead Quality | P(Inventory) | Opportunity Score |
|---|---:|---:|---:|
| P05 | 0.197 | 0.654 | 0.182 |
| P25 | 0.305 | 1.000 | 0.290 |
| P50 | 0.434 | 1.000 | 0.395 |
| P75 | 0.514 | 1.000 | 0.504 |
| P95 | 0.577 | 1.000 | 0.574 |

Inventory está saturado en gran parte de la población, lo que explica por qué el score combinado conserva buena parte del ranking de Lead Quality y actúa principalmente sobre los casos de inventario insuficiente.

## 8. Leakage

- Lead Quality: OOF temporal.
- Availability: backward-as-of.
- Spots futuros: bloqueados por `created_at <= score_time`.
- Snapshot futuro: nunca usado en fallback.
- Current `is_active`: no usado.
- Future scheduled_visit: outcome/guardrail solamente.
- Ranking de fallback: usa únicamente información conocida al score.

**LEAKAGE_CHECK = PASS**

## 9. Cierre

| Item | Estado |
|---|---|
| Fallback conceptual | **CLOSED** |
| Fallback final evaluado @K | **CLOSED — hasta K=3** |
| Lead Opportunity Score combinado | **CLOSED — P_quality × P_inventory_top3** |
| Evaluación end-to-end | **CLOSED — joint proxy + conversion guardrail** |

Lo que queda después de E020 es productización/medición online, no un blocker del assessment offline.
