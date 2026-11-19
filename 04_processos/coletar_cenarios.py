#!/usr/bin/env python3
"""Coleta controlada de event log REAL do AgroSmart (Fase 7).

Sobe o servidor sobre uma CÓPIA da amostra (nunca sobre 02_plataforma/data), executa
cenários reais pela API e pela CLI e devolve o event log produzido pelo software.
Cenários: execução contínua; POSTs válidos; entradas inválidas (rejeitadas antes de
gravar); importação de observações; rajada concorrente (disputa pela trava); importação
CLI com duplicata e com arquivo inválido; reprocessamento CLI. Nenhum limiar das regras
é alterado para produzir variantes.

Uso (na raiz FASE_7_AGROSMART):
  python 04_processos/coletar_cenarios.py --saida 04_processos/coleta --ciclos 20 --intervalo 5
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess  # nosec B404 - executa a própria plataforma com argumentos fixos
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PLATAFORMA = Path(__file__).resolve().parents[1] / "02_plataforma"
CAB_OBS = "data;talhao;cultura;percentual_folhas_doentes;praga_detectada;dias_mesma_praga;origem_dados\n"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def http(base: str, caminho: str, corpo=None, bruto: bytes | None = None):
    dados = bruto if bruto is not None else (None if corpo is None else json.dumps(corpo).encode())
    req = urllib.request.Request(base + caminho, data=dados, method="GET" if dados is None else "POST",  # nosec B310 - URL local
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # nosec B310
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", type=Path, required=True)
    ap.add_argument("--ciclos", type=int, default=20, help="ciclos da execução contínua a observar")
    ap.add_argument("--intervalo", type=float, default=5.0)
    args = ap.parse_args()
    args.saida.mkdir(parents=True, exist_ok=True)
    roteiro: list[dict] = []

    def anotar(cenario, **dados):
        item = {"instante_utc": utc(), "cenario": cenario, **dados}
        roteiro.append(item)
        print(json.dumps(item, ensure_ascii=False), flush=True)

    with tempfile.TemporaryDirectory() as tmp:
        dados = Path(tmp) / "dados"
        env = dict(os.environ, AGROSMART_DATA_DIR=str(dados), AGROSMART_SEED_DIR=str(PLATAFORMA / "data"))
        porta = porta_livre()
        base = f"http://127.0.0.1:{porta}"
        log_srv = (args.saida / "servidor_stdout.log").open("w", encoding="utf-8")
        srv = subprocess.Popen([sys.executable, "main.py", "web", "--porta", str(porta)], cwd=PLATAFORMA, env=env,  # nosec B603
                               stdout=log_srv, stderr=subprocess.STDOUT)
        try:
            fim = time.monotonic() + 30
            while time.monotonic() < fim:
                try:
                    if http(base, "/api/pronto")[0] == 200:
                        break
                except OSError:
                    time.sleep(0.2)
            anotar("servidor_pronto", porta=porta)

            st, op = http(base, "/api/operacao/iniciar", {"intervalo_s": args.intervalo, "eventos_por_ciclo": 3})
            anotar("execucao_continua_iniciada", http=st, intervalo_s=args.intervalo)

            for q in (1, 3, 6, 2, 8):
                st, r = http(base, "/api/simular", {"quantidade": q})
                anotar("post_simular_valido", http=st, quantidade=q, raw=r.get("pipeline", {}).get("raw_sensores"))
                time.sleep(1.5)
            for nome, corpo, bruto in (("quantidade_fora_do_limite", {"quantidade": 99}, None),
                                       ("talhao_inexistente", {"talhao": "Talhao Z", "quantidade": 1}, None),
                                       ("json_malformado", None, b"{quantidade: 1")):
                st, r = http(base, "/api/simular", corpo, bruto)
                anotar("post_simular_invalido", motivo=nome, http=st, erro=r.get("erro"))
            hoje = datetime.now().date().isoformat()
            st, r = http(base, "/api/importar-observacoes", {"csv": CAB_OBS + f"{hoje};Talhao A;Soja;12;Nenhuma;0;SIMULADO - coleta Fase 7\n"
                                                                                f"{hoje};Talhao B;Milho;34;Lagarta;4;SIMULADO - coleta Fase 7\n"})
            anotar("importar_observacoes_valido", http=st, importadas=r.get("observacoes_importadas"))
            st, r = http(base, "/api/importar-observacoes", {"csv": CAB_OBS + f"{hoje};Talhao C;Cafe;150;Nenhuma;0;x\n"})
            anotar("importar_observacoes_invalido", http=st, erro=r.get("erro"))
            st, r = http(base, "/api/importar-observacoes", {"csv": "coluna_errada\n1\n"})
            anotar("importar_observacoes_invalido", http=st, erro=r.get("erro"))

            resultados = []

            def disparar():
                resultados.append(http(base, "/api/simular", {"quantidade": 1})[0])

            threads = [threading.Thread(target=disparar) for _ in range(6)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            anotar("rajada_concorrente", requisicoes=len(threads), http=sorted(resultados))

            while True:
                st, op = http(base, "/api/operacao")
                ciclos = op["execucao_continua"]["ciclos_total"]
                if ciclos >= args.ciclos:
                    break
                time.sleep(1)
            st, op = http(base, "/api/operacao/parar", bruto=b"")
            anotar("execucao_continua_parada", http=st, ciclos=op["execucao_continua"]["ciclos_total"],
                   falhas=op["execucao_continua"]["falhas_total"])
            st, op = http(base, "/api/operacao")
            (args.saida / "operacao_final.json").write_text(json.dumps(op, ensure_ascii=False, indent=2), encoding="utf-8")
        finally:
            if os.name == "nt":
                srv.terminate()
            else:
                srv.send_signal(signal.SIGTERM)
            codigo = srv.wait(timeout=30)
            log_srv.close()
            anotar("servidor_encerrado", exit_code=codigo)

        # CLI depois do servidor parado: uma única autoridade de escrita por vez.
        def cli(cenario, *argumentos):
            r = subprocess.run([sys.executable, "main.py", *argumentos], cwd=PLATAFORMA, env=env,  # nosec B603
                               capture_output=True, text=True, encoding="utf-8", timeout=120)
            anotar(cenario, exit_code=r.returncode, saida=(r.stdout + r.stderr).strip().splitlines()[-1:] or [""])

        existente = json.loads((dados / "raw" / "sensores.jsonl").read_text(encoding="utf-8").splitlines()[-1])["evento"]
        novo = dict(existente, data_hora=datetime.now().isoformat(timespec="microseconds"))
        lote = Path(tmp) / "lote_com_duplicata.jsonl"
        lote.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in (novo, existente)) + "\n", encoding="utf-8")
        cli("cli_importar_sensores_com_duplicata", "importar-sensores", str(lote))
        ruim = Path(tmp) / "lote_invalido.jsonl"
        ruim.write_text(json.dumps(dict(novo, umidade_solo=140)) + "\n", encoding="utf-8")
        cli("cli_importar_sensores_invalido", "importar-sensores", str(ruim))
        cli("cli_processar", "processar")

        for origem, destino in (("processos/event_log.csv", "event_log.csv"), ("logs/agrosmart.log", "agrosmart.log"),
                                ("operacao/ciclos.jsonl", "ciclos.jsonl"), ("refined/estado_pipeline.json", "estado_pipeline_final.json")):
            if (dados / origem).exists():
                shutil.copy2(dados / origem, args.saida / destino)
    (args.saida / "roteiro_cenarios.json").write_text(json.dumps(roteiro, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Coleta concluída em {args.saida}", flush=True)


if __name__ == "__main__":
    main()
