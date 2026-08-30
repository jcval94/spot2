from __future__ import annotations

import re
import unicodedata
from typing import Any


PATTERNS: dict[str, tuple[str, ...]] = {
    "natural_light": ("iluminacion natural", "luz natural"),
    "security": ("seguridad 24/7", "control de acceso", "vigilancia", "circuito cerrado"),
    "parking": ("estacionamiento", "cajon de estacionamiento", "cajones de estacionamiento", "parking"),
    "readiness": ("listo para ocupar", "recien remodelado", "acabados modernos", "acabados de primera"),
}


def normalize(text: str | None) -> str:
    text = (text or "").lower()
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def has_claim(text: str, claim_type: str) -> bool:
    normalized = normalize(text)
    return any(phrase in normalized for phrase in PATTERNS[claim_type])


def evidence_sentence(description: str, claim_type: str) -> str:
    for sentence in re.split(r"(?<=\.)\s+", description.strip()):
        if has_claim(sentence, claim_type):
            return sentence.strip()
    return description.strip()


def audit_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    text = f"{row.get('title', '')} {row.get('description', '')}"
    description = row.get("description", "")
    attrs = row["attributes"]
    issues: list[dict[str, Any]] = []

    if has_claim(text, "natural_light") and attrs.get("natural_light") is False:
        issues.append(_issue(
            row, "R001", "natural_light", evidence_sentence(description, "natural_light"),
            "natural_light", False, "high",
            "Listing claims natural light while the structured natural_light field is false.",
        ))

    security = normalize(str(attrs.get("security_type") or ""))
    if has_claim(text, "security") and security in {"", "none"}:
        issues.append(_issue(
            row, "R002", "security", evidence_sentence(description, "security"),
            "security_type", attrs.get("security_type"), "high",
            "Listing claims security/access control while security_type is none or missing.",
        ))

    amenities = {normalize(str(x)) for x in attrs.get("amenities", [])}
    parking_spaces = attrs.get("parking_spaces")
    if (
        has_claim(text, "parking")
        and (parking_spaces is None or float(parking_spaces) == 0)
        and "parking" not in amenities
    ):
        issues.append(_issue(
            row, "R003", "parking", evidence_sentence(description, "parking"),
            "parking_spaces", parking_spaces, "medium",
            "Listing explicitly claims parking while parking_spaces is zero/missing and parking is not listed as an amenity.",
        ))

    status = normalize(str(attrs.get("building_status") or ""))
    if has_claim(text, "readiness") and status == "needs_renovation":
        issues.append(_issue(
            row, "R004", "readiness", evidence_sentence(description, "readiness"),
            "building_status", attrs.get("building_status"), "medium",
            "Listing claims ready/remodeled/modern condition while building_status is needs_renovation.",
        ))

    return issues


def _issue(
    row: dict[str, Any],
    rule_id: str,
    claim_type: str,
    evidence_text: str,
    structured_field: str,
    structured_value: Any,
    severity: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "spot_id": row["spot_id"],
        "sector_name": row.get("sector_name"),
        "type_name": row.get("type_name"),
        "rule_id": rule_id,
        "claim_type": claim_type,
        "evidence_text": evidence_text,
        "structured_field": structured_field,
        "structured_value": structured_value,
        "classification": "candidate_contradiction",
        "severity": severity,
        "reason": reason,
    }
