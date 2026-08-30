# E015 — Live GPT-5 nano benchmark

## Estado

**LIVE COMPLETE.**

Corrida autoritativa: `33296510774`  
Modelo: `gpt-5-nano`  
Hard budget: **USD 1.70**  
Costo acumulado observado: **USD 0.053522**  
Budget conservador reservado al final: **USD 0.248610**

## Holdout limpio — N=240

- 240/240 respuestas válidas;
- 0 errores API/schema;
- 194/240 listings marcados accionables;
- overlap con Rules v1: 110;
- incrementales vs Rules v1: 84;
- overlap con Rules v2: 117;
- incrementales vs Rules v2: 77;
- input tokens: 193,921;
- output tokens: 70,687;
- costo estimado del holdout: USD 0.03797085;
- latencia mediana: 2.02 s/listing.

Findings:

| classification | count |
|---|---:|
| semantic_cross_field_mismatch | 201 |
| contradiction | 113 |
| consistent | 14 |
| not_verifiable | 13 |
| ambiguous | 5 |
| unsupported_claim | 1 |

Los incrementales vs Rules **no son gold positives**.

## Challenge S001 — N=100

Diseño:
- 50 Land con patrón S001;
- 50 controles Land;
- disjunto del discovery sample y del holdout.

Resultado:

- TP = 38;
- TN = 14;
- FP = 36;
- FN = 12;
- sensitivity = **76%**;
- specificity = **28%**;
- precision vs discovery pattern = **51.35%**.

El modelo marcó 74/100 como accionables.

## Lectura

GPT-5 nano demostró que el pipeline LLM puede ser:
- estable;
- barato;
- estructurado;
- sensible a anomalías semánticas.

Pero su specificity es demasiado baja para un gate automático. El problema principal es sobre-alertamiento, no costo ni estabilidad.

Esto es compatible con EV-017: cuando el problema se restringe a **semántica residual después de reglas conocidas**, el piloto no encontró una nueva familia accionable. E015 broad audit, al permitir una búsqueda semántica más amplia, produce muchos candidatos adicionales, pero el challenge muestra que muchos pueden ser falsos positivos.

## Decisión

- **SUPPORTED:** LLM como semantic discovery / exploration.
- **NOT_SUPPORTED:** GPT-5 nano como automatic catalog-quality gate.
- **NO CLAIM:** los 77 incrementales vs Rules v2 son verdaderos issues.

Siguiente prueba justa: mismo prompt, schema, holdout y challenge con un modelo más capaz; cambiar sólo la capacidad del modelo.
