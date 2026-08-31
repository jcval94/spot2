# Entregables 7 y 8 — Uso obligatorio de IA + Product Vision

Esta carpeta cierra dos preguntas diferentes pero relacionadas:

1. **¿Dónde aportó valor real la IA/LLM y qué decisiones de governance produjo?**
2. **¿Cómo evolucionaría Spot2 durante tres meses adicionales usando los gaps demostrados por la investigación?**

La autoridad de solución continúa siendo **Codexway**. La historia experimental de IA se reconstruye especialmente desde `experimentos/**` y `AssessmentSol1/llm/**`.

## Documentos

- [01 — Uso obligatorio de IA](01_USO_OBLIGATORIO_IA.md)
- [02 — Product Vision y roadmap de tres meses](02_PRODUCT_VISION.md)
- [03 — Diseño causal y experimentación](03_EXPERIMENTACION_CAUSAL.md)

## Respuesta ejecutiva

La IA no se forzó dentro del predictor.

El uso defendible quedó en **Semantic Inventory / Catalog QA**:

    reglas determinísticas
      → residual semántico
      → LLM muestreado
      → validación humana
      → patrón repetible
      → regla determinística gratuita

La evidencia real mostró que GPT-5 nano fue barato y técnicamente viable, útil para semantic discovery, pero no produjo información incremental suficiente para justificar features LLM en la ABT y mostró overflagging en una evaluación live complementaria.

Posteriormente, las reglas determinísticas derivadas de la investigación tampoco mejoraron el Lift@10 de Lead Quality. Por eso quedaron como QA de catálogo, no como features del scorer.

La Product Vision parte de esa misma disciplina: **mejor instrumentación, outcomes y causalidad antes que más complejidad**.

## Fuera de alcance

No se construye todavía el One-Pager final.
