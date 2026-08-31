# Chronology

- Repository audit established duplicate CSV/Parquet sources and the data grains.
- Temporal audit showed that every inquiry follows lead creation, invalidating all
  inquiry-derived T0 features.
- T0 outcome drift was traced to growing inquiry exposure rather than a stable
  conversion mechanism.
- T1 was frozen as the primary contract and exact train/validation/holdout
  boundaries were pre-registered with seven-day purges.
- Existing matching metrics were demoted after entity overlap was identified.
- Existing dynamic targets were demoted after dependence on inconsistent
  `broker_response_hours` was identified.
- Availability joins were frozen to strict backward as-of; nearest joins became a
  deliberately leaky stress condition.
- Cluster and LLM findings were demoted to hypotheses until refit/evaluation under
  the corrected contracts.
- Inventory missingness was converted into explicit lower/upper bounds and listing
  compatibility was marked conditional because listing fields are unversioned.
- Lead Quality and combined Opportunity were evaluated on the same holdout with
  paired bootstrap uncertainty; the broad E102 model and its combination failed
  the operational gate. This decision is preserved but superseded by E113/E114.
- Target sensitivities confirmed that 7/14/30-day maturity barely changes the T1
  rate, while the any-visit-30-day target retains strong exposure drift.
- A live LLM run on fully fabricated controls/contradictions achieved 100% schema
  validity and added 50 recall points over lexical rules in that controlled task.
  No natural inventory payload was exported and no natural accuracy is claimed.
- E113 replaced the broad high-variance feature set with one T0-safe Industrial ×
  (small-or-paid) interaction. It passed the pre-registered selection gate on
  rolling train folds and validation before procedural holdout scoring.
- E113 achieved holdout Lift@10 1.672x (95% bootstrap CI 1.381–1.984).
  E114 retained 1.370x (1.078–1.690) after conservative inventory serviceability.
- The recommendation changed from diagnostic-only to forward shadow validation
  followed by a guarded randomized pilot. Inventory incremental value remains
  unproven because E114 ranks below E113 and the proxy does not observe fallback success.
- E115 corrected the scope of the E113 claim: the promotion code excludes the
  procedural holdout, but the broader research process had already consumed it.
  Metrics remain unchanged; only forward data can provide confirmation.
- E116 removed arbitrary row-order tie breaking from capacity metrics. Precision,
  Recall and Lift now use fractional expected capture when a score tie crosses
  the capacity boundary. Quality Lift@10 becomes 1.689x [1.381, 1.982]; the
  forward-validation requirement is unchanged.
- E117 retained the parsimonious segment as a forward-shadow candidate using an
  aggregate gate (rolling mean/median >1, 2/4 folds >1, validation >1, bounded
  Brier). Two weak folds remain explicit; no deployment claim is made.
