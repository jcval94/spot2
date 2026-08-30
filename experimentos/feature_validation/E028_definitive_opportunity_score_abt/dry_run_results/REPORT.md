# E028 protocol dry run

**This is an A/A instrumentation test, not an A/B treatment-effect result.**

- Mature candidate leads: 4,841
- Offline outcome observability: 95.19%
- Scheduled-visit rows missing event time: 14.97%
- Observed primary target rate (observable only): 38.98%
- Ambiguous unknown-event-time labels: 233
- Primary-rate retrospective uncertainty: 37.10% to 41.91%
- Control/Treatment pseudo assignment: 2,430 / 2,411
- SRM p-value: 0.7848
- Pseudo A/A delta (observable only): +0.97 pp
- Required matured sample for +2 pp MDE: 19,612
- Current candidate data covers: 24.7% of that requirement

## Interpretation

Passing this dry run means assignment and target plumbing are internally coherent.
Candidate-data AMBIGUOUS labels expose retrospective event-time limitations and are
never coerced to zero. Production must instrument the actual scheduled_visit
timestamp; failure to do so is a launch blocker.

This dry run does **not** provide causal evidence for the Opportunity system.
The definitive E028 must still be run prospectively with a frozen Treatment
artifact and full 30-day maturation.
