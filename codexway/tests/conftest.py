from __future__ import annotations

import sys
from pathlib import Path

import pytest

CODEXWAY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODEXWAY_ROOT / "src"))
sys.path.insert(0, str(CODEXWAY_ROOT))

from spot2_codexway.contracts import load_settings


@pytest.fixture(scope="session")
def settings():
    return load_settings()

