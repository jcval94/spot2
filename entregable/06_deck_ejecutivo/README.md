# Deck ejecutivo de Spot2

- [Abrir deck HTML](DECK_EJECUTIVO_SPOT2.html)
- [Abrir deck PDF](DECK_EJECUTIVO_SPOT2.pdf)

Este es el punto de entrada oficial para presentar la propuesta a un evaluador, Producto o C-Level en 12–15 minutos. Sus siete páginas explican el problema, la evidencia, un caso reproducible, la decisión y el plan de validación.

El HTML es la única fuente editorial. Es autónomo: no carga librerías, fuentes ni imágenes externas. El PDF se genera directamente desde ese archivo y debe conservar exactamente siete páginas.

## Navegación

- `Right`, `Page Down` o `Space`: siguiente página.
- `Left` o `Page Up`: página anterior.
- `Home` / `End`: primera / última página.

## Evidencia

Las cifras se trazan a los resultados canónicos en `codexway/outputs/`. El caso del lead 6 utiliza exclusivamente información disponible al momento de la primera consulta; el fragmento de código conserva los nombres técnicos necesarios para reproducir el cálculo.

La recomendación del deck es observar primero sin cambiar la operación y después ejecutar un experimento controlado con asignación fija por lead. La IA se reserva para control de calidad del catálogo y no participa en el puntaje principal.

## Regeneración

Imprimir el HTML con Chromium en modo headless, usando el tamaño de página definido por el documento, fondos habilitados y sin encabezados del navegador.

`codexway/reports/slides.pdf` permanece intacto como artefacto histórico; no es la versión editorial oficial.
