# Incidencias y correcciones — caso de uso LLM

## I-LLM-01 — Confundir generación de explicación con necesidad de LLM

**Problema:** la primera arquitectura de fallback dejaba al LLM rerankear y explicar candidatos que ya estaban completamente descritos por variables estructuradas.

**Por qué era engañoso:** la explicación podía generarse con templates y el ranking con una función determinística. El uso del LLM corría el riesgo de ser ornamental.

**Corrección:** exigir que la tarea seleccionada dependa de comprensión de lenguaje natural y tenga un baseline no-LLM explícito.

**Lección:** “usar un LLM” no es un objetivo técnico; debe existir una clase de error o trabajo que el componente determinístico no resuelva igual de bien.

## I-LLM-02 — Triage sin raw inquiry text

**Problema:** el triage era conceptualmente atractivo, pero el dataset no contiene el mensaje.

**Corrección:** conservarlo como Product Vision y no afirmar lift o capacidad semántica demostrada.

**Lección:** no usar variables estructuradas como sustituto del input lingüístico para justificar un LLM.

## I-LLM-03 — Texto sintético como riesgo para la nueva propuesta

**Problema:** el copy de listings muestra alta repetición y frases sintéticas.

**Corrección:** Rules-only es baseline obligatorio y la conclusión puede ser NOT_SUPPORTED.

**Lección:** el experimento debe poder concluir que el LLM no vale la pena.
