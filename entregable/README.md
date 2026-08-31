# Spot2 — Entrega final

Este es el punto de entrada recomendado para revisar la solución.

La documentación principal está escrita en **español y en lenguaje de negocio**. Cuando aparece un término técnico necesario para reproducir la solución, se conserva su nombre original entre paréntesis o en formato de código y se explica en palabras sencillas.

## La solución en 30 segundos

Spot2 necesita decidir **qué leads conviene atender primero** sin olvidar una segunda pregunta: **¿existe inventario que realmente pueda atender su necesidad?**

La solución separa esas dos señales:

1. **Calidad del lead:** estima qué tan probable es que el lead avance a una visita agendada.
2. **Capacidad del inventario:** determina si existe un inmueble disponible o una alternativa razonable con la información que se conocía en ese momento.
3. **Puntaje de oportunidad:** combina ambas señales para apoyar la priorización sin esconder la incertidumbre.

La solución final seleccionada es **Codexway**. Las demás líneas de investigación se conservaron como evidencia y aprendizaje, pero no cambian la definición final.

---

## Ruta recomendada de lectura

| # | Documento | Para qué sirve | Abrir |
|---:|---|---|---|
| **1** | **Análisis exploratorio de datos** | Entender los datos, sus limitaciones y los principales hallazgos de negocio. | [Abrir EDA](01_eda/README.md) |
| **2** | **Resumen ejecutivo de una página** | Entender la solución completa en pocos minutos. | [Abrir HTML](02_one_pager/ONE_PAGER_SPOT2_AESTHETIC.html) |
| **3** | **Calidad del lead** | Entender cómo se priorizan los leads y qué tan útil es la señal. | [Abrir](03_lead_quality/README.md) |
| **4** | **Inventario y alternativas** | Entender cómo se decide si una necesidad puede atenderse y qué hacer si el inmueble solicitado falla. | [Abrir](04_inventory_fallback/README.md) |
| **5** | **Puntaje de oportunidad y producción** | Entender cómo se combinan las señales y cómo llevar la solución a operación. | [Abrir](05_opportunity_produccion/README.md) |
| **6** | **Uso de IA y visión de producto** | Entender dónde aportó valor la IA, dónde no, y qué haríamos después. | [Abrir](07_ia_product_vision/README.md) |

### Anexos de evaluación

- [Matriz de cobertura del reto](MATRIZ_COBERTURA_ASSESSMENT.md)
- [Revisión crítica desde la perspectiva del evaluador](REVISION_CRITICA_EVALUADOR.md)

---

## Decisiones principales, explicadas sin jerga

| Tema | Decisión final | Qué significa |
|---|---|---|
| Momento de evaluación | **T1: primera consulta del lead** | Se califica al lead después de registrar su primera solicitud y antes de conocer la respuesta del intermediario. |
| Variable de éxito | **visita agendada** (`scheduled_visit`) | Es una señal temprana de avance comercial. No se presenta como venta ni como cierre. |
| Madurez | **7 días** | Se espera ese periodo para evitar evaluar casos demasiado recientes. |
| Modelo de calidad | **regresión logística estable + calibración Platt** | Se eligió una solución sencilla, reproducible y temporalmente segura. |
| Calidad del lead | **Lift@10 = 1.689x** | El 10% con mayor puntuación concentra aproximadamente **69% más casos positivos** que una selección aleatoria del mismo tamaño. |
| Capacidad operativa | **priorizar el 10% superior** | También se muestran escenarios de 5%, 10% y 20% para adaptar la política a la capacidad del equipo. |
| Inventario | **usar sólo información conocida en ese momento** | Nunca se utiliza un estado futuro del inventario para evaluar una decisión pasada. |
| Vigencia del inventario | **30 días** | Estados más antiguos aumentan la incertidumbre. |
| Dato desconocido | **desconocido no significa no disponible** | La ausencia de evidencia no se convierte automáticamente en una respuesta negativa. |
| Alternativas | **hasta 5 visibles** | Si el inmueble original no sirve, se pueden presentar alternativas razonables; si ninguna es defendible, se devuelve “sin resultado”. |
| Puntaje de oportunidad | **calidad × capacidad de atención conservadora** | Combina la intención comercial con la posibilidad real de atenderla. |
| Oportunidad | **Lift@10 = 1.370x** | Supera una selección aleatoria, aunque no mejora la conversión pura frente a usar sólo Calidad del lead. |
| IA | **control semántico del catálogo** | El LLM ayudó a descubrir problemas de datos, pero no se incorporó al predictor porque no demostró mejora suficiente. |
| Activación | **validación en paralelo antes de automatizar** | Primero se prueba sobre una nueva cohorte sin afectar decisiones; después, si se confirma el valor, se realiza un experimento controlado. |

---

## Qué sí demuestra la entrega

- Existe una señal útil para priorizar leads.
- El inventario necesita tratarse como una fuente temporal y cambiante.
- La incertidumbre del inventario puede hacerse explícita.
- El sistema puede proponer alternativas sin inventar disponibilidad.
- La solución puede llevarse a operación con monitoreo y controles.

## Qué todavía no demuestra

- Que el puntaje cause más ventas.
- Que incorporar inventario mejore la conversión de T1 frente a usar sólo Calidad del lead.
- Que cada alternativa propuesta vaya a ser aceptada.
- Que el sistema deba automatizarse inmediatamente.

Por eso la recomendación final es avanzar con **validación sobre datos nuevos y un experimento controlado**, no con automatización inmediata.

---

## Nota sobre la evidencia técnica

El repositorio conserva implementaciones, experimentos y auditorías más técnicas para garantizar trazabilidad. **No son lectura obligatoria para entender la solución final.** La ruta anterior contiene la narrativa oficial para evaluación.
