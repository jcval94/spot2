# E015 — Semantic cross-field discovery v2

## Status

This is **semantic discovery evidence**, not an OpenAI API result and not a human gold-label result.

The assistant manually simulated the intended LLM reasoning over the original 200-row discovery sample. That review exposed a new class of quality problem that Rules v1 did not represent: **cross-field semantic coherence**.

Because the discovery sample was inspected, every rule derived from it is explicitly post-discovery and is evaluated only on disjoint data.

## Discovery

The strongest pattern was:

```text
sector_name = Land
+
building / interior-condition language
```

Examples of the language family:

- “buena iluminación natural”;
- “recién remodelado”;
- “acabados modernos”;
- “listo para ocupar”;
- “acabados de primera”.

This is not treated as a direct factual contradiction. It is a **semantic_cross_field_mismatch**: the copy is conceptually incoherent with the listing category strongly enough to merit catalog review.

## Full-catalog projection

Across 3,000 spots:

- S001 appears in **230 Land listings**;
- **182** of those were not flagged by Rules v1;
- Rules v1 flags **322** unique spots;
- Rules v2 flags **504** unique spots;
- S001 therefore adds **182 unique review candidates**, or **6.07% of the full inventory**, before human confirmation.

These are candidate QA issues, not confirmed errors.

## Informational patterns deliberately excluded from actionability

### S002 — Retail × office/distribution language

109 listings use the phrase family “ideal para oficinas corporativas o centro de distribución” while categorized as Retail.

This is retained as `semantic_cross_field_mismatch` but **actionable=false** because adaptive re-use is plausible and the business ontology does not define incompatibility.

### S003 — strong security wording vs basic/cctv

327 listings use “seguridad 24/7 / control de acceso” while structured security is `basic` or `cctv`.

This is `ambiguous`, not actionable, because the ontology does not establish whether those categories contradict the text.

### Marketing claims without comparable fields

The semantic pass surfaced 2,570 `not_verifiable` observations across five recurring claim families:

- near shopping centers;
- road access;
- public transit access;
- market demand / appreciation;
- all services.

These do **not** count as QA positives. Missing a comparable field is not evidence that the copy is false.

## Leakage correction

The original 200-row `labeling_sample.csv` is now a **discovery sample**.

Rules v1 remains frozen.

Rules v2 adds only the promoted S001 semantic rule.

Final evaluation moves to:

- `labeling_holdout_v2.csv`: 240 listings, disjoint from discovery, broad evaluation;
- `semantic_challenge_v2.csv`: 100 disjoint Land listings, 50 S001-pattern and 50 controls, for pattern-specific precision analysis.

The challenge set is balanced by design and must **not** be used to estimate real-world prevalence.

## Revised business architecture

```text
listing
  |
  +--> Rules v1: known direct contradictions
  |
  +--> sampled / periodic LLM semantic discovery
          |
          +--> actionable new pattern?
                  |
                  v
              human review
                  |
                  v
             promote stable pattern
             into Rules v2/v3/...
```

The intended permanent role of the LLM is therefore **long-tail semantic rule discovery**, not repeated inference over already-known templated phrases.

## Final claim discipline

This evidence supports:

> Cross-field semantic review identified a material candidate pattern missed by the original rules.

It does NOT support:

> An LLM has higher precision/recall than Rules-only.

That claim still requires human labels and a clean LLM run on the v2 holdout.
