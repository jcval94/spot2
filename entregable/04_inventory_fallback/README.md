# Entregable 4 — Inventario y estrategia de alternativas

## La pregunta de negocio

Un lead puede ser muy prometedor y, aun así, no poder atenderse porque el inmueble que solicitó ya no está disponible o porque no conocemos con suficiente certeza su estado.

Por eso este componente responde una pregunta distinta a Calidad del lead:

> **Con la información que realmente conocíamos en ese momento, ¿podemos atender razonablemente la necesidad del lead?**

## Cómo funciona

La lógica sigue cinco pasos:

1. **Considerar sólo inmuebles que ya existían** cuando se evaluó al lead.
2. **Buscar el último estado de disponibilidad conocido** hasta ese momento; nunca usar un registro futuro.
3. **Comprobar compatibilidad básica** de modalidad, área, precio y geografía.
4. **Separar certeza de incertidumbre:** si falta información, el sistema no inventa una respuesta.
5. **Buscar alternativas** cuando el inmueble original no es una opción defendible.

## Una regla especialmente importante

**“Desconocido” no significa “no disponible”.**

Si no existe un registro reciente de disponibilidad, sólo sabemos que existe incertidumbre. Convertir automáticamente esa ausencia en “no disponible” castigaría leads por un problema de datos, no por una condición real del mercado.

Para reflejarlo, la solución conserva dos valores:

- una estimación **conservadora**, que cuenta sólo lo que puede defenderse con mayor certeza;
- una estimación **más amplia**, que muestra el potencial cuando parte del inventario es incierto.

## Vigencia de la información

Se usa una referencia de **30 días** para distinguir información reciente de información antigua.

Esto no significa que un inmueble con información de 31 días esté necesariamente fuera del mercado. Significa que debemos tener **menos confianza** en lo que sabemos sobre él.

## Qué pasa si el inmueble solicitado no sirve

El sistema busca alternativas que respeten las restricciones principales y las ordena de forma reproducible.

- Para calcular la capacidad agregada del inventario se utilizan las **3 mejores alternativas**.
- Para presentación al usuario o al equipo pueden mostrarse **hasta 5 alternativas**.
- Si ninguna opción cumple las condiciones mínimas, el sistema devuelve **SIN RESULTADO** en lugar de inventar una recomendación.

## Qué sabemos sobre el inventario

Los análisis muestran dos hechos relevantes:

1. **La cobertura histórica de disponibilidad cambia mucho con el tiempo.** Los periodos recientes están mucho mejor observados que los antiguos.
2. **No todos los atributos del inmueble tienen historial completo.** Podemos reconstruir bien cuándo existía un inmueble y qué disponibilidad se había observado, pero precio y algunos atributos no siempre están versionados históricamente.

Por ello, la disponibilidad está protegida contra el uso de información futura, mientras que una reconstrucción histórica perfecta de toda la compatibilidad del inmueble sigue teniendo limitaciones.

## Por qué no usamos el inmueble visitado como “respuesta correcta” de recomendación

Que un lead haya terminado visitando un inmueble no demuestra que ésa fuera la única buena alternativa disponible.

Por eso métricas del tipo “¿el inmueble histórico apareció entre los primeros K?” sirven como diagnóstico, pero **no se usan como prueba definitiva** de que la estrategia de alternativas sea buena o mala.

## Relación con Calidad del lead

| Pregunta | Calidad del lead | Inventario |
|---|---|---|
| ¿Qué queremos saber? | Si el lead parece proclive a avanzar. | Si su necesidad puede atenderse. |
| Señal principal | Probabilidad de visita agendada. | Compatibilidad + disponibilidad conocida. |
| ¿Usa disponibilidad? | No. | Sí. |
| Riesgo principal | Confundir señal temprana con venta. | Confundir falta de información con falta de inventario. |
| Uso | Ordenar leads. | Confirmar atención y proponer alternativas. |

## Decisión final

La solución de inventario se considera **metodológicamente defendible para continuar a validación**, pero no se afirma que ya haya demostrado impacto causal o incremento de conversión.

Su valor actual es operativo:

- evita recomendar usando información futura;
- hace explícita la incertidumbre;
- permite buscar alternativas de forma consistente;
- se abstiene cuando no existe evidencia suficiente.

La prueba definitiva debe hacerse con datos nuevos y registrando qué alternativas se mostraron, cuáles se aceptaron y qué resultados comerciales produjeron.
