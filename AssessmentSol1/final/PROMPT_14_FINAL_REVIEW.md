# PROMPT 14 — Final review, red-team y decisión READY TO SUBMIT

Continúa trabajando exclusivamente dentro de `AssessmentSol1/**`.

No modifiques ninguna ruta exterior.

Sólo ejecuta esta fase si Prompt 13 terminó con:

`FINAL ASSESSMENT BUILT — CONTINUE TO PROMPT 14`.

Prompt 14 NO es una fase de investigación ni optimización.

NO:
- cambies target;
- cambies scoring moment;
- cambies splits;
- cambies features/modelo por métricas;
- reabras recovery;
- cambies Inventory/fallback/Opportunity/capacity;
- busques más Lift;
- reabras Semantic Rules;
- consumas el procedural holdout para seleccionar decisiones.

Su función es auditar coherencia, reproducibilidad y calidad de la entrega.

## 1. Authorities obligatorias

Comprueba:

- `models/lead_quality_recovery/RECOVERY_DECISION.md` = RECOVERED;
- `recovery_downstream/POST_RECOVERY_FINAL_STATE.json` = FROZEN;
- Opportunity Score reconstruido post-recovery;
- capacity policy reconstruida post-recovery;
- `audit/final_audit.json` ejecutado post-recovery y con 0 blockers;
- `llm/results/prompt12_gate.json` = PASS.

Autoridades actuales esperadas:

- Lead Quality: `LQ_RECOVERY_R4_STATIC_MATCH_V1`;
- target: `T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1`;
- Opportunity Score: `OPPORTUNITY_ACTIONABILITY_GATE_V2_FROZEN_2026-08-30`;
- formula: `lead_quality_probability * inventory_actionability_gate`;
- capacity: P80 / top20 T1;
- fallback: K=3;
- Semantic Rules: excluded from Lead Quality.

## 2. Post-Recovery consistency check

Audita conjuntamente:

- notebook;
- HTML notebook;
- one-pager;
- presentation HTML;
- Assessment Report;
- README;
- frozen configs;
- reproducibility docs.

Todos deben usar el champion post-recovery.

Busca especialmente referencias accidentales a:
- Base Rate como champion actual;
- CatBoost como champion actual;
- métricas anteriores a Prompt 11.5;
- Opportunity Score V1;
- `P_quality × InventoryServiceability` como score vigente;
- P85/top15 como capacity final;
- K distinto de 3;
- Semantic Rules como feature final de Lead Quality.

Cualquier métrica/modelo stale es **BLOCKER**.

## 3. Source-of-truth audit

Clasifica cada número importante del entregable como:

- `ASSESSMENTSOL1_FROZEN`;
- `ASSESSMENTSOL1_REPRODUCED`;
- `UPSTREAM_SUPPORTING`;
- `DIAGNOSTIC_ONLY`.

E018/E019/E020 no pueden aparecer implícitamente como resultados finales de AssessmentSol1.

Si un valor histórico coincide con clean-room:
- puede declararse como corroboración.

Si difiere:
- debe prevalecer clean-room.

## 4. Arquitectura final upstream-aware

Comprueba que la entrega NO reabra líneas cerradas:

- Matching/clusters = **AUXILIARY**;
- Semantic Rules = **INVENTORY/CATALOG QA**;
- Response-time RF = **DIAGNOSTIC ONLY**.

Si alguno aparece como componente central del Lead Opportunity Score sin nueva evidencia clean-room:

**BLOCKER**.

## 5. Preguntas metodológicas obligatorias

La entrega debe permitir responder claramente:

- ¿Por qué elegiste este scoring moment final?
- ¿Por qué elegiste esta target?
- ¿Por qué esta arquitectura de Lead Quality?
- ¿Por qué este modelo frente al baseline?
- ¿Qué cambió durante el recovery de Lift?
- ¿Por qué el modelo recuperado no contiene leakage?
- ¿Qué tan fuerte es realmente la señal recuperada?
- ¿Por qué esta capacity policy?
- ¿Por qué este K de fallback?
- ¿Por qué integrar Quality e Inventory?
- ¿Por qué el resultado NO es una probabilidad conjunta calibrada?
- ¿Cuándo usarías Lead Quality en vez de Lead Opportunity Score?
- ¿Qué ocurre cuando Inventory no puede servir al lead?
- ¿Qué harías con NO_RESULT?
- ¿Cuál es el papel real del LLM?
- ¿Por qué Semantic Rules no entraron al scorer?
- ¿Qué evidencia es clean-room y cuál sólo upstream?
- ¿Qué no puedes concluir de este assessment?

No hagas preguntas prescriptivas sobre T1/CatBoost salvo que correspondan al sistema final.

En el estado actual:
- el scoring moment sí es T1, por lo que incluye defensa específica de T1;
- el champion NO es CatBoost, por lo que no presentes una defensa de CatBoost como modelo final.

## 6. Lead Quality recovery audit

Verifica:
- target/split no cambiaron para recuperar Lift;
- Availability no entra a Lead Quality;
- las features del champion son observables al scoring moment;
- validation es temporal;
- junio no se usó para selection;
- Lift@10 > 1 en 4/4 folds;
- Lift@20 > 1 en mayoría de folds;
- incertidumbre está visible;
- top5 weakness no está ocultada.

## 7. Opportunity Score audit

La entrega debe distinguir:

### Lead Quality
Propensión relativa al outcome objetivo.

### Inventory
Capacidad de servicio/actionability.

### Opportunity Score
Priorización operacional cuando ambas dimensiones importan.

Comprueba que no se llame al score:
- “joint calibrated probability”;
- “probability of conversion and availability”;
- equivalentes probabilísticos no demostrados.

Comprueba que se explique el rechazo post-recovery de la multiplicación continua:
- Lead Quality recuperado ya incluye matching context;
- multiplicar InventoryServiceability continuo generaba double counting;
- V2 conserva únicamente actionability gate dentro del score;
- Inventory continuo permanece como output separado.

## 8. Trade-off audit

Comprueba que notebook/presentación no oculten el trade-off:

- Lead Quality maximiza la prioridad por progression outcome;
- Lead Opportunity incorpora servicio operativo;
- una integración más agresiva puede concentrar oportunidades serviceable pero sacrificar positivos de Quality puro.

Debe quedar clara la regla de uso:

- “maximize scheduled visits regardless of inventory” → Lead Quality;
- “progress + serviceability” → Opportunity Score.

## 9. Capacity audit

Verifica:
- policy final = P80/top20 T1;
- frontier 5/10/15/20 correctamente representada;
- no se copió top15/P85 de E019 como autoridad final;
- selección proviene de DEVELOPMENT OOF;
- procedural holdout no participó;
- bandas rank-based manejan ties correctamente.

## 10. Fallback audit

Verifica:
- K=3;
- fallback corto;
- restricciones gobernadas;
- `NO_RESULT` permitido;
- no se relaja indefinidamente para fabricar cobertura;
- no se afirma precision histórica artificial desde `days_until_available`;
- cualquier evidencia E020 se identifica como supporting.

## 11. LLM audit

Verifica que los entregables demuestren:
- uso real de IA;
- prompt;
- Structured Outputs;
- costo;
- resultado negativo útil;
- Rules-first;
- human precision/recall unavailable;
- E017/E018 canónicos;
- PR #19 supplemental/open;
- score principal sin dependencia live de OpenAI.

Semantic Rules deben permanecer:
`EXCLUDE FROM LEAD QUALITY SCORING / KEEP FOR INVENTORY-CATALOG QA`.

## 12. Reproducibility audit

Comprueba:
- instrucciones de ejecución claras;
- paths relativos correctos;
- outputs bajo `AssessmentSol1/**`;
- ninguna dependencia runtime de `experimentos/**`;
- ningún fitted artifact histórico importado;
- score principal reproducible sin API key OpenAI;
- filesystem isolation respetado;
- hashes/configs congelados referenciados cuando sea útil.

Si el runtime exacto de Polars/pytest sigue sin haberse ejecutado después del último cambio material:
- mantenlo como limitación explícita;
- si el entorno disponible permite ejecutarlo ahora, ejecútalo;
- si falla por un bug real, BLOCKER;
- si no puede ejecutarse por limitación del entorno, no inventes PASS.

## 13. Deliverable quality audit

Revisa:
- que el notebook tenga una narrativa lineal;
- que el HTML renderice correctamente;
- que el one-pager pueda entenderse sin el notebook;
- que presentation/index.html funcione de forma standalone;
- que charts tengan títulos/ejes/leyendas legibles;
- que no haya paths rotos;
- que no haya lorem ipsum, TODOs, placeholders o texto experimental;
- que el Assessment Report no contradiga frozen configs;
- que README sea un verdadero entry point.

## 14. BLOCKER taxonomy

Es BLOCKER cualquiera de:

- target/model/split stale;
- downstream score stale;
- capacity stale;
- métricas stale;
- leakage real;
- utilización del procedural holdout para selección post-recovery;
- Semantic Rules como Lead Quality;
- matching/clusters como core scorer sin evidencia;
- response-time RF como core scorer;
- Opportunity Score presentado como probabilidad conjunta calibrada;
- deliverable faltante;
- HTML roto;
- filesystem violation;
- runtime dependency en `experimentos/**`;
- LLM requirement incompleto;
- inconsistencia entre README/report/slides/notebook/configs.

No marques como BLOCKER una limitación científica ya aceptada y bien documentada.

## 15. Final Decision

`READY TO SUBMIT` requiere:

- `RECOVERY_DECISION` = RECOVERED;
- `POST_RECOVERY_FINAL_STATE` = FROZEN;
- Opportunity Score reconstruido después del recovery;
- capacity policy reconstruida después del recovery;
- final leakage audit ejecutado después del recovery;
- cero métricas stale;
- notebook presente;
- notebook HTML presente;
- one-pager presente;
- presentation/index.html presente;
- Assessment Report presente;
- LLM prompt / schema / evidence presentes;
- reproducibilidad documentada;
- filesystem isolation PASS;
- cero BLOCKERS.

Si todo pasa, crea un estado final machine-readable bajo `AssessmentSol1/final/**` y termina exactamente con:

`READY TO SUBMIT`

Si existe cualquier BLOCKER:

documenta:
- blocker;
- evidencia;
- artifact afectado;
- corrección necesaria;

y termina exactamente con:

`DO NOT SUBMIT — BLOCKERS REMAIN`
