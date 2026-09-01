"""Generate and execute the executive assessment notebook from pipeline outputs."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

from .contracts import Settings


EXECUTIVE_CSS = """
<style id="spot2-executive-theme">
:root { --ink:#12263a; --muted:#5d6b78; --blue:#175cd3; --cyan:#12b5cb;
  --green:#16865c; --amber:#b66a00; --red:#b42318; --paper:#ffffff; --wash:#f3f6fa; }
html { scroll-behavior:smooth; }
body { background:var(--wash) !important; color:var(--ink) !important; }
.jp-Notebook { max-width:1160px; margin:0 auto; padding:42px 52px 96px !important;
  background:var(--paper); box-shadow:0 12px 42px rgba(18,38,58,.10); }
.jp-RenderedHTMLCommon { color:var(--ink); font-family:Inter,Segoe UI,Arial,sans-serif; line-height:1.55; }
.jp-RenderedHTMLCommon h1 { font-size:2.65rem; letter-spacing:-.035em; margin:.15em 0 .35em; }
.jp-RenderedHTMLCommon h2 { margin-top:2.4em; padding-top:.55em; border-top:4px solid var(--blue);
  color:var(--ink); font-size:1.8rem; letter-spacing:-.02em; }
.jp-RenderedHTMLCommon h3 { color:var(--blue); margin-top:1.7em; font-size:1.24rem; }
.jp-RenderedHTMLCommon p, .jp-RenderedHTMLCommon li { font-size:1.03rem; }
.jp-RenderedHTMLCommon table { font-size:.86rem; border-collapse:separate; border-spacing:0; width:100%; }
.jp-RenderedHTMLCommon thead th { background:#e9f0fb; color:var(--ink); }
.jp-RenderedHTMLCommon tbody tr:nth-child(even) { background:#f7f9fc; }
.jp-RenderedHTMLCommon img { display:block; max-width:100%; height:auto; margin:1rem auto;
  border-radius:12px; box-shadow:0 5px 18px rgba(18,38,58,.09); }
.jp-InputPrompt, .jp-OutputPrompt { display:none !important; }
.jp-CodeCell { border:1px solid #dbe3ec; border-radius:10px; margin:1rem 0 !important; overflow:hidden; }
.jp-CodeCell .jp-Cell-outputWrapper { padding:.35rem .75rem .8rem; }
details.code-details { background:#f7f9fc; border-bottom:1px solid #dbe3ec; }
details.code-details summary { cursor:pointer; color:var(--blue); font-weight:650; padding:.65rem .9rem; }
details.code-details[open] summary { border-bottom:1px solid #dbe3ec; }
.spot2-hero { margin:1.25rem 0 1.4rem; padding:1.45rem 1.55rem; border-radius:16px;
  background:linear-gradient(135deg,#102a43 0%,#175cd3 72%,#12b5cb 100%); color:white; }
.spot2-hero h3 { border:0 !important; color:white !important; margin:0 0 .35rem !important; padding:0 !important; }
.spot2-hero p { margin:.25rem 0; color:#e8f2ff; }
.spot2-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.75rem; margin:1rem 0; }
.spot2-card { border:1px solid #dbe3ec; border-radius:12px; padding:1rem; background:white; }
.spot2-card strong { display:block; font-size:1.25rem; color:var(--blue); line-height:1.15;
  overflow-wrap:anywhere; word-break:break-word; }
.spot2-card small { display:block; color:var(--muted); margin-top:.25rem; }
.spot2-callout { border-left:5px solid var(--cyan); background:#ecfbfd; padding:.85rem 1rem;
  border-radius:0 10px 10px 0; margin:1rem 0; }
.spot2-warning { border-left-color:var(--amber); background:#fff7e8; }
.spot2-case { border:1px solid #b8cae5; border-radius:14px; padding:1.15rem 1.25rem;
  background:linear-gradient(180deg,#f7fbff,#fff); }
.spot2-case h3 { margin-top:0; }
.spot2-meter { height:12px; border-radius:99px; background:#e4eaf1; overflow:hidden; margin:.3rem 0 .85rem; }
.spot2-meter span { display:block; height:100%; background:linear-gradient(90deg,var(--blue),var(--cyan)); }
#exec-toolbar { position:fixed; right:18px; top:18px; z-index:9999; width:220px; max-height:calc(100vh - 36px);
  overflow:auto; padding:.7rem; border:1px solid #dbe3ec; border-radius:12px; background:rgba(255,255,255,.96);
  box-shadow:0 8px 26px rgba(18,38,58,.14); font-family:Inter,Segoe UI,Arial,sans-serif; }
#exec-toolbar strong { display:block; color:var(--ink); margin:.15rem .3rem .45rem; }
#exec-toolbar a { display:block; padding:.32rem .4rem; color:#35516d; text-decoration:none; font-size:.78rem; }
#exec-toolbar a:hover { color:var(--blue); background:#eef4ff; border-radius:6px; }
#exec-toolbar button { width:100%; margin-top:.55rem; border:0; border-radius:7px; padding:.48rem;
  background:var(--blue); color:white; cursor:pointer; }
@media (max-width:1450px) { #exec-toolbar { display:none; } }
@media (max-width:800px) { .jp-Notebook { padding:24px 18px 64px !important; } .spot2-grid { grid-template-columns:1fr 1fr; } }
@media print { body { background:white !important; } #exec-toolbar, details.code-details { display:none !important; }
  .jp-Notebook { box-shadow:none; max-width:none; padding:0 !important; } .jp-CodeCell { break-inside:avoid; } }
</style>
"""


EXECUTIVE_JS = """
<script id="spot2-executive-behavior">
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.jp-CodeCell .jp-Cell-inputWrapper').forEach((input) => {
    const details = document.createElement('details');
    details.className = 'code-details';
    const summary = document.createElement('summary');
    summary.textContent = 'Ver código reproducible';
    input.parentNode.insertBefore(details, input);
    details.appendChild(summary);
    details.appendChild(input);
  });
  const headings = [...document.querySelectorAll('.jp-RenderedHTMLCommon h2')];
  const nav = document.createElement('nav');
  nav.id = 'exec-toolbar';
  nav.setAttribute('aria-label', 'Navegación del notebook');
  nav.innerHTML = '<strong>Spot2 · Assessment</strong>';
  headings.forEach((heading) => {
    const link = document.createElement('a');
    link.href = '#' + heading.id;
    link.textContent = heading.textContent.replace('¶', '').trim();
    nav.appendChild(link);
  });
  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.textContent = 'Mostrar todo el código';
  toggle.addEventListener('click', () => {
    const blocks = [...document.querySelectorAll('details.code-details')];
    const shouldOpen = blocks.some((block) => !block.open);
    blocks.forEach((block) => { block.open = shouldOpen; });
    toggle.textContent = shouldOpen ? 'Ocultar todo el código' : 'Mostrar todo el código';
  });
  nav.appendChild(toggle);
  document.body.appendChild(nav);
});
</script>
"""


def _executive_html(html: str) -> str:
    """Add a self-contained reader layer without changing notebook semantics."""
    html = html.replace('<html lang="en">', '<html lang="es">')
    html = html.replace(
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>',
        "",
    )
    math_start = html.find("<!-- Load mathjax -->")
    math_end_marker = "<!-- End of mathjax configuration -->"
    math_end = html.find(math_end_marker, math_start)
    if math_start >= 0 and math_end >= 0:
        html = html[:math_start] + html[math_end + len(math_end_marker) :]
    module_start = html.find('<script type="module">')
    module_end = html.find("</script>", module_start)
    if module_start >= 0 and module_end >= 0 and "mermaid" in html[module_start:module_end]:
        html = html[:module_start] + html[module_end + len("</script>") :]
    return html.replace("</head>", EXECUTIVE_CSS + "</head>").replace(
        "</body>", EXECUTIVE_JS + "</body>"
    )


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

    notebook_dir = root / "notebooks"
    notebook_dir.mkdir(parents=True, exist_ok=True)
    prompt = (root / "llm" / "prompt.md").read_text(encoding="utf-8")
    md = nbformat.v4.new_markdown_cell
    code = nbformat.v4.new_code_cell

    cells = [
        md(
            "# Spot2 · Lead Opportunity Score\n\n"
            "**Assessment ejecutivo reproducible.** Conecta la decisión de negocio con la evidencia, "
            "el contrato point-in-time y el código que produce cada resultado. Los Markdown extensos "
            "siguen siendo anexos; este notebook es la ruta analítica de lectura."
        ),
        md(
            "## 1. tl;dr — decisión ejecutiva\n\n"
            "El objetivo no es automatizar una decisión comercial todavía. El resultado habilita una "
            "nueva cohorte *shadow* y, si se reproduce, un piloto aleatorizado con guardas."
        ),
        code(
            "from pathlib import Path\n"
            "import json, pandas as pd\n"
            "from IPython.display import display, Markdown, HTML, Image\n"
            "ROOT = Path.cwd()\n"
            "def read_json(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))\n"
            "model = read_json(Path('outputs/metrics/t1_model_metrics.json'))\n"
            "system = read_json(Path('outputs/metrics/system_evaluation.json'))\n"
            "scores = pd.read_parquet(ROOT/'outputs/predictions/lead_opportunity_scores.parquet')\n"
            "assert model['selected_model'] == 'stable_segment_logistic'\n"
            "assert system['lead_quality_gate'] == 'GO'\n"
            "assert system['inventory_incremental_gate'] == 'NO_GO'\n"
            "assert system['decision'] == 'ELIGIBLE_FOR_NEW_FORWARD_VALIDATION_AND_GUARDED_RANDOMIZED_PILOT'\n"
            "decision_label = 'Elegible para nueva validación forward y piloto aleatorizado con guardas'\n"
            "q, q_ci = system['quality_lift_top_10pct'], system['quality_lift_top_10pct_ci']\n"
            "o, o_ci = system['opportunity_lift_top_10pct'], system['opportunity_lift_top_10pct_ci']\n"
            "display(HTML(f'''<section class=\"spot2-hero\"><h3>Recomendación: validar hacia adelante</h3>"
            "<p>{decision_label}</p></section>"
            "<div class=\"spot2-grid\">"
            "<div class=\"spot2-card\"><strong>{q:.3f}×</strong><small>Quality Lift@10 · IC {q_ci[0]:.3f}–{q_ci[1]:.3f}</small></div>"
            "<div class=\"spot2-card\"><strong>{o:.3f}×</strong><small>Opportunity lower Lift@10 · IC {o_ci[0]:.3f}–{o_ci[1]:.3f}</small></div>"
            "<div class=\"spot2-card\"><strong>{model['selected_model']}</strong><small>modelo seleccionado · calibración Platt retenida</small></div>"
            "<div class=\"spot2-card\"><strong>{system['inventory_incremental_gate'].replace('_','-')}</strong><small>valor incremental de Inventory sobre T1</small></div>"
            "</div>'''))"
        ),
        md(
            "<div class=\"spot2-callout\"><strong>Qué demuestra.</strong> En el holdout procedural, "
            "Quality y Opportunity lower superan la selección aleatoria absoluta en el top 10%. "
            "<strong>Qué no demuestra.</strong> Inventory no agrega valor incremental probado sobre "
            "Quality y el target T1 no observa el éxito del fallback.</div>"
        ),
        md(
            "## 2. Contexto y contrato analítico\n\n"
            "### 2.1 Problema de negocio y momentos de scoring\n\n"
            "T0 es una sensibilidad *cold-start* al crear el lead. **T1 es el contrato primario:** un "
            "score por lead en su primera solicitud, después de observar la demanda y antes de la "
            "respuesta del broker. T2 es un challenger para solicitudes posteriores usando sólo payloads previos."
        ),
        code(
            "manifest = read_json(Path('outputs/abt/split_manifest.json'))\n"
            "display(pd.DataFrame(manifest['partitions']).T)"
        ),
        md(
            "### 2.2 Auditoría y granularidad\n\n"
            "CSV y Parquet son representaciones duplicadas, no observaciones adicionales. Parquet es "
            "canónico. Llaves, esquema, timestamps e igualdad entre formatos son verificaciones ejecutables."
        ),
        code(
            "audit = read_json(Path('outputs/tables/data_audit.json'))\n"
            "display(pd.DataFrame(audit['tables']).T if isinstance(audit.get('tables'), dict) else audit)"
        ),
        md(
            "### 2.3 Target, madurez y censura\n\n"
            "El proxy primario es `scheduled_visit` en la primera solicitud. Siete días es el buffer "
            "de madurez por defecto. Filas sin seguimiento suficiente conservan `target = NA`; nunca se "
            "convierten silenciosamente en negativas."
        ),
        code(
            "maturity = pd.read_csv(ROOT/'outputs/tables/target_maturity_sensitivity.csv')\n"
            "target_metrics = pd.read_csv(ROOT/'outputs/metrics/target_sensitivity_metrics.csv')\n"
            "assert 7 in maturity.select_dtypes('number').astype(float).values\n"
            "display(maturity); display(target_metrics.round(4)); display(Image(filename=str(ROOT/'outputs/figures/target_drift.png')))"
        ),
        md(
            "### 2.4 Política de leakage\n\n"
            "La allowlist excluye respuesta del broker, horas de respuesta, score interno, solicitudes "
            "futuras, contadores mutables, contexto de mercado ambiguo y snapshots más cercanos o futuros. "
            "Una señal entra sólo si era demostrablemente observable al momento del score."
        ),
        code("display(Markdown((ROOT/'evidence/LEAKAGE_MATRIX.md').read_text(encoding='utf-8')))"),
        md(
            "## 3. Datos y tensión demanda–oferta\n\n"
            "### 3.1 Mezcla, volumen y segmentos\n\n"
            "La lectura comienza con la composición de demanda y su evolución temporal. Las diferencias "
            "por segmento son descriptivas: no implican causalidad y deben vigilarse por tamaño y estabilidad."
        ),
        code(
            "display(Image(filename=str(ROOT/'outputs/figures/eda_lead_mix.png')))\n"
            "display(Image(filename=str(ROOT/'outputs/figures/eda_monthly_volume.png')))\n"
            "display(Image(filename=str(ROOT/'outputs/figures/eda_target_segments.png')))\n"
            "display(pd.read_csv(ROOT/'outputs/tables/target_rate_by_segment.csv').sort_values(['segment','n'], ascending=[True,False]).head(20))"
        ),
        md(
            "### 3.2 Contexto de mercado: narrativa, no feature\n\n"
            "`market_context.month` no tiene timestamp fiable de publicación o vigencia. Sirve para "
            "entender el entorno, pero no es admisible como feature histórica."
        ),
        code(
            "display(Image(filename=str(ROOT/'outputs/figures/eda_market_context.png')))\n"
            "display(pd.read_csv(ROOT/'outputs/tables/market_context_eda.csv'))"
        ),
        md(
            "## 4. Lead Quality — selección, ranking y calibración\n\n"
            "### 4.1 Baselines antes de complejidad\n\n"
            "Tasa positiva, una regla interpretable y Regresión Logística preceden a CatBoost. La promoción "
            "usa folds temporales expansivos; el holdout no participa en la selección."
        ),
        code(
            "display(pd.DataFrame(model['metrics']).T.round(4))\n"
            "display(pd.read_csv(ROOT/'outputs/metrics/rolling_model_comparison.csv').round(4))"
        ),
        md(
            "### 4.2 Ranking bajo capacidad limitada\n\n"
            "Recall@X responde la pregunta operativa: ¿qué proporción de resultados positivos aparece "
            "al trabajar sólo el X% superior de leads?"
        ),
        code(
            "display(Image(filename=str(ROOT/'outputs/figures/gains_curve.png')))\n"
            "gains = pd.read_csv(ROOT/'outputs/tables/gains.csv')\n"
            "display(gains.query('population_fraction in [0.05, 0.1, 0.2]').round(4))"
        ),
        md(
            "### 4.3 Calibración e incertidumbre\n\n"
            "La calibración Platt se ajusta en validación y se conserva sólo si mejora. Los intervalos "
            "bootstrap separan una señal plausible de una falsa precisión puntual."
        ),
        code(
            "display(Image(filename=str(ROOT/'outputs/figures/calibration_plot.png')))\n"
            "display(pd.read_csv(ROOT/'outputs/metrics/t1_metric_intervals.csv').round(4))"
        ),
        md("### 4.4 Interpretabilidad y estabilidad temporal"),
        code(
            "display(pd.read_csv(ROOT/'outputs/tables/feature_importance.csv').head(20))\n"
            "display(pd.read_csv(ROOT/'outputs/tables/monthly_model_stability.csv').round(4))\n"
            "display(pd.read_csv(ROOT/'outputs/tables/feature_drift.csv').sort_values('value', ascending=False).head(20))"
        ),
        md(
            "## 5. Inventory, Opportunity y fallback\n\n"
            "### 5.1 Disponibilidad point-in-time\n\n"
            "Availability se une con un **backward as-of** estricto. Historia ausente o vieja significa "
            "**UNKNOWN, no UNAVAILABLE**, y se expresa como bounds lower/upper; jamás se rellena desde el futuro."
        ),
        code(
            "display(Image(filename=str(ROOT/'outputs/figures/availability_coverage.png')))\n"
            "display(pd.read_csv(ROOT/'outputs/tables/inventory_freshness_sensitivity.csv').round(4))\n"
            "display(read_json(Path('outputs/metrics/inventory_audit.json')))"
        ),
        md(
            "### 5.2 Trade-off central\n\n"
            "Los componentes se comparan sobre el mismo holdout. Como T1 no observa éxito de fallback, "
            "la comparación combinada es diagnóstico de ranking, no probabilidad calibrada de inventario."
        ),
        code(
            "system_metrics = pd.read_csv(ROOT/'outputs/metrics/system_score_metrics.csv')\n"
            "paired = pd.read_csv(ROOT/'outputs/metrics/system_score_paired_delta.csv')\n"
            "display(system_metrics.round(4)); display(paired.round(4))"
        ),
        md(
            "<div class=\"spot2-callout spot2-warning\"><strong>Decisión conservadora.</strong> "
            "Inventory puede superar random en algún bound o corte de capacidad, pero no mejora de forma "
            "incremental a Quality sobre el proxy T1. Su gate permanece <strong>NO-GO</strong>.</div>"
        ),
        md(
            "### 5.3 Política de dos ejes y alternativas\n\n"
            "Quality y Serviceability permanecen separados: verificar inventario incierto, buscar "
            "alternativas para demanda de calidad sin servicio y mantener el flujo estándar en el resto. "
            "El ranking conserva top-3 interno y muestra hasta cinco alternativas compatibles."
        ),
        code(
            "policy = scores[['quality_band','serviceability_band','diagnostic_action','deployment_status']].value_counts().reset_index(name='leads')\n"
            "display(policy.head(20))\n"
            "show = ['lead_id','lead_quality_score_0_100','inventory_serviceability_lower','inventory_serviceability_upper','inventory_confidence','fallback_spot_ids','fallback_reason_codes']\n"
            "display(scores[show].head(10))"
        ),
        md("### 5.4 Caso real anotado: lead 6 de validación"),
        code(
            "case = scores.query(\"lead_id == 6 and split == 'validation'\").iloc[0]\n"
            "fallback_ids = json.loads(case['fallback_spot_ids']) if isinstance(case['fallback_spot_ids'], str) else list(case['fallback_spot_ids'])\n"
            "assert case['diagnostic_action'] == 'source_or_offer_fallback'\n"
            "assert fallback_ids == [756, 2687, 439, 1605, 1999]\n"
            "display(HTML(f'''<section class=\"spot2-case\"><h3>Lead 6 · decisión observable en T1</h3>"
            "<div class=\"spot2-grid\"><div class=\"spot2-card\"><strong>{case.lead_quality_score_0_100:.2f}</strong><small>Quality / 100</small></div>"
            "<div class=\"spot2-card\"><strong>{100*case.inventory_serviceability_lower:.2f}–{100*case.inventory_serviceability_upper:.2f}</strong><small>Inventory lower–upper</small></div>"
            "<div class=\"spot2-card\"><strong>{100*case.opportunity_probability_lower:.2f}–{100*case.opportunity_probability_upper:.2f}</strong><small>Opportunity lower–upper</small></div>"
            "<div class=\"spot2-card\"><strong>{case.diagnostic_action}</strong><small>acción diagnóstica</small></div></div>"
            "<div class=\"spot2-meter\"><span style=\"width:{case.lead_quality_score_0_100:.2f}%\"></span></div>"
            "<p><strong>Alternativas visibles:</strong> {', '.join(map(str, fallback_ids))}</p>"
            "<p>La incertidumbre no se oculta: Opportunity conserva dos bounds y la acción deriva de "
            "Quality × Serviceability, no de una probabilidad única presentada como certeza.</p></section>'''))"
        ),
        code(
            "# Lógica simplificada y fiel al scorer\n"
            "quality = case.p_lead_quality\n"
            "inv_low = case.inventory_serviceability_lower\n"
            "inv_high = case.inventory_serviceability_upper\n"
            "opp_low, opp_high = quality * inv_low, quality * inv_high\n"
            "action = case.diagnostic_action\n"
            "visible_fallbacks = fallback_ids[:5]\n"
            "assert abs(opp_low - case.opportunity_probability_lower) < 1e-12\n"
            "assert abs(opp_high - case.opportunity_probability_upper) < 1e-12\n"
            "display({'opportunity_bounds': (round(opp_low, 4), round(opp_high, 4)),\n"
            "         'action': action, 'visible_fallbacks': visible_fallbacks})"
        ),
        md(
            "## 6. Robustez, IA y producto\n\n"
            "### 6.1 Clusters y combinaciones\n\n"
            "Los perfiles se ajustan dentro de train y se condicionan a balance y estabilidad ARI. Las "
            "combinaciones exigen N≥50, shrinkage, intervalos Wilson y BH-FDR. Ningún cluster descubierto "
            "multiplica el score de producción."
        ),
        code(
            "display(pd.read_csv(ROOT/'outputs/tables/cluster_profile_metrics.csv').round(4))\n"
            "display(pd.read_csv(ROOT/'outputs/tables/cluster_combinations.csv').head(15))"
        ),
        md(
            "### 6.2 Stress test de leakage\n\n"
            "Variantes deliberadamente inválidas muestran por qué una métrica aparente alta no equivale "
            "a un sistema desplegable. La ruta limpia no puede importar esas señales."
        ),
        code("display(read_json(Path('outputs/metrics/leakage_stress_test.json')))"),
        md(
            "### 6.3 IA con alcance acotado: Catalog QA\n\n"
            "El LLM audita contradicciones entre texto de listing y atributos estructurados. Es QA "
            "cross-sectional, no feature histórica. La precisión natural aún requiere gold humano ciego; "
            "el benchmark inyectado y controlado sólo mide sensibilidad."
        ),
        code("llm = read_json(Path('outputs/metrics/llm_audit_evaluation.json')); display(llm)"),
        md("#### Prompt LLM versionado\n\n" + prompt),
        md(
            "### 6.4 Roadmap de medición\n\n"
            "Versionar precio, geografía, copy y lifecycle; registrar exposición a cada recomendación; "
            "capturar visita y conversión a horizontes fijos; crear un holdout temporal realmente intacto; "
            "y sólo entonces lanzar un RCT *sticky* por `lead_id`."
        ),
        code("display(read_json(Path('outputs/tables/online_ab_protocol.json')))"),
        md(
            "## 7. Conclusiones y reproducción\n\n"
            "### 7.1 Lo que queda decidido\n\n"
            "`stable_segment_logistic` calibrado ofrece una señal útil de priorización absoluta. El score "
            "conservador de Opportunity también supera random, pero no supera a Quality; Inventory mantiene "
            "gate incremental NO-GO. La secuencia correcta es **shadow → validación → RCT con guardas**, "
            "mientras IA se limita a Catalog QA."
        ),
        md(
            "### 7.2 Limitaciones\n\n"
            "El target es un proxy de primer contacto; el dataset global fue inspeccionado previamente; "
            "campos del listing no están versionados por completo; el timing de mercado es incierto; falta "
            "gold natural para LLM; las métricas offline son observacionales; y no se probó uplift causal."
        ),
        md(
            "### 7.3 Cómo reproducir\n\n"
            "Desde la raíz del repositorio: `python codexway/scripts/run_all.py --skip-live-llm`. El runner "
            "audita datos, construye ABTs, entrena, evalúa, ejecuta pruebas y vuelve a generar este `.ipynb` "
            "y su HTML. Una segunda ejecución verifica fingerprints de predicción."
        ),
        code(
            "required = {\n"
            "  'T1': model['selected_model'] == 'stable_segment_logistic',\n"
            "  'quality_gate': system['lead_quality_gate'] == 'GO',\n"
            "  'inventory_incremental': system['inventory_incremental_gate'] == 'NO_GO',\n"
            "  'opportunity_absolute': system['opportunity_absolute_lift_gate'] == 'GO',\n"
            "  'case_action': case.diagnostic_action == 'source_or_offer_fallback',\n"
            "  'five_visible_fallbacks': len(fallback_ids) == 5,\n"
            "}\n"
            "assert all(required.values())\n"
            "display(HTML('<div class=\"spot2-callout\"><strong>Contrato final verificado.</strong> ' + "
            "' · '.join(f'{k}: ✓' for k in required) + '</div>'))"
        ),
    ]

    notebook = nbformat.v4.new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
            "title": "Spot2 · Lead Opportunity Score · Assessment ejecutivo",
            "authors": [{"name": "Spot2 / Codexway"}],
            "spot2": {"audience": "Evaluador, Producto y C-Level", "contract": "T1_first_inquiry"},
        },
    )
    ipynb = notebook_dir / "spot2_assessment.ipynb"
    nbformat.write(notebook, ipynb)
    executed = NotebookClient(
        notebook,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": str(root)}},
    ).execute()
    nbformat.write(executed, ipynb)

    exporter = HTMLExporter()
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True
    html, _ = exporter.from_notebook_node(executed)
    html_path = notebook_dir / "spot2_assessment.html"
    html_path.write_text(_executive_html(html), encoding="utf-8")
    return ipynb, html_path
