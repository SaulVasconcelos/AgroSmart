#!/usr/bin/env python3
"""Captura as telas REAIS usadas nos slides do pitch (requer Playwright + Chromium).

Mesmo fluxo de 03_evidencias/coletar_evidencias_execucao.py, sobre uma cópia temporária da
amostra: leitura simulada do Talhão B -> decisão sem observação de campo (ND) -> importação
da observação (34% / Lagarta / 4 dias) -> nova decisão (R2). Os dados são simulados; a
execução é real. A única intervenção na página é tirar o foco do teclado antes da foto.

Uso (na raiz do repositório):  python 05_apresentacao/capturar_telas_pitch.py
A cada execução a leitura sorteada muda; `capturas_pitch/registro.json` guarda a que foi usada.
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

RAIZ = Path(__file__).resolve().parents[1]
PLATAFORMA = RAIZ / "02_plataforma"
SAIDA = RAIZ / "05_apresentacao" / "capturas_pitch"
CAMPOS = ["regra", "severidade", "alerta", "acao", "justificativa", "avaliacao",
          "percentual_folhas_doentes", "praga_detectada", "dias_mesma_praga"]
SEM_FOCO = "document.activeElement && document.activeElement.blur()"


def http(base, caminho, corpo=None):
    dados = None if corpo is None else json.dumps(corpo).encode()
    req = urllib.request.Request(base + caminho, data=dados, method="GET" if dados is None else "POST",  # nosec B310
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # nosec B310
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    base = f"http://127.0.0.1:{porta}"
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, AGROSMART_DATA_DIR=str(Path(tmp) / "dados"), AGROSMART_SEED_DIR=str(PLATAFORMA / "data"))
        srv = subprocess.Popen([sys.executable, "main.py", "web", "--porta", str(porta), "--execucao-continua", "--intervalo", "5"],  # nosec B603
                               cwd=PLATAFORMA, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
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
            erros = []
            with sync_playwright() as pw:
                nav = pw.chromium.launch()

                def cartao(nome):
                    pag = nav.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
                    pag.on("pageerror", lambda e: erros.append(str(e)))
                    pag.goto(base + rota)
                    pag.wait_for_timeout(2500)
                    pag.evaluate(SEM_FOCO)
                    pag.locator(".panel.current-reading.selected-reading").first.screenshot(path=str(SAIDA / nome))
                    pag.close()

                cartao("exemplo_antes_nd.png")
                csv_obs = ("data;talhao;cultura;percentual_folhas_doentes;praga_detectada;dias_mesma_praga;origem_dados\n"
                           f"{evento['data_hora'][:10]};Talhao B;Milho;34;Lagarta;4;SIMULADO - captura do pitch\n")
                st_imp, _ = http(base, "/api/importar-observacoes", {"csv": csv_obs})
                _, depois = http(base, "/api/talhao?talhao=Talhao+B&" + consulta)
                cartao("exemplo_depois_r2.png")
                time.sleep(11)  # dois ciclos contínuos reais: os três talhões passam a ter leitura do dia
                pag = nav.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=2)
                pag.on("pageerror", lambda e: erros.append(str(e)))
                pag.goto(base + "/#geral")
                pag.wait_for_timeout(2500)
                pag.evaluate(SEM_FOCO)
                pag.screenshot(path=str(SAIDA / "visao_geral.png"), full_page=False)
                # Recorte dos painéis de indicadores e de prioridades (mesma página, sem edição).
                caixas = [pag.locator(sel).first.bounding_box() for sel in ("#kpiCards", "#paneGeral .panel.priorities")]
                topo = min(c["y"] for c in caixas) - 12
                base_y = max(c["y"] + c["height"] for c in caixas) + 12
                esq = min(c["x"] for c in caixas) - 12
                larg = max(c["x"] + c["width"] for c in caixas) + 12 - esq
                pag.screenshot(path=str(SAIDA / "visao_geral_prioridades.png"),
                               clip={"x": esq, "y": topo, "width": larg, "height": base_y - topo})
                pag.close()
                nav.close()
            registro = {"natureza": "Execução real do software; leitura e observação de campo SIMULADAS.",
                        "evento": evento, "http_simular": st, "http_importar": st_imp,
                        "antes": {k: antes["leitura_selecionada"].get(k) for k in CAMPOS},
                        "depois": {k: depois["leitura_selecionada"].get(k) for k in CAMPOS},
                        "erros_js": erros}
            (SAIDA / "registro.json").write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
            print("exemplo:", registro["antes"]["regra"], "->", registro["depois"]["regra"], "| erros JS:", len(erros))
        finally:
            if os.name == "nt":
                srv.terminate()
            else:
                srv.send_signal(signal.SIGTERM)
            srv.wait(timeout=30)


if __name__ == "__main__":
    main()
