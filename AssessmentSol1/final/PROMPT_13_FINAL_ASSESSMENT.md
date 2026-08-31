# PROMPT 13 — Construcción del assessment final (post-recovery)

Continúa trabajando exclusivamente dentro de `AssessmentSol1/**`.

No modifiques ninguna ruta exterior.

La investigación, el sistema post-recovery y el requisito LLM ya están congelados.

NO:
- cambies target;
- cambies scoring moment;
- cambies splits;
- agregues features;
- cambies Lead Quality;
- cambies calibrador;
- cambies Inventory;
- cambies fallback;
- cambies Opportunity Score;
- cambies capacity policy;
- busques más Lift;
- reabras Semantic Rules para scoring;
- conviertas esta fase en investigación adicional.

Si encuentras un bug metodológico real:
1. documenta la incidencia;
2. DETÉN el packaging afectado;
3. corrígelo únicamente si puede hacerse sin violar los contratos congelados;
4. vuelve a ejecutar los gates downstream relevantes antes de continuar.

## 0. Gate post-recovery obligatorio

Antes de construir cualquier entregable final, verifica que existan y sean consistentes:

- `models/lead_quality_recovery/RECOVERY_DECISION.md`;
- `recovery_downstream/POST_RECOVERY_FINAL_STATE.json`;
- Opportunity Score reconstruido con el champion recuperado;
- capacity policy post-recovery;
- `audit/final_audit.json` reejecutado después del recovery;
- `llm/results/prompt12_gate.json`.

El estado esperado del clean-room actual es:

- Lead Quality: `LQ_RECOVERY_R4_STATIC_MATCH_V1`;
- target: `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`;
- Opportunity Score: `OPPORTUNITY_ACTIONABILITY_GATE_V2_FROZEN_2026-08-30`;
- fórmula: `lead_quality_probability * inventory_actionability_gate`;
- capacity: `P80 / top 20% within T1`;
- fallback: `K=3`;
- final audit: `READY`, 0 blockers;
- LLM gate: PASS.

Si Lead Quality cambió y cualquier artifact downstream todavía usa predicciones del modelo anterior:

**DETÉN ESTA FASE.**

No construyas notebook, HTML, one-pager o presentación con resultados obsoletos.

## 1. Source of truth

Los números finales deben proceder exclusivamente de artifacts congelados de:

`AssessmentSol1/**`.

E018/E019/E020 y otros experimentos históricos son:

**UPSTREAM SUPPORTING EVIDENCE.**

No copies sus métricas como si fueran resultados de AssessmentSol1 salvo que hayan sido reproducidas dentro del clean-room final.

Cuando coincidan:
- puedes decir que AssessmentSol1 replica/confirma la evidencia previa.

Cuando difieran:
- manda AssessmentSol1;
- documenta claramente la diferencia;
- explica por qué el clean-room final es la autoridad.

## 2. Objetivo

Transforma AssessmentSol1 en una entrega única, coherente, fácil de evaluar y orientada a decisión.

El evaluador NO debe navegar decenas de experimentos para entender la solución.

Debe poder responder rápidamente:
1. qué problema resuelve el sistema;
2. cuándo scorea;
3. qué target predice;
4. cómo evita leakage;
5. cuál es el Lead Quality final;
6. cómo representa Inventory;
7. cómo funciona fallback;
8. qué significa Opportunity Score;
9. qué capacidad operativa se recomienda;
10. qué aporta el LLM y por qué no está dentro del predictor;
11. cuáles son las limitaciones;
12. cómo reproducirlo.

## 3. Narrativa principal

Cuenta aproximadamente:

1. Business problem
2. Scoring moment
3. Data
4. Target
5. Temporal design
6. Leakage prevention
7. EDA / data quality
8. ABT
9. Feature Engineering
10. Lead Quality
11. Recovery de Lead Quality
12. Inventory Serviceability
13. Fallback
14. Lead Opportunity Score
15. Capacity frontier / policy
16. End-to-end evaluation
17. LLM / AI use
18. Limitations
19. Production / scalability vision
20. Reproducibility

No conviertas la entrega en un diario de experimentos.

## 4. Lead Quality

Usa exclusivamente el champion post-recovery congelado.

Explica:
- por qué fue necesario Prompt 11.5;
- qué bug/leakage fue descartado;
- cómo se recuperó señal real sin reabrir target/splits;
- por qué el champion final es una Logistic pequeña y regularizada;
- qué features usa;
- por qué no usa Availability;
- qué tan fuerte/débil es realmente la señal.

Métricas finales deben salir del clean-room post-recovery.

No presentes el antiguo Base Rate como champion actual.

El antiguo estado pre-recovery puede aparecer sólo como contexto histórico de por qué se abrió el recovery.

## 5. Semantic Rules

Decisión cerrada:

`Semantic Rules = EXCLUDE FROM LEAD QUALITY SCORING / KEEP FOR INVENTORY-CATALOG QA`.

No presentar E018 como pendiente.

E018 histórico de referencia:
- baseline macro Lift@10 = 1.267x;
- Rules = 1.196x;
- Δ = -0.0716x;
- NOT_SUPPORTED.

No es necesario mostrar todos los números en slides; basta con la decisión salvo que aporten a la historia.

No busques subconjuntos de reglas post-hoc para rescatar Lift sobre el mismo histórico.

## 6. Matching / clusters / response-time

Mantén la arquitectura final upstream-aware:

- Matching / clusters = **AUXILIARY**;
- Semantic Rules = **INVENTORY / CATALOG QA**;
- Response-time Random Forest = **DIAGNOSTIC ONLY**.

No los presentes como componentes centrales del Lead Opportunity Score salvo evidencia clean-room nueva, que esta fase no debe producir.

## 7. Inventory / Availability / Fallback

Consulta E019/E020 como evidencia histórica reciente, no como source of truth final.

La evidencia upstream favorece conceptualmente:
- Availability point-in-time mediante backward as-of;
- probabilidad explícita de disponibilidad a 30 días;
- no crear precisión artificial usando `days_until_available`;
- fallback corto;
- máximo histórico recomendado K=3;
- `NO_RESULT` antes que relajar indefinidamente.

Pero los valores finales del assessment deben proceder de AssessmentSol1.

El clean-room actual reproduce y congela:
- Inventory scalar PIT;
- fallback máximo `K=3`;
- `NO_RESULT` cuando no existe alternativa gobernada.

Preséntalo como decisión final y explica que K=3 fue revalidado post-recovery dentro de AssessmentSol1.

No presentes el histórico E020 como si hubiera definido directamente el valor final.

## 8. Opportunity Score

Preserva estrictamente la distinción conceptual:

### Lead Quality
¿Quién muestra mayor propensión al outcome objetivo?

### Inventory Availability / Serviceability
¿Tenemos capacidad de servicio?

### Lead Opportunity
¿Dónde coinciden ambas?

E020 cerró históricamente la idea:

`P_quality × P_inventory_top3`

como integración conceptual, NO como probabilidad conjunta perfectamente calibrada.

Sin embargo, después del recovery AssessmentSol1 detectó double counting porque Lead Quality ya contiene contexto del Spot seleccionado.

Por eso el score canónico final NO es el producto histórico E020.

El clean-room final usa:

`Opportunity Score V2 = lead_quality_probability × inventory_actionability_gate`.

El Inventory Serviceability continuo se reporta por separado.

La razón debe quedar explícita:
- mantener servicio/actionability en la priorización;
- evitar volver a multiplicar fuerza de matching ya presente en Lead Quality;
- no reclamar una probabilidad conjunta que no fue calibrada como tal.

NO llames al Opportunity Score:

“probability of conversion and availability”.

Llámalo:

**Opportunity Score**.

## 9. Trade-off Quality vs Opportunity

La presentación y notebook deben mostrar el trade-off observado en AssessmentSol1.

El diagnostic rechazado `P_quality × InventoryServiceability` mostró que una integración más agresiva podía concentrar serviceability/joint positives mientras degradaba la captura de Lead Quality puro.

Esta tensión es esencial.

Si el objetivo de Growth es:

**maximize scheduled visits regardless of inventory**

→ usar **Lead Quality**.

Si el objetivo es:

**prioritize leads likely to progress AND serviceable with current/fallback inventory**

→ usar **Lead Opportunity Score**.

No escondas este trade-off.

Aclara que V2 fue diseñado precisamente para conservar actionability sin introducir el double counting del producto continuo rechazado.

## 10. Capacity

No hardcodees top 10%.

No copies P85/top15 de E019 como default final.

La política canónica post-recovery de AssessmentSol1 es:

`P80 / top 20% within T1`.

Usa la frontier 5/10/15/20% cuando sea útil.

Explica:
- top5 permanece débil;
- 10/15/20 superan Lift 1;
- top20 fue congelado por mejor combinación clean-room de Lift y recall entre capacidades operativamente viables;
- bandas finales son rank-based debido a ties reales.

Todos los números deben venir de `recovery_downstream/CAPACITY_REEVALUATION.csv`, `opportunity_score/frozen_score_config.json` o artifacts post-recovery equivalentes.

## 11. LLM / IA

Usa exclusivamente el cierre autocontenido de `AssessmentSol1/llm/**`.

Narrativa recomendada:

“We used an LLM where the dataset genuinely contained unstructured language. A Rules-first baseline captured repeatable inconsistencies deterministically. The LLM was inexpensive and technically reliable as a semantic discovery tool, but neither LLM-derived features nor the resulting deterministic semantic rules demonstrated incremental Lead Quality ranking value. Therefore the production Lead Opportunity Score remains independent of LLM inference. The LLM is retained as a sampled Catalog/Inventory QA discovery tool.”

Debe demostrarse:
- uso real;
- prompt real;
- Structured Outputs;
- costo;
- resultado;
- limitaciones;
- Rules-first;
- por qué no entra al score.

No inventes human gold.

## 12. Entregables finales

Construye dentro de `AssessmentSol1/final/**` como mínimo:

- notebook final ejecutable;
- HTML del notebook;
- executive one-pager;
- presentation HTML con `index.html`;
- Assessment Report;
- reproducibility / run instructions;
- artifact/source-of-truth index.

El README raíz de AssessmentSol1 debe dirigir al evaluador hacia estos entregables sin obligarlo a navegar carpetas experimentales.

## 13. Visuales

Prioriza pocos visuales con función clara:

- temporal/scoring design;
- Lead Quality performance y recovery;
- capacity frontier;
- Inventory/fallback behavior;
- Quality vs Opportunity trade-off;
- Opportunity Score / priority distribution;
- LLM Rules-first decision;
- architecture/end-to-end flow.

No llenes slides con métricas históricas que no son clean-room authority.

## 14. Limitaciones obligatorias

Mantén visibles:
- procedural holdout June = non-pristine / diagnostic-only;
- top5 Lead Quality Lift < 1;
- incertidumbre amplia del recovery;
- precios actuales de Spot no versionados → budget fit bloqueado/unknown;
- score ties reales → rank-based bands;
- no causal/commercial conversion claim;
- Opportunity Score no es probabilidad conjunta calibrada;
- LLM human precision/recall unavailable.

## 15. Final consistency pass

Antes de cerrar Prompt 13, verifica que:

- notebook;
- notebook HTML;
- one-pager;
- presentation;
- Assessment Report;
- README;
- frozen configs citados;

usen el champion post-recovery.

Busca explícitamente:
- `BASE_RATE` presentado como champion actual;
- CatBoost presentado como champion actual sin serlo;
- Opportunity Score V1 como vigente;
- P85/top15 como política final;
- fallback K distinto de 3;
- Semantic Rules dentro de Lead Quality;
- métricas históricas E018/E019/E020 presentadas como clean-room finales.

Cualquier inconsistencia encontrada es BLOCKER de packaging.

## Gate Prompt 13

Sólo cierra esta fase si:
- todos los entregables fueron construidos;
- todos usan source of truth post-recovery;
- no hay métricas stale;
- el score sigue reproducible sin llamada live a OpenAI;
- no se reabrió investigación.

Salida final esperada:

`FINAL ASSESSMENT BUILT — CONTINUE TO PROMPT 14`
