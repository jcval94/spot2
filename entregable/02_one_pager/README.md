# Entregable 2 — One-Pager ejecutivo

> **Audiencia:** Producto y C-Level.  
> **Solución final:** Codexway.  
> **Lectura:** 3–5 minutos.  
> **Versión PDF:** [ONE_PAGER_SPOT2.pdf](ONE_PAGER_SPOT2.pdf)

## Spot2 Lead Opportunity Score — priorizar demanda con capacidad real de servicio

### El problema

Growth recibe miles de leads con distinta intención comercial, mientras el inventario cambia constantemente. Priorizar sólo “quién parece buen lead” puede desperdiciar capacidad si el inmueble solicitado ya no está disponible; priorizar sólo inventario puede ignorar quién realmente tiene mayor probabilidad de avanzar.

### La oportunidad

Convertir una priorización manual en una decisión consistente que responda dos preguntas por separado y luego las integre:

**¿Qué tan probable es que este lead avance?** + **¿Tenemos inventario capaz de atenderlo ahora?**

### Datos y decisión metodológica

Se trabajó con **5,000 leads, 22,576 inquiries, 3,000 Spots, 30,000 snapshots de disponibilidad y contexto de mercado**. El scoring principal ocurre en **T1: inmediatamente después de la primera inquiry y antes de conocer la respuesta del broker**. El proxy de éxito es que esa primera inquiry termine en **scheduled_visit**, con **7 días de madurez**.

Se evaluaron múltiples familias de modelos y arquitecturas; la solución final fue seleccionada por **utilidad temporal, robustez y capacidad de priorización**, no únicamente por AUC.

### Cómo funciona

**1. Lead Quality.** Estima la probabilidad de progreso comercial temprano. El modelo final es una logística estable y calibrada. En el holdout procedimental obtiene **Lift@10 = 1.689x**: el 10% priorizado concentra aproximadamente 69% más positivos que una selección aleatoria equivalente.

**2. Inventory Serviceability.** Evalúa si el Spot solicitado o una alternativa puede atender la necesidad usando únicamente el último estado de inventario que era conocido en ese momento. **UNKNOWN no se trata como UNAVAILABLE.** Si el inventario exacto no alcanza, el sistema busca alternativas compatibles y puede devolver hasta **5 recomendaciones**; si no hay una opción defendible, devuelve **NO_RESULT** antes que inventar una recomendación.

**3. Lead Opportunity Score.** Combina Lead Quality con la cota conservadora de Inventory Serviceability, manteniendo ambos componentes visibles. El Opportunity Score conservador alcanza **Lift@10 = 1.370x** y supera selección aleatoria, pero no mejora el ranking de conversión pura frente a Lead Quality. Por ello el producto distingue dos objetivos: **maximizar conversión proxy** y **maximizar oportunidades que además sean atendibles**.

### Decisión operativa

**Lead de alta calidad + inventario servible → priorizar.**  
**Lead de alta calidad + inventario incierto → verificar inventario.**  
**Lead de alta calidad + baja serviceability → activar fallback.**  
**Sin candidato válido → NO_RESULT / sourcing.**

### IA con governance

Se ejecutó un piloto real con **GPT-5 nano + Structured Outputs** para auditar semántica del catálogo. Fue extremadamente barato (**USD 0.002579 en 100 listings**) y técnicamente viable, pero no aportó features incrementales justificables para el predictor. La semántica reutilizable se convirtió en reglas determinísticas gratuitas; una ablation posterior tampoco mejoró Lead Quality. La IA se retiene donde sí tiene ventaja: **semantic discovery y Catalog QA muestreado**, con revisión humana; el score principal no depende de una API LLM.

### Resultado principal

La evidencia offline demuestra una **señal defendible de priorización** y una arquitectura capaz de separar propensión comercial de capacidad de servicio. No demuestra todavía impacto causal ni valor incremental de Inventory sobre el target T1.

### Impacto esperado

- concentrar el esfuerzo de Growth en leads con mejor señal;
- reducir trabajo perdido sobre inventario no servible;
- hacer explícita la incertidumbre del inventario;
- ofrecer alternativas consistentes cuando el Spot ideal falla;
- generar una base auditable para medir impacto causal.

### Riesgos principales

- el holdout histórico es procedimental, no completamente virgen;
- el target es un proxy temprano, no cierre comercial;
- precio y otros atributos del Spot no están versionados históricamente;
- el éxito del fallback no tiene todavía un gold label limpio;
- la cobertura/frescura de Availability cambia con el tiempo.

### Siguiente paso

**No automatizar todavía.** Ejecutar una nueva cohorte en **shadow mode**, validar Lift/calibración/freshness y después lanzar un **RCT 50/50 sticky por lead_id**. El impacto real debe medirse con outcomes instrumentados —visita, alternativa aceptada y, en el futuro, cierre/valor comercial—, no con el backtest como sustituto de causalidad.

---

### La historia en una línea

**Lead → Quality → Opportunity orchestration ← Inventory → Fallback / acción**, con trazabilidad point-in-time y abstención cuando la evidencia no alcanza.
