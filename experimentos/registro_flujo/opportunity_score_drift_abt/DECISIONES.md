# Decisiones

## D1 — No lanzar el RF T1 de E005 tal cual

**Evidencia:** EV-021/EV-022.

**Estado:** vigente.

**Razón:** gran parte del rendimiento T1 desaparece al retirar clocks/progreso y el time-proxy-only es demasiado fuerte.

## D2 — Separar Availability state de freshness

**Evidencia:** EV-020/EV-023.

**Estado:** vigente.

>90 días de antigüedad se trata como unknown en backtest; producción debe consultar inventario live/current.

## D3 — No eliminar outliers automáticamente

**Evidencia:** EV-020/EV-024.

**Estado:** vigente.

Rareza no equivale a error; la mejora al borrar train anomalies no es robusta.

## D4 — Retirar prior_searches

**Evidencia:** EV-026.

**Estado:** vigente para el release candidate actual.

## D5 — No usar broker prior para routing

**Evidencia:** EV-027.

**Estado:** vigente.

La heterogeneidad bruta no se convierte en señal PIT robusta; causalidad requeriría otro RCT.

## D6 — Target predictiva y outcome causal son distintos

**Evidencia:** EV-028.

**Estado:** vigente / congelado para protocolo.

Offline: `target_scheduled_visit_30d(l,t)`.
Online: `lead_scheduled_visit_30d_from_assignment`.

## D7 — A/B lead-level, no inquiry-level

**Evidencia:** EV-028.

**Estado:** vigente.

El tratamiento altera la trayectoria y el número de inquiries/T2; randomizar inquiries contaminaría independencia y denominador.

## Hipótesis explícitamente rechazadas/refinadas

- “T1 fuerte = intención comercial estable”: refinada; gran parte es drift/progreso.
- “Outlier = dato malo”: no respaldada.
- “Broker con tasa alta = mejor broker causal”: no respaldada.
- “Availability snapshot age = señal comercial”: no respaldada; se conserva como freshness/QA.
