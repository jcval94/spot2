from __future__ import annotations

import json
from pathlib import Path
from typing import Any

UNSAFE_TAGS = {
    "LEAKAGE_EXPECTED",
    "UNKNOWN_PROVENANCE",
    "FUTURE_LEAKAGE",
    "FUTURE_SNAPSHOT_LEAKAGE",
    "NON_DEPLOYABLE",
}


class UnsafePipelineSpec(ValueError):
    pass


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def assert_product_safe(spec: dict[str, Any]) -> None:
    tags = {str(x).upper() for x in spec.get("tags", [])}
    reasons: list[str] = []
    if bool(spec.get("unsafe", False)):
        reasons.append("unsafe=true")
    if spec.get("deployable") is False:
        reasons.append("deployable=false")
    bad = sorted(tags.intersection(UNSAFE_TAGS))
    if bad:
        reasons.append("unsafe tags=" + ",".join(bad))
    if reasons:
        raise UnsafePipelineSpec(
            "Product pipeline rejected unsafe spec: " + "; ".join(reasons)
        )


def validate_spec(path: str | Path, *, mode: str = "product") -> dict[str, Any]:
    spec = load_spec(path)
    if mode == "product":
        assert_product_safe(spec)
    elif mode != "stress":
        raise ValueError(f"Unknown harness mode: {mode}")
    return spec
