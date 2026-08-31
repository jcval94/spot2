# Entregables 5 y 6 — Lead Opportunity Score + Producción

Esta carpeta integra, sin rediseñarlos, los dos componentes canónicos ya construidos:

- [Entregable 3 — Lead Quality](../03_lead_quality/README.md)
- [Entregable 4 — Inventory Availability + Fallback](../04_inventory_fallback/README.md)

La autoridad final continúa siendo **Codexway**. `experimentos/**` y `AssessmentSol1/**` se usan únicamente como evidencia complementaria, challengers, sensibilidad y auditoría metodológica.

## Documentos

1. [Lead Opportunity Score](01_LEAD_OPPORTUNITY_SCORE.md)
2. [Arquitectura de escalabilidad y puesta en producción](02_ARQUITECTURA_PRODUCCION.md)
3. [Monitoreo, gobierno, retraining y runbook de fallos](03_MONITOREO_GOBIERNO_RUNBOOK.md)

## Decisión ejecutiva

La arquitectura final de Codexway mantiene **Lead Quality e Inventory Serviceability como ejes separados** y construye un Opportunity Score conservador:

```text
Opportunity_lower = P(Lead Quality) × Inventory Serviceability_lower
Opportunity_upper = P(Lead Quality) × Inventory Serviceability_upper
```

El valor operativo no consiste en ocultar ambos componentes dentro de un único número. El producto debe mostrar simultáneamente:

- Lead Quality;
- Inventory Serviceability;
- Inventory Confidence / incertidumbre;
- Opportunity Score lower/upper;
- fallback y reason codes;
- acción recomendada.

En el holdout procedimental de Codexway, Quality-only obtiene Lift@10 **1.689x** y Opportunity conservador **1.370x**. El combinado supera claramente random en términos absolutos, pero **no mejora a Quality-only** para el target T1 de `scheduled_visit`. Por eso la evidencia final soporta forward validation y un piloto guardado, no sustitución automática del ranking comercial.

## Objetivos que no deben confundirse

1. **Maximizar progresión/conversión proxy:** priorizar por Lead Quality.
2. **Maximizar oportunidades que además puedan ser atendidas:** usar la arquitectura Opportunity + Inventory, conservando los dos ejes visibles.

El trade-off entre ambos objetivos se documenta de forma explícita.

## Límite de alcance

Esta carpeta **no** contiene One-Pager ni Product Vision.
