# Validación del Entregable 1 — EDA

**Estado final: APROBADO**

Este anexo comprueba que las cifras principales del EDA son consistentes y que la narrativa final respeta la solución seleccionada.

## 1. Completitud

- Documento de entrada: **APROBADO**
- EDA completo: **APROBADO**
- Referencias y trazabilidad: **APROBADO**
- Figuras: **disponibles**
- Tablas resumen: **disponibles**
- Enlaces principales: **revisados**

## 2. Cifras críticas reconciliadas

| Afirmación | Resultado verificado | Estado |
|---|---:|---|
| Casos T1 maduros | **4,898** | APROBADO |
| Casos positivos T1 | **1,001** | APROBADO |
| Proporción de visitas agendadas | **20.44%** | APROBADO |
| Inventario exacto con disponibilidad desconocida | **44.30%** | APROBADO |
| Brecha relativa Retail entre demanda y catálogo | **+5.89 puntos porcentuales** | APROBADO; evidencia complementaria |
| Una unión temporal ingenua habría usado información futura | **7,758 consultas / 34.36%** | APROBADO; auditoría complementaria |
| Clusterers v2 seleccionados que cumplen gate de balance | **6 de 6 familias** | APROBADO; evidencia experimental |
| Dynamic Need T1 experimental | **K=5; silhouette 0.620; ARI 1.000** | APROBADO; descriptivo/challenger |
| Broker Service balanced | **K=3; ARI 0.948; share 18.7%–57.7%** | APROBADO; capa auxiliar |
| Broker Supply compact | **70.3% / 26.0% / 3.7%** | RECHAZADO por gate 5%–65% |
| Pocket DN4 × LOC1 × BSV1 | **N=60; 31.37% suavizado; lift 1.510x** | APROBADO como discovery, NO como regla |
| Segmentos confirmados después de controlar múltiples pruebas | **0 de 19** | APROBADO; impide promoción de pockets |
| Candidatos con estado de inventario de hasta 7 días | **19.16%** | APROBADO |
| Leads con al menos un candidato reciente | **93.46%** | APROBADO |

## 3. Qué evidencia tiene prioridad

### Solución final

Codexway mantiene autoridad sobre:

- el momento de evaluación T1;
- la visita agendada como señal principal de éxito;
- las variables permitidas;
- el uso del último estado de disponibilidad conocido;
- la regla de que **desconocido no significa no disponible**;
- las limitaciones de los atributos históricos del inmueble;
- la decisión de no convertir patrones de segmentación en reglas finales sin confirmación.

**Resultado: APROBADO.**

### Auditoría complementaria

AssessmentSol1 se utilizó para cuestionar y reforzar:

- integridad de las relaciones entre tablas;
- cambios temporales;
- significado de datos faltantes;
- profundidad de alternativas;
- relación demanda/oferta;
- riesgos de utilizar información futura.

Sus decisiones alternativas no reemplazan silenciosamente la definición final.

**Resultado: APROBADO.**

### Investigación experimental

Los experimentos se utilizaron para:

- probar modelos y segmentaciones alternativas;
- estudiar necesidad dinámica y patrones locales;
- perfilar explícitamente Lead, Persona, Search Need, Spot, Broker e Inquiry Intent;
- separar Physical/Location y Broker Service/Supply;
- conservar resultados negativos como Inquiry Intent≈weekday y Broker Supply desbalanceado;
- evaluar reglas semánticas;
- documentar resultados negativos;
- identificar qué ideas no justificaban ser promovidas.

Un patrón prometedor encontrado durante exploración no se convierte automáticamente en regla productiva.

**Resultado: APROBADO.**

## 4. Contradicciones resueltas

La revisión final detectó diferencias entre líneas de investigación en temas como variable objetivo, madurez, tratamiento temporal y segmentación. Se resolvieron siguiendo una regla sencilla:

> **La evidencia complementaria puede cuestionar, explicar o reforzar la solución final, pero no la redefine salvo que revele un error metodológico objetivo.**

No se encontró un error de ese tipo que justificara reabrir la arquitectura o cambiar el modelo ganador.

## 5. Limitaciones que permanecen explícitas

La validación también confirma que el EDA **no afirma más de lo que permiten los datos**:

- una visita agendada es una señal temprana, no una venta;
- algunos atributos del inmueble no tienen historial completo;
- la cobertura de disponibilidad cambia de forma importante con el tiempo;
- ausencia de información no prueba indisponibilidad;
- los patrones locales exploratorios no se usan como reglas definitivas;
- el lift 1.510x de DN4 × LOC1 × BSV1 corresponde a discovery en un future test ya inspeccionado y no corrige multiplicidad;
- el impacto causal sólo puede demostrarse con nuevos datos y experimentación.

## Dictamen

El EDA final es consistente con la solución seleccionada, mantiene trazabilidad hacia la investigación y presenta de forma explícita las principales limitaciones.

**Resultado global: APROBADO.**
