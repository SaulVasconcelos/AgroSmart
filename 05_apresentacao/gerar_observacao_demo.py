#!/usr/bin/env python3
"""Gera o CSV de observação de campo usado na cena 4 do vídeo técnico.

A observação é SIMULADA e vale para a data de hoje: Talhão B, milho, 34% de folhas afetadas,
lagarta há 4 dias. Com uma leitura do dia que esteja como ND, o resultado esperado é R2 (Alta).

Uso:  python 05_apresentacao/gerar_observacao_demo.py
Saída: 05_apresentacao/observacao_demo.csv (para importar em Pipeline e Simulação).
"""
from datetime import date
from pathlib import Path

DESTINO = Path(__file__).resolve().parent / "observacao_demo.csv"
CABECALHO = "data;talhao;cultura;percentual_folhas_doentes;praga_detectada;dias_mesma_praga;origem_dados"


def main():
    linha = f"{date.today().isoformat()};Talhao B;Milho;34;Lagarta;4;SIMULADO - demonstracao do video"
    DESTINO.write_text(CABECALHO + "\n" + linha + "\n", encoding="utf-8")
    print(f"Gerado: {DESTINO}")
    print(linha)


if __name__ == "__main__":
    main()
