# Cronología — selección del caso de uso LLM

## 1. Triage de la primera inquiry

**Hipótesis:** usar el LLM para extraer intención, restricciones, urgencia, información faltante y razón de prioridad.

**Por qué era razonable:** T1 contiene mucha más señal que T0.

**Limitación descubierta:** el dataset no entrega el texto crudo de inquiry. Sólo existen variables estructuradas como `message_length`, `urgency_days` y `asked_visit`.

**Decisión:** conservar como visión de producción, no como experimento principal demostrable en el assessment.

Evidencia: [EV-008](../../Evidencias/EV-008_llm_triage.md).

## 2. Lead Conversion Copilot

**Hipótesis:** usar el LLM después del scoring para resumir trayectoria, proponer next-best-action y preparar el contacto del broker.

**Por qué era razonable:** T2 demuestra que la trayectoria importa y que más interacciones no equivalen necesariamente a progreso.

**Nueva duda:** una parte importante de la salida puede construirse de manera determinística a partir de los estados ya calculados.

**Decisión:** moverlo a Product Vision; no usarlo como justificación principal del LLM en la entrega.

## 3. LLM-assisted fallback

**Hipótesis:** filtrar candidatos con Python y dejar que el LLM rerankee y explique trade-offs.

**Por qué era razonable:** el assessment exige fallback y menciona explícitamente IA para evaluar recomendaciones.

**Objeción que cambia la decisión:** sector, modalidad, presupuesto, área, ubicación y disponibilidad ya son estructurados. Python puede construir un ranking y un template con esos mismos trade-offs. Sin información no estructurada relevante del lead, el LLM aporta poca ventaja específica.

**Decisión:** no seleccionar esta arquitectura como uso LLM principal. Puede existir después como UX, pero no justifica por sí sola el componente generativo.

## 4. Auditoría de texto real del inventario

Se revisaron `spots.title/description` junto con `spot_attributes`.

Aparecieron casos candidatos donde el texto afirma una característica que el campo estructurado contradice, por ejemplo:

- “buena iluminación natural” frente a `natural_light=false`;
- “Seguridad 24/7 y control de acceso” frente a `security_type=none`.

También se observó copy sintético/repetitivo, lo que introduce una hipótesis rival fuerte: **reglas simples podrían ser suficientes**.

## 5. Decisión actual

Probar:

```text
Rules only
    vs
LLM only
    vs
Rules + LLM
```

sobre labels humanos de consistencia semántica.

El LLM sólo se justifica si demuestra que interpreta variación lingüística y encuentra issues adicionales accionables que las reglas no capturan con la misma facilidad.
