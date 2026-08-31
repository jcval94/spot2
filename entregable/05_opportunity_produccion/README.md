# Entregables 5 y 6 — Puntaje de oportunidad y puesta en producción

Esta carpeta explica cómo se combinan **Calidad del lead** e **Inventario** y cómo llevar la solución a una operación real sin perder trazabilidad.

## La idea principal

No conviene esconder todo dentro de un único número.

La solución mantiene visibles tres elementos:

1. **Calidad del lead:** qué tan probable es que avance a una visita agendada.
2. **Capacidad del inventario:** qué tan defendible es que podamos atender su necesidad.
3. **Puntaje de oportunidad:** una combinación conservadora de las dos señales.

En términos técnicos, la versión conservadora se calcula como:

`probabilidad de calidad × capacidad de inventario conservadora`.

## Resultado observado

En la evaluación histórica:

- **Calidad del lead — Lift@10: 1.689x**
- **Puntaje de oportunidad conservador — Lift@10: 1.370x**

Esto significa que ambos superan una selección aleatoria, pero **incorporar inventario no mejora la predicción de visita agendada frente a usar sólo Calidad del lead**.

La interpretación correcta no es “el inventario no sirve”. La interpretación es que existen **dos objetivos de negocio diferentes**:

- si queremos maximizar visitas agendadas con capacidad limitada, usamos Calidad del lead;
- si queremos priorizar oportunidades que además puedan atenderse, usamos Calidad + Inventario y mantenemos ambas señales visibles.

## Qué debe ver la operación

Para cada lead, la salida debería mostrar:

- nivel de Calidad del lead;
- capacidad conocida del inventario;
- nivel de incertidumbre;
- Puntaje de oportunidad;
- motivo de la recomendación;
- acción sugerida.

Ejemplos de acciones:

- **Priorizar:** lead atractivo y necesidad atendible.
- **Verificar inventario:** lead atractivo, pero disponibilidad incierta.
- **Ofrecer alternativa:** el inmueble original no sirve, pero existen opciones compatibles.
- **Sin resultado:** no existe una recomendación defendible.

## Cómo llevarlo a producción

La arquitectura propuesta mantiene los componentes separados para que puedan monitorearse y actualizarse de forma independiente.

La operación necesita, entre otros elementos:

- servicio de cálculo al recibir la primera consulta;
- estado actualizado del inventario;
- registro de la versión del modelo y de la política usada;
- monitoreo de calidad de datos y resultados;
- posibilidad de volver a una versión anterior si aparece un problema;
- registro de cada decisión para poder auditarla.

## Estrategia de lanzamiento

No se recomienda encender la automatización directamente.

1. **Ejecución en paralelo:** calcular resultados sobre datos nuevos sin cambiar la operación.
2. **Validación:** comprobar que la señal, la calibración y la salud del inventario se mantienen.
3. **Experimento controlado:** comparar la política nueva contra el proceso actual.
4. **Escalamiento gradual:** ampliar sólo si el beneficio es real y no empeora la experiencia ni la carga operativa.

## Documentos de detalle

- [Puntaje de oportunidad](01_LEAD_OPPORTUNITY_SCORE.md)
- [Arquitectura de producción](02_ARQUITECTURA_PRODUCCION.md)
- [Monitoreo, gobierno y manejo de fallos](03_MONITOREO_GOBIERNO_RUNBOOK.md)

Estos documentos conservan fórmulas, métricas y controles para una revisión técnica más profunda.
