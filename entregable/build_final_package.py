from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTREGABLE = ROOT / "entregable"
ZIP_PATH = ENTREGABLE / "SPOT2_ASSESSMENT_FINAL.zip"

FILES = [
    (ENTREGABLE / "00_LEEME_PRIMERO.md", "00_LEEME_PRIMERO.md"),
    (ENTREGABLE / "06_deck_ejecutivo/DECK_EJECUTIVO_SPOT2.pdf", "01_DECK_EJECUTIVO_SPOT2.pdf"),
    (ENTREGABLE / "02_one_pager/ONE_PAGER_SPOT2.pdf", "02_ONE_PAGER_SPOT2.pdf"),
    (ROOT / "codexway/notebooks/spot2_assessment.html", "03_NOTEBOOK_SPOT2.html"),
    (ROOT / "codexway/notebooks/spot2_assessment.ipynb", "04_NOTEBOOK_SPOT2.ipynb"),
]

REQUIRED_NOTEBOOK_MARKERS = [
    "### 1.1 Mapa del trabajo ejecutado",
    "### 2.2.1 Inventario de datos antes de modelar",
    "### 3.9 Registro de hipótesis del EDA",
    "### 4.0.1 Grano final de la ABT y separación de responsabilidades",
    "### 5.1.1 Benchmark canónico y amplitud experimental",
    "### 5.1.2 Rolling temporal CV y gate de promoción",
    "### 5.5.1 Error analysis: dónde falla realmente",
    "### 6.1.1 Candidate generation: del request a un conjunto defendible",
    "### 6.2.1 Opportunity: valor absoluto sí, valor incremental de Inventory no",
    "### 6.5.1 Qué demuestra fallback y qué todavía no puede demostrar",
    "### 7.1 Mapa de experimentos y decisiones",
    "### 7.1.1 Qué no funcionó y por qué también importa",
    "### 7.2 Leakage stress test — por qué una métrica alta puede ser falsa",
    "### 7.3 IA con alcance acotado: Catalog QA, no motor de priorización",
    "### 7.4 Diseño experimental final — validar antes de automatizar",
    "### 8.1 Arquitectura end-to-end",
    "### 8.3 Monitoreo por componente",
    "### 9.2 Limitaciones finales",
    "### 9.3 Cómo reproducir la solución",
]

missing = [str(path.relative_to(ROOT)) for path, _ in FILES if not path.exists()]
if missing:
    raise SystemExit("Faltan archivos requeridos para el paquete final: " + ", ".join(missing))

nb_path = ROOT / "codexway/notebooks/spot2_assessment.ipynb"
nb = json.loads(nb_path.read_text(encoding="utf-8"))
joined = "\n".join("".join(cell.get("source", [])) for cell in nb["cells"])
for marker in REQUIRED_NOTEBOOK_MARKERS:
    if marker not in joined:
        raise SystemExit(f"Notebook incompleto: falta marcador requerido: {marker}")

code_cells = [cell for cell in nb["cells"] if cell.get("cell_type") == "code"]
if not code_cells:
    raise SystemExit("Notebook sin celdas de código")
if any(cell.get("execution_count") is None for cell in code_cells):
    raise SystemExit("El notebook final debe conservar todas las celdas de código ejecutadas")

html = (ROOT / "codexway/notebooks/spot2_assessment.html").read_text(encoding="utf-8")
for marker in [
    "Mapa del trabajo ejecutado",
    "Benchmark canónico y amplitud experimental",
    "Error analysis: dónde falla realmente",
]:
    if marker not in html:
        raise SystemExit(f"HTML del notebook desincronizado: falta {marker}")

# Todos los encabezados narrativos del IPYNB deben existir en el HTML.
# Esto hace que una futura ampliación del notebook falle si se intenta empaquetar
# con una versión HTML anterior.
headings = []
for cell in nb["cells"]:
    if cell.get("cell_type") != "markdown":
        continue
    for line in "".join(cell.get("source", [])).splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        title = stripped.lstrip("#").strip()
        title = title.replace(chr(96), "").replace("**", "").replace("*", "")
        if title:
            headings.append(title)

missing_headings = [title for title in headings if title not in html]
if missing_headings:
    raise SystemExit(
        "HTML del notebook desincronizado; faltan encabezados: "
        + " | ".join(missing_headings[:20])
    )

cell_banner = f"{len(nb['cells'])} celdas"
if cell_banner not in html:
    raise SystemExit(
        f"HTML del notebook desincronizado: no contiene el contador {cell_banner!r}"
    )

with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for src, arcname in FILES:
        zf.write(src, arcname)

with zipfile.ZipFile(ZIP_PATH, "r") as zf:
    names = zf.namelist()
    expected = [arcname for _, arcname in FILES]
    if names != expected:
        raise SystemExit(f"Contenido inesperado del ZIP: {names}")
    if zf.read("04_NOTEBOOK_SPOT2.ipynb") != nb_path.read_bytes():
        raise SystemExit("El IPYNB dentro del ZIP no coincide con el notebook canónico")
    html_path = ROOT / "codexway/notebooks/spot2_assessment.html"
    if zf.read("03_NOTEBOOK_SPOT2.html") != html_path.read_bytes():
        raise SystemExit("El HTML dentro del ZIP no coincide con el notebook canónico")

print(
    f"Paquete final construido: {ZIP_PATH} | "
    f"{len(nb['cells'])} celdas totales | {len(code_cells)} celdas de código ejecutadas"
)
