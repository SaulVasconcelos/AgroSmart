"""Gera o PDF dos slides do pitch a partir dos arquivos do deck guardados nesta pasta.

Uso (na raiz do repositório ou em qualquer pasta):

    python 05_apresentacao/slides_fonte/gerar_pdf_slides.py [saida.pdf] [pasta_de_conferencia]

Sem argumentos, grava ``05_apresentacao/slides_pitch_agrosmart.pdf``. Com o segundo argumento,
grava também um PNG de 1920 x 1080 de cada slide, desenhado na tela, para comparar com as
páginas do PDF.

Entradas, todas no repositório:
    project/deck.json, project/deck.css, project/slides/*.html   o deck (texto, ordem e estilo)
    ../capturas_pitch/*.png                                       as telas reais usadas nos slides
    fonts/*.woff2                                                 Inter e Space Grotesk

Requer Python 3 e Playwright com Chromium (``pip install playwright`` e ``playwright install
chromium``). O desenho é feito com JavaScript desligado e sem acesso à rede.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

AQUI = Path(__file__).resolve().parent
DECK = AQUI / "project"
CAPTURAS = AQUI.parent / "capturas_pitch"
FONTES = AQUI / "fonts"
SAIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI.parent / "slides_pitch_agrosmart.pdf"
CONFERENCIA = Path(sys.argv[2]) if len(sys.argv) > 2 else None

# Imagens do deck: identificador usado nos slides -> arquivo em capturas_pitch/.
IMAGENS = {
    "515e44e323497bcb5aba15c5253f6902": "visao_geral.png",
    "720ae0ec0de0269b49ec38cdc4be676b": "exemplo_antes_nd.png",
    "39ade01157d0e3de7b397891e7ba992f": "exemplo_depois_r2.png",
    "7d19c1b71a73df0b513559f38620f03c": "visao_geral_prioridades.png",
}

# Regras de base do visualizador de slides (um quadro de 1920 x 1080 por slide) e as fontes do deck.
BASE = """* { margin: 0 }
body { font: 32px/1.2 sans-serif }
body > section { width: 1920px !important; height: 1080px !important; overflow: hidden !important; box-sizing: border-box !important; position: relative; isolation: isolate }
section[hidden], aside, noscript { display: none !important }
h1 { font-size: 96px; font-weight: 600 } h2 { font-size: 64px; font-weight: 600 } h3 { font-size: 44px; font-weight: 600 }
p, li, h1, h2, h3, td, th { overflow-wrap: break-word; text-wrap: pretty }
table { width: 100%; border-collapse: separate; border-spacing: 0; border: solid #0003; border-width: 2px 0 0 2px }
th, td { padding: .35em .6em; text-align: left; border: solid #0003; border-width: 0 2px 2px 0 }
x-shape, x-icon, x-embed { display: block }
@font-face{font-family:'Inter';font-weight:400;src:url(/fonts/inter-latin-400-normal.woff2)}
@font-face{font-family:'Inter';font-weight:600;src:url(/fonts/inter-latin-600-normal.woff2)}
@font-face{font-family:'Inter';font-weight:400;font-style:italic;src:url(/fonts/inter-latin-400-italic.woff2)}
@font-face{font-family:'Space Grotesk';font-weight:600;src:url(/fonts/space-grotesk-latin-600-normal.woff2)}
@font-face{font-family:'Space Grotesk';font-weight:700;src:url(/fonts/space-grotesk-latin-700-normal.woff2)}
"""
# Uma página de 1920 x 1080 px por slide, sem margem.
IMPRESSAO = """@page { size: 1920px 1080px; margin: 0 }
html, body { width: 1920px }
body > section { break-inside: avoid; break-after: page }
body > section:last-of-type { break-after: auto }
"""


def montar_pagina():
    indice = json.loads((DECK / "deck.json").read_text(encoding="utf-8"))
    ordem = indice["order"]
    corpo = "".join((DECK / "slides" / f"{i}.html").read_text(encoding="utf-8") for i in ordem)
    pagina = (
        '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">'
        f"<title>{indice['title']}</title><style>{BASE}{IMPRESSAO}</style>"
        '<link rel="stylesheet" href="/project/deck.css"></head><body>' + corpo + "</body></html>"
    )
    return ordem, pagina


def main():
    ordem, pagina = montar_pagina()
    recusados = []

    def responder(rota):
        caminho = rota.request.url.split("://", 1)[1].split("/", 1)[1]
        if caminho == "":
            return rota.fulfill(body=pagina, content_type="text/html; charset=utf-8")
        if caminho == "project/deck.css":
            return rota.fulfill(body=(DECK / "deck.css").read_bytes(), content_type="text/css")
        if caminho.startswith("fonts/") and (FONTES / Path(caminho).name).is_file():
            return rota.fulfill(body=(FONTES / Path(caminho).name).read_bytes(), content_type="font/woff2")
        if caminho.startswith("_blob/") and caminho[6:] in IMAGENS:
            return rota.fulfill(body=(CAPTURAS / IMAGENS[caminho[6:]]).read_bytes(), content_type="image/png")
        if caminho != "favicon.ico":
            recusados.append(caminho)
        return rota.abort("aborted")

    if CONFERENCIA:
        CONFERENCIA.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        navegador = pw.chromium.launch(args=["--host-resolver-rules=MAP * ^NOTFOUND"])
        contexto = navegador.new_context(java_script_enabled=False, viewport={"width": 1920, "height": 1080})
        aba = contexto.new_page()
        aba.route("**/*", responder)
        aba.goto("http://deck.local/")
        aba.wait_for_timeout(800)
        if CONFERENCIA:
            for n, i in enumerate(ordem):
                slide = aba.locator(f"section#{i}")
                slide.scroll_into_view_if_needed()
                aba.wait_for_timeout(250)
                slide.screenshot(path=str(CONFERENCIA / f"{n + 1:02d}_{i}.png"), animations="disabled")
        aba.emulate_media(media="screen")
        aba.pdf(path=str(SAIDA), width="1920px", height="1080px", print_background=True,
                prefer_css_page_size=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        navegador.close()

    if recusados:
        sys.exit(f"Arquivos pedidos pelos slides e não encontrados: {sorted(set(recusados))}")
    print(f"{len(ordem)} slides -> {SAIDA}")


if __name__ == "__main__":
    main()
