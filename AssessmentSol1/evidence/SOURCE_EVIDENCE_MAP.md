# Source Evidence Map

Precedence used here: **most recent executed result > documentation > proposal**. A file name such as “definitive” is not evidence by itself.

| decision | source | commit_or_pr | status | executed_or_proposed | reproducible_from_raw | future_leakage_risk | AssessmentSol1_action |
|---|---|---|---|---|---|---|---|
| Use explicit T0/T1/T2 scoring instants | E016 ABT FE + Modelo 3 lineage | main `3fee8d4`; PR #15 | ACCEPT_WITH_CHANGES | executed implementation | yes | medium if historical event timing is mishandled | reimplement stage construction from raw |
| T0 uses lead intake at `leads.created_at` | E016 manifest/README | main / PR #15 | ACCEPT_WITH_CHANGES | executed | yes | medium for historical counters/internal score | block internal score; audit conditional counters |
| Current mutable Spot state cannot be used historically | E016 + EV-030 | main; PR #9 `d3394b9` | ACCEPT | executed/validated | yes | high | block raw `days_on_market,total_inquiries,total_views,is_active`; reconstruct only if event history supports it |
| Availability must be backward-as-of | EV-010, E016, EV-023 | main; PR #9 | ACCEPT_WITH_CHANGES | executed | yes | high for future snapshot joins | latest `snapshot_date <= score_time`; >90d unknown guardrail |
| Same-month Market Context is not point-in-time safe without effective/publication time | E016, EV-030, EV-038 | main; PR #9 | ACCEPT | executed policy | yes | high | blocked until source semantics are proven |
| Current inquiry broker response/hours are future information | E016, EV-028 | main; PR #9 | ACCEPT | executed contract | yes | critical | never use current response as feature |
| Prior broker-response history may be used only when event time is already realized | EV-012, EV-027 | main; PR #9 | ACCEPT_WITH_CHANGES | executed | yes | high because event time is reconstructed/missing | permit only strict as-of history; default non-model until rebuilt and audited |
| `scheduled_visit_30d` is a historically useful target candidate but not the frozen primary target | EV-028 + AssessmentSol1 P2 bake-off | PR #9 `d3394b9`; AssessmentSol1 P2 | REJECT_AS_PRIMARY_KEEP_AS_AUDIT_ALTERNATIVE | historical protocol executed + clean-room methodological bake-off | yes | label-time ambiguity | retain as Target B sensitivity/audit only; frozen primary is T1 first-inquiry eventual scheduled_visit |
| 30-day outcome timestamp reconstruction has material missing timing | EV-028 / E016 | PR #9; main | ACCEPT | executed audit | yes | critical | preserve AMBIGUOUS; never coerce to negative |
| E029 fitted RF/preprocessor/calibrator are reusable evidence, not reusable artifacts | EV-029 | PR #9 | REJECT | executed artifact | no need | research-selection bias + fitted-state contamination | do not import any joblib/schema fitted state |
| E030 historical ABT is a specification/evidence source, not runtime data | EV-030 | PR #9 | REBUILD | executed PASS | yes | research contamination if imported | rebuild all rows/features from raw |
| Raw calendar/progress clocks are known but unstable for LeadQuality | EV-021/022 + EV-038 | PR #9 | ACCEPT_WITH_CHANGES | executed | yes | drift/research proxy risk | keep as audit diagnostics initially, not model features |
| `prior_searches` should not be promoted to LeadQuality | EV-026 + EV-038 | PR #9 | REJECT | executed | yes | instability/post-hoc selection | audit-only pending new independent evidence |
| Broker prior is not a demonstrated LeadQuality driver | EV-027 | PR #9 | REJECT | executed | yes | composition + response-time ambiguity | not a default scoring feature; routing hypothesis separate |
| Clustering/persona layers are not demonstrated global propensity lift | EV-006/010/013; D038–D049 | main | REJECT | executed | yes | multiple testing + consumed holdout | may inform explanations/routing hypotheses only; no inherited clusterer |
| Matching future test has been consumed by iterative discovery | EV-013 D052 | main `50d56e1` lineage | ACCEPT | executed | n/a | research overfitting | mark contaminated; cannot confirm new matching claims |
| Rules-first LLM residual design is appropriate for current listing copy | E017 | main `a18d0d3` | ACCEPT | executed | yes | low | retain as methodological principle only |
| LLM-derived listing-copy features improve LeadQuality | E017 | main `a18d0d3` | REJECT | executed | yes | post-hoc reuse | do not add `llm_*` to scoring ABT |
| GPT-5 nano as autonomous catalog-quality gate | live E015 | PR #19 `31c58cb` | REJECT | executed live | partially | false-positive/over-alerting risk | semantic discovery only, never autonomous gate |
| Deterministic semantic Rules improve LeadQuality Lift@10% | E018 | PR #20 `6cf8f58`, run 33297920881 | REJECT | executed | yes | repeated subset-search risk | keep for Inventory/Catalog QA, not LeadQuality |
| T0/T1 historical LeadQuality evidence is neutral after drift-aware FE research | EV-038/040 | PR #9 | ACCEPT_WITH_CHANGES | executed research closure | yes | strong research contamination | use as prior evidence, not as forced outcome of clean-room rebuild |
| No previously inspected candidate period may be called pristine unseen | EV-013, EV-029, EV-040 | main + PR #9 | ACCEPT | executed governance conclusion | n/a | critical | use “procedural final holdout”; true confirmation requires new/hidden data |

## Notes on branch-only evidence

PR #9, #19 and #20 are open as of this assessment pass. Their executed artifacts/results can outrank older documentation for the narrow questions they directly tested, but their code/artifacts are **not dependencies** of AssessmentSol1.

| Promote Parquet as canonical runtime format after CSV parity | P1 raw audit + raw commit provenance | AssessmentSol1 branch; raw commit `8f850cf` | ACCEPT | executed audit | yes | low | use Parquet only; CSV remains independent parity reference |
| Treat `spots.days_on_market,total_inquiries,total_views,is_active` as backtest features | P1 raw audit | AssessmentSol1 P1 | REJECT | executed audit | yes | critical | FORBIDDEN; rebuild new as-of measures from raw events only where semantics support it |
| Treat `spot_attributes` as historically known static data | explicit assessment-owner assumption + P1 1:1/raw audit | AssessmentSol1 P1/P2 revision | ACCEPT_WITH_ASSUMPTION | contract decision | yes under assumption | medium assumption risk | authorize T1/T2 when `spots.created_at <= score_time`; do not claim raw timestamp provenance |
| Join Availability by nearest timestamp | P1 availability audit | AssessmentSol1 P1 | REJECT | executed audit | yes | critical | backward as-of only; nearest selects future snapshot in 34.36% of inquiries |
| Use `availability.competing_inquiries_30d` as point-in-time feature | P1 temporal ontology | AssessmentSol1 P1 | PENDING | executed audit | n/a | high | block until trailing-window/effective-time semantics are proven |
| Use Market Context in historical model | P1 market audit | AssessmentSol1 P1 | REJECT | executed audit | yes | high | EDA_ONLY until publication/effective timestamp exists |
| Use `broker_response_hours` to timestamp outcomes/features | P1 inquiry audit | AssessmentSol1 P1 | REJECT | executed audit | yes | critical | audit-only in P1; requires true backend response-event time |
