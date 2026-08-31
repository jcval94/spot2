from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from .contracts import Settings


TABLES = (
    "leads",
    "inquiries",
    "spots",
    "spot_attributes",
    "availability_snapshot",
    "market_context",
)

DATE_COLUMNS = {
    "leads": ["created_at"],
    "inquiries": ["inquiry_at"],
    "spots": ["created_at"],
    "availability_snapshot": ["snapshot_date"],
    "market_context": ["month"],
}


def _normalize_dates(frame: pd.DataFrame, table: str) -> pd.DataFrame:
    result = frame.copy()
    for column in DATE_COLUMNS.get(table, []):
        result[column] = pd.to_datetime(result[column], utc=True)
    return result


def load_table(settings: Settings, name: str) -> pd.DataFrame:
    if name not in TABLES:
        raise KeyError(f"Unknown canonical table: {name}")
    return _normalize_dates(pd.read_parquet(settings.data_dir / f"{name}.parquet"), name)


def load_all(settings: Settings) -> dict[str, pd.DataFrame]:
    return {name: load_table(settings, name) for name in TABLES}


def canonical_csv_frame(settings: Settings, name: str) -> pd.DataFrame:
    frame = pd.read_csv(settings.csv_data_dir / f"{name}.csv")
    return _normalize_dates(frame, name)


def dataframe_fingerprint(frame: pd.DataFrame) -> str:
    normalized = frame.copy()
    normalized = normalized.reindex(sorted(normalized.columns), axis=1)
    digest = pd.util.hash_pandas_object(normalized, index=True).values.tobytes()
    return hashlib.sha256(digest).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

