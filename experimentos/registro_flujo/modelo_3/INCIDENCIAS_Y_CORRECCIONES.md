# Incidencias y correcciones

Este archivo conserva problemas encontrados durante el flujo porque forman parte de la reproducibilidad y explican por qué el diseño final es más estricto que el inicial.

## 1. Dtype mismatch en availability as-of

Durante E003, `merge_asof` falló porque:

- snapshots `spot_id`: float64;
- availability `spot_id`: int64.

Corrección:

- coerción explícita a `int64` antes del as-of join.

Lección:

> Las relaciones point-in-time deben validar tipo y cardinalidad, no sólo nombre de llave.

---

## 2. `pd.NA` incompatible con imputación sklearn

El pipeline categórico conservaba `pd.NA`, provocando:

`TypeError: boolean value of NA is ambiguous`

Corrección:

- convertir missing categórico a `np.nan` antes del preprocesador.

Lección:

> El contrato de tipos forma parte del experimento reproducible.

---

## 3. No confundir “stage como feature” con challenger fuerte

E003 mostró Multi-Head > pooled neural, pero ese resultado fue inicialmente fácil de sobreinterpretar como evidencia de que “varios heads son necesarios”.

E005 introdujo pooled CatBoost y especialistas no lineales.

E006 confirmó que el problema era parcialmente la fuerza del challenger, no sólo la arquitectura multi-head.

Lección:

> Una conclusión arquitectónica sólo es tan fuerte como sus challengers.

---

## 4. Single holdout insuficiente

E005 produjo mejores puntos para modelos tabulares, pero varios IC95% de macro AP cruzaban cero.

El usuario pidió explícitamente cross-validation antes del registro final.

Corrección metodológica:

- E006: 4-fold rolling-origin temporal CV por lead;
- OOF disjunto;
- bootstrap por lead.

Lección:

> En datos temporales, repetir cohortes futuras es más informativo que un KFold aleatorio o un único test.

---

## 5. Riesgo de múltiples snapshots por lead

T2 genera varias filas por lead.

Se comprobó que la dominancia de `interaction_history` no fuera un artefacto de leads muy activos usando:

- todos los T2;
- primer T2 por lead;
- último T2 por lead.

El historial siguió dominando.

Lección:

> Cuando la unidad de modelado es un evento pero la unidad de dependencia es una entidad, la robustez debe revisarse a nivel entidad.

---

## 6. Ranking de feature importance no estable entre modelos

Spearman Multi-Head vs RF fue bajo (~0.25).

Corrección interpretativa:

- priorizar importancia por **familias**;
- evitar narrativas fuertes sobre “la variable #1”.

Lección:

> Rankings individuales no son equivalentes a verdad estructural cuando hay correlación e interacciones.

---

## 7. `availability_snapshot_age_days` sospechosa

Apareció predictiva, pero con dirección descriptiva contraintuitiva.

Decisión:

- no convertirla en regla de negocio;
- tratarla como posible proxy de cobertura/periodo.

Lección:

> Predictivo no implica accionable ni causal.

---

## 8. Colisiones de IDs de descubrimiento/evidencia

Mientras esta línea corría, el repo cambió y otro flujo de matching ocupó IDs D023–D033 y EV-010.

Corrección:

- preservar el flujo concurrente;
- renumerar Modelo 3 a EV-011/EV-012 y D034–D037;
- rebasar sobre el `main` más reciente.

Lección:

> El registro global necesita asignación de IDs contra el estado actual de `main`, no contra una rama antigua.

---

## 9. Divergencia del PR por cambios concurrentes

El PR de Modelo 3 quedó temporalmente no mergeable porque `main` avanzó con matching.

Corrección:

- reconstruir la rama sobre el árbol actual de `main`;
- preservar los archivos concurrentes;
- volver a pasar governance CI;
- mergear sólo después.

Lección:

> La documentación/evidencia debe integrarse contra el conocimiento acumulado más reciente.

---

## 10. Registro final sólo después de CV

D023/D024 provisionales del flujo de Modelo 3 se mantuvieron como pre-registro hasta terminar E006/E007.

Después se promovieron, con IDs definitivos D034–D037, únicamente al disponer de:

- OOF;
- folds completos;
- bootstrap;
- harness records;
- outputs validados.

Lección:

> Una hipótesis pre-registrada y un descubrimiento final son objetos distintos.
