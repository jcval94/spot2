# Incidents and evidence limitations

- Existing matching evaluation split rows by inquiry date while allowing the same
  lead in train and future test. Those metrics are not reused.
- Existing dynamic scoring inferred target event time from
  `broker_response_hours`; the field is internally inconsistent and was removed.
- Several historical discovery files contain stale cluster labels/metrics. Only
  the latest authoritative result artifacts were treated as evidence.
- The historical holdout is not globally virgin because prior experiments viewed
  outcomes from the same dataset. It is only procedurally held out from the new
  selection/calibration code.
- The supplied LLM labeling CSVs have empty human labels. Live model output can be
  generated, but no performance claim is complete until blinded review is frozen.
- Exporting natural inventory copy to an external LLM was not considered approved.
  The live run therefore used 40 fully fabricated cases only; repository listings
  stayed local. Natural-listing evaluation remains gated on explicit privacy opt-in
  and blinded human gold.
- The first Opportunity implementation collapsed stale/missing availability into
  zero serviceability. This was corrected to conservative/optimistic bounds;
  unknown history is no longer asserted to be unavailable.
- Multiplication by inventory reduced holdout AP from 0.2156 to 0.1988 and
  Lift@10 from 0.850x to 0.795x. Every final score is therefore marked diagnostic
  only under E102/E110. This result is preserved as the parent baseline and was
  superseded by the stability-constrained E113/E114 line.
- The broad Logistic was dominated by unstable, high-cardinality geography and
  had Lift@10 0.850x. E113 removed that variance and froze one interpretable,
  point-in-time-safe interaction selected on rolling train evidence plus validation.
  It must be revalidated on genuinely new forward data because the repository's
  historical holdout has been globally inspected.
