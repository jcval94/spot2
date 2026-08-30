from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd


def norm(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def has_any(text: str, phrases: tuple[str, ...]) -> bool:
    x = norm(text)
    return any(p in x for p in phrases)


NATURAL = ("iluminacion natural", "luz natural")
SECURITY = ("seguridad 24/7", "control de acceso", "vigilancia", "circuito cerrado")
PARKING = ("estacionamiento", "cajon de estacionamiento", "cajones de estacionamiento", "parking")
READINESS = ("listo para ocupar", "recien remodelado", "acabados modernos", "acabados de primera")
BUILDING_COPY = tuple(sorted(set(NATURAL + READINESS)))
OFFICE_DISTRIBUTION = ("ideal para oficinas corporativas o centro de distribucion",)


def amenities(value: object) -> set[str]:
    if pd.isna(value):
        return set()
    try:
        x = json.loads(str(value))
        return {norm(v) for v in x} if isinstance(x, list) else set()
    except (TypeError, ValueError, json.JSONDecodeError):
        return set()


def build(spots: pd.DataFrame, attrs: pd.DataFrame) -> pd.DataFrame:
    d = spots.merge(attrs, on="spot_id", how="left", validate="one_to_one").copy()
    d["original_text"] = d["title"].fillna("") + "\n" + d["description"].fillna("")
    text = d["original_text"]

    d["rule_claim_natural_light"] = text.map(lambda x: has_any(x, NATURAL)).astype(int)
    d["rule_claim_security"] = text.map(lambda x: has_any(x, SECURITY)).astype(int)
    d["rule_claim_parking"] = text.map(lambda x: has_any(x, PARKING)).astype(int)
    d["rule_claim_readiness"] = text.map(lambda x: has_any(x, READINESS)).astype(int)

    d["rule_conflict_natural_light"] = (
        d["rule_claim_natural_light"].eq(1)
        & d["natural_light"].astype("string").str.lower().eq("false")
    ).astype(int)
    d["rule_conflict_security"] = (
        d["rule_claim_security"].eq(1)
        & d["security_type"].astype("string").map(norm).isin(["", "none"])
    ).astype(int)
    amenity_sets = d["amenities"].map(amenities)
    d["rule_conflict_parking"] = (
        d["rule_claim_parking"].eq(1)
        & pd.to_numeric(d["parking_spaces"], errors="coerce").fillna(0).eq(0)
        & ~amenity_sets.map(lambda x: "parking" in x)
    ).astype(int)
    d["rule_conflict_readiness"] = (
        d["rule_claim_readiness"].eq(1)
        & d["building_status"].astype("string").map(norm).eq("needs_renovation")
    ).astype(int)

    direct_cols = [
        "rule_conflict_natural_light",
        "rule_conflict_security",
        "rule_conflict_parking",
        "rule_conflict_readiness",
    ]
    d["rule_direct_conflict_count"] = d[direct_cols].sum(axis=1)
    d["rule_direct_conflict_flag"] = d["rule_direct_conflict_count"].gt(0).astype(int)

    d["rule_land_building_copy_flag"] = (
        d["sector_name"].eq("Land")
        & text.map(lambda x: has_any(x, BUILDING_COPY))
    ).astype(int)

    # Free semantic ambiguity confirmed by the 100-row LLM pilot.
    d["rule_security_ambiguity_flag"] = (
        d["rule_claim_security"].eq(1)
        & d["security_type"].astype("string").map(norm).isin(["basic", "cctv"])
    ).astype(int)
    d["rule_retail_adaptive_use_flag"] = (
        d["sector_name"].eq("Retail")
        & text.map(lambda x: has_any(x, OFFICE_DISTRIBUTION))
    ).astype(int)
    d["rule_semantic_ambiguity_flag"] = (
        d["rule_security_ambiguity_flag"].eq(1)
        | d["rule_retail_adaptive_use_flag"].eq(1)
    ).astype(int)

    d["rule_semantic_signal_count"] = (
        d["rule_direct_conflict_flag"]
        + d["rule_land_building_copy_flag"]
        + d["rule_semantic_ambiguity_flag"]
    )

    d["rule_semantic_review_tier"] = "none"
    d.loc[d["rule_semantic_ambiguity_flag"].eq(1), "rule_semantic_review_tier"] = "ambiguity"
    d.loc[d["rule_land_building_copy_flag"].eq(1), "rule_semantic_review_tier"] = "cross_field"
    d.loc[d["rule_direct_conflict_flag"].eq(1), "rule_semantic_review_tier"] = "direct_conflict"

    cols = [
        "spot_id",
        "original_text",
        "rule_claim_natural_light",
        "rule_claim_security",
        "rule_claim_parking",
        "rule_claim_readiness",
        *direct_cols,
        "rule_direct_conflict_count",
        "rule_direct_conflict_flag",
        "rule_land_building_copy_flag",
        "rule_security_ambiguity_flag",
        "rule_retail_adaptive_use_flag",
        "rule_semantic_ambiguity_flag",
        "rule_semantic_signal_count",
        "rule_semantic_review_tier",
    ]
    return d[cols]


def main():
    root = Path(__file__).resolve().parents[2]
    src = root / "data" / "candidate" / "csv"
    out = Path(__file__).resolve().parent / "results" / "semantic_rule_sidecar_3000.csv"
    spots = pd.read_csv(src / "spots.csv")
    attrs = pd.read_csv(src / "spot_attributes.csv")
    sidecar = build(spots, attrs)
    out.parent.mkdir(parents=True, exist_ok=True)
    sidecar.to_csv(out, index=False)
    print(
        sidecar[
            [
                "rule_direct_conflict_flag",
                "rule_land_building_copy_flag",
                "rule_semantic_ambiguity_flag",
            ]
        ].sum().to_string()
    )


if __name__ == "__main__":
    main()
