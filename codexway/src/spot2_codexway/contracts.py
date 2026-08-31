from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml


@dataclass(frozen=True)
class SplitContract:
    train_start: pd.Timestamp
    train_end_exclusive: pd.Timestamp
    validation_start: pd.Timestamp
    validation_end_exclusive: pd.Timestamp
    test_start: pd.Timestamp
    test_end_exclusive: pd.Timestamp


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    codexway_root: Path
    data_dir: Path
    csv_data_dir: Path
    seed: int
    evaluation_cutoff_exclusive: pd.Timestamp
    maturity_days: int
    t0_horizon_days: int
    availability_freshness_days: int
    max_fallback_recommendations: int
    split: SplitContract
    raw: dict


def _utc(value: str) -> pd.Timestamp:
    return pd.Timestamp(value).tz_convert("UTC")


def load_settings(config_path: str | Path | None = None) -> Settings:
    codexway_root = Path(__file__).resolve().parents[2]
    repo_root = codexway_root.parent
    path = Path(config_path) if config_path else codexway_root / "config" / "base.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    split = raw["split"]
    return Settings(
        repo_root=repo_root,
        codexway_root=codexway_root,
        data_dir=repo_root / raw["data_dir"],
        csv_data_dir=repo_root / raw["csv_data_dir"],
        seed=int(raw["seed"]),
        evaluation_cutoff_exclusive=_utc(raw["evaluation_cutoff_exclusive"]),
        maturity_days=int(raw["maturity_days"]),
        t0_horizon_days=int(raw["t0_horizon_days"]),
        availability_freshness_days=int(raw["availability_freshness_days"]),
        max_fallback_recommendations=int(raw["max_fallback_recommendations"]),
        split=SplitContract(**{key: _utc(value) for key, value in split.items()}),
        raw=raw,
    )

