"""Generate and execute the assessment notebook from versioned pipeline outputs."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

from .contracts import Settings


def build_notebook(settings: Settings) -> tuple[Path, Path]:
    root = settings.codexway_root
    if sys.platform == "win32" and hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    runtime_root = root / "outputs" / "notebook_runtime"
    for name in ["ipython", "jupyter_config", "jupyter_data", "jupyter_runtime"]:
        (runtime_root / name).mkdir(parents=True, exist_ok=True)
    os.environ["IPYTHONDIR"] = str(runtime_root / "ipython")
    os.environ["JUPYTER_CONFIG_DIR"] = str(runtime_root / "jupyter_config")
    os.environ["JUPYTER_DATA_DIR"] = str(runtime_root / "jupyter_data")
    os.environ["JUPYTER_RUNTIME_DIR"] = str(runtime_root / "jupyter_runtime")
    notebook_dir = root / "notebooks"; notebook_dir.mkdir(parents=True, exist_ok=True)
    prompt = (root / "llm" / "prompt.md").read_text(encoding="utf-8")
    md = nbformat.v4.new_markdown_cell; code = nbformat.v4.new_code_cell
    cells = [
        md("# Spot2 Lead Opportunity Score\n\nA reproducible assessment of lead ranking, inventory serviceability and semantic inventory QA. Critical transformations live in tested source modules; this notebook is the reader-facing evidence trail."),
        md("## 1. Executive decision\n\nThe stability-constrained T1 challenger clears the absolute Lift@10 gate, and the conservative Opportunity score retains Lift above 1. The result is eligible for a new forward shadow period and guarded randomized pilot—not immediate automated deployment—because the historical holdout was previously consumed and fallback success is not the observed target."),
        code("from pathlib import Path\nimport json, pandas as pd\nfrom IPython.display import display, Markdown, Image\nROOT=Path.cwd()\ndef read_json(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))\nmodel=read_json(Path('outputs/metrics/t1_model_metrics.json'))\nsystem=read_json(Path('outputs/metrics/system_evaluation.json'))\ndisplay(Markdown(f\"### System gate: **{system['system_deployment_gate']}**\\n{system['decision']}\"))\ndisplay(pd.read_csv(ROOT/'outputs/metrics/system_score_metrics.csv').round(4))"),
        md("## 2. Business problem and score moments\n\nT0 is a cold-start sensitivity at lead creation. T1—the primary contract—is one score per lead at its first inquiry, after the request exists and before broker response. T2 is a challenger on later inquiries using only earlier request payloads."),
        code("manifest=read_json(Path('outputs/abt/split_manifest.json'))\ndisplay(pd.DataFrame(manifest['partitions']).T)"),
        md("## 3. Data audit\n\nCSV and Parquet are duplicate representations, not additional observations. Parquet is canonical. Primary/foreign keys, schema, timestamps and cross-format equality are executable checks."),
        code("audit=read_json(Path('outputs/tables/data_audit.json'))\ndisplay(pd.DataFrame(audit['tables']).T if isinstance(audit.get('tables'),dict) else audit)"),
        md("## 4. Demand mix and volume"),
        code("display(Image(filename=str(ROOT/'outputs/figures/eda_lead_mix.png')))\ndisplay(Image(filename=str(ROOT/'outputs/figures/eda_monthly_volume.png')))"),
        md("## 5. Outcome and segment context\n\nSegment differences are descriptive. They do not establish causality and are monitored for sample size and temporal stability."),
        code("display(Image(filename=str(ROOT/'outputs/figures/eda_target_segments.png')))\ndisplay(pd.read_csv(ROOT/'outputs/tables/target_rate_by_segment.csv').sort_values(['segment','n'],ascending=[True,False]).head(20))"),
        md("## 6. Market context — EDA only\n\n`market_context.month` lacks a reliable publication/effective timestamp. It is useful for market narrative, but not admissible as a historical feature."),
        code("display(Image(filename=str(ROOT/'outputs/figures/eda_market_context.png')))\ndisplay(pd.read_csv(ROOT/'outputs/tables/market_context_eda.csv'))"),
        md("## 7. Target, maturity and right censoring\n\nThe primary proxy is `scheduled_visit` on the first inquiry. Seven days is the default maturity buffer. Rows without adequate follow-up retain `target = NA`; they are never silently negatives."),
        code("display(pd.read_csv(ROOT/'outputs/tables/target_maturity_sensitivity.csv'))\ndisplay(pd.read_csv(ROOT/'outputs/metrics/target_sensitivity_metrics.csv').round(4))"),
        md("## 8. Why T0 is not primary\n\nThe 30-day lead-creation target rises with the number of inquiries observed in the window. T1 is more stable and maps to a precise operational event."),
        code("display(Image(filename=str(ROOT/'outputs/figures/target_drift.png')))"),
        md("## 9. Leakage policy\n\nThe clean model uses an explicit allowlist. Broker response, response hours, internal score, future inquiries, mutable spot counters, ambiguous market context and nearest/future snapshots are blocked. A feature must be demonstrably available at scoring time."),
        code("display(Markdown((ROOT/'evidence/LEAKAGE_MATRIX.md').read_text(encoding='utf-8')))"),
        md("## 10. Point-in-time availability\n\nAvailability is joined with strict backward as-of. Missing or stale history means **unknown**, represented by lower/upper serviceability bounds. It never means unavailable, and it is never filled from the future."),
        code("display(Image(filename=str(ROOT/'outputs/figures/availability_coverage.png')))\ndisplay(pd.read_csv(ROOT/'outputs/tables/inventory_freshness_sensitivity.csv').round(4))\ndisplay(read_json(Path('outputs/metrics/inventory_audit.json')))"),
        md("## 11. Baselines and model selection\n\nPositive rate, an interpretable business rule and Logistic Regression precede CatBoost. Promotion uses expanding-window folds; the holdout is not used for selection."),
        code("display(pd.DataFrame(model['metrics']).T.round(4))\ndisplay(pd.read_csv(ROOT/'outputs/metrics/rolling_model_comparison.csv').round(4))"),
        md("## 12. Ranking under capacity constraints\n\nRecall@X answers the operational question: what share of positive outcomes appears in the top X% of leads?"),
        code("display(Image(filename=str(ROOT/'outputs/figures/gains_curve.png')))\ndisplay(pd.read_csv(ROOT/'outputs/tables/gains.csv').query('population_fraction in [0.05,0.1,0.2]').round(4))"),
        md("## 13. Calibration and uncertainty\n\nCalibration is assessed against the constant train-rate baseline. Bootstrap intervals make the absence of reliable lift visible."),
        code("display(Image(filename=str(ROOT/'outputs/figures/calibration_plot.png')))\ndisplay(pd.read_csv(ROOT/'outputs/metrics/t1_metric_intervals.csv').round(4))"),
        md("## 14. Lead Quality vs Inventory vs Opportunity\n\nThe same holdout is used for all components. Because the T1 label does not observe fallback success, the combined comparison is a diagnostic and not a calibrated inventory outcome claim."),
        code("display(pd.read_csv(ROOT/'outputs/metrics/system_score_metrics.csv').round(4))\ndisplay(pd.read_csv(ROOT/'outputs/metrics/system_score_paired_delta.csv').round(4))"),
        md("## 15. Two-axis operating policy\n\nUntil a score passes the gate, quality and serviceability should stay separate: verify uncertain inventory, source alternatives for high-quality/unserved leads, and retain the current workflow otherwise."),
        code("scores=pd.read_parquet(ROOT/'outputs/predictions/lead_opportunity_scores.parquet')\ndisplay(scores[['quality_band','serviceability_band','diagnostic_action','deployment_status']].value_counts().reset_index(name='leads').head(20))"),
        md("## 16. Fallback examples\n\nRecommendations preserve sector/modality and relax geography corridor → municipality → state. Historical listing compatibility remains conditional because non-availability listing fields are not versioned."),
        code("show=['lead_id','lead_quality_score_0_100','inventory_serviceability_lower','inventory_serviceability_upper','inventory_confidence','fallback_spot_ids','fallback_reason_codes']\ndisplay(scores[show].head(10))"),
        md("## 17. Clustering and combinations\n\nProfiles are fit inside train and gated for balance and ARI stability. Combination cells require N≥50, shrinkage, Wilson intervals and BH-FDR. No discovered cluster multiplies the production score."),
        code("display(pd.read_csv(ROOT/'outputs/tables/cluster_profile_metrics.csv').round(4))\ncells=pd.read_csv(ROOT/'outputs/tables/cluster_combinations.csv'); display(cells.head(15))"),
        md("## 18. Leakage stress test\n\nDeliberately invalid variants show why high apparent performance is not automatically deployable. The clean pipeline cannot import those features."),
        code("display(read_json(Path('outputs/metrics/leakage_stress_test.json')))"),
        md("## 19. Interpretability, errors and drift"),
        code("display(pd.read_csv(ROOT/'outputs/tables/feature_importance.csv').head(20))\ndisplay(pd.read_csv(ROOT/'outputs/tables/monthly_model_stability.csv').round(4))\ndisplay(pd.read_csv(ROOT/'outputs/tables/feature_drift.csv').sort_values('value',ascending=False).head(20))"),
        md("## 20. LLM use: semantic inventory QA\n\nThe LLM audits contradictions between listing text and structured attributes. It is cross-sectional QA, not a historical model feature. Natural accuracy still requires blinded human gold; a controlled injected benchmark measures sensitivity only."),
        code("llm=read_json(Path('outputs/metrics/llm_audit_evaluation.json'))\ndisplay(llm)"),
        md("### Versioned LLM prompt\n\n" + prompt),
        md("## 21. Product and measurement roadmap\n\n1. Version price, geography, copy and lifecycle state. 2. Log every recommendation and contact exposure. 3. Capture scheduled visit and downstream conversion at fixed horizons. 4. Rebuild a genuinely untouched temporal holdout. 5. Only then consider a guarded randomized pilot."),
        code("display(read_json(Path('outputs/tables/online_ab_protocol.json')))"),
        md("## 22. Limitations\n\nThe target is a first-contact proxy; the global dataset was previously inspected; listing fields are incompletely versioned; market publication timing is unknown; natural LLM gold is absent; offline metrics are observational; and inventory does not improve ranking over Lead Quality alone."),
        md("## 23. Reproduction\n\nFrom the repository root: `python codexway/scripts/run_all.py`. The runner audits data, builds ABTs, trains models, evaluates system components, executes tests and renders this notebook/PDFs. A repeated run checks prediction fingerprints."),
        md("## 24. Final takeaway\n\nThe clean T1 model and conservative Opportunity score both exceed random top-decile prioritization with bootstrap lower bounds above 1. The next decision is a forward shadow validation and guarded experiment, while preserving the explicit caveats around target alignment and inventory versioning."),
    ]
    notebook = nbformat.v4.new_notebook(cells=cells, metadata={
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    })
    ipynb = notebook_dir / "spot2_assessment.ipynb"
    nbformat.write(notebook, ipynb)
    executed = NotebookClient(notebook, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(root)}}).execute()
    nbformat.write(executed, ipynb)
    exporter = HTMLExporter()
    html, _ = exporter.from_notebook_node(executed)
    html_path = notebook_dir / "spot2_assessment.html"
    html_path.write_text(html, encoding="utf-8")
    return ipynb, html_path
