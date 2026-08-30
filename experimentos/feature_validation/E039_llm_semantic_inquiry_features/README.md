# E039 — LLM Semantic Inquiry Features

## Estado

**BLOCKED_BY_DATA_GAP.**

El experimento está diseñado, pero el dataset candidato actual no contiene texto bruto de la inquiry. Sólo contiene `message_length`.

No se generará texto sintético a partir de las columnas estructuradas para simular esta evidencia: eso no añadiría información y produciría una demostración circular.

## Por qué este uso de LLM sí está justificado

La tarea propuesta no es pedir al LLM que estime conversión.

Es:

```
unstructured commercial language
          ↓
structured, auditable business semantics
```

Python/modelos supervisados siguen siendo responsables de aprender qué variables predicen la target.

## Tres salidas propuestas

### A. Message Semantic Extraction

Una extracción estructurada del mensaje actual:

- transaction intent;
- search maturity;
- visit intent;
- semantic urgency/timeline;
- area/budget/location flexibility;
- explicit constraints;
- requested actions/questions;
- specificity/completeness;
- ambiguity/confidence.

### B. Message × Spot Semantic Compatibility

Cruza requisitos extraídos del mensaje contra el Spot conocido al score time:

- hard constraint conflicts;
- soft preference matches;
- unknown requirements;
- semantic area/budget/location/physical fit;
- conflict/match counts.

### C. Intent Trajectory

Sólo T2. Resume cómo evolucionó el requerimiento usando exclusivamente mensajes anteriores/al score:

- intent evolution;
- search focus convergence;
- preference stability;
- flexibility changes;
- readiness progression.

No usa tiempo absoluto ni número de inquiry como sustituto de progreso.

## Qué NO produce el LLM

No existe:

`llm_conversion_probability`

ni:

`llm_opportunity_score`.

El LLM transforma lenguaje en variables. El modelo supervisado sigue calibrando la probabilidad de `target_scheduled_visit_30d`.

## Criterio de activación

E039 sólo puede ejecutarse cuando exista un campo de texto real y point-in-time, por ejemplo:

`inquiries.inquiry_message_text`.

Ese campo debe contener el contenido visible al momento de la inquiry y no texto generado/modificado con información posterior.

## Relación con el uso LLM actual del assessment

E039 **no reemplaza** al LLM Inventory Semantic Quality Auditor mientras el texto de inquiries no exista.

- Inventory Quality: ejecutable con los datos entregados.
- Semantic Inquiry FE: mayor upside potencial para T1/T2, pero hoy no evaluable honestamente.

## Confirmación

E030 test ya fue consumido por E032/E033. Si E039 se habilita después, la confirmación debe hacerse sobre una nueva cohorte temporal independiente.
