from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODEL3 = ROOT / "experimentos" / "modelo_3"
if str(MODEL3) not in sys.path:
    sys.path.insert(0, str(MODEL3))

from data_pipeline import (  # noqa: E402
    AVAIL_CAT,
    AVAIL_NUM,
    CAT_FEATURES,
    CONTEXT_NUM,
    HISTORY_NUM,
    INQUIRY_CAT,
    INQUIRY_NUM,
    LEAD_CAT,
    LEAD_NUM,
    MATCH_CAT,
    MATCH_NUM,
    NUM_FEATURES,
    SPOT_CAT,
    SPOT_NUM,
    STAGES,
    build_snapshots,
    prepare_inquiries,
    read_data,
    temporal_split,
)
from models import calibrate_by_stage, metric_bundle, metrics_table  # noqa: E402

SEED = 42
N_BOOT = 500
CORE_METRICS = [
    "roc_auc",
    "average_precision",
    "brier",
    "log_loss",
    "lift_top_10pct",
    "recall_top_20pct",
]


def load_snapshot_data() -> tuple[pd.DataFrame, pd.DataFrame, tuple[pd.DataFrame, ...]]:
    leads, inquiries_raw, spots, attrs, availability = read_data(ROOT)
    inquiries = prepare_inquiries(inquiries_raw)
    snapshots = build_snapshots(leads, inquiries, spots, attrs, availability)
    broker_map = spots[["spot_id", "broker_id"]].copy()
    snapshots = snapshots.merge(broker_map, on="spot_id", how="left")

    origin = pd.Timestamp(snapshots["created_at"].min()).to_period("M")
    lead_period = snapshots["created_at"].dt.to_period("M")
    score_period = snapshots["score_time"].dt.to_period("M")
    snapshots["lead_cohort_index"] = (
        (lead_period.dt.year - origin.year) * 12 + lead_period.dt.month - origin.month
    ).astype(float)
    snapshots["score_time_index"] = (
        (score_period.dt.year - origin.year) * 12 + score_period.dt.month - origin.month
    ).astype(float)

    split = temporal_split(snapshots)
    return snapshots, split, (leads, inquiries, spots, attrs, availability)


def make_preprocessor(cat_cols: list[str], num_cols: list[str]) -> ColumnTransformer:
    transformers = []
    if cat_cols:
        cat = Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    min_frequency=5,
                    sparse_output=False,
                    dtype=np.float32,
                ),
            ),
        ])
        transformers.append(("cat", cat, cat_cols))
    if num_cols:
        num = Pipeline([
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
        ])
        transformers.append(("num", num, num_cols))
    return ColumnTransformer(transformers, remainder="drop", sparse_threshold=0.0)


def normalize_frames(frames: Iterable[pd.DataFrame], cat_cols: list[str], num_cols: list[str]) -> None:
    for frame in frames:
        for c in cat_cols:
            if c not in frame:
                raise KeyError(f"Missing categorical feature {c}")
            frame[c] = frame[c].astype("object")
            frame[c] = frame[c].where(frame[c].notna(), np.nan)
        for c in num_cols:
            if c not in frame:
                raise KeyError(f"Missing numeric feature {c}")
            frame[c] = pd.to_numeric(frame[c], errors="coerce").replace([np.inf, -np.inf], np.nan)


def feature_lists(
    *,
    remove_cat: Iterable[str] = (),
    remove_num: Iterable[str] = (),
    add_cat: Iterable[str] = (),
    add_num: Iterable[str] = (),
) -> tuple[list[str], list[str]]:
    rc, rn = set(remove_cat), set(remove_num)
    cats = [c for c in CAT_FEATURES if c not in rc] + [c for c in add_cat if c not in CAT_FEATURES]
    nums = [c for c in NUM_FEATURES if c not in rn] + [c for c in add_num if c not in NUM_FEATURES]
    return cats, nums


def rf_specialist_predictions(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    cat_cols: list[str],
    num_cols: list[str],
    *,
    train_keep: np.ndarray | pd.Series | None = None,
    seed: int = SEED,
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    tr = train.copy().reset_index(drop=True)
    va = val.copy().reset_index(drop=True)
    te = test.copy().reset_index(drop=True)
    normalize_frames([tr, va, te], cat_cols, num_cols)

    if train_keep is None:
        keep = np.ones(len(tr), dtype=bool)
    else:
        keep = np.asarray(train_keep, dtype=bool)
        if len(keep) != len(tr):
            raise ValueError("train_keep length mismatch")
    fit_train = tr.loc[keep].copy().reset_index(drop=True)

    prep = make_preprocessor(cat_cols, num_cols)
    x_train = np.asarray(prep.fit_transform(fit_train[cat_cols + num_cols]), dtype=np.float32)
    x_val = np.asarray(prep.transform(va[cat_cols + num_cols]), dtype=np.float32)
    x_test = np.asarray(prep.transform(te[cat_cols + num_cols]), dtype=np.float32)

    y_train = fit_train["target_30d"].to_numpy(dtype=np.int64)
    y_val = va["target_30d"].to_numpy(dtype=np.int64)
    s_train = fit_train["stage_id"].to_numpy(dtype=np.int64)
    s_val = va["stage_id"].to_numpy(dtype=np.int64)
    s_test = te["stage_id"].to_numpy(dtype=np.int64)

    val_raw = np.full(len(va), np.nan)
    test_raw = np.full(len(te), np.nan)
    fit_counts: dict[str, int] = {}

    for sid, stage in STAGES.items():
        mtr, mva, mte = s_train == sid, s_val == sid, s_test == sid
        fit_counts[stage] = int(mtr.sum())
        if mtr.sum() == 0 or len(np.unique(y_train[mtr])) < 2:
            raise RuntimeError(f"Stage {stage} has insufficient training classes")
        model = RandomForestClassifier(
            n_estimators=500,
            min_samples_leaf=12,
            max_features="sqrt",
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=seed,
        )
        model.fit(x_train[mtr], y_train[mtr])
        if mva.any():
            val_raw[mva] = model.predict_proba(x_val[mva])[:, 1]
        if mte.any():
            test_raw[mte] = model.predict_proba(x_test[mte])[:, 1]

    calibrated, params = calibrate_by_stage(
        val_raw,
        y_val,
        s_val,
        test_raw,
        s_test,
    )
    meta = {
        "fit_counts": fit_counts,
        "calibration": params,
        "n_train_before_filter": int(len(tr)),
        "n_train_after_filter": int(keep.sum()),
        "n_encoded_features": int(x_train.shape[1]),
    }
    return calibrated, val_raw, meta


def metrics_for(test: pd.DataFrame, name: str, pred: np.ndarray) -> pd.DataFrame:
    return metrics_table(test.reset_index(drop=True), {name: np.asarray(pred, dtype=float)})


def macro_row(metrics: pd.DataFrame, model: str | None = None) -> pd.Series:
    x = metrics[metrics["stage"].eq("MACRO")]
    if model is not None:
        x = x[x["model"].eq(model)]
    if x.empty:
        raise RuntimeError("Macro metrics missing")
    return x.iloc[0]


def macro_metric(frame: pd.DataFrame, pred: np.ndarray, metric: str) -> float:
    values = []
    for sid in STAGES:
        mask = frame["stage_id"].to_numpy() == sid
        if not mask.any():
            continue
        values.append(metric_bundle(frame.loc[mask, "target_30d"], pred[mask])[metric])
    return float(np.nanmean(values))


def bootstrap_delta(
    test: pd.DataFrame,
    candidate: np.ndarray,
    reference: np.ndarray,
    *,
    metric: str = "average_precision",
    stage_id: int | None = None,
    n_boot: int = N_BOOT,
    seed: int = SEED,
) -> dict[str, float]:
    frame = test.reset_index(drop=True).copy()
    cand = np.asarray(candidate, dtype=float)
    ref = np.asarray(reference, dtype=float)
    if stage_id is not None:
        keep = frame["stage_id"].eq(stage_id).to_numpy()
        frame = frame.loc[keep].reset_index(drop=True)
        cand = cand[keep]
        ref = ref[keep]

    groups = {lead: np.asarray(idx, dtype=int) for lead, idx in frame.groupby("lead_id").indices.items()}
    leads = np.asarray(list(groups.keys()), dtype=object)
    rng = np.random.default_rng(seed)
    deltas = []
    for _ in range(n_boot):
        sampled = rng.choice(leads, size=len(leads), replace=True)
        idx = np.concatenate([groups[lead] for lead in sampled])
        f = frame.iloc[idx].reset_index(drop=True)
        cp = cand[idx]
        rp = ref[idx]
        if stage_id is None:
            a = macro_metric(f, cp, metric)
            b = macro_metric(f, rp, metric)
        else:
            a = metric_bundle(f["target_30d"], cp)[metric]
            b = metric_bundle(f["target_30d"], rp)[metric]
        deltas.append(a - b)

    arr = np.asarray(deltas, dtype=float)
    if stage_id is None:
        point = macro_metric(frame, cand, metric) - macro_metric(frame, ref, metric)
    else:
        point = metric_bundle(frame["target_30d"], cand)[metric] - metric_bundle(frame["target_30d"], ref)[metric]
    return {
        "metric": metric,
        "stage": "MACRO" if stage_id is None else STAGES[stage_id],
        "point_delta": float(point),
        "bootstrap_mean_delta": float(np.nanmean(arr)),
        "ci95_low": float(np.nanquantile(arr, 0.025)),
        "ci95_high": float(np.nanquantile(arr, 0.975)),
        "probability_delta_gt_0": float(np.nanmean(arr > 0)),
        "n_boot": int(n_boot),
    }


def core_metrics_dict(metrics: pd.DataFrame, model: str) -> dict[str, float]:
    row = macro_row(metrics, model)
    return {m: float(row[m]) for m in CORE_METRICS}


def stage_metrics_dict(metrics: pd.DataFrame, model: str) -> dict[str, dict[str, float]]:
    out = {}
    for stage in STAGES.values():
        x = metrics[(metrics["model"].eq(model)) & (metrics["stage"].eq(stage))]
        if x.empty:
            continue
        row = x.iloc[0]
        out[stage] = {m: float(row[m]) for m in CORE_METRICS}
    return out


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_harness_results(
    out_dir: Path,
    experiment_id: str,
    metrics: dict[str, float],
    segment_metrics: dict[str, dict[str, float]],
    conclusion: str,
    caveats: list[str],
    next_experiment: str,
) -> None:
    payload = {
        "experiment_id": experiment_id,
        "metrics": metrics,
        "segment_metrics": segment_metrics,
        "conclusion": conclusion,
        "caveats": caveats,
        "next_experiment": next_experiment,
    }
    (out_dir / "harness_results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def psi_numeric(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    a = pd.to_numeric(reference, errors="coerce").dropna().to_numpy(dtype=float)
    b = pd.to_numeric(current, errors="coerce").dropna().to_numpy(dtype=float)
    if len(a) < 20 or len(b) < 20:
        return math.nan
    edges = np.unique(np.quantile(a, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    ac, _ = np.histogram(a, bins=edges)
    bc, _ = np.histogram(b, bins=edges)
    ap = np.clip(ac / max(ac.sum(), 1), 1e-6, None)
    bp = np.clip(bc / max(bc.sum(), 1), 1e-6, None)
    return float(np.sum((bp - ap) * np.log(bp / ap)))


def add_availability_guardrail(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    age = pd.to_numeric(out["availability_snapshot_age_days"], errors="coerce")
    out["availability_snapshot_age_log1p"] = np.log1p(age.clip(lower=0))
    bucket = pd.cut(
        age,
        bins=[-np.inf, 7, 30, 90, np.inf],
        labels=["0-7d", "8-30d", "31-90d", ">90d"],
        right=True,
    ).astype("string")
    out["availability_staleness_bucket"] = bucket.fillna("missing").astype(object)
    out["availability_stale_gt90"] = age.gt(90).astype(float)
    stale = age.gt(90)
    for c in [
        "availability_is_available",
        "availability_days_until_available",
        "availability_competing_inquiries_30d",
    ]:
        out.loc[stale, c] = np.nan
    out.loc[stale, "has_availability_context"] = 0.0
    return out


def fit_iforest_by_regime(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    numeric_features: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frames = [train.copy().reset_index(drop=True), val.copy().reset_index(drop=True), test.copy().reset_index(drop=True)]
    for frame in frames:
        frame["iforest_anomaly_score"] = np.nan
        frame["iforest_anomaly_flag"] = 0.0

    def make_pipe(seed: int) -> Pipeline:
        return Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", RobustScaler()),
            (
                "iforest",
                IsolationForest(
                    n_estimators=250,
                    max_samples=256,
                    contamination=0.03,
                    random_state=seed,
                    n_jobs=-1,
                ),
            ),
        ])

    train_df = frames[0]
    models: dict[tuple, Pipeline] = {}
    summary = []

    # Stage fallbacks.
    for sid in STAGES:
        g = train_df[train_df["stage_id"].eq(sid)]
        if len(g) >= 80:
            pipe = make_pipe(SEED + sid)
            pipe.fit(g[numeric_features])
            models[(sid, "__FALLBACK__")] = pipe

    group_cols = ["stage_id", "search_sector", "search_modality"]
    for key, g in train_df.groupby(group_cols, dropna=False):
        sid = int(key[0])
        if len(g) < 80:
            continue
        pipe = make_pipe(SEED + sid + len(models))
        pipe.fit(g[numeric_features])
        models[tuple(key)] = pipe

    for frame_name, frame in zip(["train", "val", "test"], frames):
        assigned = np.zeros(len(frame), dtype=bool)
        for key, idx in frame.groupby(group_cols, dropna=False).groups.items():
            key = tuple(key if isinstance(key, tuple) else (key,))
            sid = int(key[0])
            pipe = models.get(key) or models.get((sid, "__FALLBACK__"))
            if pipe is None:
                continue
            loc = np.asarray(list(idx), dtype=int)
            score = -pipe.decision_function(frame.loc[loc, numeric_features])
            prediction = np.asarray(pipe.predict(frame.loc[loc, numeric_features]))
            flag = prediction == -1
            frame.loc[loc, "iforest_anomaly_score"] = score
            frame.loc[loc, "iforest_anomaly_flag"] = np.asarray(flag, dtype=float)
            assigned[loc] = True
        summary.append({
            "split": frame_name,
            "n": len(frame),
            "assigned_rate": float(assigned.mean()),
            "flag_rate": float(frame["iforest_anomaly_flag"].mean()),
            "score_p95": float(frame["iforest_anomaly_score"].quantile(.95)),
        })

    return frames[0], frames[1], frames[2], pd.DataFrame(summary)


def add_broker_history(
    snapshots: pd.DataFrame,
    inquiries: pd.DataFrame,
    spots: pd.DataFrame,
) -> pd.DataFrame:
    out = snapshots.copy()
    broker_by_spot = spots.set_index("spot_id")["broker_id"]
    events = inquiries.copy()
    events["broker_id"] = events["spot_id"].map(broker_by_spot)
    events = events[events["broker_id"].notna() & events["response_event_at"].notna()].copy()
    events["scheduled"] = events["broker_response"].eq("scheduled_visit").astype(int)
    events = events.sort_values(["broker_id", "response_event_at", "inquiry_id"])

    histories = {}
    for broker, g in events.groupby("broker_id"):
        times = g["response_event_at"].to_numpy(dtype="datetime64[ns]")
        scheduled = g["scheduled"].to_numpy(dtype=int)
        histories[broker] = {
            "times": times,
            "prefix_scheduled": np.cumsum(scheduled),
        }

    n_hist, n_sched, smooth, log_n, days_since_first = [], [], [], [], []
    for row in out.itertuples():
        broker = getattr(row, "broker_id", np.nan)
        if pd.isna(broker) or broker not in histories or pd.isna(row.score_time):
            n_hist.append(np.nan)
            n_sched.append(np.nan)
            smooth.append(np.nan)
            log_n.append(np.nan)
            days_since_first.append(np.nan)
            continue
        h = histories[broker]
        t = np.datetime64(pd.Timestamp(row.score_time).to_datetime64())
        # Strictly before score time: the current inquiry's response can never enter.
        n = int(np.searchsorted(h["times"], t, side="left"))
        s = int(h["prefix_scheduled"][n - 1]) if n else 0
        n_hist.append(float(n))
        n_sched.append(float(s))
        smooth.append(float((s + 1.0) / (n + 2.0)))
        log_n.append(float(np.log1p(n)))
        if n:
            first = pd.Timestamp(h["times"][0])
            days_since_first.append(float((pd.Timestamp(row.score_time) - first).total_seconds() / 86400.0))
        else:
            days_since_first.append(np.nan)

    out["broker_hist_responses"] = n_hist
    out["broker_hist_scheduled_visits"] = n_sched
    out["broker_hist_scheduled_rate_laplace"] = smooth
    out["broker_hist_log_responses"] = log_n
    out["broker_hist_days_since_first_response"] = days_since_first
    return out
