# Spot2 — Léeme primero

**José Carlos Del Valle**

Repositorio: <https://github.com/jcval94/spot2>

## Orden recomendado

1. `01_DECK_EJECUTIVO_SPOT2.pdf` — historia completa, evidencia y decisión.
2. `02_ONE_PAGER_SPOT2.pdf` — resumen ejecutivo en una página.
3. `03_NOTEBOOK_SPOT2.html` — recorrido end-to-end ejecutado: lecturas, auditoría, EDA, ABT/feature engineering, modelos, Inventory/fallback, Opportunity, IA y producción, con código plegable.
4. `04_NOTEBOOK_SPOT2.ipynb` — fuente reproducible del mismo recorrido analítico.

El notebook consolidado contiene actualmente **99 celdas totales y 35 celdas de código ejecutadas**. El ZIP se reconstruye y valida automáticamente contra los archivos canónicos del notebook para evitar distribuir una versión desactualizada.

## Conclusión

La señal comercial permite concentrar **69% más visitas** en el 10% priorizado frente a una selección al azar. Inventory se conserva como un segundo eje operativo: no se presenta como mejora incremental de conversión, sino como la señal que permite decidir si una oportunidad debe priorizarse, verificarse, recibir una alternativa o quedar sin recomendación cuando no existe evidencia suficiente.

La lectura ejecutiva es: **Oportunidad = posibilidad de avanzar × posibilidad de atenderla.**

La recomendación es observar la propuesta con datos nuevos sin automatizar y, si la señal se mantiene, validarla mediante un experimento controlado con asignación fija por lead.

El prompt exacto utilizado para la prueba de IA está incluido dentro del notebook, en el capítulo dedicado a IA. La IA se propone únicamente para control de calidad del catálogo; el puntaje principal no depende de ella.
