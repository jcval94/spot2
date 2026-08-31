from __future__ import annotations

import pandas as pd

from spot2_codexway.audit import PRIMARY_KEYS, run_audit
from spot2_codexway.data import TABLES, canonical_csv_frame, load_all


def test_expected_schema_and_unique_keys(settings):
    tables = load_all(settings)
    assert set(tables) == set(TABLES)
    required = {
        "leads": {"lead_id", "created_at", "lead_score_internal"},
        "inquiries": {"inquiry_id", "lead_id", "spot_id", "inquiry_at", "broker_response"},
        "spots": {"spot_id", "created_at", "sector_name", "modality"},
        "spot_attributes": {"spot_id", "amenities"},
        "availability_snapshot": {"snapshot_id", "spot_id", "snapshot_date", "is_available"},
        "market_context": {"state", "municipality", "corridor", "sector", "month"},
    }
    for name, frame in tables.items():
        assert required[name].issubset(frame.columns)
        assert not frame.duplicated(PRIMARY_KEYS[name]).any()


def test_csv_parquet_are_alternatives_not_additive(settings):
    tables = load_all(settings)
    for name in TABLES:
        parquet = tables[name].reset_index(drop=True).astype(object).where(tables[name].reset_index(drop=True).notna(), "<NULL>")
        csv = canonical_csv_frame(settings, name).reset_index(drop=True)
        csv = csv.astype(object).where(csv.notna(), "<NULL>")
        pd.testing.assert_frame_equal(
            parquet,
            csv,
            check_dtype=False,
            check_exact=False,
            rtol=1e-12,
            atol=1e-12,
        )


def test_foreign_keys_and_known_traps_are_audited(settings):
    audit = run_audit(settings)
    assert all(audit["duplicate_formats_equal"].values())
    assert audit["relationships"]["inquiries_lead_fk_missing"] == 0
    assert audit["relationships"]["inquiries_spot_fk_missing"] == 0
    assert audit["relationships"]["no_response_with_hours"] > 0
    assert audit["relationships"]["response_without_hours"] > 0
