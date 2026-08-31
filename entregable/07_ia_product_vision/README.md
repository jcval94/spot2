# Entregables 7 y 8 — Uso obligatorio de IA + Product Vision

Esta carpeta cierra dos preguntas diferentes pero relacionadas:

1. **¿Dónde aportó valor real la IA/LLM y qué decisiones de governance produjo?**
2. **¿Cómo evolucionaría Spot2 durante tres meses adicionales usando los gaps demostrados por la investigación?**

La autoridad de solución continúa siendo **Codexway**. La historia experimental de IA se reconstruye especialmente desde `experimentos/**` y `AssessmentSol1/llm/**`.

## Entry points oficiales

- [Entregable 7 — Uso obligatorio de IA](01_USO_OBLIGATORIO_IA.md)
- [Entregable 8 — Product Vision ejecutiva, máximo 2 párrafos](04_PRODUCT_VISION_EJECUTIVA.md)

## Anexos

- [Roadmap detallado de Product Vision](02_PRODUCT_VISION.md)
- [Diseño causal y experimentación](03_EXPERIMENTACION_CAUSAL.md)

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

## Relación con el paquete final

El One-Pager ejecutivo ya está cerrado en [../02_one_pager/README.md](../02_one_pager/README.md). La Product Vision oficial es la versión de dos párrafos; el roadmap largo se conserva como anexo.
