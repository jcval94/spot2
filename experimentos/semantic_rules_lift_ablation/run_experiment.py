from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESULTS = HERE / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

ABT_DIR = ROOT / "experimentos" / "abt_feature_engineering"
RULE_DIR = ROOT / "experimentos" / "llm_semantic_feature_pilot"
sys.path.insert(0, str(ABT_DIR))
sys.path.insert(0, str(RULE_DIR))

from build_abts import build_all, read_inputs  # noqa: E402
from feature_engineering import (  # noqa: E402
    AVAIL_CATS,
    INQUIRY_CATS,
    LEAD_CATS,
    MATCH_CATS,
    SPOT_CATS,
)
from build_rule_sidecar import build as build_rule_sidecar  # noqa: E402

SEED = 42
FOLDS = [
    {"fold": 1, "train_end": 0.45, "val_end": 0.55, "test_end": 0.65},
    {"fold": 2, "train_end": 0.55, "val_end": 0.65, "test_end": 0.75},
    {"fold": 3, "train_end": 0.65, "val_end": 0.75, "test_end": 0.85},
    {"fold": 4, "train_end": 0.75, "val_end": 0.85, "test_end": 0.95},
]
TARGET = "target_scheduled_visit_30d"
STAGES = {1: "T1_first_inquiry", 2: "T2_engaged"}
BASE_CAT = set(LEAD_CATS + INQUIRY_CATS + SPOT_CATS + MATCH_CATS + AVAIL_CATS)

RULE_NUM = [
    "rule_direct_conflict_flag",
    "rule_land_building_copy_flag",
    "rule_security_ambiguity_flag",
    "rule_retail_adaptive_use_flag",
    "rule_semantic_signal_count",
]
RULE_CAT = ["rule_semantic_review_tier"]
RULE_FEATURES = RULE_NUM + RULE_CAT

N_BOOT = 1000


def make_model(seed: int) -> CatBoostClassifier:
    return CatBoostClassifier(
        iterations=450,
        depth=6,
        learning_rate=0.04,
        loss_function="Logloss",
        eval_metric="PRAUC",
        l2_leaf_reg=4.0,
        random_seed=seed,
        thread_count=4,
        verbose=False,
        allow_writing_files=False,
    )


def frame(df: pd.DataFrame, cols: list[str], cat_cols: list[str]) -> pd.DataFrame:
    x = df[cols].copy()
    cats = set(cat_cols)
    for c in cols:
        if c in cats:
            x[c] = x[c].astype("string").fillna("__MISSING__").astype(str)
        else:
            x[c] = pd.to_numeric(x[c], errors="coerce").replace([np.inf, -np.inf], np.nan)
    return x


def lift_at(y: np.ndarray, p: np.ndarray, frac: float = 0.10) -> float:
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    base = float(y.mean())
    if base <= 0 or len(y) == 0:
        return np.nan
    n_top = max(1, int(np.ceil(len(y) * frac)))
    order = np.argsort(-p, kind="mergesort")
    return float(y[order[:n_top]].mean() / base)


def recall_at(y: np.ndarray, p: np.ndarray, frac: float = 0.20) -> float:
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    positives = int(y.sum())
    if positives == 0:
        return np.nan
    n_top = max(1, int(np.ceil(len(y) * frac)))
    order = np.argsort(-p, kind="mergesort")
    return float(y[order[:n_top]].sum() / positives)


def metrics(y: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    return {
        "roc_auc": float(roc_auc_score(y, pred)),
        "average_precision": float(average_precision_score(y, pred)),
        "lift_top_10pct": lift_at(y, pred, 0.10),
        "recall_top_20pct": recall_at(y, pred, 0.20),
    }


def attach_rules(abts: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    leads, spots, attrs, inquiries, availability, market = read_inputs(ROOT)
    sidecar = build_rule_sidecar(spots, attrs)
    keep = ["spot_id"] + RULE_FEATURES
    out = {}
    for name in ["T1", "T2"]:
        d = abts[name].merge(sidecar[keep], on="spot_id", how="left", validate="many_to_one")
        if d[RULE_FEATURES].isna().any().any():
            raise ValueError(f"Missing semantic-rule features after join for {name}")
        out[name] = d
    return out, sidecar


def split_fold(df: pd.DataFrame, lead_order: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    n = len(lead_order)
    a = max(1, int(n * cfg["train_end"]))
    b = max(a + 1, int(n * cfg["val_end"]))
    c = min(n, max(b + 1, int(n * cfg["test_end"])))
    train_ids = set(lead_order.iloc[:a]["lead_id"])
    val_ids = set(lead_order.iloc[a:b]["lead_id"])
    test_ids = set(lead_order.iloc[b:c]["lead_id"])
    return (
        df[df["lead_id"].isin(train_ids)].copy(),
        df[df["lead_id"].isin(val_ids)].copy(),
        df[df["lead_id"].isin(test_ids)].copy(),
    )


def fit_variant(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    cols: list[str],
    cat_cols: list[str],
    seed: int,
) -> np.ndarray:
    xtr = frame(train, cols, cat_cols)
    xva = frame(val, cols, cat_cols)
    xte = frame(test, cols, cat_cols)
    model = make_model(seed)
    model.fit(
        xtr,
        train[TARGET].to_numpy(dtype=int),
        cat_features=cat_cols,
        eval_set=(xva, val[TARGET].to_numpy(dtype=int)),
        use_best_model=True,
        early_stopping_rounds=50,
        verbose=False,
    )
    return model.predict_proba(xte)[:, 1]


def build_oof(
    abts: dict[str, pd.DataFrame],
    feature_sets: dict[int, list[str]],
    lead_order: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    parts = []
    fold_rows = []

    for sid, name in STAGES.items():
        d = abts["T1" if sid == 1 else "T2"].copy()
        base_cols = list(feature_sets[sid])
        base_cat = [c for c in base_cols if c in BASE_CAT]
        rules_cols = base_cols + RULE_FEATURES
        rules_cat = base_cat + RULE_CAT

        for cfg in FOLDS:
            fold = cfg["fold"]
            train, val, test = split_fold(d, lead_order, cfg)
            if min(len(train), len(val), len(test)) == 0:
                raise RuntimeError(f"Empty fold {fold} for stage {name}")

            y_test = test[TARGET].to_numpy(dtype=int)
            base_pred = fit_variant(
                train, val, test, base_cols, base_cat, SEED + sid * 100 + fold
            )
            rules_pred = fit_variant(
                train, val, test, rules_cols, rules_cat, SEED + sid * 100 + fold
            )

            for variant, pred in [("baseline", base_pred), ("semantic_rules", rules_pred)]:
                m = metrics(y_test, pred)
                fold_rows.append({
                    "fold": fold,
                    "stage_id": sid,
                    "stage": name,
                    "variant": variant,
                    "n": len(test),
                    "positive_rate": float(y_test.mean()),
                    **m,
                })

            part = test[[
                "lead_id", "inquiry_id", "spot_id", "score_time", TARGET,
                "rule_direct_conflict_flag", "rule_land_building_copy_flag",
                "rule_security_ambiguity_flag", "rule_retail_adaptive_use_flag",
                "rule_semantic_signal_count", "rule_semantic_review_tier",
            ]].copy()
            part.insert(0, "fold", fold)
            part.insert(1, "stage_id", sid)
            part.insert(2, "stage", name)
            part["baseline"] = base_pred
            part["semantic_rules"] = rules_pred
            parts.append(part)

    return pd.concat(parts, ignore_index=True), pd.DataFrame(fold_rows)


def cv_mean_metrics(fold_metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    stage_summary = (
        fold_metrics.groupby(["stage", "variant"], as_index=False)[
            ["roc_auc", "average_precision", "lift_top_10pct", "recall_top_20pct"]
        ].mean()
    )
    for row in stage_summary.itertuples():
        rows.append({
            "scope": row.stage,
            "variant": row.variant,
            "roc_auc": float(row.roc_auc),
            "average_precision": float(row.average_precision),
            "lift_top_10pct": float(row.lift_top_10pct),
            "recall_top_20pct": float(row.recall_top_20pct),
        })

    for variant in ["baseline", "semantic_rules"]:
        g = stage_summary[stage_summary["variant"].eq(variant)]
        rows.append({
            "scope": "MACRO",
            "variant": variant,
            "roc_auc": float(g["roc_auc"].mean()),
            "average_precision": float(g["average_precision"].mean()),
            "lift_top_10pct": float(g["lift_top_10pct"].mean()),
            "recall_top_20pct": float(g["recall_top_20pct"].mean()),
        })
    return pd.DataFrame(rows)


def fold_point_delta(fold_metrics: pd.DataFrame, scope: str, metric: str) -> float:
    if scope == "MACRO":
        vals = []
        for stage in STAGES.values():
            vals.append(fold_point_delta(fold_metrics, stage, metric))
        return float(np.mean(vals))
    p = fold_metrics[fold_metrics["stage"].eq(scope)].pivot(
        index="fold", columns="variant", values=metric
    )
    return float((p["semantic_rules"] - p["baseline"]).mean())


def bootstrap_deltas(oof: pd.DataFrame, fold_metrics: pd.DataFrame) -> pd.DataFrame:
    """Paired cluster bootstrap inside each temporal test fold.

    Predictions from independently trained folds are not globally rank-comparable.
    Therefore each bootstrap replicate computes the metric delta *within fold* and
    aggregates fold deltas, rather than concatenating raw probabilities across folds.
    """
    rng = np.random.default_rng(SEED + 2026)
    scopes = ["MACRO", *STAGES.values()]
    metric_names = ["lift_top_10pct", "average_precision", "roc_auc", "recall_top_20pct"]
    samples = {(scope, metric): [] for scope in scopes for metric in metric_names}

    fold_cache = {}
    for fold in sorted(oof["fold"].unique()):
        fdf = oof[oof["fold"].eq(fold)].reset_index(drop=True)
        lead_ids = fdf["lead_id"].drop_duplicates().to_numpy()
        lead_to_idx = {
            lead: np.flatnonzero(fdf["lead_id"].to_numpy() == lead)
            for lead in lead_ids
        }
        fold_cache[int(fold)] = (fdf, lead_ids, lead_to_idx)

    for _ in range(N_BOOT):
        fold_scope_deltas = {
            (scope, metric): []
            for scope in STAGES.values()
            for metric in metric_names
        }

        for fold, (fdf, lead_ids, lead_to_idx) in fold_cache.items():
            sampled = rng.choice(lead_ids, size=len(lead_ids), replace=True)
            idx = np.concatenate([lead_to_idx[x] for x in sampled])
            b = fdf.iloc[idx].reset_index(drop=True)

            for stage in STAGES.values():
                g = b[b["stage"].eq(stage)]
                if g.empty:
                    continue
                y = g[TARGET].to_numpy(dtype=int)
                try:
                    base_metrics = metrics(y, g["baseline"].to_numpy(dtype=float))
                    rule_metrics = metrics(y, g["semantic_rules"].to_numpy(dtype=float))
                except ValueError:
                    continue
                for metric in metric_names:
                    fold_scope_deltas[(stage, metric)].append(
                        rule_metrics[metric] - base_metrics[metric]
                    )

        for stage in STAGES.values():
            for metric in metric_names:
                vals = fold_scope_deltas[(stage, metric)]
                if vals:
                    samples[(stage, metric)].append(float(np.mean(vals)))

        for metric in metric_names:
            stage_vals = []
            valid = True
            for stage in STAGES.values():
                vals = fold_scope_deltas[(stage, metric)]
                if not vals:
                    valid = False
                    break
                stage_vals.append(float(np.mean(vals)))
            if valid:
                samples[("MACRO", metric)].append(float(np.mean(stage_vals)))

    rows = []
    for (scope, metric), vals in samples.items():
        arr = np.asarray(vals, dtype=float)
        rows.append({
            "scope": scope,
            "metric": metric,
            "point_delta": fold_point_delta(fold_metrics, scope, metric),
            "bootstrap_mean_delta": float(np.mean(arr)),
            "ci95_low": float(np.quantile(arr, 0.025)),
            "ci95_high": float(np.quantile(arr, 0.975)),
            "probability_delta_gt_0": float(np.mean(arr > 0)),
            "n_boot": int(len(arr)),
        })
    return pd.DataFrame(rows)


def semantic_coverage(oof: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for stage, g in oof.groupby("stage"):
        for tier, t in g.groupby("rule_semantic_review_tier", dropna=False):
            rows.append({
                "stage": stage,
                "review_tier": tier,
                "n": len(t),
                "share": len(t) / len(g),
                "positive_rate": float(t[TARGET].mean()),
                "mean_signal_count": float(t["rule_semantic_signal_count"].mean()),
            })
    return pd.DataFrame(rows)


def write_report(metrics_df: pd.DataFrame, bootstrap: pd.DataFrame, coverage: pd.DataFrame) -> str:
    def m(scope: str, variant: str) -> pd.Series:
        return metrics_df[
            metrics_df["scope"].eq(scope) & metrics_df["variant"].eq(variant)
        ].iloc[0]

    def b(scope: str, metric: str) -> pd.Series:
        return bootstrap[
            bootstrap["scope"].eq(scope) & bootstrap["metric"].eq(metric)
        ].iloc[0]

    macro_lift = b("MACRO", "lift_top_10pct")
    macro_ap = b("MACRO", "average_precision")

    if float(macro_lift["ci95_low"]) > 0 and float(macro_ap["point_delta"]) >= -0.001:
        conclusion = "SUPPORTED"
    elif float(macro_lift["point_delta"]) <= 0 and float(macro_lift["probability_delta_gt_0"]) < 0.50:
        conclusion = "NOT_SUPPORTED"
    else:
        conclusion = "INCONCLUSIVE"

    lines = [
        "# E018 — Semantic Rules Lift Ablation", "",
        f"**Conclusion: {conclusion}.**", "",
        "Question: does the free E017 semantic rule sidecar improve ranking lift over the canonical E016 ABT? Metrics are computed within each temporal test fold and then averaged; raw probabilities from different folds are never rank-mixed.",
        "",
        "## Cross-validated fold-mean results", "",
        "| Scope | Variant | AP | AUC | Lift@10% | Recall@20% |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for scope in ["T1_first_inquiry", "T2_engaged", "MACRO"]:
        for variant in ["baseline", "semantic_rules"]:
            r = m(scope, variant)
            lines.append(
                f"| {scope} | {variant} | {r.average_precision:.4f} | {r.roc_auc:.4f} | "
                f"{r.lift_top_10pct:.3f}x | {r.recall_top_20pct:.4f} |"
            )

    lines += ["", "## Paired bootstrap deltas: semantic_rules - baseline", "",
              "| Scope | Metric | Delta | 95% CI | P(delta>0) |",
              "|---|---|---:|---:|---:|"]
    for scope in ["T1_first_inquiry", "T2_engaged", "MACRO"]:
        for metric in ["lift_top_10pct", "average_precision", "roc_auc"]:
            r = b(scope, metric)
            lines.append(
                f"| {scope} | {metric} | {r.point_delta:+.4f} | "
                f"[{r.ci95_low:+.4f}, {r.ci95_high:+.4f}] | {r.probability_delta_gt_0:.1%} |"
            )

    lines += [
        "", "## Semantic coverage", "",
        f"OOF diagnostic rows with >=1 semantic signal: {(oof['rule_semantic_signal_count'] > 0).mean():.1%}.",
        "",
        "The rule features are Spot-level and therefore only tested at T1/T2; T0 is unchanged by design.",
        "",
        "## Decision rule", "",
        "SUPPORTED requires macro ΔLift@10% 95% CI entirely above zero and no material macro AP degradation (>0.001 absolute).",
        "A positive point estimate with an interval crossing zero is INCONCLUSIVE.",
        "A non-positive macro lift with bootstrap probability of improvement below 50% is NOT_SUPPORTED.",
        "",
        "## Leakage / semantics", "",
        "No LLM output is used. Features are deterministic functions of listing copy + spot attributes.",
        "They are treated as contemporaneous listing metadata, consistent with the static Spot representation in E016.",
        "Because the dataset does not version listing copy/attributes over time, production use would require confirming that these fields are immutable or reconstructable as-of score time.",
    ]

    (RESULTS / "conclusion.txt").write_text(conclusion + "\n", encoding="utf-8")
    return "\n".join(lines) + "\n"


def main() -> None:
    abts, feature_sets, _ = build_all(ROOT)
    abts_rules, sidecar = attach_rules(abts)

    leads = pd.read_csv(ROOT / "data" / "candidate" / "csv" / "leads.csv", parse_dates=["created_at"])
    lead_order = leads.sort_values(["created_at", "lead_id"])[["lead_id", "created_at"]].reset_index(drop=True)

    global oof
    oof, fold_metrics = build_oof(abts_rules, feature_sets, lead_order)
    metric_df = cv_mean_metrics(fold_metrics)
    boot = bootstrap_deltas(oof, fold_metrics)
    coverage = semantic_coverage(oof)

    oof.to_csv(RESULTS / "oof_predictions.csv", index=False)
    fold_metrics.to_csv(RESULTS / "fold_metrics.csv", index=False)
    metric_df.to_csv(RESULTS / "cv_mean_metrics.csv", index=False)
    boot.to_csv(RESULTS / "paired_bootstrap.csv", index=False)
    coverage.to_csv(RESULTS / "semantic_coverage.csv", index=False)

    report = write_report(metric_df, boot, coverage)
    (RESULTS / "REPORT.md").write_text(report, encoding="utf-8")

    conclusion = (RESULTS / "conclusion.txt").read_text().strip()
    macro_lift = boot[(boot["scope"] == "MACRO") & (boot["metric"] == "lift_top_10pct")].iloc[0]
    macro_ap = boot[(boot["scope"] == "MACRO") & (boot["metric"] == "average_precision")].iloc[0]

    summary = {
        "experiment_id": "E018_semantic_rules_lift_ablation",
        "conclusion": conclusion,
        "oof_rows": int(len(oof)),
        "oof_unique_leads": int(oof["lead_id"].nunique()),
        "semantic_signal_coverage": float((oof["rule_semantic_signal_count"] > 0).mean()),
        "macro_delta_lift_top_10pct": float(macro_lift["point_delta"]),
        "macro_delta_lift_ci95": [float(macro_lift["ci95_low"]), float(macro_lift["ci95_high"])],
        "macro_probability_lift_delta_gt_0": float(macro_lift["probability_delta_gt_0"]),
        "macro_delta_average_precision": float(macro_ap["point_delta"]),
        "rule_features": RULE_FEATURES,
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    harness_results = {
        "experiment_id": "E018_semantic_rules_lift_ablation",
        "metrics": {
            "macro_delta_lift_top_10pct": float(macro_lift["point_delta"]),
            "macro_delta_average_precision": float(macro_ap["point_delta"]),
        },
        "segment_metrics": {
            scope: {
                metric: float(
                    boot[(boot["scope"] == scope) & (boot["metric"] == metric)].iloc[0]["point_delta"]
                )
                for metric in ["lift_top_10pct", "average_precision", "roc_auc"]
            }
            for scope in STAGES.values()
        },
        "conclusion": conclusion,
        "caveats": [
            "semantic rules are Spot-level, so T0 is unchanged and excluded from the ablation",
            "listing copy and attributes are not versioned historically in the candidate data",
            "scheduled_visit remains a proxy target",
            "dataset is synthetic",
        ],
        "next_experiment": (
            "Promote semantic rule features only if lift is robustly positive; otherwise keep them for inventory QA only."
        ),
    }
    (RESULTS / "harness_results.json").write_text(
        json.dumps(harness_results, indent=2) + "\n", encoding="utf-8"
    )

    print(report)


if __name__ == "__main__":
    main()
