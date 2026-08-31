# Traceability

| Instruction artifact | SHA-256 |
|---|---|
| spot2-domain | `2C884BC5D052D3BD0F72293DF07EF1B37317A9A7C67E734B7A6E06C8E8B4932C` |
| spot2-experiment | `4FDE8A09C1F8D619EDC58CBE2157ED5035B5ECABCC88AAE78EFAE2BA834CD030` |
| spot2-experiment-sandbox | `CFDC2874F1DD38DD83F3BDDFF5CD60D4FC302ACD8EA13D7D11FB83BA79C2F82B` |
| spot2-leakage | `B20A1599AE802B7F0686C16D16A890596C0E4D3CA4382DC38E739F168567E00B` |
| spot2-research-chronicle | `1F5F710D8008A0E228BF102794527ED1D03831087417481E988EDEE7FC465F41` |

The run manifest contains the canonical raw-data and feature-policy fingerprints;
the split manifest freezes boundaries and population counts. Experiment records
capture source-code fingerprint, data fingerprint and Git commit, and are
immutable after finalization.

## Lift recovery line

| Question | Experiment | Evidence | Decision |
|---|---|---|---|
| Can clean T1 ranking exceed random at 10% capacity? | E113 | `EV-113_STABLE_SEGMENT.md` | Promote the stable-segment Logistic for forward validation |
| Does Opportunity retain absolute Lift >1? | E114 | `EV-114_OPPORTUNITY_LIFT.md` | Absolute gate GO; inventory incremental gate NO-GO |
| Is Lift invariant to row order at tied capacity boundaries? | E116 | `EV-116_TIE_AWARE_LIFT.md` | Use fractional expected capture; retain forward-validation requirement |
| Is the signal strong enough for a new forward shadow cohort? | E117 | `EV-117_FORWARD_CANDIDATE_GATE.md` | Candidate only; two weak folds remain explicit |
