# Entregable 7 — Uso obligatorio de IA

> ### Lectura en lenguaje claro
> **En una frase:** el LLM ayudó a descubrir problemas semánticos del catálogo, pero no mejoró lo suficiente el predictor; por eso se conserva como herramienta de control de calidad, no como dependencia del puntaje.
>
> Algunos nombres técnicos se conservan porque corresponden a métricas o variables reproducibles. **Lift@10** compara el 10% mejor priorizado contra elegir al azar el mismo número de casos; **target** es el resultado que se quiere anticipar; **point-in-time / as-of** significa usar sólo información que ya era conocida en ese momento; **holdout** es una muestra apartada para evaluación; **shadow** es una ejecución en paralelo que todavía no cambia decisiones reales; y **fallback** es la estrategia de respaldo cuando la opción original no puede recomendarse con suficiente confianza.
>

## 1. Decisión final

El requisito de IA se satisface con un caso real, auditable y económicamente razonable:

**Semantic Inventory Quality / Semantic Rule Discovery.**

La IA no se utiliza para:

- Lead Quality;
- Opportunity Score;
- Availability;
- fallback ranking;
- thresholds;
- explicación determinística del score.

Sí se utiliza para:

- interpretar lenguaje no estructurado de listings;
- descubrir incoherencias semánticas no cubiertas por reglas;
- identificar patrones candidatos a revisión humana;
- ampliar, cuando hay evidencia, una capa determinística de Catalog QA.

La decisión final es:

> **SUPPORTED como herramienta muestreada de semantic discovery / Catalog QA; NOT_SUPPORTED como dependencia del predictor o gate automático.**

Eso no es un fracaso del experimento. Es precisamente el resultado esperado de un proceso de selección gobernado.

---

## 2. Por qué el problema sí justificaba investigar un LLM

El dataset contiene texto libre en title/description y atributos estructurados del Spot.

Eso crea preguntas que una regla literal puede no resolver:

- ¿el copy describe un uso incompatible con el sector?
- ¿una frase aparentemente contradictoria puede ser adaptive reuse?
- ¿hay una incoherencia cross-field que no corresponde a una sola columna?
- ¿el lenguaje aporta una familia de problemas repetible?

Pero antes de pagar inferencia se auditó cuánto lenguaje real había.

### E015 — baseline offline

Sobre 3,000 Spots:

- 856 descripciones exactas únicas;
- 84.37% de filas comparte descripción exacta con al menos otro Spot;
- sólo 12 oraciones distintas componen todo el campo description;
- Rules-only encontró 330 conflictos candidatos en 322 Spots únicos, 10.73% del inventario.

Conclusión:

> El copy era extremadamente templated. Un LLM tenía que demostrar valor **incremental** sobre un baseline determinístico fuerte; reconocer las mismas 12 frases no justificaba una API.

---

## 3. Primer aprendizaje semántico: cross-field coherence

Durante E015 se identificó una categoría que Rules v1 no representaba:

**sector_name = Land + lenguaje de edificio/interiores**.

Ejemplos de la familia:

- “buena iluminación natural”;
- “recién remodelado”;
- “acabados modernos”;
- “listo para ocupar”;
- “acabados de primera”.

No se etiquetó como contradicción factual automática. Se definió como:

**semantic_cross_field_mismatch**.

La proyección sobre el catálogo encontró:

- 230 listings Land con el patrón S001;
- 182 no estaban flaggeados por Rules v1;
- Rules v1: 322 Spots únicos;
- Rules v2 post-discovery: 504;
- incremento potencial: 182 Spots, 6.07% del inventario.

Importante:

- eran **candidatos de revisión**, no errores confirmados;
- la muestra que permitió descubrir S001 dejó de ser válida como holdout;
- se creó un holdout disjunto y un challenge set separado.

Este cambio de diseño es evidencia de buena governance: cuando una muestra participa en discovery, deja de presentarse como confirmatoria.

---

## 4. Arquitectura Rules-first

La investigación convergió a:

    listing
      |
      +--> reglas conocidas
      |
      +--> residual semántico no cubierto
               |
               v
          LLM muestreado
               |
         ¿patrón nuevo?
               |
               v
          revisión humana
               |
         ¿estable y accionable?
               |
               v
          regla determinística

Principio:

> No pagar repetidamente por una semántica que ya puede expresarse con una regla estable.

El LLM se reserva para el long tail.

---

## 5. E017 — piloto real con GPT-5 nano

### Diseño

Muestra fija de 100 Spots:

- 25 Rules-positive;
- 25 Land semantic residual;
- 25 ambiguity challenge;
- 25 clean controls.

Tecnología:

- modelo: **gpt-5-nano**;
- Responses API;
- Structured Outputs;
- JSON Schema estricto;
- batch size 20;
- máximo 100 filas;
- reasoning minimal;
- verbosity low;
- store=false;
- conteo de tokens y costo persistido.

### V1 — contrato rechazado

Resultados:

- 100 registros;
- input tokens: 12,564;
- output tokens: 6,767;
- costo estimado: **USD 0.003335**.

Problema:

El modelo podía devolver combinaciones lógicamente redundantes, por ejemplo incremental_issue=false junto con new_rule_candidate=true.

La respuesta correcta fue **no aceptar el output** y simplificar el contrato.

---

## 6. Prompt exacto autoritativo de E017 V2

El runner real de E017 V2 utilizó exactamente:

> You audit residual semantics in commercial-real-estate listings.
> Literal claims and direct contradictions are already handled by deterministic rules supplied in each record.
> Classify ONLY what remains after those rules.
>
> novelty meanings:
> - no_residual_issue: no meaningful semantic issue remains.
> - covered_by_rules: the apparent problem is already captured by supplied rule flags.
> - residual_ambiguous: a real semantic ambiguity remains, but adaptive reuse or missing ontology prevents calling it actionable.
> - residual_actionable: a cross-field semantic issue remains that should be reviewed and is not already captured by the supplied rules.
>
> Constraints:
> - If novelty is no_residual_issue or covered_by_rules, residual_type MUST be none and new_rule_candidate MUST be false.
> - new_rule_candidate may be true only for a residual_* novelty and only when the pattern looks reusable across multiple listings.
> - Marketing claims without comparable structured fields are not issues.
> - Do not invent facts.
> Return only the strict structured output.

Además, el código validaba en Python las relaciones lógicas entre novelty, residual_type y new_rule_candidate.

Structured Outputs no se utilizó sólo como formato cómodo: fue un mecanismo de contrato y reproducibilidad.

---

## 7. E017 V2 — resultado real

Corrida autoritativa:

- workflow: 33296462871;
- artifact: 9727563377;
- modelo: gpt-5-nano;
- 100 registros;
- input tokens: **12,634**;
- output tokens: **4,869**;
- costo estimado: **USD 0.002579**;
- clean-control incremental issue rate: **0%**;
- new rule candidates: **0/100**;
- residual actionable: **0/100**.

El modelo marcó 28 registros como residual ambiguity, pero esas señales ya podían describirse mediante flags determinísticos utilizados en los challenge strata.

### Decisión

**LLM-derived ABT features = NOT_SUPPORTED.**

La razón no fue costo.

El piloto fue extraordinariamente barato.

La razón fue:

> **no había información incremental suficiente para justificar una dependencia externa, latencia, model drift, mantenimiento de prompt/schema y carga de reproducibilidad.**

---

## 8. Estabilidad técnica y overflagging

La evidencia complementaria live de E015 / PR #19 amplió la prueba:

- 240/240 outputs válidos en holdout;
- 100/100 outputs válidos en challenge;
- 0 errores API/schema;
- costo acumulado observado: **USD 0.053522**;
- S001 sensitivity: **76%**;
- S001 specificity: **28%**;
- precision contra el patrón de discovery: 51.35%.

Interpretación:

### Técnicamente

El flujo fue:

- estable;
- barato;
- compatible con Structured Outputs;
- reproducible a nivel de schema y metadata.

### Semánticamente

El LLM fue demasiado proclive a flaggear controles.

Una specificity de 28% contra el challenge S001 significa que un gate automático generaría demasiadas tareas falsas.

Por eso:

**SUPPORTED for discovery. NOT_SUPPORTED for unattended automatic QA.**

Los 77 candidatos incrementales observados frente a Rules v2 no son 77 errores humanos confirmados.

---

## 9. Un incidente también forma parte de la evidencia

Después de la corrida E017 V2 autoritativa hubo una reejecución:

- run 33296587433;
- fallo: Batch 2 ID mismatch.

Esa corrida no sustituyó la autoritativa.

Lección:

- validar IDs de entrada/salida;
- hacer el proceso idempotente;
- guardar artifacts;
- no seleccionar la corrida conveniente;
- distinguir estabilidad del modelo/API de errores de orquestación/contrato.

---

## 10. Promoción de semántica a reglas determinísticas

El output durable de la investigación fue un sidecar sin API.

Variables/reglas:

- rule_direct_conflict_flag;
- rule_land_building_copy_flag;
- rule_security_ambiguity_flag;
- rule_retail_adaptive_use_flag;
- rule_semantic_ambiguity_flag;
- rule_semantic_signal_count;
- rule_semantic_review_tier.

En 3,000 Spots:

| Señal | N | Share |
|---|---:|---:|
| direct conflict | 322 | 10.73% |
| Land × building copy | 230 | 7.67% |
| security ambiguity | 327 | 10.90% |
| Retail adaptive-use | 109 | 3.63% |
| semantic ambiguity | 429 | 14.30% |
| al menos una señal | 890 | 29.67% |
| dos señales | 91 | 3.03% |

AssessmentSol1 reprodujo estos conteos desde raw data con **0 llamadas OpenAI**.

Esto demuestra que parte del conocimiento descubierto con IA sobrevivió como ingeniería determinística.

---

## 11. E018 — ¿las reglas gratuitas mejoraron Lead Quality?

Se ejecutó una ablation temporal manteniendo:

- target;
- folds;
- población;
- CatBoost;
- hiperparámetros.

Único cambio:

**añadir Semantic Rules.**

Resultado macro:

| Sistema | Lift@10 |
|---|---:|
| baseline | **1.267x** |
| baseline + Semantic Rules | **1.196x** |
| delta | **-0.0716x** |

Bootstrap:

- IC95%: **[-0.1438, +0.1251]**;
- P(delta > 0): 45%.

AP y AUC se movieron ligeramente en punto, pero el Lift@10 no cumplió el gate.

### Decisión

**Semantic Rules = NOT_SUPPORTED para Lead Quality scoring.**

No se hizo búsqueda post-hoc de subconjuntos sobre el mismo OOF para “rescatar” el resultado.

Eso evita multiple testing y selection bias.

---

## 12. El resultado completo de investigación

La secuencia real fue:

    texto no estructurado
      ↓
    baseline de reglas fuerte
      ↓
    semantic discovery
      ↓
    GPT-5 nano real + Structured Outputs
      ↓
    LLM features no aportan información incremental
      ↓
    semántica reutilizable → reglas gratuitas
      ↓
    reglas evaluadas como features predictivas
      ↓
    Lift@10 no mejora
      ↓
    scoring final sin LLM
      ↓
    LLM retenido como sampled Catalog QA discovery

No hubo un salto de “usar LLM” a “poner LLM en producción”.

Hubo una secuencia de hipótesis, gates y rechazos.

---

## 13. Codexway — estado final

Codexway conserva el caso de uso:

**Semantic Inventory Quality Auditor**.

Prompt final de Codexway:

> # Semantic Inventory Quality Auditor
>
> You are a conservative data-quality auditor for commercial real-estate inventory.
> Your task is to compare the human-facing copy of one listing with the structured
> fields supplied in the same payload. Do not browse, infer external facts, or
> rewrite the listing.
>
> Report an issue only when the copy itself provides specific evidence. Distinguish:
>
> - contradiction: text and a structured value cannot both be true;
> - semantic_cross_field_mismatch: the copy describes a materially different
>   property use or physical configuration than the structured record;
> - unsupported_claim: the text makes a claim that the supplied fields cannot
>   verify;
> - not_verifiable: verification would require information outside the payload;
> - ambiguous: the language supports more than one reasonable reading.
>
> Only contradiction and semantic_cross_field_mismatch are actionable for the
> automated QA queue. Unsupported, unverifiable, or ambiguous wording must not be
> promoted as a confirmed data error. Quote the shortest exact evidence fragment.
> Never manufacture a correction. If evidence is insufficient, abstain.
>
> Return only an object conforming to the supplied JSON Schema. Set
> quality_status to critical only for a high-confidence, material actionable
> issue; use review for weaker or non-actionable concerns; otherwise use good.

Codexway añade:

- prompt versionado;
- JSON Schema estricto;
- cache hash de payload + prompt + schema + model;
- metadata de tokens/model/latencia/errors;
- store=false;
- separación entre natural listings y benchmark sintético.

---

## 14. Privacidad

Este punto cambia la interpretación de la solución final.

### Evidencia histórica

E017 demuestra uso real de API sobre 100 registros del piloto.

### Implementación final Codexway

Codexway no envía listings naturales a un endpoint externo sin opt-in de privacidad.

Su estado registra:

**NOT_SENT__EXTERNAL_INVENTORY_PRIVACY_OPT_IN_REQUIRED.**

Para validar comportamiento sin exportar datos del repositorio se usa un benchmark de 40 casos **completamente fabricados**.

Ese benchmark sirve para comprobar:

- task behavior;
- Structured Output;
- detección controlada.

No sirve para afirmar accuracy sobre listings naturales.

### Payload minimizado

La arquitectura de QA no necesita:

- información de leads;
- lead score;
- outcomes;
- futuras inquiries;
- availability futura.

Sólo necesita el subset de campos del listing necesario para la auditoría semántica.

### Producción

Antes de cualquier live natural run deben existir:

- clasificación de datos;
- endpoint/modelo aprobado;
- acuerdo de tratamiento si aplica;
- policy de retention;
- field minimization;
- secrets gestionados;
- auditoría de llamadas;
- store=false cuando el proveedor lo soporte.

---

## 15. Reproducibilidad

El sistema final puede ejecutarse con costo cero.

### Scoring principal

Lead Quality + Inventory + Opportunity:

- no requiere API;
- no requiere prompt;
- no requiere cache LLM;
- no requiere OpenAI key.

### Semantic QA

Rules-first:

- reproduce los patrones conocidos localmente;
- costo 0;
- deterministic.

LLM:

- opt-in;
- cache addressable por hash;
- schema versionado;
- prompt versionado;
- hard budget;
- max rows;
- token accounting.

Un cambio de modelo o prompt produce una nueva versión de evidencia.

---

## 16. Costo

Evidencia real:

| Evidencia | Registros | Modelo | Costo |
|---|---:|---|---:|
| E017 V1 | 100 | GPT-5 nano | USD 0.003335 |
| E017 V2 | 100 | GPT-5 nano | **USD 0.002579** |
| E015 live / PR19 | 340 | GPT-5 nano | **USD 0.053522** |
| AssessmentSol1 Rules | 3,000 | sin LLM | **USD 0** |

El costo no fue el blocker.

El blocker para el predictor fue **información incremental insuficiente**.

El blocker para automatic QA fue **specificity insuficiente / overflagging**.

---

## 17. Riesgos

### Falsos positivos

Más tickets de QA y menor confianza del operador.

### Model drift

La semántica de un modelo puede cambiar entre versiones.

### Prompt drift

Cambios de prompt alteran el benchmark aunque el modelo sea el mismo.

### Privacy

Enviar copy o atributos a un tercero requiere governance.

### Reproducibilidad

Un modelo remoto puede cambiar o ser deprecado.

### Cost amplification

Aunque una muestra sea barata, correr el LLM sobre todo el catálogo y cada actualización innecesariamente convierte un discovery tool en una dependencia recurrente.

### Human-gold gap

Sin labels humanos completos no se puede reportar precision/recall natural real.

---

## 18. Fallback del subsistema de IA

Si:

- no hay API key;
- API está caída;
- budget se agotó;
- el modelo fue retirado;
- schema validation falla;
- privacy no autoriza la llamada;

entonces:

**el Lead Opportunity Score sigue funcionando.**

Semantic QA:

1. ejecuta Rules-only;
2. conserva findings determinísticos;
3. deja el residual LLM como pending/not-run;
4. no bloquea scoring ni fallback comercial.

Un error LLM nunca se convierte en “listing correcto”.

---

## 19. Cómo escalaría

No escalaría como “LLM en cada request”.

Escalaría como:

### Rules-first continuo

Ejecutar reglas en ingest/update del Spot.

### LLM muestreado

Seleccionar:

- residuals no cubiertos;
- nuevas plantillas;
- segmentos con drift semántico;
- listings de alto impacto;
- muestras aleatorias de control.

### Human-in-the-loop

Crear una queue de revisión con:

- evidence_text;
- structured field;
- classification;
- confidence;
- rule/LLM source.

### Promotion loop

Patrones recurrentes y validados:

**LLM → human gold → deterministic rule.**

### Re-evaluación periódica

Medir:

- precision humana;
- novelty;
- rules coverage;
- cost por finding validado;
- overflag rate;
- reviewer workload.

---

## 20. Governance final

| Uso | Decisión |
|---|---|
| LLM como Lead Quality feature | **NO** |
| LLM dentro del Opportunity Score | **NO** |
| LLM para fallback ranking | **NO** |
| LLM como automatic catalog gate | **NO con evidencia actual** |
| LLM para semantic discovery | **SÍ** |
| Rules para Catalog QA | **SÍ** |
| Rules para Lead Quality | **NO** |
| Human validation de patterns | **SÍ** |
| Scoring dependiente de API | **NO** |
| Natural live export sin aprobación de privacidad | **NO** |

---

## 21. Conclusión

La mejor evidencia de uso responsable de IA no es que el LLM aparezca en el score final.

Es que:

- se identificó un problema adecuado para lenguaje;
- se construyó un baseline determinístico fuerte;
- se ejecutó un LLM real;
- se midió costo;
- se corrigió un contrato defectuoso;
- se probaron Structured Outputs;
- se detectó overflagging;
- se rechazaron features sin valor incremental;
- se transformó semántica durable a reglas gratuitas;
- se evaluaron esas reglas;
- se rechazaron también para scoring cuando no mejoraron Lift;
- se dejó el LLM donde sí tiene una ventaja plausible: **semantic discovery**.

Ésa es una decisión de AI governance, no una exclusión cosmética.


---

## 22. Evidencia fuente

- **Codexway — arquitectura principal**
- **Codexway — prompt final**
- **Codexway — schema final**
- **Codexway — evaluación LLM**
- **E015 — LLM Inventory Semantic Audit**
- **E015 — prompt histórico**
- **E017 — GPT-5 nano semantic feature pilot**
- **E017 — runner V2 con prompt exacto**
- **E017 — decisión de features**
- **E018 — Semantic Rules Lift Ablation**
- **AssessmentSol1 — LLM README**
- **AssessmentSol1 — evaluación LLM**
- **AssessmentSol1 — decisión final**
- **AssessmentSol1 — uso de IA**
- **AssessmentSol1 — costos históricos**
