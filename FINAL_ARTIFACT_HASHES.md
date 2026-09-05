# Spot2 — Final Artifact Integrity Manifest

**Project status:** CLOSED  
**Finalized:** 2026-09-05

This manifest records the Git blob object identifiers for the principal submitted artifacts. These hashes identify the exact file contents stored in the repository at closure time.

| Artifact | Path | Git blob SHA-1 |
|---|---|---|
| Final package | `entregable/SPOT2_ASSESSMENT_FINAL.zip` | `3c271a88dfe749804f4d05ee7e59dbbdc5271aa7` |
| Executive One Pager | `entregable/02_one_pager/ONE_PAGER_SPOT2.pdf` | `7dcd43c19d266d4b6b019ee08d3df2e931ac7e4e` |
| Executive Deck | `entregable/06_deck_ejecutivo/DECK_EJECUTIVO_SPOT2.pdf` | `84b6d0eb952e79c00331a55d845b2cdf429c96aa` |
| Executed assessment notebook | `codexway/notebooks/spot2_assessment.ipynb` | `c70bf053aa875af3411638c5253d4e752f036ca8` |

## Verification

These are Git blob object IDs, not plain-file `sha1sum` values. Git computes a blob object ID over the canonical blob representation (`blob <size>\0<content>`), so the values can be used to verify that the repository still contains the exact versioned objects recorded at closure.

No modeling, feature, metric, threshold, or deliverable-content changes are intended after this closure point. Future experimentation belongs in `post-submission-research` or another explicitly post-submission branch.
