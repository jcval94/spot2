from __future__ import annotations

from typing import Any

from .rules import normalize


BUILDING_COPY = (
    "buena iluminacion natural",
    "recien remodelado",
    "acabados modernos",
    "listo para ocupar",
    "acabados de primera",
)
RETAIL_ALT_USE_COPY = ("ideal para oficinas corporativas o centro de distribucion",)
SECURITY_STRONG_COPY = ("seguridad 24/7", "control de acceso")
NOT_VERIFIABLE_COPY: dict[str, tuple[str, ...]] = {
    "near_shopping_centers": ("ubicacion estrategica cerca de centros comerciales",),
    "road_access": ("excelente ubicacion con acceso a vias principales",),
    "transit_access": ("facil acceso a transporte publico y avenidas principales",),
    "market_demand": ("zona de alta plusvalia y demanda comercial",),
    "all_services": ("cuenta con todos los servicios",),
}


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    normalized = normalize(text)
    return any(phrase in normalized for phrase in phrases)


def semantic_observations(row: dict[str, Any]) -> list[dict[str, Any]]:
    description = row.get("description", "")
    sector = row.get("sector_name", "")
    attrs = row["attributes"]
    observations: list[dict[str, Any]] = []

    if sector == "Land" and _contains_any(description, BUILDING_COPY):
        observations.append({
            "spot_id": row["spot_id"],
            "pattern_id": "S001",
            "classification": "semantic_cross_field_mismatch",
            "actionable": True,
            "severity": "medium",
            "evidence_text": description,
            "structured_context": "sector_name=Land",
            "reason": (
                "The listing is categorized as Land but uses building/interior-condition "
                "language. This is not a direct factual contradiction; it is a catalog "
                "coherence issue that merits review."
            ),
        })

    if sector == "Retail" and _contains_any(description, RETAIL_ALT_USE_COPY):
        observations.append({
            "spot_id": row["spot_id"],
            "pattern_id": "S002",
            "classification": "semantic_cross_field_mismatch",
            "actionable": False,
            "severity": "low",
            "evidence_text": description,
            "structured_context": "sector_name=Retail",
            "reason": (
                "Retail is described as suitable for corporate offices or a distribution "
                "center. Re-use is plausible, so this remains informational until business "
                "ontology rules define incompatibility."
            ),
        })

    security = normalize(str(attrs.get("security_type") or ""))
    if _contains_any(description, SECURITY_STRONG_COPY) and security in {"basic", "cctv"}:
        observations.append({
            "spot_id": row["spot_id"],
            "pattern_id": "S003",
            "classification": "ambiguous",
            "actionable": False,
            "severity": "low",
            "evidence_text": description,
            "structured_context": f"security_type={attrs.get('security_type')}",
            "reason": (
                "The copy makes a strong security claim, but the ontology does not define "
                "whether basic/cctv is incompatible with 24/7 security or access control."
            ),
        })

    for claim_type, phrases in NOT_VERIFIABLE_COPY.items():
        if _contains_any(description, phrases):
            observations.append({
                "spot_id": row["spot_id"],
                "pattern_id": f"NV_{claim_type}",
                "classification": "not_verifiable",
                "actionable": False,
                "severity": "low",
                "evidence_text": description,
                "structured_context": None,
                "reason": (
                    "The listing makes a marketing/location claim for which the supplied "
                    "structured payload has no directly comparable field."
                ),
            })

    return observations
