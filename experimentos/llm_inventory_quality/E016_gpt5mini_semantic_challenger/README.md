# E016 — GPT-5 mini semantic challenger

## Estado

**PRE-REGISTERED / LIVE RUN PENDING**

## Pregunta

¿Un modelo un escalón más capaz reduce el sobre-alertamiento observado con GPT-5 nano cuando se mantiene constante el benchmark semántico?

## Tratamiento

Único cambio intencional frente al live E015 autoritativo:

```text
gpt-5-nano
      ↓
gpt-5-mini
```

Se mantienen:

- mismo prompt E015 v2;
- mismo JSON Schema;
- mismo actionability contract;
- mismo holdout de 240;
- mismo challenge S001 de 100;
- reasoning effort = minimal;
- Responses API;
- Structured Outputs;
- store=false.

## Benchmark de referencia — nano

EV-018:

- S001 sensitivity: 0.76;
- S001 specificity: 0.28;
- S001 precision vs discovery pattern: 0.5135;
- holdout actionable: 194/240;
- incremental vs Rules v2: 77;
- costo live acumulado: USD 0.053522.

## Criterios pre-registrados

### Primary

Mejorar specificity frente a nano.

### Guardrail

Sensitivity S001 >= 0.70.

### Decision bands

**SUPPORTED as stronger semantic reviewer**
- specificity >= 0.70;
- sensitivity >= 0.70;
- 0 API/schema errors or error rate <= 2%;
- costo <= USD 2.00.

**INCONCLUSIVE**
- specificity mejora materialmente vs 0.28, pero queda <0.70;
- o sensitivity <0.70.

**NOT_SUPPORTED as capacity fix**
- specificity no mejora materialmente;
- o costo/error rate viola guardrails.

Incluso si SUPPORTED, el modelo no reemplaza Rules v2 para S001 conocido. El uso potencial sería revisión semántica residual/sampled discovery.

## Budget

Hard cap compartido: **USD 2.00**.

El runner reserva costo máximo conservador antes de cada intento. Si la siguiente llamada puede superar el budget, termina limpiamente y conserva resultados parciales.

## Evidencia

Se registrará en EV-019 después de la corrida.
