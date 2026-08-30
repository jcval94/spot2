# Arquitectura — LLM Semantic Inventory Quality

## Principio

Separar lo que debe ser determinístico de lo que requiere comprensión lingüística.

```text
                         spots
                   title + description
                          |
                          v
                +-------------------+
                | Claim extraction  |
                |       LLM         |
                +---------+---------+
                          |
                          | normalized claims
                          v
spot_attributes ---> +-----------------------+
spots structured --->| Semantic comparison   |
fields                | + deterministic rules|
                     +-----------+-----------+
                                 |
                                 v
                     +-----------------------+
                     | Quality decision      |
                     | GOOD / REVIEW /       |
                     | CRITICAL              |
                     +-----------+-----------+
                                 |
                    +------------+------------+
                    |                         |
                    v                         v
              catalog QA                evidence/report
                    |
              [future only]
                    v
            fallback quality gate
```

## Responsabilidades

### Python / reglas

Python sigue siendo la fuente de verdad para:

- joins `spots <-> spot_attributes`;
- null handling;
- tipos/unidades;
- reglas determinísticas;
- agregación de findings;
- severidad derivada de reglas explícitas;
- caching;
- métricas;
- evaluación contra gold labels.

### LLM

El LLM se limita a:

- interpretar lenguaje;
- reconocer paráfrasis;
- extraer claims;
- asociar claims a una familia de atributos;
- señalar contradicciones basadas en datos presentes;
- abstenerse cuando no pueda verificarlos.

### Humano

La revisión humana es la fuente de verdad para el benchmark:

- define gold labels;
- resuelve ambigüedades;
- valida si un flag es accionable;
- decide si la taxonomía debe ampliarse.

## Contrato de entrada

Ejemplo conceptual:

```json
{
  "spot_id": 24,
  "sector_name": "Office",
  "type_name": "Single",
  "modality": "rent",
  "title": "...",
  "description": "...",
  "attributes": {
    "natural_light": false,
    "security_type": "none",
    "parking_spaces": 9,
    "building_status": "good",
    "amenities": []
  }
}
```

No se envían:

- outcomes;
- lead score;
- historial futuro;
- availability futura;
- información de leads;
- campos que no aportan al audit.

## Contrato de salida

Salida estructurada propuesta:

```json
{
  "spot_id": 24,
  "quality_status": "review",
  "issues": [
    {
      "claim_type": "natural_light",
      "evidence_text": "Amplio espacio con buena iluminación natural.",
      "structured_field": "natural_light",
      "structured_value": false,
      "classification": "contradiction",
      "severity": "high",
      "reason": "The listing explicitly claims natural light while the structured field is false."
    }
  ],
  "abstentions": [],
  "summary": "One high-confidence semantic contradiction."
}
```

Valores controlados:

- `classification`: `consistent | contradiction | unsupported_claim | ambiguous | not_verifiable`;
- `severity`: `low | medium | high | critical`;
- `quality_status`: `good | review | critical`.

## Regla de grounding

Un issue de tipo `contradiction` exige simultáneamente:

1. evidencia textual explícita;
2. un campo estructurado comparable;
3. conflicto entre ambos.

Si falta 2, debe ser `unsupported_claim` o `not_verifiable`, nunca contradicción.

Esto evita que el LLM convierta plausibilidad subjetiva en un error de catálogo.

## Tecnología

### Primera versión

- SDK oficial de OpenAI;
- Responses API directa;
- Structured Output;
- Pydantic/JSON Schema para validación;
- `OPENAIAPI` como secret principal;
- `OPENAI_MODEL` configurable;
- ejecución stateless.

### Por qué no un agente

No hay necesidad actual de:

- tool calling autónomo;
- navegación;
- handoffs;
- memoria;
- loops;
- planificación multi-step.

La propia guía actual del OpenAI Agents SDK distingue este caso: Responses API directa encaja cuando el flujo es corto y la aplicación quiere controlar estado/orquestación; Agents SDK se reserva para loops, tools, guardrails, handoffs o sessions.

### Cuándo reconsiderar Agents SDK

Sólo si evoluciona hacia un sistema que:

- abre tickets de QA;
- consulta fuentes adicionales;
- solicita revisión humana;
- corrige una ficha;
- vuelve a validar;
- coordina distintas herramientas.

Ese sistema sí sería un Inventory QA Agent. Esta propuesta todavía no lo necesita.

## Seguridad operacional

El LLM nunca modifica inventario automáticamente en v1.

```text
LLM flag -> evidence -> QA queue -> human decision
```

Después de validación podría existir auto-pass para `GOOD`, pero `CRITICAL` debe mantenerse revisable y trazable.

## Integración con Lead Opportunity Score

Fase inicial:

```text
Semantic QA
   |
   +----> catálogo / data quality

Lead Quality x Availability
   |
   +----> Opportunity Score
```

Son componentes separados.

Fase futura, sólo con evidencia:

```text
eligible fallback candidates
        |
semantic quality gate
        |
trusted candidates
        |
fallback ranking
```

El audit mejora la confiabilidad del inventario; no reemplaza el scoring.
