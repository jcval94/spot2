# FEATURE_POLICY — P5–6

## Governing rule

A feature may enter a model only if it is present in `FEATURE_REGISTRY.csv`, has a defensible temporal lineage, is allowed for the stage, and belongs to the pre-registered feature set being evaluated.

No target, split, maturity assumption, ABT boundary, or forbidden-feature decision may be changed because of model performance.

## Missingness

Four states are distinguished:

1. **structural / not applicable** — e.g. rent budget for a sale-only lead; represented explicitly and never median-imputed as if unknown;
2. **genuinely unknown/not stated** — e.g. missing urgency; carry a flag/state and allow train-fitted numeric imputation only where a model requires a finite value;
3. **temporally unavailable** — blocked, not imputed;
4. **ordinary observed value**.

All learned imputation statistics fit on TRAIN only.

## Fold-aware transforms

The following require TRAIN-only fit: imputation statistics, scaling, learned bins, frequency encoding, target encoding, rare-category filtering, clusterers, and any learned category map.

Deterministic arithmetic, applicability flags, log1p, ratios, interval tests and strict-prior trajectory calculations do not require fit.

## LeadQuality separation

Core T1 contains only intake, current inquiry and T0→T1 refinement. Matching/Inventory variables are excluded unless Ablation E is explicitly selected.

## Clustering

Clustering is optional and interpretive. No cluster is in the frozen core T1 ablation plan. If a cluster later influences prediction, its estimator must fit inside each TRAIN fold. Broker Supply and Inquiry Intent are not reconstructed. Broker Service is rejected in this phase because clean temporal/incremental proof is absent.

Historical combination cells such as DN4 × LOC1 × BSV1 are `HERITED_EXPLORATORY_HYPOTHESIS` only and never multipliers/rules.

## Semantic Rules

E018 is **NOT_SUPPORTED** for LeadQuality ranking: macro ΔLift@10% = -0.0716, 95% CI crosses zero, P(delta>0)=45%. Therefore semantic rules are `QA_ONLY`; no CORE+SEMANTIC_RULES model ablation is authorized.

No `llm_*` feature is allowed.

## Price compatibility

Although budget-to-price compatibility is conceptually useful for Matching, the frozen P4 contract blocks unversioned Spot prices. It is REJECTED until historical price effective time/versioning exists.
