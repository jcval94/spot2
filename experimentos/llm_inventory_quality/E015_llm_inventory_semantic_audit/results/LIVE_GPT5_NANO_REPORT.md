# E015 — Live GPT-5 nano report

## Estado

**LIVE COMPLETE / técnicamente válido.**

Run: `33296510774`  
Modelo: `gpt-5-nano`  
Budget hard cap: **USD 1.70**  
Costo acumulado observado: **USD 0.053522**  
Budget conservador reservado: **USD 0.248610**  
Errores API/schema: **0** en holdout y challenge.

## Holdout limpio

N = **240**.

- 240/240 respuestas válidas;
- 0 errores;
- 194 listings marcados como accionables;
- 110 coinciden con Rules v1;
- 84 son incrementales vs Rules v1;
- 117 coinciden con Rules v2;
- 77 son incrementales vs Rules v2;
- input tokens: 193,921;
- output tokens: 70,687;
- costo estándar estimado del holdout: USD 0.03797085;
- latencia mediana: 2.02 s/listing.

Distribución de findings:

| clasificación | count |
|---|---:|
| semantic_cross_field_mismatch | 201 |
| contradiction | 113 |
| consistent | 14 |
| not_verifiable | 13 |
| ambiguous | 5 |
| unsupported_claim | 1 |

## Challenge Land S001

N = **100**:
- 50 casos S001;
- 50 controles;
- conjunto disjunto del discovery sample y del holdout general.

Resultados frente al patrón de discovery S001:

- TP = 38;
- TN = 14;
- FP = 36;
- FN = 12;
- sensitivity = **0.76**;
- specificity = **0.28**;
- precision vs S001 discovery pattern = **0.5135**.

El modelo marcó 74/100 como accionables.

## Interpretación

GPT-5 nano **sí puede ejecutar** la tarea semántica con Structured Outputs de forma estable y a costo despreciable. Sin embargo, el prompt/tamaño de modelo actual tiene un sesgo fuerte hacia sobre-alertar.

La evidencia más clara es el challenge S001:

- recupera 76% de los casos;
- pero dispara sobre 72% de los controles;
- specificity 28% es insuficiente para un QA gate automático.

Los 77 candidatos incrementales sobre Rules v2 en el holdout **no deben interpretarse como 77 verdaderos issues adicionales**. Sin gold labels humanos y dado el exceso de FP en el challenge, una fracción material puede ser sobre-detección.

## Qué demuestra

- Responses API + Structured Outputs funciona para el caso;
- `gpt-5-nano` puede auditar 340 listings con 0 errores;
- costo acumulado del run completo < USD 0.06;
- el modelo tiene sensibilidad útil para semantic discovery;
- el modelo/prompt actual no tiene specificity suficiente para auto-QA.

## Qué no demuestra

- precision/recall humano global;
- que los 77 incrementales vs Rules v2 sean correctos;
- que nano sea superior a Rules v2;
- que el LLM deba bloquear listings automáticamente.

## Decisión

**SUPPORTED como semantic discovery tool.  
NOT_SUPPORTED por ahora como automatic catalog-quality gate.**

El siguiente experimento debe mantener:
- mismo holdout;
- mismo challenge;
- misma taxonomía;
- misma regla de actionability;

y cambiar únicamente el modelo a un challenger más capaz, con presupuesto explícito.
