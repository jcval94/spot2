# Entregable 2 — One Pager ejecutivo

- [Abrir fuente HTML](ONE_PAGER_SPOT2_AESTHETIC.html)
- [Abrir PDF final](ONE_PAGER_SPOT2.pdf)
- [Consultar QA visual](design-qa.md)

El One Pager resume la decisión para Producto y C-Level en 60–90 segundos: existe una señal útil para priorizar oportunidades, el inventario ayuda a decidir qué acción tomar, pero su mejora adicional todavía debe comprobarse. La recomendación es observar primero sin cambiar la operación y después medir impacto con un experimento controlado.

El HTML es la única fuente editorial; el PDF se deriva directamente de él. La metodología, las métricas completas y los riesgos permanecen en los anexos técnicos del repositorio.

## Regeneración

Desde la raíz del repositorio, con Chrome y Playwright ya disponibles:

```powershell
python -c "from pathlib import Path; from playwright.sync_api import sync_playwright; src=Path('entregable/02_one_pager/ONE_PAGER_SPOT2_AESTHETIC.html').resolve(); out=Path('entregable/02_one_pager/ONE_PAGER_SPOT2.pdf').resolve(); p=sync_playwright().start(); browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True); page=browser.new_page(); page.goto(src.as_uri(), wait_until='load'); page.emulate_media(media='print'); page.pdf(path=str(out), format='Letter', print_background=True, display_header_footer=False, prefer_css_page_size=True, margin={'top':'0','right':'0','bottom':'0','left':'0'}); browser.close(); p.stop()"
```

Contrato de salida: una página Letter, fondos impresos, texto extraíble y sin encabezados del navegador.
