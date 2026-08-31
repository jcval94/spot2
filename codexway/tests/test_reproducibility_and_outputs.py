from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
from pypdf import PdfReader
from sklearn.linear_model import LogisticRegression


def test_seeded_estimator_is_reproducible():
    x = np.arange(200, dtype=float).reshape(-1, 2)
    y = np.tile([0, 1], 50)
    first = LogisticRegression(random_state=42, max_iter=1000).fit(x, y).predict_proba(x)[:, 1]
    second = LogisticRegression(random_state=42, max_iter=1000).fit(x, y).predict_proba(x)[:, 1]
    np.testing.assert_allclose(first, second, rtol=0, atol=0)


def test_final_outputs_if_present(settings):
    score_path = settings.codexway_root / "outputs" / "predictions" / "lead_opportunity_scores.parquet"
    assert score_path.exists(), "run the codexway pipeline before validating final deliverables"
    scores = pd.read_parquet(score_path)
    assert len(scores) == 5000
    assert scores["lead_id"].is_unique
    assert scores["lead_quality_score_0_100"].between(0, 100).all()
    assert scores["opportunity_score_0_100"].between(0, 100).all()
    assert scores["data_fingerprint"].nunique() == 1
    assert len(scores["data_fingerprint"].iloc[0]) == 64


def test_pdf_page_contract_if_present(settings):
    one = settings.codexway_root / "reports" / "one_pager.pdf"
    slides = settings.codexway_root / "reports" / "slides.pdf"
    if one.exists():
        assert len(PdfReader(str(one)).pages) == 1
    if slides.exists():
        assert 5 <= len(PdfReader(str(slides)).pages) <= 8
