from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from openai import OpenAI


HERE = Path(__file__).resolve().parents[1]
PROMPT_PATH = HERE / "prompts" / "system_prompt.md"
SCHEMA_PATH = HERE / "schema" / "audit_response.schema.json"


def api_key() -> str:
    value = (
        os.getenv("OPENAIKEY")
        or os.getenv("OPENAIAPI")
        or os.getenv("OPENAI_API_KEY")
    )
    if not value:
        raise RuntimeError(
            "Missing OPENAIKEY, OPENAIAPI, or OPENAI_API_KEY environment variable."
        )
    return value


def model_name() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-5-nano")


def build_payload(row: dict[str, Any]) -> dict[str, Any]:
    amenities = row.get("amenities", [])
    if isinstance(amenities, str):
        try:
            amenities = json.loads(amenities)
        except json.JSONDecodeError:
            amenities = []

    return {
        "spot_id": str(row["spot_id"]),
        "sector_name": row.get("sector_name"),
        "type_name": row.get("type_name"),
        "modality": row.get("modality"),
        "title": row.get("title"),
        "description": row.get("description"),
        "attributes": {
            "natural_light": _parse_bool(row.get("natural_light")),
            "security_type": row.get("security_type") or None,
            "parking_spaces": _parse_number(row.get("parking_spaces")),
            "building_status": row.get("building_status") or None,
            "amenities": amenities,
        },
    }


def _parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None or str(value).strip() == "":
        return None
    normalized = str(value).strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    return None


def _parse_number(value: Any) -> int | float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    if value is None or str(value).strip() == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def input_hash(payload: dict[str, Any], model: str, prompt: str, schema: dict[str, Any]) -> str:
    material = {
        "model": model,
        "prompt": prompt,
        "schema": schema,
        "payload": payload,
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def audit(payload: dict[str, Any], *, model: str | None = None) -> dict[str, Any]:
    model = model or model_name()
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    client = OpenAI(api_key=api_key())

    started = time.perf_counter()
    response = client.responses.create(
        model=model,
        instructions=prompt,
        input=json.dumps(payload, ensure_ascii=False),
        text={
            "format": {
                "type": "json_schema",
                "name": "inventory_semantic_audit",
                "schema": schema,
                "strict": True,
            }
        },
        max_output_tokens=700,
        store=False,
    )
    latency_ms = (time.perf_counter() - started) * 1000
    parsed = json.loads(response.output_text)

    usage = getattr(response, "usage", None)
    return {
        "status": "ok",
        "response_id": getattr(response, "id", None),
        "model": model,
        "latency_ms": latency_ms,
        "input_tokens": getattr(usage, "input_tokens", None) if usage else None,
        "output_tokens": getattr(usage, "output_tokens", None) if usage else None,
        "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        "audit": parsed,
    }
