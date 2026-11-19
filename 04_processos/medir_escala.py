#!/usr/bin/env python3
"""Experimento controlado: duração das etapas do pipeline × volume do Raw (Fase 7).

Testa a HIPÓTESE levantada pela análise do event log (reconstrução integral das camadas a
cada execução). Roda numa cópia temporária da amostra, acrescenta leituras simuladas até
cada tamanho-alvo e executa processar() instrumentado 3 vezes por tamanho. Os tempos vêm do
event log gerado (gatilho experimento_escala), não de estimativa.

Uso (na raiz FASE_7_AGROSMART):
  python 04_processos/medir_escala.py --saida 04_processos/resultado
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import shutil
import statistics
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

PLATAFORMA = Path(__file__).resolve().parents[1] / "02_plataforma"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", type=Path, required=True)
    ap.add_argument("--tamanhos", default="144,500,1000,2000,4000,8000")
    ap.add_argument("--repeticoes", type=int, default=3)
    args = ap.parse_args()
    tamanhos = [int(x) for x in args.tamanhos.split(",")]
    with tempfile.TemporaryDirectory() as tmp:
        dados = Path(tmp) / "dados"
        shutil.copytree(PLATAFORMA / "data", dados, ignore=shutil.ignore_patterns("logs", "processos", "operacao"))
        os.environ["AGROSMART_DATA_DIR"] = str(dados)  # antes de importar os módulos
        sys.path.insert(0, str(PLATAFORMA))
        from agrosmart import pipeline as p
        from agrosmart.rastreio import Caso, caminho_event_log
        from agrosmart.simulador import TALHOES, gerar_leitura

        rng = random.Random(2026)
        instante = datetime(2026, 11, 1, 0, 0)
        atual = p.processar()["raw_sensores"]
        casos_por_tamanho = {}
        for alvo in tamanhos:
            while atual < alvo:
                instante += timedelta(minutes=10)
                for talhao in TALHOES:
                    if atual >= alvo:
                        break
                    p.adicionar_evento(gerar_leitura(talhao, instante, rng), origem="experimento_escala")
                    atual += 1
            casos_por_tamanho[alvo] = []
            for _ in range(args.repeticoes):
                caso = Caso("experimento_escala", "experimento")
                caso.registrar("Entrada recebida", detail=f"raw={atual}")
                p.processar(caso=caso)
                caso.concluir("sucesso")
                casos_por_tamanho[alvo].append(caso.case_id)
        with caminho_event_log().open(newline="", encoding="utf-8") as f:
            eventos = list(csv.DictReader(f))
        args.saida.mkdir(parents=True, exist_ok=True)
        shutil.copy2(caminho_event_log(), args.saida / "event_log_experimento_escala.csv")

    etapas = ["Publicar Trusted", "Aplicar regras R1–R7", "Publicar Refined"]
    linhas = []
    for alvo, casos in casos_por_tamanho.items():
        linha = {"raw_sensores": alvo, "repeticoes": len(casos)}
        total = []
        for etapa in etapas:
            valores = [float(e["duration_ms"]) for e in eventos
                       if e["case_id"] in casos and e["activity"] == etapa and e["lifecycle"] == "complete"]
            linha[f"{etapa} mediana_ms"] = round(statistics.median(valores), 2)
            total.append(statistics.median(valores))
        linha["soma_medianas_ms"] = round(sum(total), 2)
        linhas.append(linha)
    with (args.saida / "escala_pipeline.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    xs = [linha["raw_sensores"] for linha in linhas]
    ys = [linha["soma_medianas_ms"] for linha in linhas]
    reg = statistics.linear_regression(xs, ys)
    resumo = {"linhas": linhas, "regressao_linear": {"ms_por_1000_registros": round(reg.slope * 1000, 2), "intercepto_ms": round(reg.intercept, 2),
                                                     "pearson_r": round(statistics.correlation(xs, ys), 4), "n_tamanhos": len(xs)},
              "metodo": "mediana de N repetições por tamanho; tempos medidos por perf_counter dentro de processar(); mesma máquina; sem carga concorrente"}
    (args.saida / "escala_pipeline.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
