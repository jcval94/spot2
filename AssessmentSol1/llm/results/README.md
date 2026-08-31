# LLM results

This directory separates three evidence classes:

1. **historical canonical real-API evidence** — summarized from merged E017/E018 with hashes in `../UPSTREAM_EVIDENCE.md`;
2. **open-PR supplemental live evidence** — PR #19 only, never promoted to canonical while open;
3. **AssessmentSol1 reproduction** — deterministic Rules baseline recomputed from raw Spot/attribute data with no API call.

Files:
- `rules_baseline_reproduction.json` — machine-readable clean-room reproduction;
- `rules_baseline_summary.csv` — compact deterministic counts;
- `upstream_evidence_snapshot.json` — frozen provenance snapshot.

Optional runner outputs:
- `rules_sidecar_3000.csv` from `--mode rules`;
- `live_usage.csv` and `live_evaluation.json` from an explicitly requested `--mode live`;
- `cache_evaluation.json` from `--mode evaluate-cache`.

Prompt 12 intentionally performs **no new paid API run** because existing versioned real-API evidence is sufficient.
