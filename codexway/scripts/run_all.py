"""Run the complete codexway assessment from the repository root or codexway/."""

from __future__ import annotations

import sys
from pathlib import Path

CODEXWAY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODEXWAY / "src"))
sys.path.insert(0, str(CODEXWAY))

from spot2_codexway.pipeline import main

if __name__ == "__main__":
    raise SystemExit(main(["all", *sys.argv[1:]]))
