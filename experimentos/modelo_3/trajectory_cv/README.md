# E007 — Trayectoria y progreso con rolling temporal CV

## Pregunta

¿Las variables explícitas de progresión/estancamiento mejoran el scoring dinámico una vez controlamos la arquitectura con rolling temporal CV?

## Parent

E006 fija los folds y revalida la arquitectura. E007 conserva exactamente esos folds.

## Cambio primario

Añadir features point-in-time de trayectoria:

- tiempo desde inquiry previa;
- tiempo desde última respuesta ya realizada;
- tiempo desde última aceptación ya observable;
- gap medio y dispersión entre inquiries;
- velocidad de inquiries;
- cobertura de respuesta histórica;
- inquiries históricas todavía no resueltas;
- inquiries posteriores a última aceptación;
- diversidad/revisita de spots;
- repetición del spot actual;
- cambios de área, presupuesto, urgencia y longitud del mensaje contra la primera inquiry;
- escalamiento de asked_visit.

## Modelos evaluados

Se añaden estas features a los candidatos más relevantes de E005/E006:

- Multi-Head;
- specialist Random Forest;
- specialist CatBoost;
- pooled CatBoost + stage.

También se construye un híbrido elegido **dentro de cada fold con validation**, nunca mirando el bloque test del fold.

## Métrica primaria de feature engineering

T2 Average Precision OOF.

Se reportan también macro AP/AUC, métricas por etapa, estabilidad por fold y bootstrap por lead contra el mismo modelo sin trajectory features.

## Registro

No se promoverá el hallazgo a `conocimiento_agregado` hasta finalizar E006 y E007.


## Resultado final

E007 terminó correctamente sobre los mismos folds de E006 y la conclusión es **SUPPORTED** para T2.

Trajectory features mejoran:

- pooled CatBoost T2: ΔAP +0.0161, IC95% [+0.0003, +0.0322]; ΔAUC +0.0117, IC95% [+0.0004, +0.0237].
- Multi-Head T2: ΔAP +0.0155, IC95% [+0.0013, +0.0303]; ΔAUC +0.0176, IC95% [+0.0055, +0.0297].

No son una mejora universal:

- RF T2 empeora AP -0.0095, IC95% [-0.0191, -0.0002].
- Specialist CatBoost no mejora de forma robusta con este bloque completo.

### Lectura

El concepto de trayectoria/progreso queda validado como señal incremental, pero su uso debe ser específico a la familia de modelo. La opción simple más defendible pasa a ser pooled CatBoost + stage + trajectory como baseline operativo, manteniendo especialistas como challengers.

Para detalle y caveats: [EV-012](../../Evidencias/EV-012_modelo_3_trajectory_cv.md).
