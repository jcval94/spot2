# Entregable 3 — Modelo de Calidad del Lead

## Qué responde

Este componente responde una sola pregunta:

> **Después de recibir la primera consulta de un lead, ¿qué tan probable es que esa consulta termine en una visita agendada?**

La predicción se realiza antes de conocer la respuesta del intermediario y sin utilizar información futura.

## Qué modelo se eligió

La solución final usa una **regresión logística sencilla y calibrada**.

Se probaron alternativas más complejas —incluidos modelos de árboles, modelos por etapas, segmentaciones y variables derivadas con IA—, pero ninguna mostró una ventaja suficientemente estable para justificar más complejidad.

La decisión fue conservar el modelo que ofrecía la mejor combinación de:

- utilidad para priorizar;
- estabilidad en el tiempo;
- facilidad de explicación;
- menor riesgo de utilizar información futura;
- reproducibilidad.

## Resultado principal

En la muestra de evaluación:

| Indicador | Resultado | Interpretación sencilla |
|---|---:|---|
| Proporción de visitas agendadas | **21.22%** | Aproximadamente 1 de cada 5 casos es positivo. |
| Lift@10 | **1.689x** | El 10% mejor puntuado concentra ~69% más positivos que elegir al azar. |
| Recall@10 | **16.98%** | Ese 10% contiene cerca de 17% de todos los positivos. |
| PR-AUC | **0.2391** | Supera la referencia natural de 0.2122, aunque la separación global es moderada. |
| ROC-AUC | **0.5478** | La señal global es limitada; por eso el caso de uso es priorización, no clasificación perfecta. |

El intervalo de confianza de Lift@10 es **1.381x a 1.982x**, lo que apoya que la concentración observada no depende de una sola muestra afortunada.

## Qué significa y qué no significa

**Sí significa:** una forma útil de ordenar leads cuando el equipo no puede atenderlos todos al mismo tiempo.

**No significa:** probabilidad de venta, valor total del cliente ni garantía de que un lead cierre.

La variable de éxito utilizada es una **visita agendada** (`scheduled_visit`), que funciona como señal temprana de avance comercial.

## Por qué no se automatiza todavía

La evaluación histórica fue utilizada durante la investigación, por lo que no debe tratarse como una prueba completamente nueva e independiente.

La siguiente validación debe hacerse con **datos futuros no utilizados durante el desarrollo**, primero en paralelo sin cambiar la operación. Si el resultado se mantiene, entonces puede probarse mediante un experimento controlado.

## Documento detallado

[Leer el documento completo del modelo](MODELO_CALIDAD_LEAD.md)

El documento detallado conserva definiciones, métricas adicionales, controles contra fuga de información futura y trazabilidad metodológica. No es necesario leerlo para comprender la decisión principal.
