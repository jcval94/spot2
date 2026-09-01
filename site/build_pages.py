from pathlib import Path
from shutil import copy2, copytree, rmtree
import html
import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
SITE = ROOT / "site"

if OUT.exists():
    rmtree(OUT)
OUT.mkdir(parents=True)

copy2(SITE / "index.html", OUT / "index.html")
copy2(SITE / "styles.css", OUT / "styles.css")
(OUT / ".nojekyll").write_text("", encoding="utf-8")

downloads = OUT / "downloads"
downloads.mkdir()

copies = [
    (ROOT / "entregable/02_one_pager/ONE_PAGER_SPOT2_AESTHETIC.html", OUT / "one-pager.html"),
    (ROOT / "entregable/06_deck_ejecutivo/DECK_EJECUTIVO_SPOT2.html", OUT / "deck.html"),
    (ROOT / "entregable/02_one_pager/ONE_PAGER_SPOT2_AESTHETIC.html", downloads / "ONE_PAGER_SPOT2.html"),
    (ROOT / "entregable/02_one_pager/ONE_PAGER_SPOT2.pdf", downloads / "ONE_PAGER_SPOT2.pdf"),
    (ROOT / "entregable/06_deck_ejecutivo/DECK_EJECUTIVO_SPOT2.html", downloads / "DECK_EJECUTIVO_SPOT2.html"),
    (ROOT / "entregable/06_deck_ejecutivo/DECK_EJECUTIVO_SPOT2.pdf", downloads / "DECK_EJECUTIVO_SPOT2.pdf"),
    (ROOT / "codexway/notebooks/spot2_assessment.html", downloads / "spot2_assessment.html"),
    (ROOT / "codexway/notebooks/spot2_assessment.ipynb", downloads / "spot2_assessment.ipynb"),
    (ROOT / "entregable/SPOT2_ASSESSMENT_FINAL.zip", downloads / "SPOT2_ASSESSMENT_FINAL.zip"),
]

missing = [str(src.relative_to(ROOT)) for src, _ in copies if not src.exists()]
if missing:
    raise SystemExit("Missing required site assets: " + ", ".join(missing))

for src, dst in copies:
    copy2(src, dst)

# Reviewer-friendly notebook: preserve outputs, hide code inputs in the web view.
nb_html = (ROOT / "codexway/notebooks/spot2_assessment.html").read_text(encoding="utf-8")
hide_code = """<style>
.jp-InputArea, .input, div.input_area, .code_cell .input, .jp-Cell-inputWrapper {display:none!important}
body{max-width:1180px;margin:auto!important;padding:24px!important}
</style>"""
if "</head>" in nb_html:
    nb_html = nb_html.replace("</head>", hide_code + "</head>", 1)
else:
    nb_html = hide_code + nb_html
(OUT / "notebook.html").write_text(nb_html, encoding="utf-8")

DOCS = [
    ("eda", "Análisis exploratorio de datos", "entregable/01_eda/EDA_FINAL.md"),
    ("lead-quality", "Modelo de calidad del lead", "entregable/03_lead_quality/MODELO_CALIDAD_LEAD.md"),
    ("inventory", "Inventory y fallback", "entregable/04_inventory_fallback/README.md"),
    ("opportunity", "Lead Opportunity Score", "entregable/05_opportunity_produccion/01_LEAD_OPPORTUNITY_SCORE.md"),
    ("architecture", "Arquitectura de producción", "entregable/05_opportunity_produccion/02_ARQUITECTURA_PRODUCCION.md"),
    ("monitoring", "Monitoreo, gobierno y runbook", "entregable/05_opportunity_produccion/03_MONITOREO_GOBIERNO_RUNBOOK.md"),
    ("ai", "Uso de IA", "entregable/07_ia_product_vision/01_USO_OBLIGATORIO_IA.md"),
    ("product-vision", "Product Vision", "entregable/07_ia_product_vision/02_PRODUCT_VISION.md"),
    ("causal", "Experimentación causal", "entregable/07_ia_product_vision/03_EXPERIMENTACION_CAUSAL.md"),
]

doc_css = """
:root{--ink:#18222c;--muted:#657585;--line:#dfe6ed;--bg:#f7f9fb;--accent:#1a5f8a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.62}
header{position:sticky;top:0;z-index:5;background:rgba(247,249,251,.94);backdrop-filter:blur(9px);border-bottom:1px solid var(--line)}
header div{width:min(1050px,calc(100% - 32px));margin:auto;padding:12px 0;display:flex;justify-content:space-between;align-items:center;gap:14px}
header a{text-decoration:none;font-weight:750;color:#31556d}main{width:min(1050px,calc(100% - 32px));margin:34px auto 70px;background:#fff;border:1px solid var(--line);border-radius:18px;padding:clamp(24px,5vw,58px);box-shadow:0 12px 32px rgba(20,35,50,.06)}
h1,h2,h3,h4{line-height:1.18;letter-spacing:-.025em}h1{font-size:clamp(2rem,5vw,3.5rem);margin-top:0}h2{margin-top:2.4em;border-top:1px solid var(--line);padding-top:1em}h3{margin-top:1.8em}
p,li{color:#334554}a{color:var(--accent)}img{max-width:100%;height:auto;border-radius:12px;border:1px solid var(--line)}table{width:100%;border-collapse:collapse;margin:20px 0;display:block;overflow:auto}th,td{padding:9px 11px;border:1px solid var(--line);text-align:left;vertical-align:top}th{background:#eef3f7}
pre{overflow:auto;background:#15212b;color:#e7eef4;padding:16px;border-radius:12px}code{font-family:"SFMono-Regular",Consolas,monospace;font-size:.9em}blockquote{margin:22px 0;padding:2px 18px;border-left:4px solid #88a9bf;color:#506778}
.badge{font-size:.75rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase;color:#7890a1}
"""

def render_doc(slug, title, rel):
    src = ROOT / rel
    text = src.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["extra", "toc", "sane_lists"])
    dest = OUT / "docs" / slug
    dest.mkdir(parents=True, exist_ok=True)

    # Preserve sibling asset directories so relative image/table links continue to work.
    for sibling in src.parent.iterdir():
        if sibling.is_dir():
            copytree(sibling, dest / sibling.name, dirs_exist_ok=True)

    page = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · Spot2</title><style>{doc_css}</style></head>
<body><header><div><a href="../../">← Entrega Spot2</a><span class="badge">Documento técnico renderizado</span></div></header>
<main>{body}</main></body></html>"""
    (dest / "index.html").write_text(page, encoding="utf-8")

for item in DOCS:
    render_doc(*item)

print(f"Built reviewer site at {OUT}")
