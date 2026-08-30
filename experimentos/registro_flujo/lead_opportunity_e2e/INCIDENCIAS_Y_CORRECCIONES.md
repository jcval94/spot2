# Incidencias y correcciones — FL-005

## El relevance histórico contradice las restricciones de negocio

**Problema:** usar el spot histórico de scheduled_visit como gold de recomendación producía Hit@K casi nulo.

**Diagnóstico:** sólo 16.5% de futuras visitas alternativas coincide con corredor y ~1% satisface el conjunto estricto de restricciones.

**Corrección:** no optimizar el recomendador para reproducir un proceso orgánico que no representa exposición a recomendaciones. Evaluar fallback por Constraint-valid Coverage@K y availability; conservar Hit@K como diagnóstico negativo.

## Multiplicación vs conversión pura

**Problema:** el score combinado reduce performance contra scheduled_visit puro.

**Corrección:** reconocer que son objetivos distintos. La evaluación primaria end-to-end usa joint_success y mantiene scheduled_visit como guardrail.

**Lección:** un score de marketplace no debe ser juzgado sólo por la demanda si su objetivo explícito incluye capacidad de oferta.
