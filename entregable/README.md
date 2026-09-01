# Spot2 — Entrega final

**José Carlos Del Valle**

Este paquete presenta una propuesta para ayudar a Spot2 a concentrar su esfuerzo comercial en las oportunidades con mayor posibilidad de avanzar, sin prometer inventario que todavía no puede confirmarse.

## Abrir primero

1. [Deck ejecutivo — PDF, 7 páginas](06_deck_ejecutivo/DECK_EJECUTIVO_SPOT2.pdf)

   La historia completa, la evidencia y la decisión recomendada en 12–15 minutos.
2. [One Pager — PDF, 1 página](02_one_pager/ONE_PAGER_SPOT2.pdf)

   La conclusión en una lectura de 60–90 segundos.
3. [Notebook ejecutado — HTML](../codexway/notebooks/spot2_assessment.html)

   Resultados reproducibles, código plegable y el prompt utilizado para la prueba de IA.

También está disponible el [paquete mínimo para envío](SPOT2_ASSESSMENT_FINAL.zip), que reúne únicamente el deck, el One Pager y el notebook en sus formatos finales.

## Qué encontramos

- El 10% de oportunidades priorizadas por la señal comercial concentra **69% más visitas** que una selección al azar equivalente.
- Al incorporar inventario, el grupo priorizado concentra **37% más visitas** que una selección al azar; sin embargo, la mejora adicional frente a usar sólo la señal comercial **todavía no está demostrada**.
- La información de inventario sí permite tomar mejores decisiones operativas: verificar disponibilidad, proponer alternativas compatibles o reconocer que aún no existe una recomendación defendible.

## Recomendación

**No automatizar todavía.** Primero debe observarse el desempeño con una nueva cohorte sin cambiar la operación. Después, si la señal se mantiene, debe realizarse un experimento controlado con asignación fija por lead para medir impacto real en visitas, alternativas aceptadas y cierres.

La IA queda acotada a **control de calidad del catálogo**. El modelo principal no depende de una API de IA.

## Evidencia y anexos

- [EDA y calidad de datos](01_eda/README.md)
- [Modelo de calidad comercial](03_lead_quality/README.md)
- [Inventario y alternativas](04_inventory_fallback/README.md)
- [Puntaje de oportunidad y operación](05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md)
- [Uso de IA y prompt exacto](07_ia_product_vision/01_USO_OBLIGATORIO_IA.md)
- [Visión ejecutiva de producto](07_ia_product_vision/04_PRODUCT_VISION_EJECUTIVA.md)
- [Matriz de cobertura](MATRIZ_COBERTURA_ASSESSMENT.md)
- [Revisión crítica](REVISION_CRITICA_EVALUADOR.md)

`entregable/**` contiene la narrativa final. `codexway/**` conserva la implementación y la evidencia canónica. Las demás ramas del repositorio documentan pruebas y alternativas históricas; no sustituyen la solución final.
