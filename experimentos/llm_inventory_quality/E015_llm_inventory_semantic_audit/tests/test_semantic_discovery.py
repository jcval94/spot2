from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from src.rules_v2 import audit_row_v2  # noqa: E402
from src.semantic_discovery import semantic_observations  # noqa: E402


def row(sector: str, description: str, security_type: str = "basic"):
    return {
        "spot_id": "1",
        "sector_name": sector,
        "type_name": "Single",
        "title": "",
        "description": description,
        "attributes": {
            "natural_light": True,
            "security_type": security_type,
            "parking_spaces": 5,
            "building_status": "good",
            "amenities": [],
        },
    }


class TestSemanticDiscovery(unittest.TestCase):
    def test_land_building_copy_is_actionable_semantic_mismatch(self):
        observations = semantic_observations(
            row("Land", "Recién remodelado con acabados modernos.")
        )
        s001 = [x for x in observations if x["pattern_id"] == "S001"]
        self.assertEqual(len(s001), 1)
        self.assertTrue(s001[0]["actionable"])
        self.assertEqual(
            s001[0]["classification"], "semantic_cross_field_mismatch"
        )

    def test_retail_alternate_use_is_not_actionable_by_default(self):
        observations = semantic_observations(
            row("Retail", "Ideal para oficinas corporativas o centro de distribución.")
        )
        s002 = [x for x in observations if x["pattern_id"] == "S002"]
        self.assertEqual(len(s002), 1)
        self.assertFalse(s002[0]["actionable"])

    def test_not_verifiable_marketing_claim_is_informational(self):
        observations = semantic_observations(
            row("Office", "Zona de alta plusvalía y demanda comercial.")
        )
        self.assertEqual(observations[0]["classification"], "not_verifiable")
        self.assertFalse(observations[0]["actionable"])

    def test_v2_promotes_land_pattern_but_v1_remains_separate(self):
        issues = audit_row_v2(
            row("Land", "Espacio listo para ocupar con acabados de primera.")
        )
        self.assertTrue(any(x["rule_id"] == "S001" for x in issues))


if __name__ == "__main__":
    unittest.main()
