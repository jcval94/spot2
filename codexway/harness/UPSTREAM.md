# Harness provenance

The implementation follows the contract/fingerprint discipline from the Spot2
experimental harness, but it is a self-contained rewrite with a narrower API. It
does not import `experimentos/` at runtime.

- Repository commit inspected: `643dd0a607de8f22b0c50f689f63c142e0de8d27`
- Upstream harness SHA-256:
  `6AEFDFA1F96F1CE3BD4E3D54A41A3CFDF7C908970B47C2ACD96CC37932F08766`
- Portability change: canonical Parquet/dataframe fingerprints replace raw CSV
  byte hashes, which differed across CRLF working trees on Windows.
- Deliberately omitted: legacy finalization paths under `$RUNNER_TEMP`, old
  inquiry-level target semantics, and dynamic response-time reconstruction.

