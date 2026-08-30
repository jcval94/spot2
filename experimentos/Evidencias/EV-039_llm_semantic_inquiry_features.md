# EV-039 — LLM Semantic Inquiry Features

**Estado:** diseño completo / **BLOCKED_BY_DATA_GAP**.

**Experimento:** [E039](../feature_validation/E039_llm_semantic_inquiry_features/)

## Hallazgo que bloquea la ejecución

El esquema real de `inquiries` contiene:

- `message_length`;
- requested area/budget;
- urgency;
- channel;
- asked_visit;
- broker response fields.

Pero no contiene un campo de texto bruto como:

- `inquiry_message_text`;
- `message_text`;
- `message_body`;
- equivalente.

También se buscó en el repositorio y no existe una fuente alternativa de mensaje bruto.

Por tanto, no es posible evaluar honestamente un LLM de semántica de inquiry con el dataset actual.

## Decisión de diseño

No se generará texto sintético desde columnas estructuradas para simular esta señal.

Eso sólo produciría una re-expresión de información ya presente y no probaría que el lenguaje libre añada información incremental.

## Uso futuro propuesto

El LLM no generará una probabilidad de conversión. Producirá variables estructuradas y auditables en tres familias:

1. **Message semantics**
   - intent;
   - maturity/readiness;
   - urgency/timeline;
   - constraints;
   - flexibility;
   - requested actions;
   - specificity/ambiguity.

2. **Lead×Spot semantic compatibility**
   - hard conflicts;
   - soft matches;
   - unknown requirements;
   - semantic fit por dimensión.

3. **Intent trajectory**
   - converging/diverging search;
   - requirement stability;
   - preference convergence;
   - readiness evolution.

El modelo supervisado seguirá siendo responsable de aprender `P(target_scheduled_visit_30d)`.

## Leakage

- T1: sólo texto de la primera inquiry al score time.
- T2: sólo mensajes con `inquiry_at <= score_time`.
- nunca broker response/outcome/future inquiry/future availability.
- ausencia de mención = `unknown`, no `false`.

## Reproducibilidad futura

E039 ya contiene:

- [experiment_spec.json](../feature_validation/E039_llm_semantic_inquiry_features/experiment_spec.json)
- [semantic_feature_schema.json](../feature_validation/E039_llm_semantic_inquiry_features/semantic_feature_schema.json)
- [PROMPT.md](../feature_validation/E039_llm_semantic_inquiry_features/PROMPT.md)
- [LEAKAGE_CONTRACT.md](../feature_validation/E039_llm_semantic_inquiry_features/LEAKAGE_CONTRACT.md)
- [README.md](../feature_validation/E039_llm_semantic_inquiry_features/README.md)

## Relación con el uso LLM actual

E039 no sustituye al Inventory Semantic Quality Auditor mientras el texto de inquiries no exista.

- Inventory Semantic Quality: evaluable con los datos entregados.
- Semantic Inquiry Features: mayor potencial para recuperar T1/T2, pero bloqueado por dato faltante.

## Conocimiento acumulado

Hallazgos promovidos: [DESCUBRIMIENTOS.md](../conocimiento_agregado/DESCUBRIMIENTOS.md).
