# LLM Inventory Semantic Quality — propuesta

**Estado:** ACTIVE / E015 en ejecución.  
**Experimento:** [`E015_llm_inventory_semantic_audit`](E015_llm_inventory_semantic_audit/).  
**Evidencia central:** [EV-014](../Evidencias/EV-014_llm_inventory_quality.md).

## Problema de negocio

Spot2 puede tener un inventario estructuralmente válido —precios, modalidad, área, disponibilidad y llaves correctas— y aun así publicar o recomendar una ficha cuya redacción comercial contradice los atributos del inmueble.

Eso introduce tres riesgos:

1. pérdida de confianza del lead o broker cuando la ficha promete algo que los datos no respaldan;
2. recomendaciones fallback técnicamente válidas pero apoyadas en metadata comercial dudosa;
3. data quality invisible para validadores tabulares tradicionales.

El objetivo del LLM no será predecir conversión ni escribir una descripción bonita. Será **interpretar afirmaciones expresadas en lenguaje natural y contrastarlas contra la ficha estructurada**.

## Por qué aquí sí existe una ventaja potencial del LLM

Un template sólo reexpresa campos ya conocidos. Un conjunto de reglas puede detectar frases explícitas conocidas, pero la misma afirmación puede expresarse de muchas maneras:

- “seguridad 24/7”;
- “acceso controlado”;
- “vigilancia permanente”;
- “circuito cerrado y caseta”.

El LLM puede normalizar esa variación lingüística a un claim común y compararlo con `security_type`, `amenities` u otros atributos.

La hipótesis a validar es:

> Un LLM encuentra contradicciones o claims no soportados que un baseline razonable de reglas no detecta, manteniendo suficiente precisión para que sus flags sean útiles en una revisión de catálogo.

No se asumirá que la hipótesis es cierta. Los textos son sintéticos y repetitivos; es perfectamente posible que las reglas cubran casi toda la señal.

## Señal que motivó la propuesta

Un spot-check manual del dataset mostró candidatos claros a inconsistencia semántica. Ejemplos:

- un listing dice “buena iluminación natural” mientras `natural_light=false`;
- un listing menciona “Seguridad 24/7 y control de acceso” mientras `security_type=none`;
- existen frases físicamente poco plausibles para determinados tipos de inmueble.

Estos ejemplos **no estiman prevalencia** y no son todavía un resultado experimental. Sólo justifican construir el audit.

## Alcance

Entradas principales:

- `spots.title`;
- `spots.description`;
- `spots.sector_name`;
- `spots.type_name`;
- `spots.modality`;
- atributos estructurados de `spot_attributes`.

El LLM podrá:

- extraer claims explícitos del texto;
- mapear cada claim a una familia de atributos;
- marcar contradicción, claim no soportado o ambigüedad;
- citar el fragmento de texto que originó el flag;
- asignar severidad y recomendar revisión.

El LLM **no** podrá:

- modificar automáticamente la ficha;
- inventar atributos;
- decidir disponibilidad;
- calcular Lead Quality;
- decidir elegibilidad comercial;
- usar outcomes futuros;
- convertirse en un componente obligatorio del Lead Opportunity Score antes de demostrar valor.

## Rol en el assessment

Esta línea atiende el uso obligatorio de IA con un problema de negocio verificable: **calidad semántica del inventario**.

La evaluación busca responder una pregunta falsable:

> ¿Qué inconsistencias relevantes encuentra el LLM que las reglas determinísticas no encuentran, y con qué precisión?

Si no añade cobertura útil, la conclusión será que no se justifica productizar este uso del LLM.

## Documentos

- [Plan experimental](PLAN.md)
- [Arquitectura](ARCHITECTURE.md)
- [EVIDENCIA.md](EVIDENCIA.md)
- [Flujo de decisiones LLM](../registro_flujo/llm_use_case/)


## Estado de ejecución

E015 ya completó Fase 0–1:

- 3,000 spots auditados;
- 856 descripciones exactas únicas;
- 84.37% de filas reutilizan una descripción exacta;
- 12 oraciones únicas componen todo el copy de description;
- Rules-only marca 322 spots únicos como candidatos a revisión;
- gold sample humano de 200 listings preparado.

Estos resultados fortalecen la hipótesis rival: **Rules-only puede ser suficiente**. La API de OpenAI sólo se justificará si añade cobertura útil sobre el gold set.

Evidencia: [EV-015](../Evidencias/EV-015_llm_inventory_semantic_audit.md).
