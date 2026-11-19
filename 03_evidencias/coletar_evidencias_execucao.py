#!/usr/bin/env python3
"""Coleta evidências REAIS de execução ponta a ponta e monitoramento (Fase 7).

Sobe o servidor sobre uma cópia temporária da amostra com execução contínua ligada,
registra um exemplo rastreado de entrada → decisão → saída (incluindo a reavaliação após
importar a observação de campo do dia), acompanha o monitoramento pelo terminal, captura
telas reais (Playwright/Chromium, se disponível) e encerra por SIGTERM.

Uso (na raiz FASE_7_AGROSMART):  python 03_evidencias/coletar_evidencias_execucao.py
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess  # nosec B404 - executa a própria plataforma
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PLATAFORMA = RAIZ / "02_plataforma"
SAIDA = RAIZ / "03_evidencias" / "execucao"
CAPTURAS = RAIZ / "03_evidencias" / "capturas"


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
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    base = f"http://127.0.0.1:{porta}"
    with tempfile.TemporaryDirectory() as tmp:
        dados = Path(tmp) / "dados"
        env = dict(os.environ, AGROSMART_DATA_DIR=str(dados), AGROSMART_SEED_DIR=str(PLATAFORMA / "data"))
        saida_srv = (SAIDA / "servidor_stdout.log").open("w", encoding="utf-8")
        srv = subprocess.Popen([sys.executable, "main.py", "web", "--porta", str(porta), "--execucao-continua", "--intervalo", "5"],  # nosec B603
                               cwd=PLATAFORMA, env=env, stdout=saida_srv, stderr=subprocess.STDOUT)
        try:
            for _ in range(150):
                try:
                    if http(base, "/api/pronto")[0] == 200:
                        break
                except OSError:
                    time.sleep(0.2)
            # 1) Exemplo rastreado: entrada simulada → decisão sem campo → importa campo → nova decisão
            st, sim = http(base, "/api/simular", {"talhao": "Talhao B", "quantidade": 1})
            evento = sim["eventos"][0]
            consulta = urllib.parse.urlencode({"talhao": "Talhao B", "sensor_id": evento["sensor_id"], "data_hora": evento["data_hora"]})
            _, antes = http(base, "/api/talhao?" + consulta)
            dia = evento["data_hora"][:10]
            csv_obs = ("data;talhao;cultura;percentual_folhas_doentes;praga_detectada;dias_mesma_praga;origem_dados\n"
                       f"{dia};Talhao B;Milho;34;Lagarta;4;SIMULADO - evidência Fase 7\n")
            st_imp, imp = http(base, "/api/importar-observacoes", {"csv": csv_obs})
            _, depois = http(base, "/api/talhao?" + consulta)
            campos = ["regra", "severidade", "alerta", "acao", "justificativa", "avaliacao", "origem_observacao",
                      "percentual_folhas_doentes", "praga_detectada", "dias_mesma_praga"]
            exemplo = {
                "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "natureza": "Execução real do software; leitura e observação de campo SIMULADAS.",
                "entrada_post_api_simular": {"payload": {"talhao": "Talhao B", "quantidade": 1}, "http": st, "evento_gerado": evento},
                "saida_refined_sem_observacao_de_campo": {k: antes["leitura_selecionada"].get(k) for k in campos},
                "entrada_post_importar_observacoes": {"csv": csv_obs, "http": st_imp, "importadas": imp.get("observacoes_importadas")},
                "saida_refined_apos_observacao": {k: depois["leitura_selecionada"].get(k) for k in campos},
                "pipeline_apos": imp.get("pipeline"),
            }
            (SAIDA / "exemplo_entrada_saida.json").write_text(json.dumps(exemplo, ensure_ascii=False, indent=2), encoding="utf-8")
            print("exemplo:", exemplo["saida_refined_sem_observacao_de_campo"]["regra"], "->", exemplo["saida_refined_apos_observacao"]["regra"], flush=True)

            # 2) Monitoramento pelo terminal durante a execução contínua
            mon = subprocess.run([sys.executable, "main.py", "monitorar", "--url", base, "--intervalo", "5", "--vezes", "6"],  # nosec B603
                                 cwd=PLATAFORMA, capture_output=True, text=True, encoding="utf-8", timeout=120)
            (SAIDA / "monitorar_terminal.txt").write_text("$ python main.py monitorar --url <servidor> --intervalo 5 --vezes 6\n" + mon.stdout,
                                                          encoding="utf-8")
            _, op = http(base, "/api/operacao")
            (SAIDA / "api_operacao.json").write_text(json.dumps(op, ensure_ascii=False, indent=2), encoding="utf-8")
            (SAIDA / "api_pronto.json").write_text(json.dumps(http(base, "/api/pronto")[1], ensure_ascii=False, indent=2), encoding="utf-8")
            (SAIDA / "api_health.json").write_text(json.dumps({**http(base, "/api/health")[1], "persistencia": "<pasta temporária>"},
                                                              ensure_ascii=False, indent=2), encoding="utf-8")

            # 3) Capturas reais da interface (opcional: requer Playwright + Chromium)
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                print("playwright indisponível: capturas não geradas", flush=True)
            else:
                with sync_playwright() as pw:
                    nav = pw.chromium.launch()
                    erros = []
                    for nome, largura, altura, rota in (
                            ("21_ferramentas_execucao_continua_desktop", 1440, 900, "#pipeline"),
                            ("22_ferramentas_execucao_continua_mobile", 390, 844, "#pipeline"),
                            ("23_visao_geral_apos_execucao_continua_desktop", 1440, 900, "#geral"),
                            ("24_talhao_b_leitura_rastreada_desktop", 1440, 900,
                             "?talhao=Talhao+B&" + urllib.parse.urlencode({"data_hora": evento["data_hora"], "sensor_id": evento["sensor_id"]}) + "#talhoes")):
                        pag = nav.new_page(viewport={"width": largura, "height": altura})
                        pag.on("pageerror", lambda e: erros.append(str(e)))
                        pag.goto(base + "/" + rota)
                        pag.wait_for_timeout(2500)
                        if "pipeline" in rota:
                            pag.locator("#painelOperacao").scroll_into_view_if_needed()
                            pag.wait_for_timeout(300)
                            pag.screenshot(path=str(CAPTURAS / f"{nome}.png"), full_page=False)
                        else:
                            pag.screenshot(path=str(CAPTURAS / f"{nome}.png"), full_page=True)
                        pag.close()
                    nav.close()
                    (SAIDA / "capturas_erros_js.json").write_text(json.dumps({"excecoes_js": erros}, ensure_ascii=False), encoding="utf-8")
        finally:
            if os.name == "nt":
                srv.terminate()
            else:
                srv.send_signal(signal.SIGTERM)
            codigo = srv.wait(timeout=30)
            saida_srv.close()
        for origem, destino in (("logs/agrosmart.log", "agrosmart.log"), ("operacao/ciclos.jsonl", "ciclos.jsonl"),
                                ("processos/event_log.csv", "event_log_execucao.csv")):
            if (dados / origem).exists():
                shutil.copy2(dados / origem, SAIDA / destino)
    (SAIDA / "encerramento.json").write_text(json.dumps({"sinal": "SIGTERM" if os.name != "nt" else "terminate", "exit_code": codigo},
                                                        ensure_ascii=False), encoding="utf-8")
    print("evidências em", SAIDA, "exit_code servidor:", codigo, flush=True)


if __name__ == "__main__":
    main()
