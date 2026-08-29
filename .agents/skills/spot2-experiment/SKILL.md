---
name: spot2-experiment
description: Use when proposing, implementing, comparing, documenting, or interpreting a Spot2 experiment so every change has a parent, a primary hypothesis, a leakage review, comparable metrics, and an auditable conclusion.
---

# Spot2 Experiment

## Purpose

Turn an idea into the smallest useful experiment that can support, reject, or leave the hypothesis inconclusive.

Governing question: **What changed relative to the parent experiment, and what happened?**

Prioritize traceability over the number of experiments.

## Required inputs

Before execution, establish:

- business or modeling question;
- falsifiable hypothesis;
- parent experiment, if one exists;
- primary change being tested;
- scoring time;
- target;
- eligible population;
- data sources;
- feature changes;
- validation strategy;
- evaluation metrics.

Use `spot2-domain` for semantic interpretation and `spot2-leakage` for point-in-time review.

The repository harness is the standard validator and recorder of the experiment contract.

## Identity and lineage

Every governed experiment receives:

`E###_<short_name>`

Examples:

- `E001_baseline`
- `E002_first_inquiry`
- `E003_lead_spot_match`
- `E004_broker_profile`

Declare `parent_experiment`. A baseline may use `null`.

Never reuse an experiment ID for materially different settings.

Do not retroactively invent IDs or parent relationships for legacy experiments unless there is explicit evidence for that lineage.

## Primary change

Every experiment declares exactly one `primary_change`.

Examples:

- add lead-spot compatibility features;
- add broker historical profile;
- change scoring from T0 to T1;
- replace the modeling family;
- add an external data source.

List other material changes under `secondary_changes`.

The more material changes occur simultaneously, the weaker attribution becomes.

## Experiment specification

Before running, create a machine-readable spec containing at least:

### Identity
- `experiment_id`
- `parent_experiment`

### Question
- `question`
- `hypothesis`
- `primary_change`
- `secondary_changes`

### Scoring
- stage or name;
- exact timestamp definition.

### Target
- event;
- horizon;
- anchor;
- censoring rule.

### Population
- eligibility;
- exclusions;
- analysis period.

### Data sources
List repository files used so the harness can fingerprint them.

### Features
Separate:
- `inherited`
- `added`
- `removed`

### Validation
Use temporal validation by default. Record strategy, time column, and split description.

### Metrics

Core metrics:

- `roc_auc`
- `average_precision`
- `brier`
- `log_loss`
- `lift_top_10pct`
- `recall_top_20pct`

Additional metrics are allowed but do not remove the core set.

### Segments

Review at least sector, modality, and lead type when sample size permits.

### Leakage

Attach the point-in-time review for newly added information.

Every added feature must be covered by the leakage review.

## Comparability

A candidate is directly comparable with its parent only when these remain materially equivalent:

- scoring moment;
- target;
- population;
- data sources;
- validation design.

If they differ, record:

`COMPARISON_STATUS = NON_EQUIVALENT`

This does not make the experiment invalid. It prevents an invalid claim that a metric delta is caused only by the model or feature change when the underlying question also changed.

## Execution boundary

This skill does not calculate metrics and does not create a second training framework.

`harness/experiment_harness.py` owns:

- contract validation;
- leakage-contract validation;
- parent comparability;
- data fingerprints;
- experiment record creation.

Individual experiment code continues to own feature construction and model fitting until repeated patterns justify a shared abstraction.

## Results

After execution, provide:

- experiment ID;
- core metrics;
- segment metrics when available;
- conclusion;
- caveats;
- next experiment.

Valid conclusions:

### SUPPORTED
The available evidence supports the hypothesis.

### NOT_SUPPORTED
The available evidence does not support the hypothesis or contradicts it.

### INCONCLUSIVE
The design or evidence does not support a sufficiently strong decision.

Do not convert `NOT_SUPPORTED` into a favorable narrative.

## Interpretation

Always separate:

### Finding
What was directly observed.

### Interpretation
What it may mean.

### Caveat
What limits that interpretation.

### Next experiment
The smallest next test that resolves the most important uncertainty.

Association is not causation unless the design justifies causal language.

## Immutability

Once an experiment record is finalized, do not silently alter target, population, feature set, split, scoring time, or conclusion-supporting metrics.

A material change requires a new experiment ID.

## Final checks

Before considering an experiment governed, verify:

- domain semantics are clear;
- added features have leakage evidence;
- leakage check passes;
- parent is explicit or intentionally null;
- primary change is identifiable;
- comparison status is explicit;
- core metrics are present;
- unfavorable results are retained;
- conclusion matches the evidence;
- next experiment follows from the remaining uncertainty.

The intended evidence chain is:

`question -> change -> measurement -> conclusion -> next question`.
