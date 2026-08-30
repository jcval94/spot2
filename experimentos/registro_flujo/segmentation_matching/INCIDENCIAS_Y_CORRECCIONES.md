# Incidencias y correcciones — Segmentación y Matching

Sólo se registran incidencias que cambiaron diseño, reproducibilidad o interpretación.

## 1. EV-006 quedó stale tras un rerun

Se reconciliaron clusterers, Persona, Intent y métricas contra el run autoritativo `33278286046` y se restauró la trazabilidad.

**Lección:** la interpretabilidad debe apuntar al artifact autoritativo actual.

## 2. Join Availability por spot_id multiplica filas

El join directo expande Inquiry ~10.02x.

**Corrección:** latest `snapshot_date <= inquiry_at` mediante backward as-of.

## 3. response_hours no reconcilia con outcome

Hay `no_response` con response_hours y respuestas sin response_hours.

**Corrección:** excluirlo de Broker Service y degradar interpretaciones de velocidad.

## 4. total_inquiries no equivale a events

`spots.total_inquiries` no reconcilia con `inquiries`.

**Corrección:** no usarlo como historia PIT.

## 5. Market Context sin semántica PIT suficiente

Coverage baja y sin effective/publication timestamp.

**Corrección:** auditarlo pero excluirlo de E006–E016.

## 6. Primera ejecución v4 calculó resultados pero falló harness

Run `33286801380`.

El paso científico terminó, pero finalize no encontró el filename exacto `E009_dynamic_need_t1_results.json`.

**Corrección:** alinear spec ID, model key, filename y `results.experiment_id`.

**Lección:** la identidad del experimento es parte del contrato reproducible.

## 7. Broker Supply fue bloqueado por el gate

Primer intento: 98.3% dominante.  
Segundo: 70.3% / 26.0% / 3.7%, aun después de compactación/winsorization.

Run `33287041844` falla deliberadamente por el gate 5%–65%.

**Corrección científica:** declarar Supply no soportado y pivotar a Service.

**Lección:** un gate metodológico debe poder matar una hipótesis.

## 8. E013/E014 copian métricas del padre sólo para harness

Como Supply falló antes de elegibilidad, E013/E014 no son tratamientos ejecutados. Los result files lo dicen explícitamente.

**Lección:** no leer métricas sin estado/caveat.

## 9. El future test pasó de confirmatorio a exploratorio para pockets

Fue usado sucesivamente para comparar modelos e inspeccionar celdas, y esas celdas guiaron iteraciones posteriores.

**Corrección de cierre:** congelarlo para reproducción y exigir nueva cohorte/A-B para confirmación.

**Lección:** un holdout deja de ser independiente cuando guía nuevas hipótesis.

## 10. IDs cortos pueden colisionar entre líneas

E006/E007 existen en líneas históricas distintas.

**Corrección:** trazabilidad por folder + EV + discovery + run, no sólo experiment ID.

## 11. README generado podía borrar links manuales

`matching_profiles_v4/README.md` se regenera desde `run_profiles.py`.

**Corrección:** preservar enlaces de interpretabilidad/decisión en el generador.

**Lección:** documentación generada debe actualizarse en su fuente.
