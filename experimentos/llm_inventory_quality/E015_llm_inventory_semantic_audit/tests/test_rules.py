from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from src.rules import audit_row  # noqa: E402


def row(description: str, **attrs):
    base_attrs = {
        "natural_light": True,
        "security_type": "basic",
        "parking_spaces": 5,
        "building_status": "good",
        "amenities": [],
    }
    base_attrs.update(attrs)
    return {
        "spot_id": "1",
        "sector_name": "Office",
        "type_name": "Single",
        "title": "",
        "description": description,
        "attributes": base_attrs,
    }


class TestRules(unittest.TestCase):
    def test_natural_light_contradiction(self):
        issues = audit_row(row("Amplio espacio con buena iluminación natural.", natural_light=False))
        self.assertEqual([x["rule_id"] for x in issues], ["R001"])

    def test_security_contradiction(self):
        issues = audit_row(row("Seguridad 24/7 y control de acceso.", security_type="none"))
        self.assertEqual([x["rule_id"] for x in issues], ["R002"])

    def test_parking_amenity_prevents_flag(self):
        issues = audit_row(row("Cuenta con todos los servicios y estacionamiento.", parking_spaces=0, amenities=["parking"]))
        self.assertFalse(any(x["rule_id"] == "R003" for x in issues))

    def test_parking_zero_flags(self):
        issues = audit_row(row("Cuenta con todos los servicios y estacionamiento.", parking_spaces=0, amenities=[]))
        self.assertTrue(any(x["rule_id"] == "R003" for x in issues))

    def test_readiness_contradiction(self):
        issues = audit_row(row("Espacio listo para ocupar con acabados de primera.", building_status="needs_renovation"))
        self.assertEqual([x["rule_id"] for x in issues], ["R004"])

    def test_clean_listing(self):
        issues = audit_row(row("Espacio versátil adaptable a diferentes giros."))
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
