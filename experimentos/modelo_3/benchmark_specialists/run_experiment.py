from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier, early_stopping, log_evaluation
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

HERE = Path(__file__).resolve().parent
MODEL3 = HERE.parent
ROOT = MODEL3.parents[1]
RESULTS = HERE / "results"
CHARTS = RESULTS / "charts"
RESULTS.mkdir(parents=True, exist_ok=True)
CHARTS.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(MODEL3))

from data_pipeline import (  # noqa: E402
    CAT_FEATURES,
    NUM_FEATURES,
    build_snapshots,
    make_preprocessor,
    prepare_inquiries,
    read_data,
    stage_balanced_weights,
    temporal_split,
)
from models import (  # noqa: E402
    PooledStageModel,
    SharedMultiHead,
    STAGES,
    calibrate_by_stage,
    metric_bundle,
    metrics_table,
    predict,
    set_seed,
    train_model,
)

SEED = 42
N_BOOT = 500

SPECIALIST_MODELS = [
    "specialist_random_forest_calibrated",
    "specialist_extra_trees_calibrated",
    "specialist_lightgbm_calibrated",
    "specialist_catboost_calibrated",
]

MODEL_LABELS = {
    "multihead_calibrated": "Multi-Head",
    "pooled_nn_calibrated": "Pooled NN + stage",
    "separate_logistic": "Separate Logistic",
    "specialist_random_forest_calibrated": "Specialist Random Forest",
    "specialist_extra_trees_calibrated": "Specialist ExtraTrees",
    "specialist_lightgbm_calibrated": "Specialist LightGBM",
    "specialist_catboost_calibrated": "Specialist CatBoost",
    "pooled_catboost_calibrated": "Pooled CatBoost + stage",
    "validation_selected_hybrid": "Validation-selected hybrid",
}


def normalize_frames(*frames: pd.DataFrame) -> None:
    for frame in frames:
        for c in CAT_FEATURES:
            frame[c] = frame[c].astype("object")
            frame[c] = frame[c].where(frame[c].notna(), np.nan)
        for c in NUM_FEATURES:
            frame[c] = pd.to_numeric(frame[c], errors="coerce").replace([np.inf, -np.inf], np.nan)


def catboost_frame(frame: pd.DataFrame, include_stage: bool = False) -> pd.DataFrame:
    cols = CAT_FEATURES + NUM_FEATURES
    x = frame[cols].copy()
    for c in CAT_FEATURES:
        x[c] = x[c].astype("string").fillna("__MISSING__").astype(str)
    for c in NUM_FEATURES:
        x[c] = pd.to_numeric(x[c], errors="coerce").replace([np.inf, -np.inf], np.nan)
    if include_stage:
        x["stage_name"] = frame["stage_id"].map(STAGES).astype(str)
    return x


def fit_neural_models(
    x_train: np.ndarray,
    y_train: np.ndarray,
    s_train: np.ndarray,
    weights: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    s_val: np.ndarray,
    x_test: np.ndarray,
    s_test: np.ndarray,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, object], dict[str, pd.DataFrame]]:
    raw_val: dict[str, np.ndarray] = {}
    final_test: dict[str, np.ndarray] = {}
    calibration: dict[str, object] = {}
    histories: dict[str, pd.DataFrame] = {}

    set_seed()
    multi = SharedMultiHead(x_train.shape[1])
    multi, h_multi = train_model(
        multi, x_train, y_train, s_train, weights, x_val, y_val, s_val
    )
    mv = predict(multi, x_val, s_val)
    mt = predict(multi, x_test, s_test)
    mt_cal, mcal = calibrate_by_stage(mv, y_val, s_val, mt, s_test)
    raw_val["multihead_calibrated"] = mv
    final_test["multihead_calibrated"] = mt_cal
    calibration["multihead_calibrated"] = mcal
    histories["multihead"] = h_multi

    set_seed()
    pooled = PooledStageModel(x_train.shape[1])
    pooled, h_pooled = train_model(
        pooled, x_train, y_train, s_train, weights, x_val, y_val, s_val
    )
    pv = predict(pooled, x_val, s_val)
    pt = predict(pooled, x_test, s_test)
    pt_cal, pcal = calibrate_by_stage(pv, y_val, s_val, pt, s_test)
    raw_val["pooled_nn_calibrated"] = pv
    final_test["pooled_nn_calibrated"] = pt_cal
    calibration["pooled_nn_calibrated"] = pcal
    histories["pooled_nn"] = h_pooled

    return raw_val, final_test, calibration, histories


def fit_logistic(
    x_train: np.ndarray,
    y_train: np.ndarray,
    s_train: np.ndarray,
    x_val: np.ndarray,
    s_val: np.ndarray,
    x_test: np.ndarray,
    s_test: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    val = np.full(len(x_val), np.nan)
    test = np.full(len(x_test), np.nan)
    for sid in STAGES:
        tr, va, te = s_train == sid, s_val == sid, s_test == sid
        clf = LogisticRegression(max_iter=2500, solver="liblinear", random_state=SEED)
        clf.fit(x_train[tr], y_train[tr])
        val[va] = clf.predict_proba(x_val[va])[:, 1]
        test[te] = clf.predict_proba(x_test[te])[:, 1]
    return val, test


def fit_sklearn_specialists(
    factory,
    x_train: np.ndarray,
    y_train: np.ndarray,
    s_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    s_val: np.ndarray,
    x_test: np.ndarray,
    s_test: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    val = np.full(len(x_val), np.nan)
    test = np.full(len(x_test), np.nan)
    for sid in STAGES:
        tr, va, te = s_train == sid, s_val == sid, s_test == sid
        model = factory()
        model.fit(x_train[tr], y_train[tr])
        val[va] = model.predict_proba(x_val[va])[:, 1]
        test[te] = model.predict_proba(x_test[te])[:, 1]
    return val, test


def fit_lightgbm_specialists(
    x_train: np.ndarray,
    y_train: np.ndarray,
    s_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    s_val: np.ndarray,
    x_test: np.ndarray,
    s_test: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    val = np.full(len(x_val), np.nan)
    test = np.full(len(x_test), np.nan)
    for sid in STAGES:
        tr, va, te = s_train == sid, s_val == sid, s_test == sid
        model = LGBMClassifier(
            objective="binary",
            n_estimators=600,
            learning_rate=0.03,
            num_leaves=31,
            min_child_samples=30,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            random_state=SEED + sid,
            n_jobs=4,
            verbosity=-1,
        )
        model.fit(
            x_train[tr],
            y_train[tr],
            eval_set=[(x_val[va], y_val[va])],
            eval_metric="average_precision",
            callbacks=[early_stopping(50, verbose=False), log_evaluation(0)],
        )
        val[va] = model.predict_proba(x_val[va])[:, 1]
        test[te] = model.predict_proba(x_test[te])[:, 1]
    return val, test


def make_catboost(seed: int) -> CatBoostClassifier:
    return CatBoostClassifier(
        iterations=600,
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


def fit_catboost_specialists(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    val_pred = np.full(len(val), np.nan)
    test_pred = np.full(len(test), np.nan)
    cat_cols = list(CAT_FEATURES)
    for sid in STAGES:
        tr = train["stage_id"].eq(sid).to_numpy()
        va = val["stage_id"].eq(sid).to_numpy()
        te = test["stage_id"].eq(sid).to_numpy()
        xtr = catboost_frame(train.loc[tr])
        xva = catboost_frame(val.loc[va])
        xte = catboost_frame(test.loc[te])
        model = make_catboost(SEED + sid)
        model.fit(
            xtr,
            train.loc[tr, "target_30d"].to_numpy(dtype=int),
            cat_features=cat_cols,
            eval_set=(xva, val.loc[va, "target_30d"].to_numpy(dtype=int)),
            use_best_model=True,
            early_stopping_rounds=50,
            verbose=False,
        )
        val_pred[va] = model.predict_proba(xva)[:, 1]
        test_pred[te] = model.predict_proba(xte)[:, 1]
    return val_pred, test_pred


def fit_catboost_pooled(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    xtr = catboost_frame(train, include_stage=True)
    xva = catboost_frame(val, include_stage=True)
    xte = catboost_frame(test, include_stage=True)
    cat_cols = list(CAT_FEATURES) + ["stage_name"]
    model = make_catboost(SEED + 91)
    model.fit(
        xtr,
        train["target_30d"].to_numpy(dtype=int),
        cat_features=cat_cols,
        eval_set=(xva, val["target_30d"].to_numpy(dtype=int)),
        use_best_model=True,
        early_stopping_rounds=50,
        verbose=False,
    )
    return model.predict_proba(xva)[:, 1], model.predict_proba(xte)[:, 1]


def add_calibrated(
    name: str,
    val_pred: np.ndarray,
    test_pred: np.ndarray,
    y_val: np.ndarray,
    s_val: np.ndarray,
    s_test: np.ndarray,
    raw_val: dict[str, np.ndarray],
    final_test: dict[str, np.ndarray],
    calibration: dict[str, object],
) -> None:
    calibrated, params = calibrate_by_stage(
        val_pred, y_val, s_val, test_pred, s_test
    )
    raw_val[name] = val_pred
    final_test[name] = calibrated
    calibration[name] = params


def validation_stage_selection(
    val: pd.DataFrame,
    raw_val: dict[str, np.ndarray],
    final_test: dict[str, np.ndarray],
) -> tuple[dict[str, str], np.ndarray, pd.DataFrame]:
    candidates = [
        "multihead_calibrated",
        "pooled_nn_calibrated",
        "specialist_random_forest_calibrated",
        "specialist_extra_trees_calibrated",
        "specialist_lightgbm_calibrated",
        "specialist_catboost_calibrated",
        "pooled_catboost_calibrated",
    ]
    selection: dict[str, str] = {}
    rows = []
    stage_val = val["stage_id"].to_numpy(dtype=int)
    y = val["target_30d"].to_numpy(dtype=int)

    for sid, stage_name in STAGES.items():
        mask = stage_val == sid
        scores = {}
        for model in candidates:
            ap = float(average_precision_score(y[mask], raw_val[model][mask]))
            scores[model] = ap
            rows.append({"stage": stage_name, "model": model, "validation_ap": ap})
        selection[stage_name] = max(scores, key=scores.get)

    hybrid = np.full(len(next(iter(final_test.values()))), np.nan)
    for sid, stage_name in STAGES.items():
        chosen = selection[stage_name]
        # test ordering matches the shared stage arrays; use stage masks from prediction coverage
        # caller will replace using its test stage vector.
    return selection, hybrid, pd.DataFrame(rows)


def apply_hybrid(
    selection: dict[str, str],
    final_test: dict[str, np.ndarray],
    stage_test: np.ndarray,
) -> np.ndarray:
    out = np.full(len(stage_test), np.nan)
    for sid, stage_name in STAGES.items():
        mask = stage_test == sid
        out[mask] = final_test[selection[stage_name]][mask]
    return out


def macro_ap_auc(df: pd.DataFrame, pred: np.ndarray) -> tuple[float, float]:
    aps, aucs = [], []
    y = df["target_30d"].to_numpy(dtype=int)
    s = df["stage_id"].to_numpy(dtype=int)
    for sid in STAGES:
        mask = s == sid
        if mask.sum() == 0 or len(np.unique(y[mask])) < 2:
            continue
        aps.append(float(average_precision_score(y[mask], pred[mask])))
        aucs.append(float(roc_auc_score(y[mask], pred[mask])))
    return float(np.mean(aps)), float(np.mean(aucs))


def scope_metric(df: pd.DataFrame, pred: np.ndarray, scope: str, metric: str) -> float:
    y = df["target_30d"].to_numpy(dtype=int)
    s = df["stage_id"].to_numpy(dtype=int)
    if scope == "MACRO":
        ap, auc = macro_ap_auc(df, pred)
        return ap if metric == "average_precision" else auc
    sid = {v: k for k, v in STAGES.items()}[scope]
    mask = s == sid
    if metric == "average_precision":
        return float(average_precision_score(y[mask], pred[mask]))
    return float(roc_auc_score(y[mask], pred[mask]))


def bootstrap_deltas(
    test: pd.DataFrame,
    predictions: dict[str, np.ndarray],
    reference: str = "multihead_calibrated",
    n_boot: int = N_BOOT,
) -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 771)
    lead_ids = test["lead_id"].drop_duplicates().to_numpy()
    lead_to_idx = {
        lead: np.flatnonzero(test["lead_id"].to_numpy() == lead)
        for lead in lead_ids
    }
    scopes = ["MACRO", "T0_cold", "T1_first_inquiry", "T2_engaged"]
    metrics = ["average_precision", "roc_auc"]
    challengers = [m for m in predictions if m != reference]
    values = {(m, s, k): [] for m in challengers for s in scopes for k in metrics}

    for _ in range(n_boot):
        sampled = rng.choice(lead_ids, size=len(lead_ids), replace=True)
        idx = np.concatenate([lead_to_idx[x] for x in sampled])
        bdf = test.iloc[idx].reset_index(drop=True)
        ref_pred = predictions[reference][idx]
        for model in challengers:
            pred = predictions[model][idx]
            for scope in scopes:
                for metric in metrics:
                    try:
                        delta = scope_metric(bdf, pred, scope, metric) - scope_metric(
                            bdf, ref_pred, scope, metric
                        )
                    except ValueError:
                        continue
                    values[(model, scope, metric)].append(delta)

    rows = []
    for (model, scope, metric), arr in values.items():
        a = np.asarray(arr, dtype=float)
        point = scope_metric(test, predictions[model], scope, metric) - scope_metric(
            test, predictions[reference], scope, metric
        )
        rows.append({
            "model": model,
            "scope": scope,
            "metric": metric,
            "point_delta": float(point),
            "bootstrap_mean_delta": float(np.mean(a)),
            "ci95_low": float(np.quantile(a, 0.025)),
            "ci95_high": float(np.quantile(a, 0.975)),
            "probability_delta_gt_0": float(np.mean(a > 0)),
            "n_boot": int(len(a)),
        })
    return pd.DataFrame(rows)


def plot_macro(metrics: pd.DataFrame) -> None:
    p = (
        metrics[metrics["stage"].eq("MACRO")]
        .sort_values("average_precision", ascending=True)
        .copy()
    )
    p["label"] = p["model"].map(MODEL_LABELS).fillna(p["model"])
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(p["label"], p["average_precision"])
    ax.set_xlabel("Macro Average Precision")
    ax.set_ylabel("")
    ax.set_title("Modelo 3 benchmark — macro Average Precision")
    fig.tight_layout()
    fig.savefig(CHARTS / "macro_average_precision.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def plot_stage(metrics: pd.DataFrame) -> None:
    keep = [
        "multihead_calibrated",
        "specialist_random_forest_calibrated",
        "specialist_lightgbm_calibrated",
        "specialist_catboost_calibrated",
        "pooled_catboost_calibrated",
        "validation_selected_hybrid",
    ]
    p = metrics[metrics["model"].isin(keep) & ~metrics["stage"].eq("MACRO")].copy()
    stages = list(STAGES.values())
    models = [m for m in keep if m in set(p["model"])]
    x = np.arange(len(stages))
    width = 0.8 / max(1, len(models))
    fig, ax = plt.subplots(figsize=(11, 6))
    for i, model in enumerate(models):
        vals = [
            float(p[(p["model"].eq(model)) & (p["stage"].eq(stage))]["average_precision"].iloc[0])
            for stage in stages
        ]
        ax.bar(x + (i - (len(models) - 1) / 2) * width, vals, width, label=MODEL_LABELS[model])
    ax.set_xticks(x)
    ax.set_xticklabels(stages)
    ax.set_ylabel("Average Precision")
    ax.set_title("Average Precision por etapa")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(CHARTS / "stage_average_precision.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def build_report(
    metrics: pd.DataFrame,
    bootstrap: pd.DataFrame,
    selection: dict[str, str],
    conclusion: str,
    best_specialist: str,
) -> str:
    macro = metrics[metrics["stage"].eq("MACRO")].sort_values("average_precision", ascending=False)
    mh = macro[macro["model"].eq("multihead_calibrated")].iloc[0]
    best = macro[macro["model"].eq(best_specialist)].iloc[0]
    boot = bootstrap[
        bootstrap["model"].eq(best_specialist)
        & bootstrap["scope"].eq("MACRO")
        & bootstrap["metric"].eq("average_precision")
    ].iloc[0]

    lines = [
        "# Multi-Head vs especialistas tabulares", "",
        "## Respuesta", "",
        f"**Conclusión gobernada: {conclusion}.**",
        f"El mejor especialista fijo por macro AP fue **{MODEL_LABELS[best_specialist]}**: "
        f"AP {best['average_precision']:.3f} vs {mh['average_precision']:.3f} del Multi-Head "
        f"(delta {best['average_precision'] - mh['average_precision']:+.3f}).",
        f"Bootstrap por lead para ese delta: IC95% [{boot['ci95_low']:+.3f}, {boot['ci95_high']:+.3f}], "
        f"P(delta>0)={boot['probability_delta_gt_0']:.1%}.",
        "",
        "## Ranking macro", "",
        "| Modelo | ROC-AUC | AP | Brier | Log loss | Lift@10% | Recall@20% |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in macro.itertuples():
        lines.append(
            f"| {MODEL_LABELS.get(row.model, row.model)} | {row.roc_auc:.3f} | "
            f"{row.average_precision:.3f} | {row.brier:.3f} | {row.log_loss:.3f} | "
            f"{row.lift_top_10pct:.2f}x | {row.recall_top_20pct:.3f} |"
        )

    lines += ["", "## Average Precision por etapa", "",
              "| Modelo | T0 | T1 | T2 |",
              "|---|---:|---:|---:|"]
    for model in macro["model"]:
        vals = {}
        for stage in STAGES.values():
            vals[stage] = metrics[
                metrics["model"].eq(model) & metrics["stage"].eq(stage)
            ]["average_precision"].iloc[0]
        lines.append(
            f"| {MODEL_LABELS.get(model, model)} | {vals['T0_cold']:.3f} | "
            f"{vals['T1_first_inquiry']:.3f} | {vals['T2_engaged']:.3f} |"
        )

    lines += ["", "## Modelo elegido por validation para cada etapa", ""]
    for stage, model in selection.items():
        lines.append(f"- **{stage}:** {MODEL_LABELS.get(model, model)}.")

    lines += [
        "",
        "El híbrido usa esa selección sin mirar test. Aun así, es una selección entre varias familias sobre el mismo validation set, por lo que debe interpretarse como una arquitectura candidata y no como una estimación libre de selection bias.",
        "",
        "## Lectura arquitectónica", "",
        "- Si un pooled CatBoost fuerte iguala o supera al multi-head, la ventaja de E003 puede provenir parcialmente de que el challenger pooled original era débil, no necesariamente de necesitar heads.",
        "- Si los especialistas ganan sólo en T2, la arquitectura más razonable es híbrida: compartir un esquema de scoring, pero permitir un especialista tabular para la etapa engaged.",
        "- Si el Multi-Head gana de forma robusta en macro AP y en T2, entonces el shared backbone conserva evidencia a favor incluso frente a challengers tabulares fuertes.",
        "",
        "## Controles", "",
        "- Misma construcción point-in-time de E003.",
        "- Misma ventana futura de 30 días y mismo censoring.",
        "- Mismo split temporal por lead; ningún lead cruza train/validation/test.",
        "- Validation se usa para early stopping, calibración y selección del híbrido.",
        "- El bootstrap remuestrea leads completos para respetar la dependencia entre snapshots de un mismo lead.",
        "",
        "## Caveats", "",
        "- scheduled_visit sigue siendo un proxy, no la etiqueta final oculta.",
        "- Los datos son sintéticos.",
        "- Se prueban varias familias; el híbrido puede sobreajustarse al validation set.",
        "- Diferencias pequeñas con IC95% que cruza cero se consideran inconclusas.",
        "",
        "## Siguiente paso", "",
        "Si aparece un ganador robusto por etapa, el siguiente experimento debe hacer feature engineering de trayectoria/progreso únicamente sobre ese ganador y medir lift incremental contra este benchmark congelado.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    set_seed()
    leads, inquiries_raw, spots, attrs, availability = read_data(ROOT)
    inquiries = prepare_inquiries(inquiries_raw)
    snapshots = temporal_split(build_snapshots(leads, inquiries, spots, attrs, availability))

    train = snapshots[snapshots["split"].eq("train")].copy().reset_index(drop=True)
    val = snapshots[snapshots["split"].eq("val")].copy().reset_index(drop=True)
    test = snapshots[snapshots["split"].eq("test")].copy().reset_index(drop=True)
    normalize_frames(train, val, test)

    prep = make_preprocessor()
    x_train = np.asarray(prep.fit_transform(train[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)
    x_val = np.asarray(prep.transform(val[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)
    x_test = np.asarray(prep.transform(test[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)

    y_train = train["target_30d"].to_numpy(dtype=np.int64)
    y_val = val["target_30d"].to_numpy(dtype=np.int64)
    s_train = train["stage_id"].to_numpy(dtype=np.int64)
    s_val = val["stage_id"].to_numpy(dtype=np.int64)
    s_test = test["stage_id"].to_numpy(dtype=np.int64)
    weights = stage_balanced_weights(train)

    raw_val, final_test, calibration, histories = fit_neural_models(
        x_train, y_train, s_train, weights, x_val, y_val, s_val, x_test, s_test
    )
    for name, hist in histories.items():
        hist.to_csv(RESULTS / f"training_history_{name}.csv", index=False)

    lv, lt = fit_logistic(x_train, y_train, s_train, x_val, s_val, x_test, s_test)
    raw_val["separate_logistic"] = lv
    final_test["separate_logistic"] = lt

    rv, rt = fit_sklearn_specialists(
        lambda: RandomForestClassifier(
            n_estimators=500,
            min_samples_leaf=12,
            max_features="sqrt",
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=SEED,
        ),
        x_train, y_train, s_train, x_val, y_val, s_val, x_test, s_test
    )
    add_calibrated(
        "specialist_random_forest_calibrated",
        rv, rt, y_val, s_val, s_test, raw_val, final_test, calibration
    )

    ev, et = fit_sklearn_specialists(
        lambda: ExtraTreesClassifier(
            n_estimators=500,
            min_samples_leaf=10,
            max_features="sqrt",
            class_weight="balanced",
            n_jobs=-1,
            random_state=SEED + 17,
        ),
        x_train, y_train, s_train, x_val, y_val, s_val, x_test, s_test
    )
    add_calibrated(
        "specialist_extra_trees_calibrated",
        ev, et, y_val, s_val, s_test, raw_val, final_test, calibration
    )

    gv, gt = fit_lightgbm_specialists(
        x_train, y_train, s_train, x_val, y_val, s_val, x_test, s_test
    )
    add_calibrated(
        "specialist_lightgbm_calibrated",
        gv, gt, y_val, s_val, s_test, raw_val, final_test, calibration
    )

    cv, ct = fit_catboost_specialists(train, val, test)
    add_calibrated(
        "specialist_catboost_calibrated",
        cv, ct, y_val, s_val, s_test, raw_val, final_test, calibration
    )

    pcv, pct = fit_catboost_pooled(train, val, test)
    add_calibrated(
        "pooled_catboost_calibrated",
        pcv, pct, y_val, s_val, s_test, raw_val, final_test, calibration
    )

    selection, _, val_scores = validation_stage_selection(val, raw_val, final_test)
    final_test["validation_selected_hybrid"] = apply_hybrid(selection, final_test, s_test)
    val_scores.to_csv(RESULTS / "validation_model_scores.csv", index=False)
    (RESULTS / "validation_stage_selection.json").write_text(
        json.dumps(selection, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (RESULTS / "calibration.json").write_text(
        json.dumps(calibration, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    metrics = metrics_table(test, final_test)
    metrics.to_csv(RESULTS / "metrics_by_stage.csv", index=False)
    ranking = metrics[metrics["stage"].eq("MACRO")].sort_values(
        "average_precision", ascending=False
    ).reset_index(drop=True)
    ranking["rank_ap"] = np.arange(1, len(ranking) + 1)
    ranking.to_csv(RESULTS / "model_ranking.csv", index=False)

    bootstrap = bootstrap_deltas(test, final_test)
    bootstrap.to_csv(RESULTS / "bootstrap_deltas_vs_multihead.csv", index=False)

    specialist_macro = ranking[ranking["model"].isin(SPECIALIST_MODELS)].copy()
    best_specialist = specialist_macro.iloc[0]["model"]
    b = bootstrap[
        bootstrap["model"].eq(best_specialist)
        & bootstrap["scope"].eq("MACRO")
        & bootstrap["metric"].eq("average_precision")
    ].iloc[0]
    point_delta = float(b["point_delta"])
    if point_delta > 0 and float(b["ci95_low"]) > 0:
        conclusion = "SUPPORTED"
    elif point_delta <= 0 and float(b["ci95_high"]) < 0:
        conclusion = "NOT_SUPPORTED"
    else:
        conclusion = "INCONCLUSIVE"

    best_row = ranking[ranking["model"].eq(best_specialist)].iloc[0]
    best_segments = {}
    for stage in STAGES.values():
        row = metrics[
            metrics["model"].eq(best_specialist) & metrics["stage"].eq(stage)
        ].iloc[0]
        best_segments[stage] = {
            k: float(row[k])
            for k in [
                "roc_auc", "average_precision", "brier", "log_loss",
                "lift_top_10pct", "recall_top_20pct"
            ]
        }

    harness_results = {
        "experiment_id": "E005_multihead_vs_specialists",
        "metrics": {
            k: float(best_row[k])
            for k in [
                "roc_auc", "average_precision", "brier", "log_loss",
                "lift_top_10pct", "recall_top_20pct"
            ]
        },
        "segment_metrics": best_segments,
        "conclusion": conclusion,
        "caveats": [
            "scheduled_visit is a supervised proxy rather than the hidden final commercial outcome",
            "the dataset is synthetic",
            "the validation-selected hybrid evaluates a model-selection strategy and may carry validation selection bias",
            "multiple challenger families are tested, so small point differences are not treated as decisive without lead-level bootstrap support"
        ],
        "next_experiment": "Engineer explicit trajectory/progression and stalling features on the best stage architecture, then compare against this frozen benchmark."
    }
    (RESULTS / "harness_results.json").write_text(
        json.dumps(harness_results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    summary = {
        "experiment_id": "E005_multihead_vs_specialists",
        "conclusion": conclusion,
        "primary_metric": "macro_average_precision",
        "best_specialist": best_specialist,
        "best_specialist_macro_ap": float(best_row["average_precision"]),
        "multihead_macro_ap": float(
            ranking[ranking["model"].eq("multihead_calibrated")]["average_precision"].iloc[0]
        ),
        "best_specialist_delta_ap_vs_multihead": point_delta,
        "best_specialist_delta_ap_ci95": [float(b["ci95_low"]), float(b["ci95_high"])],
        "best_specialist_probability_delta_gt_0": float(b["probability_delta_gt_0"]),
        "validation_stage_selection": selection,
        "test_population": {
            "rows": int(len(test)),
            "unique_leads": int(test["lead_id"].nunique()),
            "by_stage": {
                STAGES[sid]: int(test["stage_id"].eq(sid).sum()) for sid in STAGES
            }
        }
    }
    (RESULTS / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    plot_macro(metrics)
    plot_stage(metrics)
    report = build_report(metrics, bootstrap, selection, conclusion, best_specialist)
    (RESULTS / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
