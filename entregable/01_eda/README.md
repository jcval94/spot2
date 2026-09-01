# Entregable 1 — Análisis exploratorio de datos

Este documento es la entrada recomendada al análisis de datos de Spot2.

## Qué queríamos entender

Antes de construir un modelo había que responder tres preguntas sencillas:

1. **¿Qué tipo de leads llegan y qué necesitan?**
2. **¿Qué tan confiable es la información disponible en cada momento?**
3. **¿La dinámica de los leads y la del inventario se comportan igual?**

La respuesta a la tercera pregunta fue especialmente importante: **no**. La intención comercial del lead es relativamente estable, mientras que la visibilidad y profundidad del inventario cambian mucho con el tiempo. Por eso la solución final mantiene ambas dimensiones separadas.

## Principales hallazgos

- **Retail muestra la mayor presión relativa entre demanda e inventario histórico:** representa 30.40% de la demanda y 24.51% del catálogo en la muestra de desarrollo.
- **La primera consulta aporta información nueva:** por ejemplo, la necesidad de área se refina respecto a lo declarado inicialmente.
- **Los datos faltantes tienen significados distintos:** “no aplica”, “no se declaró” y “no sabemos” no deben tratarse como si fueran lo mismo.
- **La información de disponibilidad cambia fuertemente con el tiempo:** la cobertura histórica es mucho menor al inicio y se vuelve casi completa en periodos recientes.
- **No conocer la disponibilidad no equivale a saber que un inmueble no está disponible.**
- **La profundidad de alternativas aumenta con el tiempo**, aun cuando la proporción de visitas agendadas se mantiene relativamente estable.
- **No todos los atributos del inmueble tienen historial completo**, por lo que algunas comparaciones históricas deben interpretarse con cautela.
- **El clustering por entidad sí produjo conocimiento útil:** Search Need separa renta/venta/flexible; Dynamic Need muestra cómo se refina la necesidad en T1; Spot se entiende mejor separando Physical y Location; y Broker Service produce perfiles estables.
- **Los resultados negativos también cambiaron la solución:** Inquiry Intent aprendía casi sólo el día de la semana y Broker Supply no sostuvo clusters balanceados, por lo que ambos fueron descartados como reglas.
- **La combinación DN4 × LOC1 × BSV1 fue el pocket histórico más fuerte:** N=60, 36.67% de visitas, 31.37% suavizado y 1.510x de lift. Se conserva como hipótesis de routing para nueva cohorte/A-B, no como multiplicador del puntaje.
- **La confirmación gobernada evitó sobreajuste:** 0 de 19 celdas elegibles superaron BH-FDR 10%, por lo que el entregable final separa claramente discovery de evidencia confirmatoria.

## Momento de evaluación

La solución principal evalúa al lead en **T1**, es decir:

- ya existe su primera consulta;
- todavía no conocemos la respuesta del intermediario;
- no utilizamos consultas posteriores;
- no utilizamos estados futuros del inventario.

La señal de éxito es que esa primera consulta termine en **visita agendada** (`scheduled_visit`). Se usa como indicador temprano de progreso comercial, no como sinónimo de venta.

## Documento completo

➡️ [Leer el EDA final](EDA_FINAL.md)

El documento completo conserva cifras, controles temporales, gráficos y trazabilidad para quien quiera profundizar.

## Material de apoyo

- [Referencias y origen de la evidencia](REFERENCIAS.md)
- [Validación de cifras y consistencia](VALIDACION.md)
- [Figuras](figuras/)
- [Tablas](tablas/)

## Lectura de cinco minutos

Si el tiempo es limitado, recomendamos:

1. leer el resumen ejecutivo del EDA;
2. revisar la comparación entre demanda e inventario;
3. revisar cómo cambia la disponibilidad en el tiempo;
4. revisar la diferencia entre “desconocido” y “no disponible”;
5. leer las secciones **15 y 16** para entender los perfiles por entidad y las combinaciones de compatibilidad;
6. terminar con la tabla que conecta **hallazgo → evidencia → implicación → decisión**.

La idea central es sencilla: **priorizar bien no depende sólo de saber quién parece un buen lead; también depende de saber qué inventario era realmente observable y utilizable en ese momento.**
