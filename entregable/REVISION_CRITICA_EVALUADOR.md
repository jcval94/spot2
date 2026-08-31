# Revisión crítica final — perspectiva del evaluador

## Dictamen ejecutivo

La entrega presenta una sola solución coherente y deja claro qué partes están demostradas y cuáles todavía necesitan validación.

**Conclusión:** la solución está suficientemente cerrada para ser evaluada como propuesta técnica y de producto. **Todavía no debe presentarse como una automatización lista para producción**, porque falta comprobar su impacto con datos nuevos y un experimento controlado.

## Lo más sólido de la propuesta

### 1. La decisión se toma en un momento bien definido

El lead se evalúa en **T1: después de registrar su primera consulta y antes de conocer la respuesta del intermediario**.

La señal de éxito es una **visita agendada** (`scheduled_visit`) durante esa primera consulta, esperando 7 días para que el resultado madure.

Esto evita usar información que sólo apareció después de la decisión.

### 2. Se protege explícitamente contra información futura

La solución no se limita a separar entrenamiento y evaluación por fechas. También impide utilizar:

- respuestas posteriores del intermediario;
- consultas futuras del mismo lead;
- estados futuros de disponibilidad;
- atributos actuales como si siempre hubieran sido iguales;
- información de mercado cuya fecha efectiva no puede reconstruirse.

Para disponibilidad, la regla es sencilla: **usar el último estado conocido hasta ese momento, nunca uno posterior**.

### 3. El modelo final es simple por una razón

Se probaron alternativas más complejas, pero la solución final conserva una regresión logística estable porque ofrece una señal reproducible, interpretable y temporalmente defendible.

Su resultado operativo más importante es:

- **Lift@10 = 1.689x**
- intervalo de confianza de **1.381x a 1.982x**

En palabras sencillas: el 10% de leads mejor puntuados concentra aproximadamente **69% más visitas agendadas** que elegir al azar el mismo número de casos.

### 4. No se confunde “buen lead” con “inventario disponible”

La propuesta separa dos preguntas:

1. **¿Qué tan probable es que este lead avance?**
2. **¿Podemos atender razonablemente su necesidad con el inventario conocido?**

Esta separación es una fortaleza porque un lead atractivo puede no tener inventario atendible, y un inmueble adecuado puede existir para un lead poco prometedor.

### 5. La incertidumbre del inventario se muestra, no se oculta

Una regla central es:

> **Desconocido no significa no disponible.**

Si la información de un inmueble es antigua o incompleta, el sistema reduce su confianza. No convierte automáticamente la falta de evidencia en una respuesta negativa.

Si el inmueble original no funciona, puede proponer alternativas. Si ninguna es defendible, devuelve **sin resultado** en lugar de fabricar una recomendación.

### 6. Los resultados negativos también forman parte de la decisión

La investigación no presenta cada experimento como un éxito.

Entre las ideas que **no** se promovieron están:

- modelos más complejos que no mostraron estabilidad suficiente;
- variables derivadas con un LLM;
- reglas semánticas que no mejoraron la priorización;
- segmentos locales interesantes pero no confirmados;
- la afirmación de que Inventario ya mejora la conversión T1.

Esto fortalece la entrega porque demuestra selección, no acumulación de experimentos.

## Las principales limitaciones

### 1. La señal global del modelo es moderada

El ROC-AUC es **0.5478**, por lo que el modelo no separa perfectamente casos positivos y negativos.

La defensa correcta no es ocultarlo: el valor observado está principalmente en **ordenar mejor la parte superior de la lista**, no en clasificar con precisión a toda la población.

Por eso Lift@10 es más relevante para el caso de uso que presentar AUC como única métrica.

### 2. La muestra histórica de evaluación no es completamente nueva

El conjunto histórico fue consultado durante la investigación general. Por ello, sus resultados deben verse como evidencia retrospectiva, no como una confirmación totalmente independiente.

La mitigación propuesta es correcta: **probar primero con una cohorte futura no utilizada durante el desarrollo**.

### 3. La visita agendada no es una venta

`scheduled_visit` es una señal temprana de avance comercial. No mide cierre, ingresos ni valor total.

La solución debe presentarse como priorización de progreso comercial temprano.

### 4. Inventario todavía no demuestra mejora incremental sobre esa señal

El Puntaje de oportunidad conservador obtiene:

- **Lift@10 = 1.370x**

Supera una selección aleatoria, pero queda por debajo de Calidad del lead (**1.689x**) si el único objetivo es predecir la visita agendada.

Esto no significa que Inventario carezca de valor. Significa que responde a otra pregunta: **si la oportunidad puede realmente atenderse**.

Su valor incremental debe medirse con resultados que registren recomendaciones mostradas, alternativas aceptadas y desenlaces comerciales.

### 5. No todos los atributos del inmueble tienen historial completo

La disponibilidad sí puede reconstruirse respetando el tiempo. Sin embargo, precio, geografía y otros atributos no siempre cuentan con un historial efectivo completo.

Por eso no se afirma que toda la compatibilidad histórica del inmueble sea perfectamente reconstruible.

### 6. Todavía no existe una “respuesta correcta” limpia para las alternativas

El inmueble que históricamente terminó visitándose no necesariamente era la única alternativa válida ni sabemos qué opciones fueron mostradas en ese momento.

Por eso no conviene usarlo como verdad absoluta para evaluar recomendaciones.

### 7. La cobertura del inventario cambia con el tiempo

Los periodos recientes están mejor instrumentados que los antiguos. Parte de una aparente mejora puede provenir de tener mejores datos, no necesariamente de un cambio real del mercado.

### 8. La IA no tiene etiquetas humanas suficientes para medir precisión completa

El piloto con GPT-5 nano demostró costo bajo, estabilidad técnica y utilidad para descubrir patrones. No existe evidencia suficiente para afirmar una precisión humana completa sobre el catálogo natural.

Por eso se mantiene como herramienta de apoyo al control de calidad.

## Preguntas difíciles y respuesta recomendada

### “¿Por qué confiar en un modelo con AUC cercano a 0.55?”

Porque el uso propuesto no es clasificar perfectamente a todos los leads, sino **priorizar cuando la capacidad es limitada**. El 10% mejor ordenado muestra Lift@10 de 1.689x. Aun así, la baja separación global se reconoce como limitación y exige validación futura.

### “¿Por qué usar Puntaje de oportunidad si su Lift es menor?”

Porque mide un objetivo diferente. Para maximizar visitas agendadas se prioriza por Calidad del lead. Para priorizar casos que además puedan atenderse se incorporan Inventario e incertidumbre. La entrega no afirma que ambos objetivos sean equivalentes.

### “¿Por qué conservar dos números en lugar de uno?”

Porque ocultar Calidad e Inventario dentro de un único puntaje dificultaría entender por qué se toma una decisión. La operación necesita saber si el problema es baja intención, falta de inventario o falta de información.

### “¿Cuál es la política final de alternativas?”

Se usan las **3 mejores alternativas** para construir el componente agregado de capacidad del inventario y pueden mostrarse **hasta 5** alternativas visibles.

### “¿Qué porcentaje de leads debería priorizarse?”

La política base es el **10% superior**, con escenarios de 5%, 10% y 20% para adaptarse a la capacidad operativa.

### “¿Por qué usar IA si no quedó dentro del modelo?”

Porque se probó donde sí existía una ventaja potencial: texto no estructurado del catálogo. Fue útil para descubrir problemas semánticos, pero no aportó suficiente valor predictivo. La decisión responsable fue conservarla donde ayuda y no convertirla en dependencia artificial.

### “¿Por qué no automatizar ya?”

Porque aún faltan cuatro piezas de evidencia:

1. validación con datos completamente nuevos;
2. historial más completo de atributos del inmueble;
3. registro de qué alternativas se muestran y aceptan;
4. prueba causal de que la nueva política mejora resultados reales.

## Estado de la entrega

| Tema | Estado |
|---|---|
| EDA y calidad de datos | **Cerrado** |
| Modelo de Calidad del lead | **Cerrado para evaluación; pendiente de validación futura** |
| Inventario y alternativas | **Cerrado metodológicamente; pendiente de evidencia causal** |
| Puntaje de oportunidad | **Cerrado como diseño; valor incremental de Inventario no demostrado** |
| Uso de IA | **Cerrado; IA retenida sólo donde mostró utilidad** |
| Arquitectura de producción | **Diseñada, no presentada como implementación productiva completa** |
| Visión de producto | **Cerrada** |
| Medición causal | **Diseñada; pendiente de ejecución** |

## Conclusión

La mayor fortaleza del paquete no es una sola métrica. Es que distingue con claridad:

- lo que el modelo puede predecir;
- lo que el inventario permite atender;
- lo que simplemente desconocemos;
- lo que se aprendió en experimentos;
- lo que todavía necesita probarse con datos nuevos.

La solución **no pretende ser más precisa de lo que la evidencia permite**. Para una evaluación, eso es una fortaleza. Para una puesta en producción, el siguiente paso correcto es validación futura seguida de un experimento controlado.
