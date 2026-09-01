# Spot2 — Entrega final

**José Carlos Del Valle**

Este paquete presenta una propuesta para ayudar a Spot2 a concentrar su esfuerzo comercial en las oportunidades con mayor posibilidad de avanzar, sin prometer inventario que todavía no puede confirmarse.

## Abrir primero

1. [Deck ejecutivo — PDF, 7 páginas](06_deck_ejecutivo/DECK_EJECUTIVO_SPOT2.pdf)

   La historia completa, la evidencia y la decisión recomendada en 12–15 minutos.
2. [One Pager — PDF, 1 página](02_one_pager/ONE_PAGER_SPOT2.pdf)

   La conclusión ejecutiva en una lectura de 60–90 segundos.
3. [Notebook ejecutado — HTML](../codexway/notebooks/spot2_assessment.html)

   Resultados reproducibles, código plegable y el prompt utilizado para la prueba de IA.

También está disponible el [paquete mínimo para envío](SPOT2_ASSESSMENT_FINAL.zip), que reúne únicamente el deck, el One Pager y el notebook en sus formatos finales.

## Qué encontramos

- El 10% de oportunidades priorizadas por Lead Quality concentra **69% más visitas** que una selección al azar equivalente.
- **Quality e Inventory cumplen funciones distintas:** Quality ordena dónde invertir atención; Inventory decide si priorizar, verificar disponibilidad, ofrecer una alternativa o abstenerse.
- El Opportunity Score conservador sigue siendo mejor que el azar para el target histórico (**Lift@10 = 1.37x**), pero **no mejora a Quality-only (1.69x) para anticipar visitas**. Por eso no se presenta Inventory como uplift incremental de conversión.
- La lectura ejecutiva del sistema es: **Oportunidad = posibilidad de avanzar × posibilidad de atenderla**.

## Impacto esperado

Con la misma capacidad comercial, la propuesta permite trabajar primero el grupo con mayor señal y dedicar menos atención inicial a oportunidades menos prometedoras. El inventario convierte esa prioridad en una siguiente acción concreta, sin confundir falta de información con falta de oferta.

## Recomendación

**Usar la señal primero en observación, sin automatizar.** Debe probarse con una nueva cohorte manteniendo la operación actual. Si la señal se sostiene, el siguiente paso es un experimento controlado con asignación fija por lead para medir impacto real en visitas, alternativas aceptadas y cierres.

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
