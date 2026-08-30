# FL-003 — Segmentación, perfiles y Matching

**Estado:** **CLOSED / DECISION-READY**

## Pregunta original

¿Podemos convertir Lead, Search Need, Spot y Broker en perfiles interpretables que mejoren el matching/routing, sin mezclar conceptos, sin leakage point-in-time y con evidencia de lift fuera de muestra?

## Respuesta final

Sí podemos construir una **representación mucho más limpia**, pero la evidencia no justifica convertir el sistema en reglas rígidas de clusters ni reemplazar universalmente el mejor benchmark global.

La representación recomendada queda:

```text
Lead
 ├─ Persona actual (acquisition/history)
 ├─ Search Need T0
 └─ Dynamic Need T1
          │
          ▼
Spot
 ├─ Physical Space
 └─ Location
          │
          ▼
Broker
 ├─ legacy profile para benchmark global
 └─ Broker Service como faceta auxiliar
          │
          ▼
Availability backward-as-of
          │
          ▼
matching / ranking model
```

No usar Broker Supply clusters ni Inquiry Intent weekday.

**E007** permanece como referencia global.  
**E012/E016** quedan como challengers orientados a lift/routing.

El mejor pocket exploratorio es **DN4 × LOC1 × BSV1 = 1.510x lift suavizado**, pero exige nueva cohorte o A/B online antes de activarse.

## Por qué la línea se considera cerrada

La investigación ya cubrió:

- clustering multi-método y balance;
- perfiles Lead/Persona/Need/Spot/Broker/Intent;
- corrección point-in-time del clustering;
- interpretabilidad;
- auditoría relacional completa;
- descomposición Spot Physical vs Location;
- flat compatibility;
- Dynamic Need T0→T1;
- rediseño de Persona;
- dos intentos de Broker Supply;
- Broker Service;
- matching jerárquico;
- bootstrap por `lead_id`;
- resultados negativos e inconclusos;
- diseño A/B online y power analysis;
- gates de leakage, balance y disponibilidad.

Seguir buscando combinaciones sobre el mismo future test ya no produciría evidencia independiente.

## Qué no significa “cerrado”

No significa que el pocket 1.51x esté listo para producción.

Quedan como fase posterior:

- réplica temporal en una cohorte nueva;
- A/B online de routing;
- target comercial real si aparece;
- enriquecimiento de Broker Supply;
- monitoreo de drift/cobertura.

Eso requiere **nueva evidencia**, no más tuning sobre el mismo holdout.

## Navegación

- [CRONOLOGIA.md](CRONOLOGIA.md)
- [DECISIONES.md](DECISIONES.md)
- [TRAZABILIDAD.md](TRAZABILIDAD.md)
- [INCIDENCIAS_Y_CORRECCIONES.md](INCIDENCIAS_Y_CORRECCIONES.md)
- [CIERRE.md](CIERRE.md)

## Decisión canónica

- [DECISION_SEGMENTACION.md](../../matching_profiles_v4/DECISION_SEGMENTACION.md)

## Fuentes canónicas

- [EV-006 — Profile clustering v2](../../Evidencias/EV-006_profile_clustering_v2.md)
- [EV-010 — Relational audit + Matching A/B](../../Evidencias/EV-010_matching_ab_v3.md)
- [EV-013 — Semantic profiles v4](../../Evidencias/EV-013_matching_profiles_v4.md)
- [Interpretabilidad v3](../../matching_ab_v3/INTERPRETABILIDAD.md)
- [Interpretabilidad v4](../../matching_profiles_v4/INTERPRETABILIDAD.md)
- [Descubrimientos acumulados](../../conocimiento_agregado/DESCUBRIMIENTOS.md)
