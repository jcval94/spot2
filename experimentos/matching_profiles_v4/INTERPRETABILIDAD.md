# Interpretabilidad — Matching Profiles v4

Este documento consolida la interpretación de los perfiles nuevos de E008–E016 y las combinaciones de mayor lift observadas en el mismo future test usado por la línea E006/E007.

> **Regla de lectura:** los nombres son etiquetas descriptivas. No son clases causales ni reglas de routing listas para producción. Las combinaciones locales se descubrieron exploratoriamente y requieren réplica temporal o A/B online.

## 1. Estado final de las familias

| Familia | IDs | Calidad | Uso recomendado |
|---|---|---|---|
| Behavioral Persona | BP1–BP3 | Balanceada y muy estable; GMM K=3, ARI=1.000 | Interpretabilidad / diagnóstico; **no sustituir** Persona actual en scoring porque empeoró AP/lift |
| Dynamic Need T1 | DN1–DN5 | Muy separada y estable; K-Means K=5, silhouette=0.620, ARI=1.000 | Mantener como representación T1 candidata y para descubrir compatibilidad |
| Broker Supply v1 | BS1–BS3 | **Rechazada**: 98.3% en BS1 | No usar |
| Broker Supply compact | BSP1–BSP3 | **Rechazada**: 70.3% / 26.0% / 3.7%; viola 5%–65% | No forzar clustering; usar descriptores directos si se requiere Supply |
| Broker Service v1 | BV1–BV4 | Balanceada pero poco estable, ARI=0.229 | Sólo evidencia histórica |
| Broker Service balanced | BSV1–BSV3 | Balanceada y estable; Bisecting K=3, ARI=0.948 | Perfil Broker preferido para interpretabilidad y experimentos locales |
| Physical / Location | PH1–PH4 / LOC1–LOC7 | Heredadas de EV-010 | Mantener; siguen siendo la separación más limpia de Spot |

## 2. Behavioral Persona — BP1 a BP3

La nueva Persona excluye `source`; por eso semánticamente es mejor que P1–P7 para representar madurez/comportamiento.

| Perfil | N | Share | Señales | Interpretación |
|---|---:|---:|---|---|
| **BP1** | 1,445 | 59.0% | prior_inquiries=0; 100% no conversión previa; retail sobrerrepresentado | **Lead temprano / baja historia**, segmento mainstream |
| **BP2** | 644 | 26.3% | manufacturing 47%; no conversión previa; prior inquiries bajas | **Lead industrial/manufactura con baja madurez histórica** |
| **BP3** | 362 | 14.8% | prior inquiries mediana 35.5; 85% convirtió antes | **Lead maduro / experimentado** |

**Conclusión semántica:** BP3 es especialmente claro como madurez alta.  
**Conclusión predictiva:** sustituir Persona actual por `source + BP` bajó AP de 0.2098 a 0.2027 y Lift@10 de 1.001x a 0.937x. Por ello BP se conserva como interpretación, no como reemplazo del score.

## 3. Dynamic Need T1 — DN1 a DN5

Dynamic Need excluye weekday y usa solamente información conocida en la inquiry: modalidad solicitada, área, presupuestos, urgency, asked_visit, channel, message length y deltas contra la necesidad T0.

| Perfil | N calibración | Share | Señales dominantes | Nombre interpretable |
|---|---:|---:|---|---|
| **DN1** | 4,401 | 65.0% | 76% rent; área/presupuestos cerca del centro | **Renta mainstream / necesidad estable** |
| **DN2** | 873 | 12.9% | budgets altos; sale 63%; área ligeramente menor vs T0 | **Venta / presupuesto alto** |
| **DN3** | 776 | 11.5% | budgets bajos; sale 56%; requested area mayor vs T0 | **Venta value / expansión moderada de área** |
| **DN4** | 364 | 5.4% | budgets muy bajos (-1.3 a -1.5 IQR); área solicitada mucho mayor que T0 (+1.15 IQR) | **Stretch-space: busca mucho más espacio con presupuesto bajo** |
| **DN5** | 358 | 5.3% | budgets muy altos (+1.1 IQR); área solicitada menor que T0 | **Premium-budget / reducción de área** |

### DN4 es el perfil nuevo más importante

DN4 aparece repetidamente en las combinaciones de mayor lift. No debe interpretarse como “Lead de baja calidad”: representa una **tensión fuerte entre ambición de espacio y presupuesto**. Esa tensión parece interactuar con Location y Broker Service.

## 4. Transición Search Need T0 → Dynamic Need T1

| Need T0 | DN1 | DN2 | DN3 | DN4 | DN5 |
|---|---:|---:|---:|---:|---:|
| **N1 renta** | **99.82%** | 0% | 0% | 0% | 0.18% |
| **N2 venta** | 33.25% | 26.54% | 23.79% | 9.22% | 7.20% |
| **N3 both/flexible** | 36.16% | 23.26% | 20.74% | 11.72% | 8.12% |

**Interpretación:** N1/renta es extremadamente estable. La información incremental de T1 está concentrada sobre todo en N2/N3: venta/flexible se fragmenta en regímenes de presupuesto y cambio de área muy distintos.

## 5. Broker Supply — resultado negativo

### Primer intento

- BS1: 295/300 brokers = **98.3%**.
- BS2: 4 brokers.
- BS3: 1 broker.

### Segundo intento compacto/winsorizado

- **BSP1:** 211 brokers = 70.3%.
- **BSP2:** 78 = 26.0%.
- **BSP3:** 11 = 3.7%.
- ARI=0.949, pero falla el gate de balance 5%–65%.

**Conclusión:** el problema no era sólo escala/outliers. La información de Supply disponible no sostiene una segmentación natural balanceada bajo el estándar del proyecto.

**Recomendación:** no seguir cambiando K para forzar grupos. Si Supply se necesita, usar variables directas de especialización —sector/modalidad/región dominante, entropía, escala de inventario— o recolectar atributos adicionales.

## 6. Broker Service balanced — BSV1 a BSV3

Este perfil sí pasa el gate: min 18.7%, max 57.7%, ARI=0.948.

| Perfil | N brokers | Share | Señales | Nombre interpretable |
|---|---:|---:|---|---|
| **BSV1** | 173 | 57.7% | channel entropy alta; más inquiries; response mix diversificado | **Servicio diversificado / mayor actividad** |
| **BSV2** | 71 | 23.7% | accepted 58.3%; baja entropía de response; rejected 8.3%; menor volumen | **Acceptance-heavy / servicio concentrado** |
| **BSV3** | 56 | 18.7% | urgency alta; scheduled_visit 25.4%; accepted 37.2% | **Urgente / orientado a calendarizar visita** |

**Importante:** ninguna señal usa `broker_response_hours`.

Añadir BSV como feature marginal casi no cambia AP frente a E012 (ΔAP ≈ -0.00002), así que su valor actual es de segmentación/interacción, no de mejora global demostrada.

## 7. Comparación de modelos

| Modelo | AP | Lift@10 inquiry | Recall@20 | Lead AP | Lead AUC | Lead Lift@10 |
|---|---:|---:|---:|---:|---:|---:|
| E006 baseline | 0.2098 | 1.001x | 19.72% | 0.3752 | 0.5469 | 1.112x |
| **E012 Dynamic Need** | **0.21135** | **1.108x** | **21.96%** | 0.3801 | 0.5584 | 1.140x |
| E015 + Broker Service | 0.21134 | 1.118x | 21.86% | 0.3809 | 0.5595 | 1.154x |
| **E016 hierarchy Service** | 0.21068 | **1.172x** | 19.83% | 0.4049 | 0.5730 | 1.365x |
| **E007 old compatibility** | **0.21171** | 1.033x | 20.68% | **0.4270** | **0.5899** | **1.407x** |

**Lectura:** E012/E016 concentran mejor positivos en el top del ranking, pero E007 conserva el mejor AP global y las mejores métricas lead-level. No existe un nuevo ganador universal.

## 8. Nuevo récord local de compatibilidad

Baseline future scheduled_visit ≈20.77%.

| Rank | Combinación | N | Raw visit | Smoothed | Lift | Wilson lower / baseline |
|---:|---|---:|---:|---:|---:|---:|
| 1 | **DN4 × LOC1 × BSV1** | 60 | **36.67%** | **31.37%** | **1.510x** | **1.234x** |
| 2 | **N3→DN4 × BSV1** | 83 | 31.33% | 28.52% | **1.373x** | **1.077x** |
| 3 | N2→DN2 × BSV3 | 57 | 31.58% | 27.85% | 1.341x | 1.011x |
| 4 | DN4 × LOC1 | 90 | 30.00% | 27.69% | 1.333x | 1.036x |
| 5 | DN2 × PH1 × BSV3 | 59 | 30.51% | 27.23% | 1.311x | 0.975x |
| 6 | PH3 × BSV2 | 159 | 28.30% | 27.11% | 1.305x | 1.053x |
| 7 | DN4 × BSV1 | 153 | 28.10% | 26.90% | 1.295x | 1.039x |
| 8 | DN2 × BSV3 | 90 | 28.89% | 26.86% | 1.293x | 0.989x |

### DN4 × LOC1 × BSV1

Esta es la mejor celda encontrada hasta ahora:

- **DN4:** demanda “stretch-space”: quiere significativamente más área con presupuesto relativamente bajo.
- **LOC1:** centro metropolitano CDMX–Naucalpan.
- **BSV1:** Broker Service diversificado/de mayor actividad.
- N=60.
- raw scheduled_visit 36.7%.
- smoothed 31.4%.
- lift suavizado **1.51x**.
- incluso el límite inferior Wilson de la tasa, dividido por el baseline, es **1.23x**.

Esto supera:
- EV-010: 1.366x.
- primera pasada v4 DN4×BV1: 1.427x.

**Cautela crítica:** fue descubierta exploratoriamente en el future test y se evaluaron múltiples celdas. El intervalo Wilson no corrige multiple testing ni convierte el hallazgo en causal. Es una hipótesis prioritaria para réplica/A-B, no una regla productiva.

## 9. Recomendación de segmentación al cierre

**Conservar para scoring/experimentos**
- Search Need N1–N3.
- Dynamic Need DN1–DN5 como capa T1.
- Physical PH1–PH4.
- Location LOC1–LOC7.
- Broker legacy mientras no haya evidencia global suficiente para reemplazarlo.
- BSV1–BSV3 como capa adicional/interpretable y para routing experimental.

**No promover**
- Behavioral Persona BP como reemplazo de Persona en scoring.
- Broker Supply BS/BSP como cluster.
- Inquiry Intent weekday.
- E013/E014: no fueron elegibles porque Supply falló el gate.

**Próximo test causal preferente**
- tratamiento de routing específico para familias DN4, especialmente DN4×LOC1×BSV1;
- randomización sticky por lead;
- no multiplicar el score por 1.51.
