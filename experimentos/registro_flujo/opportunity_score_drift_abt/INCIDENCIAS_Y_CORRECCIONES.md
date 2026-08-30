# Incidencias y correcciones

## 1. Drift confundido con intención

**Problema:** el holdout inicial favorecía fuertemente T1/RF y podía interpretarse como intención estable.

**Corrección:** rolling temporal CV + PSI + ablación de clocks/progreso.

**Lección:** point-in-time correcto no significa distribución estable.

## 2. scheduled_visit sin timestamp

**Problema:** en candidate data el event time se reconstruye con `broker_response_hours`; 14.97% de scheduled_visit carece de ese campo. El pipeline histórico podía convertir parte de esa incertidumbre en 0.

**Corrección:** target canónica con estado `AMBIGUOUS_UNKNOWN_EVENT_TIME`; producción exige timestamp backend real.

**Lección:** un evento conocido con tiempo desconocido no es un negativo.

## 3. Colisiones de IDs por ramas concurrentes

**Problema:** mientras esta línea usaba E008–E016/EV-013–EV-021, `main` incorporó Matching Profiles v4 usando E008–E016 y EV-013/EV-014.

**Corrección:** rebase científico desde `main`, reserva de bloque E020–E028 / EV-020–EV-028 / D060–D077 y reconstrucción de índices centrales desde `main`.

**Lección:** leer `main` antes de asignar IDs y volver a comprobarlo antes de merge.

## 4. [skip ci] ocultó la cabeza real del PR

**Problema:** el último commit reconciliado incluía `[skip ci]`, por lo que no hubo workflow asociado al HEAD aunque existían resultados válidos de runs anteriores.

**Corrección:** nuevo commit de integración sin skip, seguido de CI sobre el árbol rebasado.

**Lección:** usar `[skip ci]` sólo para commits generados por workflows ya validados, no para la reconciliación final.

## 5. Duplicados en DESCUBRIMIENTOS de la rama

**Problema:** sucesivos appends duplicaron D052–D055.

**Corrección:** no parchear el archivo viejo; reconstruir desde el `DESCUBRIMIENTOS.md` limpio de `main` y añadir cada hallazgo una sola vez.

**Lección:** los índices canónicos deben reconstruirse contra main durante integraciones concurrentes.
