#!/usr/bin/env python3
"""Captura, em 2x, as telas REAIS do AgroMonitor usadas no vídeo pitch animado.

Mesmo fluxo de 05_apresentacao/capturar_telas_pitch.py, sobre uma cópia temporária da amostra:
leitura simulada do Talhão B -> decisão sem observação de campo (ND) -> importação da observação
(34% / Lagarta / 4 dias) -> nova decisão (R2) -> dois ciclos da execução contínua -> Visão Geral
e painel de execução contínua. Os dados são simulados; a execução é real. Nenhuma tela é
redesenhada: a única intervenção na página é tirar o foco do teclado antes da foto.

Saídas: public/tex/*.png (texturas), src/layout.json (posição dos elementos, em px de CSS)
e public/tex/registro.json (a leitura usada e o que as telas mostravam).

A leitura do simulador é sorteada: o script repete a execução até ela cair no caso contado no
roteiro (ND sem observação, R2 com ela) e registra em registro.json qual tentativa foi usada.

Uso:  python scripts/capturar_telas_filme.py [raiz do repositório AgroSmart]
(sem argumento, usa a raiz do repositório em que esta pasta está)
"""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess  # nosec B404 - executa a própria plataforma
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

FILME = Path(__file__).resolve().parents[1]
TEX = FILME / "public" / "tex"
VIEW = {"width": 1920, "height": 1080}
SEM_FOCO = "document.activeElement && document.activeElement.blur()"
CAMPOS = ["regra", "severidade", "alerta", "acao", "justificativa", "avaliacao",
          "percentual_folhas_doentes", "praga_detectada", "dias_mesma_praga", "umidade_solo", "temperatura"]

CAIXAS_JS = """(sels) => { const o = {}; for (const [k, s] of Object.entries(sels)) {
  const e = typeof s === 'string' ? document.querySelector(s) : null; if (!e) { o[k] = null; continue; }
  const r = e.getBoundingClientRect(); o[k] = {x: r.x + scrollX, y: r.y + scrollY, w: r.width, h: r.height}; } return o; }"""


def http(base, caminho, corpo=None):
    dados = None if corpo is None else json.dumps(corpo).encode()
    req = urllib.request.Request(base + caminho, data=dados, method="GET" if dados is None else "POST",  # nosec B310
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # nosec B310
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def tentativa(plataforma, numero):
    """Uma execução completa. Devolve True se a leitura sorteada caiu no caso do roteiro (ND -> R2)."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    base = f"http://127.0.0.1:{porta}"
    layout, textos, erros = {}, {}, []
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, AGROSMART_DATA_DIR=str(Path(tmp) / "dados"), AGROSMART_SEED_DIR=str(plataforma / "data"))
        srv = subprocess.Popen([sys.executable, "main.py", "web", "--porta", str(porta), "--execucao-continua", "--intervalo", "5"],  # nosec B603
                               cwd=plataforma, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        try:
            for _ in range(150):
                try:
                    if http(base, "/api/pronto")[0] == 200:
                        break
                except OSError:
                    time.sleep(0.2)
            st, sim = http(base, "/api/simular", {"talhao": "Talhao B", "quantidade": 1})
            evento = sim["eventos"][0]
            consulta = urllib.parse.urlencode({"data_hora": evento["data_hora"], "sensor_id": evento["sensor_id"]})
            rota = "/?talhao=Talhao+B&" + consulta + "#talhoes"
            _, antes = http(base, "/api/talhao?talhao=Talhao+B&" + consulta)
            with sync_playwright() as pw:
                nav = pw.chromium.launch()

                def pagina(caminho):
                    pag = nav.new_page(viewport=VIEW, device_scale_factor=2)
                    pag.on("pageerror", lambda e: erros.append(str(e)))
                    pag.goto(base + caminho)
                    pag.evaluate("document.fonts.ready")
                    pag.wait_for_timeout(2500)
                    pag.evaluate(SEM_FOCO)
                    return pag

                def cartao(nome):
                    pag = pagina(rota)
                    card = pag.locator(".panel.current-reading.selected-reading").first
                    card.scroll_into_view_if_needed()
                    card.screenshot(path=str(TEX / f"cartao_{nome}.png"))
                    sels = {"cartao": ".panel.current-reading.selected-reading",
                            "titulo": ".selected-reading .reading-heading",
                            "linha_regra": ".selected-reading > p.small-note",
                            "metricas": ".selected-reading .reading-metrics",
                            "completude": ".selected-reading .completeness",
                            "evidencias": ".selected-reading .field-evidence",
                            "orientacao": ".selected-reading .recommendation",
                            "motivo": ".selected-reading .reading-reason",
                            "origem": ".selected-reading details.origin"}
                    layout[f"cartao_{nome}"] = pag.evaluate(CAIXAS_JS, sels)
                    textos[f"cartao_{nome}"] = card.inner_text()
                    pag.close()

                cartao("antes_nd")
                csv_obs = ("data;talhao;cultura;percentual_folhas_doentes;praga_detectada;dias_mesma_praga;origem_dados\n"
                           f"{evento['data_hora'][:10]};Talhao B;Milho;34;Lagarta;4;SIMULADO - captura do pitch\n")
                st_imp, _ = http(base, "/api/importar-observacoes", {"csv": csv_obs})
                _, depois = http(base, "/api/talhao?talhao=Talhao+B&" + consulta)
                cartao("depois_r2")
                time.sleep(11)  # dois ciclos contínuos reais: os três talhões passam a ter leitura do dia

                # Visão Geral em 4x: de uma única foto saem a página inteira (reduzida para 2x) e os
                # recortes em alta dos indicadores e da linha do Talhão B, para os planos fechados.
                pag = nav.new_page(viewport=VIEW, device_scale_factor=4)
                pag.on("pageerror", lambda e: erros.append(str(e)))
                pag.goto(base + "/#geral")
                pag.evaluate("document.fonts.ready")
                pag.wait_for_timeout(2500)
                pag.evaluate(SEM_FOCO)
                pag.screenshot(path=str(TEX / "visao_geral_4x.png"), full_page=False)
                linhas = pag.locator("#priorityList .priority-row")
                idx_b = next(i for i in range(linhas.count()) if "Talhão B" in linhas.nth(i).inner_text())
                pag.evaluate(f"document.querySelectorAll('#priorityList .priority-row')[{idx_b}].id = 'linhaTalhaoB'")
                paineis = pag.locator("#paneGeral .panel")
                for i in range(paineis.count()):
                    pag.evaluate(f"document.querySelectorAll('#paneGeral .panel')[{i}].dataset.filme = 'painel{i}'")
                sels = {"kpis": "#kpiCards", "kpi_leituras": "#kpiCards > *:first-child",
                        "prioridades": "#paneGeral .panel.priorities", "lista": "#priorityList",
                        "linha_b": "#linhaTalhaoB", "linha_b_selo": "#linhaTalhaoB .priority-severity > *",
                        "linha_b_regra": "#linhaTalhaoB .priority-rule", "titulo": "#pageTitle",
                        "umidade": "#chartUmidade", "temperatura": "#chartTemperatura"}
                for i in range(paineis.count()):
                    sels[f"painel{i}"] = f"#paneGeral .panel[data-filme=painel{i}]"
                layout["visao_geral"] = pag.evaluate(CAIXAS_JS, sels)
                textos["kpis"] = pag.locator("#kpiCards").inner_text()
                textos["linha_b"] = linhas.nth(idx_b).inner_text()
                textos["prioridades"] = pag.locator("#priorityList").inner_text()
                pag.close()
                from PIL import Image
                grande = Image.open(TEX / "visao_geral_4x.png").convert("RGB")
                grande.resize((VIEW["width"] * 2, VIEW["height"] * 2), Image.LANCZOS).save(TEX / "visao_geral.png")
                for nome, chave in (("kpis_4x", "kpis"), ("linha_talhao_b_4x", "linha_b")):
                    c = layout["visao_geral"][chave]
                    grande.crop((round(c["x"] * 4), round(c["y"] * 4), round((c["x"] + c["w"]) * 4), round((c["y"] + c["h"]) * 4))).save(TEX / f"{nome}.png")
                (TEX / "visao_geral_4x.png").unlink()

                pag = pagina("/#pipeline")
                painel = pag.locator("#painelOperacao")
                painel.scroll_into_view_if_needed()
                pag.wait_for_timeout(600)
                pag.evaluate(SEM_FOCO)
                painel.screenshot(path=str(TEX / "painel_operacao.png"))
                layout["painel_operacao"] = pag.evaluate(CAIXAS_JS, {"painel": "#painelOperacao", "status": "#operacaoStatus", "ciclos": "#operacaoCiclos"})
                textos["painel_operacao"] = painel.inner_text()
                pag.close()
                nav.close()
            registro = {"natureza": "Execução real do software; leitura e observação de campo SIMULADAS.",
                        "capturado_em": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "viewport": VIEW, "escala": 2,
                        "evento": evento, "http_simular": st, "http_importar": st_imp,
                        "antes": {k: antes["leitura_selecionada"].get(k) for k in CAMPOS},
                        "depois": {k: depois["leitura_selecionada"].get(k) for k in CAMPOS},
                        "textos_nas_telas": textos, "erros_js": erros}
            linha = textos.get("linha_b", "")
            serve = (registro["antes"]["regra"], registro["depois"]["regra"]) == ("ND", "R2") and "Alta" in linha and "R2" in linha
            registro["tentativa"] = numero
            registro["criterio"] = ("A leitura do simulador é sorteada. A captura é repetida até a leitura do Talhão B cair no caso "
                                    "contado no roteiro: ND sem observação de campo, R2 com ela, e Talhão B com prioridade Alta (R2) "
                                    "na Visão Geral. Nenhum valor é digitado nem editado.")
            print(f"tentativa {numero}:", registro["antes"]["regra"], "->", registro["depois"]["regra"], "| linha:", linha.replace("\n", " | "), "| erros JS:", len(erros))
            if serve:
                (TEX / "registro.json").write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
                (FILME / "src" / "layout.json").write_text(json.dumps(layout, ensure_ascii=False, indent=1), encoding="utf-8")
            return serve
        finally:
            if os.name == "nt":
                srv.terminate()
            else:
                srv.send_signal(signal.SIGTERM)
            srv.wait(timeout=30)


def main():
    raiz = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else FILME.parents[2]
    TEX.mkdir(parents=True, exist_ok=True)
    for numero in range(1, 21):
        if tentativa(raiz / "02_plataforma", numero):
            return
    raise SystemExit("Nenhuma das 20 tentativas caiu no caso ND -> R2.")


if __name__ == "__main__":
    main()
