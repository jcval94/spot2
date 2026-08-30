# Assessment — disposición final de modelos auxiliares

Este documento congela la decisión de assessment para tres líneas que no deben quedar como pendientes abiertos.

## Matriz final

| Componente | Evidencia / experimentos | Rol definitivo | Estado para el assessment |
|---|---|---|---|
| Matching / clusters | E007 / E012 / E015 / E016; EV-013 | Segmentación, interpretabilidad y routing auxiliar. No entra en la fórmula principal del Lead Opportunity Score. | ✅ CLOSED / AUXILIARY |
| Semantic rules | EV-018 | Catalog / Inventory QA. Excluidas del ABT de Lead Quality por no superar el gate de Lift@10%. | ✅ CLOSED / EXCLUDE FROM SCORING |
| Response-time RF | EV-002 | Diagnóstico operacional de SLA. Excluido del scoring T0/T1 por observabilidad temporal y por falta de señal incremental robusta. | ✅ CLOSED / DIAGNOSTIC ONLY |

---

## 1. Matching / clusters — CLOSED / AUXILIARY

### Decisión

Los perfiles y clusters se conservan como una capa secundaria de:

- segmentación e interpretabilidad;
- análisis de heterogeneidad;
- generación de hipótesis de routing;
- eventual tie-breaker o challenger bajo nueva evidencia independiente.

No sustituyen al modelo supervisado de Lead Quality ni forman parte de la fórmula principal:

```text
Lead Opportunity Score = P_quality × P_inventory_top3
```

### Evidencia

La línea E007/E012/E015/E016 encontró pockets con lift local, incluyendo DN4 × LOC1 × BSV1, pero las mejoras globales no separan robustamente a los challengers bajo bootstrap y el mismo future holdout fue consumido durante discovery.

Por tanto, cualquier activación de routing por clusters requiere nueva cohorte temporal o A/B online. No es un blocker del assessment.

### Regla de uso

- **ALLOW:** explicabilidad, segmentación, visualización, análisis de pockets, diseño de experimentos.
- **DO NOT USE:** reemplazo del LOS, regla productiva automática o claim causal.
- **REOPEN ONLY IF:** existe nueva cohorte independiente o A/B test que confirme un routing concreto.

---

## 2. Semantic rules — CLOSED / EXCLUDE FROM SCORING

### Decisión

Las variables semánticas determinísticas de EV-018 no se incorporan al ABT canónico de Lead Quality.

Se conservan para:

- Inventory QA;
- Catalog Quality;
- detección de inconsistencias;
- priorización de revisión de listings.

### Evidencia

EV-018 mantuvo constante target, población, folds, CatBoost e hiperparámetros y aisló únicamente las semantic rules.

Resultado macro:

- Lift@10 baseline: **1.267x**;
- Lift@10 + Rules: **1.196x**;
- delta: **-0.0716x**;
- IC95%: **[-0.1438, +0.1251]**;
- P(delta > 0): **45.0%**.

Guardrails:

- AP: 0.5122 -> 0.5141;
- AUC: 0.6063 -> 0.6114.

El intervalo de Lift cruza cero: no se demuestra daño concluyente, pero tampoco se cumple el gate de promoción. La decisión correcta es excluirlas del scoring, no seguir optimizando post-hoc sobre el mismo OOF.

### Regla de uso

- **ALLOW:** QA de catálogo e inventario.
- **DO NOT USE:** feature del Lead Quality final.
- **REOPEN ONLY IF:** nueva representación semántica, nueva fuente o nueva cohorte demuestra lift incremental bajo validación temporal independiente.

---

## 3. Response-time RF — CLOSED / DIAGNOSTIC ONLY

### Decisión

El experimento EV-002 se conserva únicamente como diagnóstico operacional. `broker_response_hours` no forma parte del modelo final de Lead Quality.

### Razón temporal

Para la inquiry actual:

```text
score_time = inquiry_at
inquiry_at < broker_response_event
```

Por tanto, `broker_response_hours` no es observable al scorear T1 y usarlo como feature de la inquiry actual introduciría información posterior al punto de decisión.

La única response history admisible es la de respuestas de inquiries estrictamente anteriores cuyo evento ya hubiera ocurrido antes o en `score_time`, tal como se implementa en la línea point-in-time posterior.

### Evidencia predictiva

EV-002 encontró que:

- añadir response time no mejoró AUC de forma material en la réplica multivariable inmediata;
- su permutation importance fue negativa o cercana a cero;
- incluso en targets posteriores a primera respuesta, el efecto incremental siguió siendo pequeño.

No existe razón metodológica ni empírica para incorporarlo al scoring principal.

### Regla de uso

- **ALLOW:** análisis de SLA, operación y tiempos de servicio.
- **DO NOT USE:** predictor current-inquiry en T0/T1.
- **REOPEN ONLY IF:** se redefine un scoring point posterior donde la respuesta ya sea observable y exista una pregunta de negocio distinta.

---

## Disposición final en la arquitectura

```text
                    +-----------------------------+
                    | Lead Quality                |
                    | CatBoost + stage + trajectory|
                    +--------------+--------------+
                                   |
                                   v
                            P_quality
                                   |
                                   |       +----------------------+
                                   +------>| Inventory Availability|
                                           +----------+-----------+
                                                      |
                                                      v
                                              P_inventory_top3
                                                      |
                                                      v
                                  Lead Opportunity Score
                                  = P_quality × P_inventory_top3
                                                      |
                                                      v
                                               fallback top-3

Auxiliares fuera del LOS:
- Matching / clusters -> segmentación / interpretación / hipótesis de routing.
- Semantic rules -> Catalog / Inventory QA.
- Response-time RF -> SLA / diagnóstico operacional.
```

## Conclusión

Ninguna de estas tres líneas permanece como gap del assessment.

- Matching / clusters: **cerrado como auxiliar**.
- Semantic rules: **cerrado y rechazado para scoring**.
- Response-time RF: **cerrado y excluido por observabilidad + evidencia**.

El sistema principal permanece sin cambios: Lead Quality + Inventory Availability + LOS + fallback point-in-time.
