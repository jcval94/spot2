# Cronología

## Base

### E020–E027

El EDA profundo y las ablaciones detectan:

- drift temporal fuerte;
- clocks/progreso peligrosos;
- Availability como guardrail;
- outliers no eliminables automáticamente;
- prior_searches perjudicial;
- broker prior no robusto.

### E028–E030

Se congelan:

- target canónica;
- protocolo A/B;
- release candidate T2;
- ABT definitiva point-in-time.

## Recuperación T0/T1

### E031

Ladder de FE con algoritmo fijo:

1. atomic;
2. scale/specificity;
3. semantic Need;
4. soft profiles;
5. semantic interactions.

Selección sólo train/validation.

### E032

T0 one-shot test:

- AUC 0.4897;
- AP/prevalence 0.964x;
- Lift@10 0.824x.

NOT_RECOVERED.

### E033

T1 one-shot test:

- AUC 0.4637;
- atomic 0.4975;
- ΔAUC IC95% completamente negativo.

NOT_RECOVERED.

### E034

Se crea catálogo gobernado de Feature Engineering.

### E035

Segunda ola sólo rolling train:

- missingness;
- frequency;
- bins;
- geo/inventory-relative.

T0: no signal. T1: pista débil/inestable.

### E036

Se descompone geo vs inventory.

Ninguna variante obtiene fold AUC >0.50.

### E037

Target encoding temporal suavizado.

T0: no signal.

T1: señal débil en AUC/AP, sin Lift@10 ni estabilidad suficiente.

### E038

Se congela Feature Policy v2:

neutralidad sólo para LeadQuality; capas semánticas siguen activas.

### E039

Se diseña LLM Semantic Inquiry Features.

No se ejecuta porque el dataset no contiene raw inquiry text.

### E040

Revisión de cierre: CLOSED / DECISION-READY.
