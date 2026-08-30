# E015 — LLM Inventory Semantic Audit

**Estado:** ejecución parcial: Fase 0–1 implementadas; evaluación LLM pendiente de `OPENAIAPI` y labels humanos.

## Pregunta

¿Un LLM detecta inconsistencias semánticas accionables entre el copy de un listing y sus atributos estructurados que un baseline determinístico razonable no detecta?

## Diseño

Se compararán tres brazos sobre el mismo gold set humano:

- **A — Rules only**
- **B — LLM only**
- **C — Rules + LLM**

La primera entrega de este experimento implementa y ejecuta la parte que no requiere API:

1. perfilado completo del copy;
2. baseline Rules-only;
3. muestra estratificada para etiquetado humano;
4. prompt, schema y cliente OpenAI listos para ejecución;
5. evaluador preparado para comparar A/B/C cuando existan labels.

## Hallazgo preliminar

El copy es extremadamente repetitivo: el catálogo de 3,000 spots utiliza sólo 12 oraciones únicas en `description`. Esto convierte a Rules-only en un baseline particularmente fuerte y eleva el estándar que debe superar el LLM.

Los resultados reproducibles viven en `results/`.

## Ejecución

Offline:

```bash
python experimentos/llm_inventory_quality/E015_llm_inventory_semantic_audit/run_offline.py
python -m unittest discover -s experimentos/llm_inventory_quality/E015_llm_inventory_semantic_audit/tests
```

Live, después de configurar `OPENAIAPI`:

```bash
export OPENAIAPI="..."
python experimentos/llm_inventory_quality/E015_llm_inventory_semantic_audit/run_live.py \
  --input experimentos/llm_inventory_quality/E015_llm_inventory_semantic_audit/labeling/labeling_sample.csv
```

Evaluación, después del etiquetado humano:

```bash
python experimentos/llm_inventory_quality/E015_llm_inventory_semantic_audit/src/evaluate.py
```

## Regla de interpretación

Un flag es una **inconsistencia candidata**, no una afirmación de que el texto o el campo estructurado sea necesariamente correcto. La acción recomendada es revisión de catálogo, no corrección automática.
