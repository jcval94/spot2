# Double-counting audit

## Verdict

**PASS for the final T1 product architecture.**

The frozen Lead Quality champion is `BASE_RATE + RAW`, probability `0.20375457875457875`, with **zero predictive features**. Therefore it cannot contain Spot match, availability, location, price, area fit or other Inventory constructs.

Inventory Serviceability owns the matching/serviceability concepts:

- modality compatibility;
- sector / geographic relaxation tier;
- relative area fit;
- backward-as-of availability;
- snapshot freshness/confidence;
- budget fit only when a historical versioned price exists (currently blocked).

The final Opportunity Score is therefore:

`constant clean Lead Quality prior × Inventory Serviceability`.

No Inventory component is counted inside the clean Lead Quality factor.

## Selected-Spot challenger

A pre-registered Lead Quality Ablation E deliberately contained selected-Spot context:

- selected Spot area ratio/gap;
- modality and sector compatibility;
- preferred municipality/corridor match;
- backward-as-of availability known/state;
- snapshot age;
- physical-attribute completeness.

This is a **conceptual overlap with Inventory**. Its classification is:

**EXPERIMENTAL / CHALLENGER_ONLY / PROHIBITED_FROM_FINAL_OPPORTUNITY_SCORE.**

The challenger was not promoted and cannot redefine Lead Quality. Using E inside the final multiplicative score would double count matching/availability and is prohibited.

## Component matrix

| Construct | Clean LeadQuality | Ablation E | Frozen Inventory | Final duplication |
|---|---|---|---|---|
| Spot match | No | Yes | Yes | No — E excluded |
| Availability | No | Yes | Yes | No — E excluded |
| Location | No | Yes | Yes | No — E excluded |
| Price/budget fit | No | No PIT-authorized price | Blocked/unknown | No |
| Area fit | No | Yes | Yes | No — E excluded |
| Freshness | No | Yes | Yes | No — E excluded |
| Lead prior | Constant prevalence | Learned challenger context | No | No |

`inventory_confidence` remains separately reported and is **not multiplied into Opportunity Score**, so freshness is not counted twice inside Inventory itself.

## Decision

The only conceptually coherent final architecture under the frozen evidence is the one already frozen: clean Lead Quality prior × separate Inventory Serviceability. Any future promotion of Spot-context Lead Quality would require a new score-contract version and a fresh double-counting review.
