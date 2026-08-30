from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
ARTIFACTS = HERE / "artifacts"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="CSV with point-in-time T2 features.")
    ap.add_argument("--output", required=True, help="Output CSV with prediction.")
    ap.add_argument("--artifacts", default=str(ARTIFACTS))
    args = ap.parse_args()

    art = Path(args.artifacts)
    schema = json.loads((art / "feature_schema.json").read_text(encoding="utf-8"))
    cats = schema["categorical_features"]
    nums = schema["numeric_features"]
    required = cats + nums

    d = pd.read_csv(args.input)
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise SystemExit(f"Missing E029 scoring features: {missing}")

    for c in cats:
        d[c] = d[c].astype("object")
        d[c] = d[c].where(d[c].notna(), np.nan)
    for c in nums:
        d[c] = pd.to_numeric(d[c], errors="coerce").replace([np.inf, -np.inf], np.nan)

    prep = joblib.load(art / "preprocessor.joblib")
    model = joblib.load(art / "rf_t2.joblib")
    calibrator = joblib.load(art / "platt_calibrator.joblib")

    x = np.asarray(prep.transform(d[required]), dtype=np.float32)
    raw = np.clip(model.predict_proba(x)[:, 1], 1e-6, 1 - 1e-6)
    if calibrator is not None:
        logit = np.log(raw / (1 - raw)).reshape(-1, 1)
        pred = calibrator.predict_proba(logit)[:, 1]
    else:
        pred = raw

    out = d.copy()
    out["e029_leadquality_raw"] = raw
    out["e029_leadquality"] = pred
    out.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
