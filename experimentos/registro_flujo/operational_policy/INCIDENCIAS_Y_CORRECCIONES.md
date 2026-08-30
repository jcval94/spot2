# Incidencias y correcciones — FL-004

## Raw scores entre folds

**Riesgo:** tratar un cutoff numérico global como estable aunque las escalas cambian entre modelos/folds.

**Corrección:** calcular ranking y capacity metrics dentro de cada fold/stage y congelar un percentile threshold.

**Lección:** para una política de capacidad, el percentil es más robusto que una probabilidad cruda cuando existe drift de calibración entre folds.

## Maduración del target de Availability

**Riesgo:** usar como training una observación cuya etiqueta de disponibilidad a 30 días termina después del inicio del test.

**Corrección:** exigir `label_mature_at < test_start`.

**Lección:** el futuro puede construir y, pero el label debe estar completamente observado antes de entrenar un fold futuro.

## False precision con days_until_available

**Riesgo:** imponer una función decreciente intuitiva sin evidencia.

**Corrección:** revisar rates empíricos; al no ser monotónicos, excluir el campo del calibrador final.
