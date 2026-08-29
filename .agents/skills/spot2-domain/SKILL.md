---
name: spot2-domain
description: Use when interpreting Spot2 entities, tables, joins, units, business concepts, feature meaning, or data semantics before designing targets, features, profiles, matching, or models.
---

# Spot2 Domain

## Purpose

Maintain one canonical interpretation of the Spot2 assessment data.

Answer: **What does this data represent, and how does it relate to the rest of the system?**

Do not decide whether a feature is point-in-time safe, how an experiment should be evaluated, or which model should be used.

## Sources of truth

Use this precedence:

1. `assessment.md`
2. `feature_dictionary.md`
3. Actual table schemas and values
4. Experiment-specific documentation

If sources conflict, surface the discrepancy. Do not resolve it through an undocumented assumption.

## Canonical entities

### Lead
- ID: `lead_id`
- Table: `leads`
- Grain: one row per lead
- Represents demand for commercial real estate.

### Spot
- ID: `spot_id`
- Table: `spots`
- Grain: one row per commercial property/listing
- Represents supply.

### Broker
- Observed ID: `spots.broker_id`
- There is currently no broker master table in the candidate data.

Broker characteristics may be derived only from supported historical data. Do not invent broker demographics, performance attributes, or metadata.

`leads.user_type = broker` describes the type of lead. It does not establish identity with `spots.broker_id`.

### Inquiry
- ID: `inquiry_id`
- Relates `lead_id` to `spot_id`
- Grain: one lead-to-spot interaction.

An inquiry may contain information that became available after lead creation. Its presence in the table does not imply that every field is valid at every scoring stage.

### Spot attributes
- Key: `spot_id`
- Expected relation: 1:1 with `spots`.

### Availability snapshot
- ID: `snapshot_id`
- Grain: a spot availability observation at a point in time.

Availability is temporal. Historical analysis must not silently substitute the current state of a spot.

### Market context
Documented grain:

`state × municipality × corridor × sector × month`

Municipality and corridor are related geographic dimensions but are not necessarily a strict hierarchy.

## Economic rules

### Rent
Compare a lead's monthly rent budget against `price_total_mxn_rent`.

### Sale
Compare a lead's total purchase budget against `price_total_mxn_sale`.

Never silently mix price per square meter, total price, monthly rent, and sale price.

## Core concepts

### Lead Quality
Estimated likelihood of success under the proxy target declared by an experiment.

The candidate repository does not expose the hidden `outcomes` ground truth. A target built from candidate-visible events is a proxy and must be described as such.

### Inventory Availability
Ability of inventory observable at the relevant moment to satisfy a lead.

Conceptually consider sector, modality, area, budget, location, and availability.

### Lead Opportunity Score
Combination of Lead Quality and Inventory Availability. The exact formula belongs to an experiment, not to this skill.

### Fallback
A viable alternative when the preferred spot cannot satisfy the lead. The exact compatibility rule must be declared by the implementation or experiment.

## Workflow

When resolving a domain question:

1. Identify the entity or metric.
2. Confirm its grain and key.
3. Confirm units and nullable semantics when relevant.
4. Identify valid relationships to other entities.
5. Distinguish documented facts from inference.
6. Mark unsupported interpretation as `ASSUMPTION` or `UNKNOWN`.

## Required output

For material domain decisions, record entity, grain, key, interpretation, relevant relationships, units when applicable, and any assumption or uncertainty.

## Final checks

Verify that you did not:

- confuse lead type with broker identity;
- mix rent and sale units;
- treat corridor and municipality as interchangeable;
- invent a broker attribute;
- call a candidate-built target true conversion ground truth;
- make a temporal-safety decision that belongs to `spot2-leakage`.

This skill defines **what the data means**, not **when it can be used** or **whether it improves a model**.
