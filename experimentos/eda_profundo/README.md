# E009 — EDA profundo para el modelo multi-head

## Objetivo

Profundizar el EDA previo al feature engineering del Modelo 3 sin entrenar ni modificar el modelo supervisado.

La pregunta es: **¿qué propiedades de distribución, colas, outliers, drift, dependencias sintéticas y estructura temporal deben entenderse antes de diseñar features?**

## Estructura

- `base_eda/`: migración íntegra del EDA general realizado previamente en esta conversación.
- `run_deep_eda.py`: análisis reproducible profundo.
- `FINDINGS.md`: interpretación de resultados.
- `results/`: evidencia tabular.
- `figures/`: histogramas y diagnósticos visuales.
- `EVIDENCIA.md`: enlace a la evidencia central EV-009.

## Alcance analítico

1. Distribuciones e histogramas en escala natural y logarítmica.
2. Colas y outliers con Tukey global y estratificado por sector × modalidad.
3. Búsqueda de relaciones deterministas, clipping y señales del generador sintético.
4. Dinámica temporal por cohortes.
5. Estructura de Market Context como panel.
6. Trayectorias de Availability Snapshot.
7. Heterogeneidad descriptiva de brokers con soporte.
8. Compatibilidad Lead ↔ Spot en crudo.
9. Isolation Forest diagnóstico en Lead, Spot e Inquiry.

## Isolation Forest: dónde sí y dónde no

Se usa con `contamination=0.03` **como lente diagnóstica**, no como estimación de registros malos.

### Lead

Estratificado por `search_sector × search_modality`.

Incluye únicamente información T0 observable:
- área objetivo;
- presupuestos;
- historial previo;
- conversión previa declarada.

Se excluye `lead_score_internal` porque el repo ya lo trata como campo de score previo y no queremos que defina qué es “anómalo”.

### Spot

Estratificado por `sector_name × modality`.

Incluye atributos físicos/económicos relativamente estáticos. Se excluyen:
- `days_on_market`;
- `total_views`;
- `total_inquiries`;
- `is_active`.

Son campos de estado actual y no son point-in-time seguros para scoring histórico.

### Inquiry

Estratificado por sector/modalidad del lead.

Incluye sólo información observable en `inquiry_at`:
- longitud;
- área solicitada;
- presupuestos solicitados;
- urgencia;
- `asked_visit`.

Se excluyen `broker_response` y `broker_response_hours`.

### No se aplica a Market Context ni Availability Snapshot

Ambas son estructuras temporales. Una rareza debe evaluarse contra el régimen/tiempo o contra la trayectoria del mismo spot, no como si fueran observaciones IID de una sola nube.

## Regla de interpretación de outliers

Un outlier no se elimina automáticamente.

Para este dataset hay colas genuinas por escala de inmueble y hay señales claras de generación sintética. La decisión posterior debe distinguir:

- error de calidad;
- valor válido pero extremo;
- régimen distinto;
- clipping;
- variable redundante/determinista.

## Hallazgos principales

Ver `FINDINGS.md`. Los descubrimientos materialmente reutilizables están registrados en `experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md`.

## Reproducibilidad

```bash
pip install -r experimentos/eda_profundo/requirements.txt
python experimentos/eda_profundo/run_deep_eda.py
```

El script sólo lee `data/candidate/csv/` y escribe dentro de `experimentos/eda_profundo/`.

## Fuera de alcance

- selección final de features;
- winsorization automática;
- entrenamiento del Modelo 3;
- tuning;
- inferencia causal;
- uso de outcomes ocultos.
