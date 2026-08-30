---
name: spot2-research-chronicle
description: Use when a Spot2 research line spans multiple experiments, changes its recommendation, is being handed off, or is ready to close. Maintains a durable research-flow chronicle under experimentos/registro_flujo/ without duplicating scientific evidence.
---

# Spot2 Research Chronicle

## Purpose

Preserve the **evolution of reasoning across experiments**.

The experiment system already answers:

- what was tested;
- what metrics resulted;
- what evidence supports a discovery.

This skill answers:

> How did a research line evolve from its original question to the current decision, and why did the recommendation change?

Do not use this skill to duplicate experiment READMEs or evidence dumps.

## When to use

Use this skill when any of the following is true:

1. a line has at least three materially related experiments;
2. a later experiment refines, supersedes, or contradicts an earlier recommendation;
3. the user asks to document the full process, history, reasoning, or conversation;
4. the line is being handed to another analyst/agent;
5. the user asks whether the line is closed;
6. a research phase is being formally closed.

For a single isolated experiment, use `spot2-experiment` and the normal evidence chain instead.

## Canonical location

Use:

`experimentos/registro_flujo/<line_name>/`

Global index:

`experimentos/registro_flujo/README.md`

Do not put flow chronicles at repository root.

## Required files for a closed multi-experiment line

### README.md

Must contain:

- flow ID/name;
- status;
- original question;
- current answer;
- why the line is or is not closed;
- navigation to the other flow files;
- links to canonical evidence.

Valid high-level states:

- `ACTIVE`
- `DECISION-READY`
- `CLOSED / DECISION-READY`
- `SUPERSEDED`

### CRONOLOGIA.md

Record experiments and important analytical steps in order.

For each important step include:

- question/hypothesis at that moment;
- experiment or analysis;
- primary methodological change;
- result;
- decision made with the evidence available **at that time**;
- what new uncertainty led to the next step.

Do not rewrite history as if the final answer was obvious from the start.

### DECISIONES.md

Maintain a decision log.

Each material decision should say:

- decision;
- evidence available;
- whether it remains current, was refined, or was discarded;
- reason it changed.

Explicitly preserve rejected hypotheses.

### TRAZABILIDAD.md

Map:

`question -> experiment -> evidence -> discovery -> decision`

Link to:

- experiment folders;
- EV records;
- discovery IDs;
- harness records or result directories where useful.

Do not copy large result tables when the evidence file already owns them.

### INCIDENCIAS_Y_CORRECCIONES.md

Record only incidents that materially improved reproducibility or interpretation, for example:

- leakage discovered;
- invalid join/cardinality;
- split redesign;
- dtype/data-contract failure;
- challenger too weak;
- mistaken causal interpretation;
- ID/evidence collision;
- concurrent-branch integration issue.

For each incident include:

- what failed or was misleading;
- correction;
- lesson.

Do not turn ordinary coding noise into a diary.

### CIERRE.md

A line may be marked `CLOSED / DECISION-READY` only when all material closure criteria are explicit.

Minimum closure review:

- question is answerable and answered;
- target/scoring/population are frozen enough for the decision;
- leakage has been reviewed;
- credible challengers were tested;
- uncertainty was tested at the appropriate unit;
- temporal robustness was checked when time matters;
- unfavorable/inconclusive results are retained;
- discoveries link to evidence;
- current decision is explicit;
- open items are separated into:
  - blockers;
  - optional refinement;
  - productization;
  - questions that require a new target/data source.

## Closure rule

Do not keep a research line open merely because another optimization is possible.

Close when the **decision question** is resolved to the required standard.

Examples that usually do **not** block architectural closure:

- feature ablation for parsimony;
- threshold tuning;
- deployment work;
- monitoring;
- production calibration.

Examples that **do** block closure:

- conclusion depends on one obviously weak challenger;
- known leakage is unresolved;
- result depends on one unstable temporal split when temporal generalization is central;
- current evidence contradicts the recommendation;
- key artifacts/results are missing.

## Relationship to other skills

### spot2-experiment-sandbox

Authority for placement, evidence registry, and accumulated knowledge.

The chronicle lives inside the sandbox.

### spot2-experiment

Authority for individual experiment contracts and lineage.

The chronicle summarizes experiment lineage; it does not replace specs/harness records.

### spot2-leakage

Authority for point-in-time review.

The chronicle records leakage decisions but does not invent a new leakage framework.

## Evidence discipline

The chronicle is a narrative index, not a new source of truth.

For numeric claims:

1. prefer linking to the canonical EV file;
2. when including a key number for readability, keep it consistent with the EV/result;
3. never create a new conclusion that is absent from accumulated knowledge without updating the discovery/evidence chain.

## Supersession discipline

Never delete an old decision because later evidence changed it.

Write:

- what was believed;
- why it was reasonable then;
- what new experiment changed the conclusion.

This is especially important for technical assessments, because the quality of the reasoning process can be as important as the final model.

## Concurrent repository changes

Before assigning:

- discovery IDs;
- evidence IDs;
- flow IDs;

read the current `main`.

If another branch occupied an ID, renumber the new flow rather than overwriting concurrent work.

Before merge:

- rebase/merge against current `main`;
- preserve concurrent discoveries;
- rerun repository governance when documentation paths or IDs change.

## Final handoff

When closing a research line, provide:

1. closure status;
2. current decision;
3. strongest evidence;
4. what was explicitly rejected;
5. what remains optional;
6. path to `experimentos/registro_flujo/<line_name>/`.

A line is not fully handed off if a future reviewer still needs the original chat to understand why the recommendation changed.
