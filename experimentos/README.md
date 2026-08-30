# Experimentos — sandbox científico de Spot2

Esta carpeta es el límite por defecto para todo el trabajo experimental del proyecto.

## Regla principal

Todo código, análisis, resultado, gráfico, artifact, prueba, arnés o documento generado como parte de experimentación debe vivir dentro de `experimentos/`.

Excepciones estructurales:

- `.agents/skills/`: ubicación requerida para skills del repositorio.
- `.github/workflows/`: ubicación requerida por GitHub Actions.
- entradas canónicas ya existentes del reto, como `data/`, `assessment.md` y `feature_dictionary.md`.
- cualquier excepción que el usuario solicite explícitamente.

## Estructura

- `_sistema/`: herramientas compartidas de experimentación.
- `conocimiento_agregado/`: síntesis acumulativa de descubrimientos.
- `Evidencias/`: registro central de evidencia.
- `registro_flujo/`: cronología y evolución de decisiones para líneas multi-experimento.
- una carpeta por experimento o línea exploratoria.

## Trazabilidad mínima

Todo experimento debe poder recorrerse así:

`experimento -> EVIDENCIA.md -> Evidencias/EV-... -> resultado fuente`

y todo descubrimiento así:

`conocimiento_agregado/DESCUBRIMIENTOS.md -> EV-... -> experimento/resultados`

Los resultados negativos e inconclusos también se conservan.

## Convención

No crear una nueva abstracción o carpeta global por cada idea. Una línea de trabajo nueva comienza dentro de su propia carpeta de experimento y sólo se promueve a `_sistema/` cuando se reutiliza de forma real.


## Registro de flujo

Cuando una línea acumula varios experimentos o llega a una decisión de cierre, documentar su evolución en `registro_flujo/<line_name>/` usando la skill `spot2-research-chronicle`.

Ese registro responde **cómo cambió la decisión**; los resultados numéricos y descubrimientos siguen teniendo como fuente canónica `Evidencias/` y `conocimiento_agregado/`.
