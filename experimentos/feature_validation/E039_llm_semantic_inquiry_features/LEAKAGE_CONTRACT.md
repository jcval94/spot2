# Leakage contract — E039

## Unidad temporal

Toda extracción se materializa con `feature_generated_for_score_time`.

### T1

Permitido:

- primer mensaje de inquiry;
- lead fields conocidos al alta;
- Spot consultado;
- Spot attributes seguros;
- availability backward-as-of si la salida es de serviceability/matching y no LeadQuality.

Bloqueado:

- broker response;
- response hours;
- mensajes siguientes;
- scheduled_visit;
- futuros cambios de inventario.

### T2

Permitido:

- mensajes con `inquiry_at <= score_time`;
- snapshots históricos construidos point-in-time.

Bloqueado:

- cualquier mensaje posterior;
- cualquier outcome posterior;
- current-state aggregates retrospectivos.

## Regla de unknown

Ausencia de mención no equivale a negación.

Ejemplo:

`parking = unknown`

no:

`parking = false`.

## Model versioning

Las features LLM deben guardar:

- extractor_version;
- schema_version;
- prompt_version;
- model_identifier;
- generated_at;
- source_message_hash.

Un cambio de prompt/schema/model requiere nueva versión del extractor y revalidación.
