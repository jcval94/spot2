# Spot2 — Entrega final

Este es el **índice maestro** de la solución final del assessment.

## Regla de autoridad

La solución presentada al evaluador es una sola:

**Codexway = solución ganadora y autoridad final.**

- `entregable/**` contiene la narrativa final.
- `codexway/**` conserva la implementación y evidencia canónica.
- `experimentos/**` demuestra amplitud de investigación, challengers y resultados negativos.
- `AssessmentSol1/**` aporta auditorías metodológicas y evidencia complementaria.

Cuando una rama histórica utiliza otro target, modelo, capacidad, K o fórmula, esa evidencia se presenta únicamente como challenger. **No redefine la solución final.**

---

# Ruta recomendada para el evaluador

| # | Entregable | Qué responde | Entry point |
|---:|---|---|---|
| **1** | **EDA** | ¿Qué aprendimos del mercado, los leads y la calidad temporal de los datos? | [Abrir EDA](01_eda/README.md) |
| **2** | **One-Pager** | ¿Cuál es la solución y por qué importa al negocio? | [Abrir One-Pager](02_one_pager/README.md) · [PDF](02_one_pager/ONE_PAGER_SPOT2.pdf) |
| **3** | **Lead Quality** | ¿Qué tan probable es que el lead avance en T1? | [Abrir Lead Quality](03_lead_quality/README.md) |
| **4** | **Inventory** | ¿Podemos atender al lead con inventario conocido point-in-time? | [Abrir Inventory](04_inventory_fallback/README.md) |
| **5** | **Opportunity + Fallback** | ¿Cómo combinamos propensión y serviceability y qué hacemos si el Spot falla? | [Abrir Opportunity](05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md) |
| **6** | **Producción** | ¿Cómo llevaríamos la solución a operación, monitoreo y rollback? | [Arquitectura](05_opportunity_produccion/02_ARQUITECTURA_PRODUCCION.md) · [Runbook](05_opportunity_produccion/03_MONITOREO_GOBIERNO_RUNBOOK.md) |
| **7** | **Uso de IA** | ¿Dónde se utilizó un LLM, qué funcionó y qué se rechazó? | [Abrir Uso de IA](07_ia_product_vision/01_USO_OBLIGATORIO_IA.md) |
| **8** | **Product Vision** | ¿Qué haríamos con tres meses adicionales y cómo mediríamos impacto? | [Visión ejecutiva — 2 párrafos](07_ia_product_vision/04_PRODUCT_VISION_EJECUTIVA.md) |

### Anexos útiles

- [Product Vision — roadmap detallado](07_ia_product_vision/02_PRODUCT_VISION.md)
- [Diseño causal / RCT](07_ia_product_vision/03_EXPERIMENTACION_CAUSAL.md)
- [Matriz final de cobertura](MATRIZ_COBERTURA_ASSESSMENT.md)
- [Revisión crítica como evaluador](REVISION_CRITICA_EVALUADOR.md)

---

# Decisiones canónicas congeladas

| Tema | Decisión final |
|---|---|
| Autoridad | **Codexway** |
| Scoring moment | **T1 — primera inquiry, después de persistir el request y antes de broker response** |
| Target Lead Quality | **scheduled_visit en la primera inquiry** |
| Madurez | **7 días** |
| Modelo Lead Quality | **stable_segment_logistic + calibración Platt** |
| Lead Quality Lift@10 | **1.689x**, IC95% [1.381x, 1.982x] |
| Capacidad | **top 10% default**; escenarios 5/10/20% |
| Threshold de referencia | **≈0.2531 en validation**, no cutoff universal |
| Availability | **strict backward-as-of** |
| Freshness Inventory | **30 días** |
| UNKNOWN | **UNKNOWN ≠ UNAVAILABLE** |
| Fallback — agregación | **top-3 interno** para componente de serviceability |
| Fallback — presentación | **hasta 5 recomendaciones visibles** |
| Opportunity final | **p_quality × inventory_serviceability_lower** |
| Opportunity upper | p_quality × inventory_serviceability_upper |
| Opportunity Lift@10 | **1.370x**, IC95% [1.078x, 1.690x] |
| Valor incremental Inventory sobre target T1 | **NO-GO / no demostrado** |
| Actionability Gate | **challenger AssessmentSol1; no arquitectura final** |
| IA | **Semantic Catalog QA / discovery; no dependencia del scorer** |
| Activación | **forward shadow → RCT guardado**, no automatización inmediata |

---

# Artefactos de formato

| Artefacto | Ruta | Estado |
|---|---|---|
| Notebook renderizado | [Codexway HTML](../codexway/notebooks/spot2_assessment.html) | Disponible |
| Notebook reproducible | [Codexway IPYNB](../codexway/notebooks/spot2_assessment.ipynb) | Disponible |
| One-Pager PDF | [ONE_PAGER_SPOT2.pdf](02_one_pager/ONE_PAGER_SPOT2.pdf) | **Final** |
| Slides PDF | [Codexway slides](../codexway/reports/slides.pdf) | Disponible; **pendiente de revalidación editorial contra el paquete final** |
| Prompt de IA | [Uso de IA](07_ia_product_vision/01_USO_OBLIGATORIO_IA.md) | Incluye prompt exacto y evidencia real |

---

# QA final del paquete

La revisión de cierre comprobó:

- nombres y target canónicos;
- T1 y madurez de 7 días;
- modelo final;
- métricas principales;
- capacidad top10;
- threshold ≈0.2531;
- K interno 3 / K visible 5;
- fórmula Opportunity final;
- separación de challengers históricos;
- links relativos dentro de `entregable/**`;
- Product Vision oficial de dos párrafos;
- One-Pager de una página.

No se detectó un bug metodológico que justificara reabrir modelos o arquitectura.

Los puntos deliberadamente no sobreafirmados son:

1. el valor incremental de Inventory sobre el target T1;
2. el éxito causal del fallback;
3. el full historical matching con atributos del Spot no versionados;
4. la precisión humana real del LLM sin human gold;
5. deployment sin una nueva cohorte forward.

Para el detalle: [Matriz de cobertura](MATRIZ_COBERTURA_ASSESSMENT.md) y [Revisión crítica](REVISION_CRITICA_EVALUADOR.md).
