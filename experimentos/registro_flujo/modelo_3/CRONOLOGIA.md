# Cronología — Modelo 3

## 1. Hipótesis inicial: varios momentos del funnel necesitan comportamiento distinto

El punto de partida fue que Lead Quality no debía ser un score estático.

Se distinguieron:

- **T0:** lead recién creado;
- **T1:** primera inquiry;
- **T2:** lead engaged, segunda inquiry en adelante.

La primera alternativa seria elegida fue **Modelo 3: shared representation + heads específicos por etapa**.

### E003 — Multi-Head

Implementado en `experimentos/modelo_3/`.

PR: [#3 — Add Modelo 3 shared multi-head stage scoring](https://github.com/jcval94/spot2/pull/3).

Diseño central:

- target móvil: `scheduled_visit` futuro dentro de 30 días desde cada `score_time`;
- split temporal por `lead_id`;
- right censoring;
- exclusión de scores posteriores a conversión;
- disponibilidad unida backward-as-of;
- respuestas históricas sólo cuando ya eran observables.

Resultado:

- Multi-Head macro AP 0.508;
- pooled NN macro AP 0.497;
- T2 fue la etapa con mayor señal.

**Decisión provisional:** Multi-Head parecía justificado frente al pooled neural original.

---

## 2. La pregunta cambia: ¿qué hace que T2 funcione?

El usuario pidió entender qué información estaba detrás del mejor desempeño de T2.

### Interpretabilidad T2

PR: [#5 — Analyze T2 predictive drivers for Modelo 3](https://github.com/jcval94/spot2/pull/5).

Se usaron:

- permutation importance del head T2;
- importancia por familias;
- Random Forest challenger;
- dirección descriptiva;
- robustez usando una sola observación T2 por lead.

Hallazgo central:

- `interaction_history` domina;
- la señal persiste en primer y último T2 por lead;
- el patrón se interpreta mejor como **progreso vs estancamiento**.

También apareció la primera señal de que un Random Forest T2 podía superar ligeramente al head neuronal.

**Cambio de pregunta:** ya no bastaba con preguntar si Multi-Head ganaba al pooled NN; había que compararlo con especialistas tabulares fuertes.

---

## 3. E005: challengers fuertes cambian la lectura

PR: [#8 — Benchmark Modelo 3 against nonlinear stage specialists](https://github.com/jcval94/spot2/pull/8).

Se mantuvieron iguales:

- target;
- población;
- scoring;
- features;
- split;
- controles point-in-time.

Se comparó:

- Multi-Head;
- pooled NN;
- Logistic por etapa;
- Random Forest;
- ExtraTrees;
- LightGBM;
- specialist CatBoost;
- pooled CatBoost + stage;
- híbrido seleccionado con validation.

Resultado:

- modelos tabulares mejoraron los puntos estimados;
- T1-RF sí mostró ventaja robusta;
- pooled CatBoost mejoró AUC macro;
- macro AP global todavía fue **INCONCLUSIVE** con un único holdout.

**Decisión correcta en ese momento:** no declarar ganador global.

---

## 4. El usuario exige cross-validation antes del registro final

Esto cambia la calidad de la evidencia.

Se pre-registraron dos experimentos:

### E006 — Architecture rolling temporal CV

`experimentos/modelo_3/architecture_cv/`

Diseño:

- cuatro folds forward-chaining por `leads.created_at`;
- cada lead permanece íntegro dentro de cada fold;
- validation inmediatamente anterior al test;
- bloques test disjuntos;
- predicciones OOF;
- bootstrap por lead.

### E007 — Trajectory / progression CV

`experimentos/modelo_3/trajectory_cv/`

Mismos folds de E006.

Único cambio principal:

- añadir variables explícitas de trayectoria/progresión.

PR conjunto: [#10 — Add rolling temporal CV and trajectory progression experiments](https://github.com/jcval94/spot2/pull/10).

---

## 5. E006 resuelve la incertidumbre arquitectónica

OOF:

- 7,980 snapshots;
- 1,936 leads.

Macro AP:

- Specialist CatBoost: 0.4720;
- Specialist RF: 0.4698;
- pooled CatBoost + stage: 0.4665;
- Multi-Head: 0.4498.

Deltas vs Multi-Head:

- Specialist CatBoost: +0.0222 AP, IC95% [+0.0068,+0.0361];
- RF: +0.0201, IC95% [+0.0078,+0.0321];
- pooled CatBoost: +0.0167, IC95% [+0.0016,+0.0315].

Además:

- T1 favorece robustamente modelos tabulares;
- T2 también favorece RF/CatBoost frente al head T2.

**Conclusión:** la superioridad del Multi-Head deja de ser defendible.

---

## 6. E007 valida trajectory, pero no como feature universal

Se añadieron 19 features point-in-time:

- gaps entre inquiries;
- velocidad;
- respuestas ya resueltas;
- inquiries pendientes;
- tiempo desde aceptación;
- revisitas/diversidad de spots;
- cambios de área/presupuesto/urgencia;
- escalamiento de `asked_visit`;
- cambio de canal.

Resultado T2:

- pooled CatBoost: ΔAP +0.0161, IC95% [+0.0003,+0.0322];
- Multi-Head: ΔAP +0.0155, IC95% [+0.0013,+0.0303];
- RF: ΔAP -0.0095, IC95% [-0.0191,-0.0002];
- specialist CatBoost: delta no robustamente positivo.

**Conclusión:** trajectory es información real, pero su utilidad depende de la arquitectura.

---

## 7. Decisión final

Se abandona Multi-Head como recomendación por defecto.

Baseline operativo recomendado:

**pooled CatBoost + stage + trajectory/progression**

Razones:

1. evidencia robusta en rolling CV;
2. una sola arquitectura;
3. menos complejidad de despliegue;
4. trajectory añade señal en T2;
5. evita un meta-router inestable.

Specialist CatBoost/RF se conservan como challengers.

---

## 8. Cierre y persistencia

GitHub Actions en `main`:

- validó E006;
- ejecutó E006;
- finalizó harness;
- validó outputs;
- validó E007;
- ejecutó E007;
- finalizó harness;
- persistió resultados;
- subió artifacts.

Commit de resultados:

`35af3b30e2028051f4f427e89b5e5db7437e2a50`

La evidencia final vive en EV-011/EV-012 y los harness records correspondientes.
