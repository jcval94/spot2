# PRE_P8_AUDIT — alignment, drift and repair review

**Assessment source:** repository `assessment.md`.  
**Audit date:** 2026-08-30.  
**Overall status:** **NEEDS ONE HARD GATE BEFORE P8**.

AssessmentSol1 is methodologically well aligned with the technical assessment, especially on leakage, temporal validation, target definition and negative-result discipline. The principal unresolved blocker is procedural/reproducibility: Prompt-4's authoritative runtime materialization has not produced `p4_qa_summary.json = PASS`.

## Alignment with the original assessment

| Original assessment area | Current status | Audit conclusion |
|---|---|---|
| EDA / FE | Strong | Business/temporal EDA exists; proxy rates by segment and Market Context narrative were added in this audit. Final notebook narrative still pending. |
| Lead Quality | Strong methodology, weak signal | Frozen target, temporal CV, baselines, Logistic/CatBoost, calibration, error analysis are present. Champion is correctly simple: **BASE_RATE + RAW**. |
| Threshold analysis | Repaired | A constant score cannot support a meaningful cutoff; `THRESHOLD_POLICY.md` makes that explicit instead of inventing one. |
| Inventory Availability | Partial | PIT candidate/availability architecture and FE exist; final serviceability heuristic/model and fallback evaluation are still pending. |
| Lead Opportunity Score | Pending | Must wait for independent Inventory evidence. |
| Scalability / monitoring | Pending final phase | Temporal/monitoring risks are already identified but production narrative is not finalized. |
| AI use | Repaired/documented | `llm/AI_USAGE.md` records actual methodological LLM use and negative semantic-feature evidence. |
| Product vision | Pending final phase | Not a blocker before P8. |
| Notebook / one-pager / slides | Pending final packaging | Expected at the end, not before P8. |

## Flags

### PRE8-001 — P4 runtime authority missing
**Severity:** BLOCKER.

The repository contains a P3 `qa_summary.json` with `status=PASS`, but Prompt 4 explicitly superseded that architecture. Current authority requires:

- `abt/artifacts/p4_qa_summary.json`;
- `abt/artifacts/p4_artifact_manifest.json`;
- P4 QA status `PASS`.

Those files are absent.

**Repair applied:** P3 manifest/QA now carry `SUPERSEDED_P3_EVIDENCE_ONLY`; `abt/artifacts/AUTHORITY.json` and `audit/pre_p8_gate.py` prevent accidental reuse.

**Remaining action:** run `python AssessmentSol1/abt/validate_abts.py` with project dependencies before P8.

### CAL-001 — learned calibrator selected on immaterial gain
**Severity:** HIGH, REPAIRED.

Platt improved CALIBRATION Brier by only ~0.0000195 and Log Loss by ~0.0000597. The frozen rule says RAW wins if learned calibration is not materially better.

The first implementation accepted any positive gain.

**Repair:** champion corrected from `BASE_RATE + PLATT` to **`BASE_RATE + RAW`**, using the existing 0.001 practical-tie tolerance as the materiality floor.

This correction is based only on CALIBRATION and is documented as a methodological inconsistency. It does not reset the consumed holdout.

### MET-001 — constant-score ranking metrics could mislead
**Severity:** MEDIUM, REPAIRED.

For a constant Base Rate:
- top-k Lift/Precision/Recall depend on arbitrary tie order;
- trapezoidal PR-AUC can appear spuriously high;
- calibration slope is not identifiable.

**Repair:** code now reports these as undefined for constant scores. AP/AUC/Brier/LogLoss remain valid.

### INV-001 — stale snapshot semantic contradiction
**Severity:** MEDIUM, REPAIRED.

`inventory/README.md` previously said >90d stale snapshots become UNKNOWN, while P4 implementation correctly keeps an existing snapshot historically known and carries freshness separately.

**Repair:** documentation now matches the P4 contract: missing snapshot = UNKNOWN; stale snapshot = known + stale.

### INV-002 — same-day Availability has no observation timestamp
**Severity:** MEDIUM, OPEN CAVEAT.

`snapshot_date` is date-only. Same-day backward matching assumes the business-date snapshot was usable at score time.

Sensitivity using previous-day-only snapshots shows small impact in this dataset:
- May coverage 100.00% → 99.63%;
- May no-serviceable remains 0%;
- same-day snapshots are ~3–5% of covered candidates.

**Decision:** not a current blocker, but production needs ingestion/event timestamps or a documented snapshot SLA.


### INV-003 — Historical price compatibility is not reconstructable
**Severity:** MEDIUM, OPEN CAVEAT FOR INVENTORY/FALLBACK.

The original assessment explicitly expects price/range compatibility in Inventory/Fallback. The delivered Spot prices are unversioned current/extract fields, so AssessmentSol1 correctly blocks them from historical point-in-time performance claims.

**Consequence:** P9 may use current prices for a present-state recommendation demo, clearly labeled as current-serving logic, but historical backtest metrics must not pretend those prices were known unchanged at past score times. A defensible historical price-compatibility evaluation requires price version history/effective timestamps.

### GOV-001 — stale P3 artifacts looked authoritative
**Severity:** MEDIUM, REPAIRED.

P3 artifacts remain useful evidence but are forbidden as current inputs. Explicit authority metadata now prevents the old `PASS` from being confused with Prompt 4.

### ASSUMP-001 — Spot structural/attribute immutability is not source-proven
**Severity:** MEDIUM, DOCUMENTED.

The original assessment does not provide version history or explicitly guarantee immutable listing attributes. AssessmentSol1 uses an explicit modeling assumption for structural candidate fields and `spot_attributes`.

The wording was repaired so it no longer implies the candidate package supplied that guarantee.

This assumption must remain visible in Inventory/fallback conclusions and should be tested against versioned production data later.

### HLD-001 — procedural holdout consumed before freeze
**Severity:** HIGH, PERMANENT CAVEAT.

The holdout cannot be made pristine again. It did not drive feature/model/calibration decisions, but the strict protocol was violated by the execution export.

June remains diagnostic-only. Final confirmation requires new/hidden evidence.

## Drift conclusion

### LeadQuality
No repair is justified:
- DEVELOPMENT prevalence is broadly stable;
- May CAL prevalence = **20.83%**;
- June mature diagnostic prevalence = **19.41%**;
- core categorical mix remains very stable;
- numeric T1 intent/need shifts are small to moderate.

### Clock drift
First-inquiry lag changes strongly and remains audit-only. Future total-inquiry exposure also declines near the extraction boundary and remains forbidden as a predictor.

### Inventory
This is the real drift regime:
- Availability coverage rises from ~54% in 2025H1 to ~100%;
- candidate depth roughly doubles;
- freshness distribution changes.

Inventory must therefore be evaluated by temporal cohort and coverage state independently of LeadQuality.

## Feature-registry reconciliation

Static audit passed:

- A Lead Intake: 27/27 registered, allowed, no forbidden;
- B Current Inquiry: 13/13;
- C Refinement: 13/13;
- E Selected Spot Context: 10/10 with Matching/Inventory roles;
- T2 trajectory: 33/33;
- `llm_*`: explicitly REJECTED/FORBIDDEN.

No silent Inventory/Matching feature is present in T1 core.

## Split/population reconciliation

- split assignments: 5,000 rows / 5,000 unique leads;
- DEVELOPMENT 4,368;
- CALIBRATION 312;
- PROCEDURAL_HOLDOUT 290;
- POST_HOLDOUT_AUDIT 30;
- prediction-population overlap: 0 across development OOF / calibration / June diagnostic.

## Go / no-go for Prompt 8

**NO-GO today solely because PRE8-001 is still open.**

Once the Prompt-4 runtime gate produces an authoritative PASS, Prompt 8 may proceed under these rules:

1. T1 target/model remain frozen;
2. P8 uses DEVELOPMENT folds only for decisions;
3. June has no selection authority;
4. T0 exposure drift is an audit target, never a predictor;
5. T2 history stays strictly before current score time and respects fold boundary crossing;
6. P8 remains bounded to `T2_BASELINE vs T2_TRAJECTORY` — no new feature/model zoo.

After P8, prioritize the original assessment's Inventory/Fallback and combined Opportunity Score rather than extending stage modeling indefinitely.
