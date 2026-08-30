from pathlib import Path
import sys

import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from build_abts import project_abt


def test_project_abt_does_not_duplicate_feature_metadata_columns():
    df = pd.DataFrame(
        {
            "lead_id": [1],
            "stage_id": [1],
            "stage": ["T1_first_inquiry"],
            "score_time": [pd.Timestamp("2026-01-01")],
            "split": ["train"],
            "target_scheduled_visit_30d": [0],
            "observation_end": [pd.Timestamp("2026-03-01")],
            "censor_cutoff": [pd.Timestamp("2026-01-30")],
            "inquiry_id": [10],
            "spot_id": [20],
            "broker_id": [30],
            "inquiry_number": [1.0],
        }
    )
    projected = project_abt(df, ["inquiry_number"])
    assert projected.columns.is_unique
    assert list(projected.columns).count("inquiry_number") == 1
