---
name: spot2-experiment-sandbox
description: Use for every Spot2 repository change, experiment, analysis, artifact, report, or exploratory implementation to keep agent-generated work isolated under experimentos/, linked to evidence, and reflected in accumulated knowledge unless the user explicitly requests a different repository location.
---

# Spot2 Experiment Sandbox

## Purpose

Protect the main repository from experimental sprawl while preserving a complete, auditable history of what was tried and what was learned.

Default rule:

> Everything generated or modified as part of experimental work must live under `experimentos/`.

Do not create new root-level code, analysis, artifacts, notebooks, reports, tests, harnesses, or exploratory folders unless the user explicitly requests that location.

## Allowed structural exceptions

Only these locations may be outside `experimentos/` without a new explicit user instruction:

1. `.agents/skills/`
   - Repository skills must live here so agents can discover them.
2. `.github/workflows/`
   - GitHub requires workflow definitions here.
   - Workflows must be thin launchers whose code, results, and artifacts point back into `experimentos/`.
3. Canonical challenge inputs already owned by the repository:
   - `data/`
   - `assessment.md`
   - `feature_dictionary.md`
   - candidate-facing canonical documentation already present in the repo.

Treat these as inputs or platform constraints, not permission to place experimental outputs beside them.

Any other exception requires an explicit instruction from the user for that specific change.

## Canonical experiment area

Use:

`experimentos/<experiment_name>/`

Each experiment should keep together, as applicable:

- specification;
- executable code;
- requirements;
- README;
- results;
- plots;
- model artifacts;
- local notes;
- `EVIDENCIA.md`.

Do not scatter one experiment across unrelated repository folders.

## System utilities

Shared experiment infrastructure created by the agent belongs in:

`experimentos/_sistema/`

Examples:

- experiment harness;
- harness tests;
- experiment templates;
- validation utilities.

Do not place shared experimental infrastructure at repository root.

## Accumulated knowledge

Canonical accumulated findings live in:

`experimentos/conocimiento_agregado/`

The primary index is:

`experimentos/conocimiento_agregado/DESCUBRIMIENTOS.md`

When an experiment yields a material finding, update this knowledge base.

A discovery must include:

- what was observed;
- what it means;
- what it does **not** prove;
- status: `SUPPORTED`, `NOT_SUPPORTED`, `INCONCLUSIVE`, or `PROPOSAL`;
- experiment path;
- evidence ID / evidence path;
- next implication when useful.

Never add a discovery without evidence.

Never delete an old discovery merely because a later experiment disagrees. Mark it superseded or refined and link the newer evidence.

## Evidence registry

Canonical evidence lives in:

`experimentos/Evidencias/`

Every experiment must have a corresponding evidence entry.

Recommended naming:

`EV-###_<experiment_name>.md`

Evidence entries must identify:

- experiment;
- evidence status;
- exact source artifacts/results;
- key numeric results where relevant;
- leakage/validation caveats;
- related accumulated discoveries.

Evidence is not a duplicate result dump. It is the index that lets a reviewer trace a claim back to the files that support it.

## Mandatory experiment-to-evidence link

Every experiment folder must contain:

`EVIDENCIA.md`

That file links to its canonical entry under `experimentos/Evidencias/`.

The canonical evidence entry links back to the experiment and its underlying result files.

Therefore the chain is always:

`discovery -> evidence -> experiment/result`

and:

`experiment -> EVIDENCIA.md -> canonical evidence -> discovery`

## Workflow rule

A workflow may exist in `.github/workflows/`, but it should:

- execute code under `experimentos/`;
- read experiment requirements from `experimentos/`;
- persist committed results under `experimentos/`;
- persist traceability records under `experimentos/Evidencias/` when appropriate;
- avoid introducing new root-level artifact directories.

## Before writing to the repository

Ask internally:

1. Is this an explicit user-requested exception?
2. Is it a required skill or GitHub workflow?
3. Is it a canonical input already owned by the challenge?

If all answers are no, the destination must begin with:

`experimentos/`

## Before completing an experiment

Verify:

- all generated files are inside the experiment sandbox;
- the experiment has `EVIDENCIA.md`;
- the central evidence entry exists;
- material findings are represented in accumulated knowledge;
- claims link to evidence;
- negative or inconclusive results are preserved;
- no root-level experimental debris was introduced.

## Cleanup / migration

When legacy agent-generated work exists outside `experimentos/`, prefer migrating it into the sandbox and updating references rather than maintaining two parallel experiment areas.

Do not rewrite scientific conclusions during a mechanical migration.

## Multi-experiment research flow

When a research line spans several governed experiments, changes its recommendation, or reaches closure, use `spot2-research-chronicle` and maintain:

`experimentos/registro_flujo/<line_name>/`

This registry documents chronology and decision evolution. It does **not** replace `Evidencias/` or `conocimiento_agregado/`.

## Fundamental rule

Repository cleanliness and scientific traceability are both hard constraints.

An experiment is not complete merely because the code ran. It is complete when its code, result, evidence, and resulting knowledge are all traceable inside the experiment sandbox.
