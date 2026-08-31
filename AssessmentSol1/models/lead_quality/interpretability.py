from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent


def logistic_coefficients(model_payload: dict) -> pd.DataFrame:
    pre = model_payload["preprocessor"]
    model = model_payload["model"]
    names = pre.get_feature_names_out()
    coef = model.coef_[0]
    return (
        pd.DataFrame(
            {
                "encoded_feature": names,
                "coefficient": coef,
                "odds_ratio": np.exp(coef),
                "direction": np.where(
                    coef > 0, "POSITIVE",
                    np.where(coef < 0, "NEGATIVE", "NEUTRAL"),
                ),
            }
        )
        .sort_values("coefficient", key=lambda s: s.abs(), ascending=False)
    )


def catboost_importance(model_payload: dict) -> pd.DataFrame:
    return (
        pd.DataFrame(
            {
                "feature": model_payload["features"],
                "importance": model_payload["model"].get_feature_importance(),
            }
        )
        .sort_values("importance", ascending=False)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()

    frozen = json.loads((HERE / "FROZEN_MODEL_CONFIG.json").read_text())
    if frozen["model_family"] == "BASE_RATE":
        payload = {
            "champion": "BASE_RATE + PLATT",
            "feature_importance_defined": False,
            "reason": (
                "The champion has no feature-dependent ranking. "
                "No causal or per-feature attribution exists."
            ),
            "challenger_interpretability": (
                "Logistic A coefficients are diagnostic only; see "
                "metrics/logistic_a_top_coefficients.csv and "
                "metrics/logistic_a_coefficient_stability.csv."
            ),
        }
        print(json.dumps(payload, indent=2))
        return

    if args.model is None:
        raise SystemExit("--model is required for a learned champion")
    model_payload = joblib.load(args.model)
    family = model_payload["model_family"]
    if family == "LOGISTIC":
        out = logistic_coefficients(model_payload)
    elif family == "CATBOOST":
        out = catboost_importance(model_payload)
    else:
        raise ValueError(family)
    print(out.to_csv(index=False))


if __name__ == "__main__":
    main()
