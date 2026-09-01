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
            "**Assessment end-to-end reproducible y auditable.** Este notebook no es un resumen decorativo: recorre fuentes canónicas, auditoría, EDA, contrato temporal, "
            "feature engineering, modelado, Inventory, fallback, Opportunity, IA, robustez y producción. "
            "Los anexos conservan el detalle exhaustivo; este notebook muestra la evidencia ejecutada que conecta todo el trabajo."
        ),
        md(
            "## 1. tl;dr — decisión ejecutiva\n\n"
            "El objetivo no es automatizar una decisión comercial todavía. El resultado habilita una "
            "nueva cohorte *shadow* y, si se reproduce, un piloto aleatorizado con guardas."
        ),
        code(
            "from pathlib import Path\n"
            "import json, pandas as pd, numpy as np, yaml\n"
            "import matplotlib.pyplot as plt\n"
            "from IPython.display import display, Markdown, HTML, Image, SVG\n"
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
        md("""### 1.1 Mapa del trabajo ejecutado

Este artefacto funciona como **hilo conductor técnico de toda la solución**, no como sustituto de los anexos. El recorrido reproducible es:

1. **Lectura de fuentes:** seis tablas canónicas Parquet, con CSV como control de equivalencia.
2. **Auditoría:** llaves, grano, timestamps, missingness, duplicados y relaciones.
3. **EDA:** composición de demanda, target por segmento, temporalidad, mercado, disponibilidad, candidate depth y perfiles.
4. **Contrato temporal:** T0/T1/T2, madurez del target, censura y matriz explícita de leakage.
5. **ABT point-in-time:** una fila por lead en T1, allowlist/denylist y transformaciones determinísticas.
6. **Lead Quality:** baselines, challengers, rolling temporal CV, calibración, ranking por capacidad, estabilidad y error analysis.
7. **Inventory:** candidate generation, Availability backward-as-of, frescura, incertidumbre y bounds lower/upper.
8. **Fallback:** top-3 interno para serviceability, hasta cinco alternativas visibles, reason codes y NO_RESULT.
9. **Opportunity:** combinación conservadora de Quality × Inventory, comparación contra Quality-only y gates.
10. **Robustez e IA:** stress tests, clustering gobernado, resultados negativos y Catalog QA con LLM.
11. **Producción:** scoring contract, monitoreo, rollback, shadow validation y protocolo RCT.
12. **Trazabilidad:** cada claim principal apunta a outputs, tablas, evidencia o entregables finales.

**Regla de lectura:** una conclusión sólo aparece aquí si está respaldada por una celda ejecutada o por un artefacto canónico generado por el pipeline.
"""),
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
        md("""### 2.2.1 Inventario de datos antes de modelar

La lectura parte del grano real de cada fuente. No se mezclan tablas por comodidad: primero se define qué representa cada registro y qué reloj gobierna su uso.

| Fuente | Filas | Grano / rol |
|---|---:|---|
| leads | 5,000 | una necesidad inicial por lead; intake observable desde T0 |
| inquiries | 22,576 | eventos lead–spot; en T1 sólo se usa la primera inquiry y su payload contemporáneo |
| spots | 3,000 | catálogo de listings; varios campos son estado mutable actual, no historia versionada |
| spot_attributes | 3,000 | atributos físicos 1:1 del spot |
| availability_snapshot | 30,000 | historia temporal 1:N por spot; exige join backward-as-of |
| market_context | 500 | agregado geografía × sector × mes; útil para EDA, no para el modelo limpio sin publication time |

La limpieza relacional es alta: 0 duplicados de PK en las tablas canónicas y 0 huérfanos en las relaciones críticas auditadas. El riesgo principal no está en “arreglar datos rotos”, sino en **usar datos correctos en el momento equivocado**.
"""),
        md(
            "### 2.3 Lectura directa de las seis fuentes canónicas\n\n"
            "El notebook no parte únicamente de métricas precalculadas: vuelve a leer las seis tablas "
            "Parquet canónicas y deja visible su grano, tamaño y una muestra acotada. Los CSV se usan "
            "sólo como control de equivalencia; nunca se concatenan con Parquet."
        ),
        code(
            "DATA = ROOT.parent/'data'/'candidate'/'parquet'\n"
            "CSV_DATA = ROOT.parent/'data'/'candidate'/'csv'\n"
            "raw_names = ['leads','inquiries','spots','spot_attributes','availability_snapshot','market_context']\n"
            "raw = {name: pd.read_parquet(DATA/f'{name}.parquet') for name in raw_names}\n"
            "inventory = pd.DataFrame({name: {'rows': len(df), 'columns': df.shape[1]} for name, df in raw.items()}).T\n"
            "display(inventory)\n"
            "display(raw['leads'].head(3)); display(raw['inquiries'].head(3)); display(raw['spots'].head(3))"
        ),
        md(
            "### 2.4 Equivalencia CSV ↔ Parquet, llaves y missingness\n\n"
            "La duplicidad de formatos es una trampa potencial del assessment. Se valida que CSV y Parquet "
            "representen las mismas tablas y se inspeccionan llaves, rangos temporales y ausencia de datos "
            "antes de construir cualquier target o feature."
        ),
        code(
            "equiv = []\n"
            "for name in raw_names:\n"
            "    csv_df = pd.read_csv(CSV_DATA/f'{name}.csv')\n"
            "    pq_df = raw[name]\n"
            "    equiv.append({'table': name, 'rows_parquet': len(pq_df), 'rows_csv': len(csv_df), "
            "'same_rows': len(pq_df)==len(csv_df), 'same_columns': set(pq_df.columns)==set(csv_df.columns)})\n"
            "display(pd.DataFrame(equiv))\n"
            "missing = pd.read_csv(ROOT/'outputs/tables/data_quality_missingness.csv')\n"
            "display(missing.head(35))"
        ),
        md("""### 2.4.1 Calidad de datos que sí cambió la arquitectura

Tres hallazgos de calidad de datos alteraron directamente el diseño:

- **Join explosion:** unir inquiries con Availability sólo por spot_id expande 22,576 inquiries a 226,151 filas, aproximadamente **10.017×**. El grano deja de ser lead/inquiry.
- **Fuga temporal:** escoger el snapshot “más cercano” haría que **7,758 inquiries (34.36%)** recibieran información de un snapshot futuro.
- **Missingness semántico:** ausencia de presupuesto, urgencia o cobertura de Availability no siempre significa cero/no; se distinguen estados como desconocido, no aplicable y stale.

Por eso el pipeline separa auditoría, feature policy e Inventory. La ausencia de observación se conserva como información y no se rellena con el futuro.
"""),
        md(
            "### 2.5 Target, madurez y censura\n\n"
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
        md("""### 2.5.1 Target: qué predice realmente el sistema

El target final de Codexway es **scheduled_visit en la primera inquiry**, no cierre, revenue ni aceptación de fallback. Es un proxy temprano de progreso comercial elegido porque es observable con un contrato temporal defendible.

Con madurez de siete días:

- **4,898** T1 maduros;
- **1,001** positivos;
- prevalencia **20.44%**;
- **102** leads recientes quedan censurados y no se fuerzan a negativo.

La sensibilidad de madurez es estable: la prevalencia permanece alrededor de 20.4% al mover el buffer de 7 a 14 o 30 días. Esto reduce el riesgo de que el resultado dependa de un cutoff conveniente, pero no elimina la limitación conceptual: optimizamos progreso temprano, no valor económico final.
"""),
        md(
            "### 2.6 Política de leakage\n\n"
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
        md("""### 3.1.1 Qué mostró el EDA de demanda

La demanda es amplia y no existe una sola “persona Spot2”:

- **Sector:** Retail 30.56%, Office 29.00%, Industrial 24.98%, Land 15.46%.
- **Modalidad:** rent 50.06%, sale 29.80%, both 20.14%.
- **Tipo de usuario:** tenant_direct 39.12%, intermediario 36.08%, investor 19.94%, developer 4.86%.
- **Adquisición:** organic 29.26%, paid 24.92%, referral 20.34%, con el resto distribuido entre social, email y event.

En DEVELOPMENT, Retail también aparece con mayor presión relativa frente al catálogo histórico: **30.40% de demanda vs 24.51% de catálogo (+5.89 pp; índice ≈1.24×)**. Esto es una señal de tensión relativa, no una prueba de serviceability: todavía faltan disponibilidad, área, precio, geografía y vigencia.

La primera inquiry además **refina la necesidad**: por ejemplo, la mediana de área solicitada cambia frente al intake. Ese hallazgo es una de las razones por las que T1 es el momento principal de scoring.
"""),
        md(
            "### 3.2 Contexto de mercado: narrativa, no feature\n\n"
            "`market_context.month` no tiene timestamp fiable de publicación o vigencia. Sirve para "
            "entender el entorno, pero no es admisible como feature histórica."
        ),
        code(
            "display(Image(filename=str(ROOT/'outputs/figures/eda_market_context.png')))\n"
            "display(pd.read_csv(ROOT/'outputs/tables/market_context_eda.csv'))"
        ),
        md("### 3.3 Clustering por entidad: qué estructura latente existe en los datos\n\nEl clustering se usa aquí como **herramienta de EDA y descubrimiento de perfiles**, no como variable objetivo ni como regla de priorización. La línea experimental comparó K-Means, Bisecting K-Means, BIRCH y Gaussian Mixture entre K=3 y K=7; la selección fue **resultado-free** y combinó separación, balance y estabilidad. Los perfiles se aprendieron en una ventana temprana y se congelaron antes del tramo predictivo para evitar look-ahead.\n\n| Entidad / faceta | Solución descriptiva | Qué separa | Lectura |\n|---|---:|---|---|\n| Lead | K-Means, 6 perfiles | geografía preferida e historial de búsquedas | el lead no es homogéneo: ubicación y madurez de búsqueda forman grupos claros |\n| Lead Persona | Bisecting, 7 perfiles | canal de adquisición + historia | útil para describir origen/madurez; no implica calidad causal |\n| Search Need | K-Means, 3 perfiles | renta, venta y modalidad flexible/both | confirma que **quién es** y **qué necesita** son facetas distintas |\n| Spot | Bisecting, 7 perfiles | geografía y atributos físicos | motivó separar después **Physical Space** y **Location** |\n| Broker | Bisecting, 7 perfiles | mezcla de regiones/modalidades y comportamiento histórico | aporta segmentación, pero no justifica routing automático |\n| Inquiry Intent | K-Means, 7 perfiles | casi exclusivamente día de la semana | técnicamente estable, pero semánticamente pobre; se descarta como representación final |\n\nTodos los clusterers seleccionados en v2 pasaron el gate de balance (cluster mínimo ≥5% y máximo ≤70%). El resultado importante no es el ID numérico del cluster, sino **qué dimensiones del problema aparecen de forma consistente**.\n"),
        code("from pathlib import Path\nimport matplotlib.pyplot as plt\n\nEXPERIMENTS_ROOT = ROOT.parent / 'experimentos'\nif not EXPERIMENTS_ROOT.exists():\n    EXPERIMENTS_ROOT = ROOT / 'experimentos'\n\nV2 = EXPERIMENTS_ROOT / 'profile_clustering_v2' / 'results'\nclusterers_v2 = pd.read_csv(V2 / 'selected_clusterers.csv')\nprofiles_v2 = pd.read_csv(V2 / 'profile_interpretability.csv')\n\ncluster_summary = (\n    clusterers_v2.loc[:, [\n        'profile_family','method','k','silhouette',\n        'min_cluster_share','max_cluster_share','stability_ari','balance_ok'\n    ]]\n    .rename(columns={\n        'profile_family':'familia',\n        'method':'método',\n        'silhouette':'silhouette',\n        'min_cluster_share':'share_mín',\n        'max_cluster_share':'share_máx',\n        'stability_ari':'ARI_estabilidad',\n        'balance_ok':'balance_ok'\n    })\n)\ndisplay(cluster_summary.round(3))\n\n# Interpretabilidad completa: permite inspeccionar todos los perfiles, no sólo ejemplos escogidos.\ndisplay(\n    profiles_v2[['profile_family','profile_id','n_reference','share_reference','top_signals']]\n    .sort_values(['profile_family','share_reference'], ascending=[True,False])\n    .reset_index(drop=True)\n)\n\n# Distribución de perfiles por familia.\nfor family, g in profiles_v2.groupby('profile_family', sort=False):\n    fig, ax = plt.subplots(figsize=(7, 2.8))\n    gg = g.sort_values('share_reference')\n    ax.barh(gg['profile_id'], gg['share_reference'])\n    ax.set_title(f'{family}: peso de cada perfil en calibración')\n    ax.set_xlabel('share de referencia')\n    ax.set_ylabel('perfil')\n    plt.tight_layout()\n    plt.show()\n"),
        md("### 3.4 Refinamiento semántico: separar persona, necesidad, espacio, ubicación y servicio\n\nEl experimento posterior `matching_profiles_v4` tomó la estructura anterior y la hizo más útil para negocio. La mejora conceptual más importante fue **dejar de pedirle a un solo cluster que represente demasiadas cosas a la vez**:\n\n- **Lead / Behavioral Persona (BP1–BP3):** separa madurez e historia. BP3 es el lead más experimentado, con alta conversión previa e historial de inquiries.\n- **Search Need T0 (N1–N3):** renta, venta y flexible/both.\n- **Dynamic Need T1 (DN1–DN5):** actualiza la necesidad cuando ya existe una inquiry. DN4 es el perfil *stretch-space*: solicita mucho más espacio con presupuesto relativamente bajo.\n- **Spot:** se descompone en **Physical Space (PH1–PH4)** y **Location (LOC1–LOC7)**; esta separación es más interpretable que un Spot cluster único.\n- **Broker Service (BSV1–BSV3):** sí produce grupos balanceados y estables. BSV1 representa servicio más diversificado/mayor actividad; BSV2 acceptance-heavy; BSV3 mayor urgencia/orientación a calendarizar.\n- **Broker Supply:** se intentó dos veces y se **rechazó**. La solución compacta quedó 70.3% / 26.0% / 3.7%, violando el gate 5%–65%. Forzar otro K habría fabricado segmentación.\n- **Inquiry Intent:** se descarta porque aprendía weekday.\n- **Availability:** no se clusteriza; es un estado temporal directo y debe conservar su significado operativo.\n\nUna señal especialmente útil del EDA es la transición T0→T1: el perfil de renta N1 permanece en DN1 en **99.82%** de los casos, mientras venta y flexible se redistribuyen. La información nueva de T1 está, por tanto, concentrada en los casos donde la necesidad comercial realmente se refina.\n"),
        code("V4 = EXPERIMENTS_ROOT / 'matching_profiles_v4' / 'results'\nclusterers_v4 = pd.read_csv(V4 / 'selected_clusterers.csv')\nprofiles_v4 = pd.read_csv(V4 / 'profile_interpretability.csv')\ntransition_v4 = pd.read_csv(V4 / 'need_t0_t1_transition_matrix.csv')\n\ndisplay(\n    clusterers_v4[[\n        'profile_family','method','k','silhouette',\n        'stability_ari','min_cluster_share','max_cluster_share','balance_ok'\n    ]].round(3)\n)\n\n# Perfiles v4 relevantes para lectura de negocio.\ndisplay(\n    profiles_v4[\n        profiles_v4['profile_family'].isin([\n            'behavioral_persona','dynamic_need_t1','broker_service_balanced'\n        ])\n    ][['profile_family','profile_id','n_reference','share_reference','top_signals']]\n    .reset_index(drop=True)\n)\n\ndisplay(Markdown('**Transición Search Need T0 → Dynamic Need T1**'))\ndisplay(transition_v4)\n"),
        md("### 3.5 Combinaciones poderosas: dónde aparecieron pockets de compatibilidad\n\nAl cruzar los perfiles surgieron **pockets locales con tasas de visita muy superiores al baseline histórico (~20.77%)**. Éstos son los hallazgos más fuertes de `matching_profiles_v4`:\n\n| Rank | Combinación | N | Visita raw | Tasa suavizada | Lift histórico | Wilson lower / baseline |\n|---:|---|---:|---:|---:|---:|---:|\n| 1 | **DN4 × LOC1 × BSV1** | 60 | **36.67%** | **31.37%** | **1.510×** | **1.234×** |\n| 2 | **N3→DN4 × BSV1** | 83 | 31.33% | 28.52% | **1.373×** | **1.077×** |\n| 3 | N2→DN2 × BSV3 | 57 | 31.58% | 27.85% | 1.341× | 1.011× |\n| 4 | **DN4 × LOC1** | 90 | 30.00% | 27.69% | **1.333×** | **1.036×** |\n| 5 | DN2 × PH1 × BSV3 | 59 | 30.51% | 27.23% | 1.311× | 0.975× |\n| 6 | PH3 × BSV2 | 159 | 28.30% | 27.11% | **1.305×** | **1.053×** |\n| 7 | **DN4 × BSV1** | 153 | 28.10% | 26.90% | **1.295×** | **1.039×** |\n| 8 | DN2 × BSV3 | 90 | 28.89% | 26.86% | 1.293× | 0.989× |\n\nLa celda más llamativa combina:\n\n- **DN4:** necesidad *stretch-space* — busca mucho más espacio con presupuesto relativamente bajo;\n- **LOC1:** ubicación centro metropolitano CDMX–Naucalpan;\n- **BSV1:** broker con servicio diversificado y mayor actividad.\n\nTambién en la versión v2 aparecieron interacciones Lead × Spot × Broker con lift local >1.3×, por ejemplo **L1 × S1 × B5 (N=93, lift 1.314×)** y **L1 × S5 × B2 (N=35, lift 1.304×)**. Esto reforzó la hipótesis de que la compatibilidad entre entidades contiene señal que los marginales no capturan completamente.\n\n> **Cautela metodológica:** “poderosa” significa *prometedora para investigación*, no *lista para producción*. Estas celdas fueron descubiertas inspeccionando el mismo future test y hubo múltiples comparaciones. Por eso no se multiplica el Opportunity Score por 1.51 ni se convierte DN4 × LOC1 × BSV1 en hard routing. En la confirmación gobernada final de Codexway, ninguna celda elegible justificó promoción tras corrección por multiplicidad. El valor del hallazgo es generar una hipótesis concreta para una nueva cohorte temporal o un A/B sticky por `lead_id`.\n"),
        code("top_v4 = pd.read_csv(V4 / 'top_service_compatibility_cells.csv')\n\ndef combo_label(r):\n    parts = []\n    if pd.notna(r.get('need_transition')) and str(r.get('need_transition')).strip():\n        parts.append(str(r['need_transition']))\n    if pd.notna(r.get('dynamic_need_profile')) and str(r.get('dynamic_need_profile')).strip():\n        parts.append(str(r['dynamic_need_profile']))\n    if pd.notna(r.get('physical_profile')) and str(r.get('physical_profile')).strip():\n        parts.append(str(r['physical_profile']))\n    if pd.notna(r.get('location_profile')) and str(r.get('location_profile')).strip():\n        parts.append(str(r['location_profile']))\n    if pd.notna(r.get('broker_service_balanced_profile')) and str(r.get('broker_service_balanced_profile')).strip():\n        parts.append(str(r['broker_service_balanced_profile']))\n    return ' × '.join(parts)\n\ntop_show = top_v4.head(12).copy()\ntop_show['combinación'] = top_show.apply(combo_label, axis=1)\ndisplay(\n    top_show[[\n        'combinación','interaction','n','visit_rate','smoothed_rate',\n        'lift_vs_global','wilson_low_lift'\n    ]].rename(columns={\n        'interaction':'tipo_interacción',\n        'visit_rate':'tasa_visita_raw',\n        'smoothed_rate':'tasa_suavizada',\n        'lift_vs_global':'lift_vs_global',\n        'wilson_low_lift':'wilson_lower_vs_baseline'\n    }).round(3)\n)\n\nfig, ax = plt.subplots(figsize=(8, 4.5))\nplot_df = top_show.head(8).sort_values('lift_vs_global')\nax.barh(plot_df['combinación'], plot_df['lift_vs_global'])\nax.axvline(1.0, linestyle='--', linewidth=1)\nax.set_xlabel('lift histórico vs baseline')\nax.set_ylabel('combinación')\nax.set_title('Pockets exploratorios de compatibilidad — matching_profiles_v4')\nplt.tight_layout()\nplt.show()\n\n# Referencia v2: primeras combinaciones Lead × Spot × Broker por sinergia residual.\ncomb_v2 = pd.read_csv(V2 / 'top_3entity_combinations.csv')\ndisplay(\n    comb_v2[[\n        'lead_profile','spot_profile','broker_profile','n',\n        'scheduled_visit_rate','smoothed_visit_rate',\n        'lift_vs_global','residual_synergy','wilson_low','wilson_high'\n    ]].head(10).round(3)\n)\n"),
        md(
            "### 3.6 EDA integrado: hallazgos que cambiaron la solución\n\n"
            "El EDA final consolidó Codexway, experimentos y AssessmentSol1 sin alterar la solución ganadora. "
            "Aquí se recuperan los hallazgos que sí cambiaron decisiones: presión Retail, refinamiento T0→T1, "
            "missingness semántico, deriva de candidate depth, cobertura/vigencia y el riesgo de joins futuros."
        ),
        code(
            "eda_metrics = pd.read_csv(ROOT.parent/'entregable/01_eda/tablas/01_metricas_eda_clave.csv')\n"
            "focus_topics = ['Contrato T1','Demanda vs oferta','Refinamiento','Datos faltantes','Exposición','Inventario','Disponibilidad','Vigencia','Compatibilidad']\n"
            "display(eda_metrics[eda_metrics['tema'].isin(focus_topics)].reset_index(drop=True))"
        ),
        md("### 3.7 Evidencia visual del EDA final"),
        code(
            "eda_fig_dir = ROOT.parent/'entregable/01_eda/figuras'\n"
            "eda_gallery = [\n"
            " ('01_demanda_vs_oferta_sector.svg','Demanda vs oferta por sector'),\n"
            " ('02_target_vs_coverage_temporal.svg','Target y cobertura cambian con el tiempo'),\n"
            " ('03_candidate_depth_temporal.svg','La profundidad de candidatos deriva'),\n"
            " ('04_refinamiento_area.svg','La primera consulta refina la necesidad'),\n"
            " ('09_join_availability_leakage.svg','Nearest availability puede mirar al futuro'),\n"
            " ('14_unknown_no_es_unavailable.svg','UNKNOWN no es UNAVAILABLE'),\n"
            " ('16_no_estacionariedad_clocks.svg','No estacionariedad de múltiples clocks'),\n"
            " ('22_quality_inventory_quadrant.svg','Quality e Inventory son dos ejes distintos'),\n"
            "]\n"
            "for filename, caption in eda_gallery:\n"
            "    path = eda_fig_dir/filename\n"
            "    assert path.exists(), path\n"
            "    display(Markdown(f'**{caption}**'))\n"
            "    display(SVG(filename=str(path)))"
        ),
        md(
            "### 3.8 De EDA a decisiones de ingeniería\n\n"
            "- T1 gana a T0 porque la consulta aporta información nueva.\n"
            "- UNKNOWN no es UNAVAILABLE: incertidumbre y vigencia sobreviven al scoring.\n"
            "- market_context permanece EDA_ONLY por ausencia de publication time.\n"
            "- Conteos de consultas futuras y estado mutable del listing quedan fuera del modelo limpio.\n"
            "- Los pockets de clusters quedan como hipótesis: 0/19 celdas pasan BH-FDR 10% en confirmación."
        ),
        md("""### 3.9 Registro de hipótesis del EDA

El EDA no se cerró con una colección de gráficas; cada hallazgo se convirtió en una decisión o en una hipótesis gobernada.

| Hipótesis | Evidencia | Estado / consecuencia |
|---|---|---|
| T1 aporta información adicional frente a T0 | refinamiento del request y sensibilidades T0/T1/T2 | **Soportada** → T1 canónico |
| Availability puede tratarse como estado actual | coverage/freshness drift y 34.36% de riesgo con nearest snapshot | **Rechazada** → backward-as-of |
| UNKNOWN equivale a UNAVAILABLE | missing/stale Availability | **Rechazada** → bounds + confidence |
| Market Context puede entrar directo al modelo | no existe publication time fiable | **Rechazada** → EDA_ONLY |
| Candidate depth es una señal estable de lead | cambia materialmente con el tiempo | **Rechazada** para Quality → pertenece a Inventory |
| Pockets de clusters pueden convertirse en reglas | lifts locales altos, pero múltiples comparaciones | **Inconclusa** → hipótesis para nueva cohorte |
| La compatibilidad entre entidades contiene estructura | perfiles y combinaciones interpretables | **Soportada descriptivamente**, no como multiplicador |
| Un modelo más complejo debe ganar por defecto | challengers complejos no dominaron estabilidad + top-decile | **Rechazada** → champion simple y estable |

Este registro explica por qué varias ideas interesantes terminan **fuera** del score final: investigar algo y no promoverlo es parte del trabajo, no trabajo perdido.
"""),
        md(
            "## 4. ABT y feature engineering point-in-time\n\n"
            "El modelado empieza sólo después de congelar el reloj. La ABT T1 mantiene un registro por lead "
            "en su primera inquiry y separa señales de intake, payload contemporáneo y transformaciones "
            "determinísticas T0→T1."
        ),
        code(
            "abt_t1 = pd.read_parquet(ROOT/'outputs/abt/abt_t1_first_inquiry.parquet')\n"
            "policy = yaml.safe_load((ROOT/'config/feature_policy.yaml').read_text(encoding='utf-8'))['clean_t1']\n"
            "summary = {\n"
            " 'rows': len(abt_t1), 'columns': abt_t1.shape[1],\n"
            " 'target_observed': int(abt_t1['target'].notna().sum()),\n"
            " 'target_positive': int((abt_t1['target']==1).sum()),\n"
            " 'allow_features': len(policy['allow']), 'forbidden_features': len(policy['forbidden'])}\n"
            "display(pd.Series(summary, name='ABT T1'))\n"
            "display(pd.DataFrame({'allow': pd.Series(policy['allow']), 'forbidden': pd.Series(policy['forbidden'])}))"
        ),
        md("""### 4.0.1 Grano final de la ABT y separación de responsabilidades

La ABT T1 tiene **una fila por lead en su primera inquiry**. La función de construcción ordena por lead, timestamp e inquiry_id y valida unicidad de lead_id antes de modelar.

El registro conserva:

- lead_id e inquiry_id de la primera consulta;
- prediction_timestamp;
- variables de intake ya observables;
- payload de la inquiry actual;
- transformaciones determinísticas;
- target únicamente para evaluación.

Una decisión estructural importante es que **Spot state y Availability no forman parte de Lead Quality**. Se reservan para Inventory y Opportunity. Esto evita que el mismo matching se use primero para inflar Quality y después vuelva a multiplicarse dentro de Inventory.
"""),
        md(
            "### 4.1 Features derivadas y consistencia T0→T1\n\n"
            "Las transformaciones priorizan semántica y reproducibilidad: ratios de área/presupuesto, "
            "días desde creación, estados de missingness y una interacción estable de baja cardinalidad. "
            "No se promueven features por correlación aislada."
        ),
        code(
            "derived = ['days_from_lead_creation','area_request_to_target_ratio',"
            "'rent_request_to_lead_budget_ratio','sale_request_to_lead_budget_ratio',"
            "'industrial_small_or_paid_interaction']\n"
            "available = [c for c in derived if c in abt_t1.columns]\n"
            "display(abt_t1[['lead_id','inquiry_id','target'] + available].head(12))"
        ),
        md("""### 4.1.1 Contrato de features: qué entra y qué queda fuera

La feature policy no se deduce automáticamente de todas las columnas disponibles. Se gobierna con allowlist/forbidden list.

**Puede entrar**
- contexto de intake ya conocido;
- payload contemporáneo de la primera inquiry;
- días desde creación del lead;
- ratios de área y presupuesto;
- estados de missingness con significado;
- interacciones de baja cardinalidad si sobreviven la validación temporal.

**No puede entrar**
- respuesta del broker o tiempos posteriores;
- inquiries futuras o acumulados construidos con ellas;
- scores internos del proceso;
- Availability nearest/future;
- estado mutable actual del listing tratado como historia;
- Market Context sin publication time fiable;
- variables de T2 dentro del scorer T1.

La regla de ingeniería es más estricta que “no usar el target”: **cada feature debe demostrar observabilidad al score_time**.
"""),
        md("### 4.2 T0 y T2 como sensibilidades, no como mezcla de scores"),
        code("display(read_json(Path('outputs/metrics/t0_t2_sensitivity_metrics.json')))"),
        md(
            "## 5. Lead Quality — selección, ranking y calibración\n\n"
            "### 5.1 Baselines antes de complejidad\n\n"
            "Tasa positiva, una regla interpretable y Regresión Logística preceden a CatBoost. La promoción "
            "usa folds temporales expansivos; el holdout no participa en la selección."
        ),
        code(
            "display(pd.DataFrame(model['metrics']).T.round(4))\n"
            "display(pd.read_csv(ROOT/'outputs/metrics/rolling_model_comparison.csv').round(4))"
        ),
        md("""### 5.1.1 Benchmark canónico y amplitud experimental

La solución final es sencilla, pero no nació de una búsqueda pequeña. Dentro de Codexway se compararon baselines, reglas, regresiones y CatBoost bajo el mismo contrato T1:

| Modelo | ROC-AUC | PR-AUC | Brier | Lift@10 |
|---|---:|---:|---:|---:|
| Positive rate | 0.5000 | 0.2122 | 0.1672 | 1.000× |
| Business rule | 0.5157 | 0.2165 | 0.2501 | 0.986× |
| Logistic lead-only | 0.4823 | 0.2098 | 0.1733 | 0.932× |
| Logistic clean amplio | 0.4881 | 0.2156 | 0.1744 | 0.850× |
| Logistic sin asked_visit | 0.4852 | 0.2152 | 0.1743 | 0.987× |
| CatBoost | 0.4922 | 0.2086 | 0.2423 | 0.826× |
| **Stable segment logistic** | **0.5478** | **0.2391** | **0.1655 raw** | **1.689×** |
| **Selected calibrated** | **0.5478** | **0.2391** | **0.1658** | **1.689×** |

Además se investigaron, en ramas experimentales con contratos distintos, especialistas CatBoost/RF, multi-head, trajectory T2, Dynamic Need, clusters, matching profiles y semantic rules. Esos resultados se usan como **evidencia de investigación**, no como leaderboard mezclado.

La conclusión del benchmark final es incómoda pero valiosa: **más variables y más flexibilidad no produjeron un ranking mejor bajo el contrato limpio T1**.
"""),
        md("""### 5.1.2 Rolling temporal CV y gate de promoción

La selección no depende de un único split. El stable segment logistic se evalúa en cuatro folds temporales expansivos:

| Fold | Lift@10 |
|---|---:|
| 1 | 0.784× |
| 2 | 1.443× |
| 3 | 1.753× |
| 4 | 0.875× |

Resumen:
- media: **1.214×**;
- mediana: **1.159×**;
- folds > 1: **2/4**.

El gate exige media y mediana >1, al menos 2/4 folds >1, Lift@10 de validation >1 y Brier de validation no materialmente peor que el baseline constante.

En validation:
- Lift@10 = **1.442×**;
- Brier = **0.15611**;
- Brier baseline constante = **0.15691**.

**Pasa el gate**, pero no todos los folds ganan. Por eso la evidencia correcta es “señal temporal suficiente para promoción a validación”, no “modelo estable en cualquier periodo”.

El holdout 2026 es además **procedural, no pristine**: no participó en el gate de esta ejecución, pero el dataset había sido inspeccionado durante la investigación. La confirmación real requiere una nueva cohorte forward.
"""),
        md("""### 5.1.3 Champion final: simple, deliberadamente de baja resolución

El modelo final es una **Regresión Logística regularizada** cuyo predictor promovido es:

industrial_small_or_paid_interaction

Definición: search_sector = Industrial AND (company_size = small OR source = paid).

Coeficiente estandarizado: **+0.1204**.

Se eligió porque combina:
- baja cardinalidad;
- disponibilidad desde T0/T1;
- ausencia de mutable history;
- menor superficie de leakage;
- concentración operativa;
- facilidad de explicar y monitorear.

Después de Platt, el holdout contiene esencialmente dos niveles de score:
- **0.187899**;
- **0.253098**.

Eso es una fortaleza de gobernanza y una limitación predictiva. El notebook no debe fingir una granularidad que el modelo no posee.
"""),
        md(
            "### 5.2 Ranking bajo capacidad limitada\n\n"
            "Recall@X responde la pregunta operativa: ¿qué proporción de resultados positivos aparece "
            "al trabajar sólo el X% superior de leads?"
        ),
        code(
            "display(Image(filename=str(ROOT/'outputs/figures/gains_curve.png')))\n"
            "gains = pd.read_csv(ROOT/'outputs/tables/gains.csv')\n"
            "display(gains.query('population_fraction in [0.05, 0.1, 0.2]').round(4))"
        ),
        md("""### 5.2.1 Política capacity-first y empates

El sistema no usa 0.5 como cutoff por convención. La operación se define por capacidad:

| Capacidad trabajada | Precision | Recall | Lift |
|---:|---:|---:|---:|
| 5% | 35.83% | 8.49% | **1.689×** |
| 10% | 35.83% | **16.98%** | **1.689×** |
| 20% | 28.37% | 26.80% | **1.337×** |

La política final congela **top 10%** como default y escenarios 5/10/20%.

El threshold de validation asociado al P90 es aproximadamente **0.253098**. No es una frontera universal de “lead bueno”; es una consecuencia de la capacidad disponible en esta muestra.

Como existen muchos empates, Lift@K se calcula de forma **tie-aware**: si el corte atraviesa un bloque de scores iguales, se usa captura esperada fraccional en vez de depender del orden físico de las filas.
"""),
        md(
            "### 5.3 Calibración e incertidumbre\n\n"
            "La calibración Platt se ajusta en validación y se conserva sólo si mejora. Los intervalos "
            "bootstrap separan una señal plausible de una falsa precisión puntual."
        ),
        code(
            "display(Image(filename=str(ROOT/'outputs/figures/calibration_plot.png')))\n"
            "display(pd.read_csv(ROOT/'outputs/metrics/t1_metric_intervals.csv').round(4))"
        ),
        md("""### 5.3.1 Calibración: se retiene, pero no se sobrevende

Platt scaling se ajusta únicamente sobre validation.

Antes:
- Brier = 0.1561106;
- Log Loss = 0.4909444.

Después:
- Brier = **0.1560762**;
- Log Loss = **0.4908026**.

La mejora es marginal, pero cumple la regla de retención. En el holdout:
- Brier seleccionado = **0.16577**;
- baseline de prevalencia = **0.16725**;
- Brier skill score ≈ **0.0088**.

La tabla de calibración muestra que la banda alta está **subcalibrada**: predicción media 0.2531 frente a tasa observada 0.3583.

Por eso el score sirve para **ranking y priorización**, pero sus probabilidades no deben presentarse como probabilidades económicas definitivas.
"""),
        md("### 5.4 Interpretabilidad y estabilidad temporal"),
        code(
            "display(pd.read_csv(ROOT/'outputs/tables/feature_importance.csv').head(20))\n"
            "display(pd.read_csv(ROOT/'outputs/tables/monthly_model_stability.csv').round(4))\n"
            "display(pd.read_csv(ROOT/'outputs/tables/feature_drift.csv').sort_values('value', ascending=False).head(20))"
        ),
        md("""### 5.4.1 Estabilidad temporal: señal útil, heterogeneidad real

Lift@10 mensual en el holdout 2026:

| Mes | Lift@10 |
|---|---:|
| Enero | 1.207× |
| Febrero | 1.281× |
| Marzo | 2.554× |
| Abril | 1.432× |
| Mayo | 1.650× |
| Junio | 1.823× |

Todos los meses quedan por encima de 1, pero marzo es claramente atípico. Junto con los folds rolling débiles, esto obliga a monitorear prevalence, Lift/Recall@K, Brier, distribución del segmento Industrial-small/paid y drift de la feature final.

La estabilidad no se resume como “pasó/no pasó”; se conserva la heterogeneidad temporal porque es parte del riesgo de despliegue.
"""),
        md(
            "### 5.5 Error analysis y desempeño por segmento\n\n"
            "El notebook no termina en una métrica agregada. Se inspeccionan errores, segmentos y estabilidad "
            "mensual para detectar dónde el ranking falla, dónde hay soporte pequeño y dónde una mejora aparente "
            "podría ser artefacto temporal."
        ),
        code(
            "display(pd.read_csv(ROOT/'outputs/tables/error_analysis.csv').head(30))\n"
            "display(pd.read_csv(ROOT/'outputs/tables/segment_metrics.csv').round(4).head(40))"
        ),
        md("""### 5.5.1 Error analysis: dónde falla realmente

Con el cutoff operacional 0.253098, el holdout contiene:
- **120 false positives** de prioridad;
- **296 false negatives**.

Todos los false positives están en la banda alta y todos los false negatives en la banda baja. El problema no es una frontera mal afinada entre probabilidades cercanas: el problema es que la hipótesis de segmentación es **demasiado gruesa**.

Por sector:

| Sector | N | AUC | AP | Lift@10 |
|---|---:|---:|---:|---:|
| Industrial | 434 | **0.616** | **0.318** | **1.401×** |
| Land | 281 | 0.500 | 0.192 | 1.000× |
| Office | 478 | 0.500 | 0.205 | 1.000× |
| Retail | 518 | 0.500 | 0.193 | 1.000× |

Esto es consistente con la arquitectura: fuera de Industrial, el modelo es prácticamente un prior.

La siguiente mejora no es mover el threshold. Requiere **nuevas señales PIT** que separen mejor positivos y negativos dentro y fuera del segmento.
"""),
        md("""### 5.6 Qué se intentó y por qué no reemplaza al champion

| Hipótesis / familia | Resultado útil | Decisión |
|---|---|---|
| CatBoost generalista | en Codexway: PR-AUC 0.2086, Lift@10 0.826×, Brier 0.2423 | **No promover** |
| Specialist CatBoost / RF | competitivos en rolling histórico bajo otro stack | evidencia auxiliar; contrato no equivalente |
| Shared backbone / Multi-Head | mejoró un pooled neural inicial | después superado por tabulares; no canónico |
| Trajectory / progression | señal puntual en T2 | mantener como extensión T2, no contaminar T1 |
| Dynamic Need | segmentación interpretable, mejora puntual con IC cruzando cero | auxiliar / routing hypothesis |
| Clusters / matching pockets | pockets locales de alto lift | no convertir en reglas sin confirmación independiente |
| Semantic rules / LLM features | sin lift incremental robusto | fuera del predictor |

El valor de esta investigación no es “tener muchos modelos”, sino **reducir el espacio de decisiones** hasta una solución defendible. El champion final es pequeño porque varias alternativas más sofisticadas no justificaron su promoción bajo el mismo estándar temporal.
"""),
        md(
            "## 6. Inventory, Opportunity y fallback\n\n"
            "### 6.1 Disponibilidad point-in-time\n\n"
            "Availability se une con un **backward as-of** estricto. Historia ausente o vieja significa "
            "**UNKNOWN, no UNAVAILABLE**, y se expresa como bounds lower/upper; jamás se rellena desde el futuro."
        ),
        code(
            "display(Image(filename=str(ROOT/'outputs/figures/availability_coverage.png')))\n"
            "display(pd.read_csv(ROOT/'outputs/tables/inventory_freshness_sensitivity.csv').round(4))\n"
            "display(read_json(Path('outputs/metrics/inventory_audit.json')))"
        ),
        md(
            "### 6.2 Trade-off central\n\n"
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
            "### 6.3 Política de dos ejes y alternativas\n\n"
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
        md("### 6.4 Caso real anotado: lead 6 de validación"),
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
            "### 6.5 Profundidad de candidatos y cobertura de fallback\n\n"
            "La capacidad de atención no es estática: el número de candidatos por lead cambia materialmente "
            "con el tiempo. Por eso candidate depth no entra a Lead Quality y el fallback permite NO_RESULT "
            "antes que violar hard constraints."
        ),
        code(
            "inv_candidates = pd.read_parquet(ROOT/'outputs/abt/abt_inventory_candidates.parquet')\n"
            "depth = inv_candidates.groupby('lead_id').size().rename('candidate_depth')\n"
            "display(depth.describe(percentiles=[.1,.25,.5,.75,.9,.95]).to_frame())\n"
            "fallback_counts = scores['fallback_spot_ids'].apply(lambda x: len(json.loads(x)) if isinstance(x,str) and x.startswith('[') else 0)\n"
            "display(fallback_counts.value_counts().sort_index().rename_axis('visible_fallbacks').to_frame('leads'))"
        ),
        md(
            "## 7. Robustez, IA y producto\n\n"
            "### 7.1 Clusters y combinaciones\n\n"
            "Los perfiles se ajustan dentro de train y se condicionan a balance y estabilidad ARI. Las "
            "combinaciones exigen N≥50, shrinkage, intervalos Wilson y BH-FDR. Ningún cluster descubierto "
            "multiplica el score de producción."
        ),
        code(
            "display(pd.read_csv(ROOT/'outputs/tables/cluster_profile_metrics.csv').round(4))\n"
            "display(pd.read_csv(ROOT/'outputs/tables/cluster_combinations.csv').head(15))"
        ),
        md(
            "### 7.2 Stress test de leakage\n\n"
            "Variantes deliberadamente inválidas muestran por qué una métrica aparente alta no equivale "
            "a un sistema desplegable. La ruta limpia no puede importar esas señales."
        ),
        code("display(read_json(Path('outputs/metrics/leakage_stress_test.json')))"),
        md(
            "### 7.3 IA con alcance acotado: Catalog QA\n\n"
            "El LLM audita contradicciones entre texto de listing y atributos estructurados. Es QA "
            "cross-sectional, no feature histórica. La precisión natural aún requiere gold humano ciego; "
            "el benchmark inyectado y controlado sólo mide sensibilidad."
        ),
        code("llm = read_json(Path('outputs/metrics/llm_audit_evaluation.json')); display(llm)"),
        md("#### Prompt LLM versionado\n\n" + prompt),
        md(
            "### 7.4 Roadmap de medición\n\n"
            "Versionar precio, geografía, copy y lifecycle; registrar exposición a cada recomendación; "
            "capturar visita y conversión a horizontes fijos; crear un holdout temporal realmente intacto; "
            "y sólo entonces lanzar un RCT *sticky* por `lead_id`."
        ),
        code("display(read_json(Path('outputs/tables/online_ab_protocol.json')))"),
        md(
            "## 8. Producción, gobierno y trazabilidad\n\n"
            "El trabajo no se cierra en un modelo offline. La entrega deja contrato de scoring, readiness, "
            "protocolo A/B, evidencia de decisiones y una ruta reproducible para volver a generar ABTs, "
            "predicciones, métricas, notebook y HTML."
        ),
        code(
            "display(read_json(Path('outputs/metrics/deployment_readiness.json')))\n"
            "display(read_json(Path('outputs/tables/online_ab_protocol.json')))"
        ),
        md(
            "### 8.1 Evidencia y artefactos canónicos\n\n"
            "- evidence/LEAKAGE_MATRIX.md: qué puede y qué no puede entrar.\n"
            "- evidence/DECISIONS.md: decisiones metodológicas.\n"
            "- evidence/TRACEABILITY.md: trazabilidad de claims.\n"
            "- outputs/metrics/: métricas versionadas.\n"
            "- outputs/predictions/lead_opportunity_scores.parquet: salida operacional.\n"
            "- entregable/: narrativa final en español."
        ),
        code(
            "artifacts = [\n"
            " ROOT/'outputs/predictions/lead_opportunity_scores.parquet',\n"
            " ROOT/'outputs/metrics/t1_model_metrics.json',\n"
            " ROOT/'outputs/metrics/system_evaluation.json',\n"
            " ROOT/'outputs/tables/error_analysis.csv',\n"
            " ROOT/'evidence/LEAKAGE_MATRIX.md',\n"
            " ROOT.parent/'entregable/01_eda/EDA_FINAL.md',\n"
            " ROOT.parent/'entregable/03_lead_quality/MODELO_CALIDAD_LEAD.md',\n"
            " ROOT.parent/'entregable/05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md',\n"
            "]\n"
            "artifact_check = pd.DataFrame({'artifact':[str(p.relative_to(ROOT.parent)) for p in artifacts], 'exists':[p.exists() for p in artifacts]})\n"
            "assert artifact_check['exists'].all()\n"
            "display(artifact_check)"
        ),
        md(
            "## 9. Conclusiones y reproducción\n\n"
            "### 9.1 Lo que queda decidido\n\n"
            "`stable_segment_logistic` calibrado ofrece una señal útil de priorización absoluta. El score "
            "conservador de Opportunity también supera random, pero no supera a Quality; Inventory mantiene "
            "gate incremental NO-GO. La secuencia correcta es **shadow → validación → RCT con guardas**, "
            "mientras IA se limita a Catalog QA."
        ),
        md(
            "### 9.2 Limitaciones\n\n"
            "El target es un proxy de primer contacto; el dataset global fue inspeccionado previamente; "
            "campos del listing no están versionados por completo; el timing de mercado es incierto; falta "
            "gold natural para LLM; las métricas offline son observacionales; y no se probó uplift causal."
        ),
        md(
            "### 9.3 Cómo reproducir\n\n"
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
