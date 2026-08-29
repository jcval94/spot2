# Lead attention experiment — empirical findings

Equivalent temporal analysis was executed against the same repository CSVs on 2026-08-29 while GitHub Actions returned no workflow runs for this private repo. The Actions workflow remains ready in .github/workflows/lead-attention-experiment.yml.

## Dataset used

- leads: 5,000
- inquiries: 22,576
- market_context: 500
- T0 eligible after 30-day right-censoring: 4,836
- T1 eligible first-inquiry records: 4,794
- inquiries with measured broker_response_hours: 19,178

## Main result

### T0 — lead creation, conservative leakage-safe baseline

- ROC AUC: 0.492
- Average Precision: 0.527
- Lift top 10%: 0.87x

Adding prior_searches, prior_inquiries and has_converted_before did not improve this temporal baseline in a separate ablation:

- ROC AUC: 0.488
- Average Precision: 0.522

### T1 — re-score immediately after first inquiry

Using only information known when the first inquiry arrives:

- ROC AUC: 0.632
- Average Precision: 0.621
- Lift top 10%: 1.22x

This is the strongest signal in the experiment. A two-stage architecture is justified: initial score at lead creation, followed by a dynamic re-score once interaction data exists.

Ablating explicit urgency and asked_visit did not reduce performance; in the equivalent run it slightly improved ROC AUC to 0.634. Therefore the evidence supports interaction-aware re-scoring, but does not support claiming that urgency alone drives the improvement.

## Response-time hypothesis

Observed scheduled-visit rate:

- broker response <= 6 hours: 19.64% (n=7,586)
- broker response > 24 hours: 21.21% (n=2,645)
- fast / slow rate ratio: 0.93x

Response-time buckets were roughly flat:

- <=2h: 19.15%
- 2–6h: 19.96%
- 6–12h: 19.69%
- 12–24h: 19.92%
- 24–48h: 21.55%
- >48h: 19.21%

A temporal predictive diagnostic using pre-response fields had ROC AUC 0.507. Adding response hours changed it only to 0.510.

Conclusion: this synthetic dataset does not support the claim that faster broker response causes or strongly predicts scheduled visits. broker_response_hours should not be sold as a winning feature. If Spot2 believes SLA speed matters operationally, validate it with a randomized routing/SLA experiment in production.

## LLM interpretation

The data does not contain raw inquiry text, so an incremental LLM-vs-non-LLM lift cannot be measured honestly.

The defensible LLM role is operational triage:
- extract intent and constraints from the raw message
- summarize the inquiry for the broker
- detect missing information
- propose a handling SLA
- produce a transparent priority reason

The current evidence supports dynamic re-scoring after interaction; it does not prove that an LLM itself improves conversion.

## Geographic context

Adding the provided month-matched market_context to T0 changed ROC AUC from 0.492 to 0.497. Exact state + municipality + corridor + sector + month coverage was only about 23.0%.

That is a small positive signal, but coverage is low enough that stronger municipality-level external enrichment is worth testing.

Recommended next sources:
1. INEGI municipality indicators
2. INEGI DENUE establishment density / sector mix
3. SEPOMEX postal-code catalog for spots where settlement is available
4. coordinate-based transport/accessibility features for spots
5. CONAPO population projections
6. Banxico time-series macro context

All external joins must be reproducible as-of the scoring timestamp.
