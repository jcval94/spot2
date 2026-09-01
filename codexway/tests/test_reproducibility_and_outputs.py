from __future__ import annotations

import hashlib

import nbformat
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


def test_executive_notebook_contract_if_present(settings):
    notebook_path = settings.codexway_root / "notebooks" / "spot2_assessment.ipynb"
    html_path = settings.codexway_root / "notebooks" / "spot2_assessment.html"
    assert notebook_path.exists() and html_path.exists(), "run the pipeline to render the notebook"

    notebook = nbformat.read(notebook_path, as_version=4)
    headings = [
        line
        for cell in notebook.cells
        if cell.cell_type == "markdown"
        for line in cell.source.splitlines()
        if line.startswith("## ") and not line.startswith("### ")
    ]
    assert len(headings) == 9
    assert headings[0].startswith("## 1. tl;dr")
    assert headings[-1].startswith("## 9. Conclusiones")

    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    assert code_cells and all(cell.execution_count is not None for cell in code_cells)
    assert not [
        output
        for cell in code_cells
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]

    html = html_path.read_text(encoding="utf-8")
    assert 'id="spot2-executive-theme"' in html
    assert 'id="spot2-executive-behavior"' in html
    assert "Ver código reproducible" in html
    assert '<html lang="es">' in html
    assert '<script src="https://' not in html
