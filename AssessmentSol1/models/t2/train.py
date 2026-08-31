from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ABT = ROOT / "abt"
FEATURES = ROOT / "features"
LQ = ROOT / "models" / "lead_quality"
for p in (ABT, FEATURES, LQ):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from build_t2 import build_t2
from build_features import add_t1_deterministic_features, build_t2_trajectory
from train import fit_logistic
from evaluate import metric_bundle

RANDOM_SEED = 20260830


def feature_sets() -> tuple[list[str], list[str]]:
    groups = json.loads((FEATURES / "feature_groups.json").read_text())
    baseline: list[str] = []
    for name in ("A_LEAD_INTAKE", "B_CURRENT_INQUIRY", "C_REFINEMENT"):
        baseline.extend(groups["t1"][name])
    baseline = list(dict.fromkeys(baseline))
    trajectory = list(groups["t2"]["TRAJECTORY"])
    return baseline, baseline + trajectory


def main() -> None:
    repo_root = HERE.parents[3]
    split = json.loads((ROOT / "splits" / "split_contract.json").read_text())
    dev_end = pd.Timestamp(split["development_end_exclusive"])

    audit_pl, model_pl = build_t2(
        repo_root,
        max_score_time_exclusive=dev_end.to_pydatetime(),
    )
    df = audit_pl.to_pandas()
    df["score_time"] = pd.to_datetime(df["score_time"], utc=True)
    valid_ids = set(model_pl["inquiry_id"].to_list())
    df = df.loc[df["inquiry_id"].isin(valid_ids)].copy()

    df = add_t1_deterministic_features(df)
    traj = build_t2_trajectory(repo_root)
    df = df.merge(traj, on="inquiry_id", how="left", validate="one_to_one")

    strict = pd.to_datetime(df["_strict_prior_max_time"], utc=True, errors="coerce")
    if (strict.notna() & (strict >= df["score_time"])).any():
        raise AssertionError("T2 trajectory contains same-time/future history")

    assignments = pd.read_csv(ROOT / "splits" / "split_assignments_t1.csv")
    assignments["lead_id"] = assignments["lead_id"].astype(int)
    df = df.merge(
        assignments[["lead_id","F1_role","F2_role","F3_role","F4_role"]],
        on="lead_id",
        how="left",
        validate="many_to_one",
    )

    base_features, trajectory_features = feature_sets()
    rows = []
    for fold in split["folds"]:
        fid = fold["id"]
        start = pd.Timestamp(fold["validation_start"])
        end = pd.Timestamp(fold["validation_end_exclusive"])
        role = f"{fid}_role"

        train = df.loc[
            df[role].eq("TRAIN") & (df["score_time"] < start)
        ].copy()
        val = df.loc[
            df[role].eq("VALIDATION")
            & (df["score_time"] >= start)
            & (df["score_time"] < end)
        ].copy()

        for variant, features in [
            ("T2_BASELINE", base_features),
            ("T2_TRAJECTORY", trajectory_features),
        ]:
            fitted = fit_logistic(train, features)
            prob = fitted.predict_proba(val)
            m = metric_bundle(val["target_value"].astype(int).to_numpy(), prob)
            rows.append({
                "variant": variant,
                "fold": fid,
                "train_n": len(train),
                "validation_n": len(val),
                **m,
            })

    out = HERE / "metrics"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "canonical_python_fold_metrics.csv", index=False)


if __name__ == "__main__":
    main()
