from __future__ import annotations

import math
import random
from typing import Iterable

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

SEED = 42
STAGES = {0: "T0_cold", 1: "T1_first_inquiry", 2: "T2_engaged"}
CORE_METRICS = ["roc_auc", "average_precision", "brier", "log_loss", "lift_top_10pct", "recall_top_20pct"]


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(max(1, min(4, torch.get_num_threads())))


def metric_bundle(y_true: Iterable[int], pred: Iterable[float]) -> dict[str, float]:
    y = np.asarray(list(y_true), dtype=int)
    p = np.clip(np.asarray(list(pred), dtype=float), 1e-6, 1 - 1e-6)
    out = {"n": float(len(y)), "positive_rate": float(y.mean()) if len(y) else math.nan}
    if len(y) == 0 or len(np.unique(y)) < 2:
        out.update({m: math.nan for m in CORE_METRICS})
        return out
    out.update({
        "roc_auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
    })
    order, base = np.argsort(-p), float(y.mean())
    top10 = order[: max(1, int(math.ceil(0.10 * len(y))))]
    top20 = order[: max(1, int(math.ceil(0.20 * len(y))))]
    out["lift_top_10pct"] = float(y[top10].mean() / base) if base > 0 else math.nan
    out["recall_top_20pct"] = float(y[top20].sum() / y.sum()) if y.sum() > 0 else math.nan
    return out


class SharedMultiHead(nn.Module):
    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(), nn.Dropout(0.10), nn.Linear(128, 64), nn.ReLU()
        )
        self.heads = nn.ModuleList([nn.Linear(64, 1) for _ in STAGES])

    def forward(self, x: torch.Tensor, stage: torch.Tensor) -> torch.Tensor:
        z = self.backbone(x)
        logits = torch.empty(x.shape[0], device=x.device)
        for head_id, head in enumerate(self.heads):
            mask = stage == head_id
            if mask.any():
                logits[mask] = head(z[mask]).squeeze(1)
        return logits


class PooledStageModel(nn.Module):
    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim + len(STAGES), 128), nn.ReLU(), nn.Dropout(0.10),
            nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 1),
        )

    def forward(self, x: torch.Tensor, stage: torch.Tensor) -> torch.Tensor:
        onehot = torch.nn.functional.one_hot(stage, num_classes=len(STAGES)).float()
        return self.net(torch.cat([x, onehot], dim=1)).squeeze(1)


def predict(model: nn.Module, x: np.ndarray, stage: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        logits = model(torch.from_numpy(x.astype(np.float32)), torch.from_numpy(stage.astype(np.int64)))
    return torch.sigmoid(logits).cpu().numpy()


def train_model(
    model: nn.Module, x_train: np.ndarray, y_train: np.ndarray, stage_train: np.ndarray,
    weights: np.ndarray, x_val: np.ndarray, y_val: np.ndarray, stage_val: np.ndarray,
    max_epochs: int = 80, patience: int = 10,
) -> tuple[nn.Module, pd.DataFrame]:
    ds = TensorDataset(
        torch.from_numpy(x_train.astype(np.float32)), torch.from_numpy(y_train.astype(np.float32)),
        torch.from_numpy(stage_train.astype(np.int64)), torch.from_numpy(weights.astype(np.float32)),
    )
    loader = DataLoader(ds, batch_size=512, shuffle=True, generator=torch.Generator().manual_seed(SEED))
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss(reduction="none")
    best_state, best_loss, stale, history = None, float("inf"), 0, []

    for epoch in range(1, max_epochs + 1):
        model.train()
        batch_losses = []
        for xb, yb, sb, wb in loader:
            optimizer.zero_grad()
            loss_rows = criterion(model(xb, sb), yb)
            loss = (loss_rows * wb).sum() / wb.sum()
            loss.backward()
            optimizer.step()
            batch_losses.append(float(loss.detach()))

        vp = predict(model, x_val, stage_val)
        vloss = float(log_loss(y_val, np.clip(vp, 1e-6, 1 - 1e-6), labels=[0, 1]))
        history.append({"epoch": epoch, "train_loss": np.mean(batch_losses), "val_log_loss": vloss})
        if vloss < best_loss - 1e-5:
            best_loss, stale = vloss, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            stale += 1
            if stale >= patience:
                break
    if best_state:
        model.load_state_dict(best_state)
    return model, pd.DataFrame(history)


def calibrate_by_stage(
    val_pred: np.ndarray, y_val: np.ndarray, stage_val: np.ndarray,
    test_pred: np.ndarray, stage_test: np.ndarray,
) -> tuple[np.ndarray, dict[str, dict[str, float | str]]]:
    out = test_pred.copy().astype(float)
    params = {}
    for sid, name in STAGES.items():
        vm, tm = stage_val == sid, stage_test == sid
        if vm.sum() < 40 or len(np.unique(y_val[vm])) < 2:
            params[name] = {"intercept": 0.0, "coefficient": 1.0, "status": "identity"}
            continue
        vlogit = np.log(np.clip(val_pred[vm], 1e-6, 1 - 1e-6) / np.clip(1 - val_pred[vm], 1e-6, 1))
        tlogit = np.log(np.clip(test_pred[tm], 1e-6, 1 - 1e-6) / np.clip(1 - test_pred[tm], 1e-6, 1))
        cal = LogisticRegression(solver="lbfgs", C=1e6, max_iter=2000).fit(vlogit.reshape(-1, 1), y_val[vm])
        out[tm] = cal.predict_proba(tlogit.reshape(-1, 1))[:, 1]
        params[name] = {
            "intercept": float(cal.intercept_[0]), "coefficient": float(cal.coef_[0, 0]), "status": "platt"
        }
    return out, params


def separate_logistic_predictions(
    x_train: np.ndarray, y_train: np.ndarray, stage_train: np.ndarray,
    x_test: np.ndarray, stage_test: np.ndarray,
) -> np.ndarray:
    out = np.full(len(x_test), np.nan)
    for sid in STAGES:
        tr, te = stage_train == sid, stage_test == sid
        if tr.sum() and te.sum() and len(np.unique(y_train[tr])) == 2:
            clf = LogisticRegression(max_iter=2500, solver="liblinear").fit(x_train[tr], y_train[tr])
            out[te] = clf.predict_proba(x_test[te])[:, 1]
    return out


def metrics_table(test_df: pd.DataFrame, predictions: dict[str, np.ndarray]) -> pd.DataFrame:
    rows = []
    for model, pred in predictions.items():
        model_rows = []
        for sid, stage in STAGES.items():
            mask = test_df["stage_id"].to_numpy() == sid
            if mask.sum() == 0 or np.isnan(pred[mask]).all():
                continue
            r = {"model": model, "stage": stage, **metric_bundle(test_df.loc[mask, "target_30d"], pred[mask])}
            rows.append(r); model_rows.append(r)
        macro = {m: float(np.nanmean([r[m] for r in model_rows])) for m in ["positive_rate"] + CORE_METRICS}
        macro["n"] = float(sum(r["n"] for r in model_rows))
        rows.append({"model": model, "stage": "MACRO", **macro})
    return pd.DataFrame(rows)
