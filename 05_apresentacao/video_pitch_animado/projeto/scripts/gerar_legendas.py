#!/usr/bin/env python3
"""Gera out/legendas.srt com o texto da narração, nos tempos do filme.

Cada frase tem o intervalo em que é dita no arquivo de narração (medido pelas pausas da fala);
o script desloca esse intervalo para o ponto em que o trecho da cena entra no filme.
Uso:  python scripts/gerar_legendas.py
"""
import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
T = json.loads((RAIZ / "src/timeline.json").read_text(encoding="utf-8"))
S = json.loads((RAIZ / "src/som.json").read_text(encoding="utf-8"))
FPS, BAT = T["fps"], T["batida_s"]


def arred(x: float) -> int:
    return math.floor(x + 0.5)


FRASES = [  # cena, início e fim no arquivo de narração (s), texto
    ("s01", 0.00, 3.48, "Uma lavoura monitorada produz dados o tempo todo."),
    ("s01", 4.11, 9.66, "Os sensores medem umidade e temperatura, e quem anda\npelo campo anota o que vê nas plantas."),
    ("s01", 10.05, 15.33, "Mas essas informações ficam separadas,\ne nenhuma delas diz onde está a urgência."),
    ("s01", 16.47, 19.01, "Um alerta sem explicação é difícil de confiar."),
    ("s01", 20.00, 24.46, "E, quando falta a observação de campo,\no sensor sozinho não prova que está tudo bem."),
    ("s02", 25.34, 28.74, "Este é o AgroMonitor, um módulo do AgroSmart."),
    ("s03", 29.73, 35.52, "Ele foi pensado para quem decide no campo: o produtor rural,\no agrônomo e o gestor da operação."),
    ("s04", 36.65, 41.80, "Ele cruza sensores e observações de campo\ne mostra as prioridades de cada talhão."),
    ("s05", 42.62, 47.14, "Aqui, o Talhão B aparece com prioridade alta,\npela regra R2."),
    ("s06", 48.01, 48.83, "E quando falta dado?"),
    ("s07", 49.60, 53.78, "Sem observação de campo, a resposta é indeterminada,\nnunca normal."),
    ("s07", 54.55, 58.54, "Registrada a observação, a mesma leitura\npassa a prioridade alta."),
    ("s08", 59.76, 66.02, "Toda prioridade mostra o porquê: a regra aplicada,\na evidência usada e a orientação sugerida."),
    ("s09", 67.18, 73.05, "Cada execução deixa rastro no event log, da entrada recebida\naté a publicação do resultado."),
    ("s10", 73.95, 74.92, "E roda sozinho."),
    ("s11", 75.81, 82.07, "Um comando sobe a plataforma em um container, e a execução\ncontínua gera e processa leituras em ciclos."),
    ("s12", 82.88, 85.88, "São 63 testes automatizados aprovados,"),
    ("s12", 86.27, 93.20, "22 de 22 verificações no container e nenhuma vulnerabilidade\ncrítica ou alta com correção disponível."),
    ("s13", 93.97, 95.82, "O software está entregue e testado."),
    ("s13", 96.22, 97.71, "Os dados são simulados."),
    ("s13", 97.98, 101.74, "Sensores físicos, login e notificações ficam no roadmap."),
    ("s14", 102.61, 107.53, "A nossa proposta de valor: saber onde olhar primeiro\nna lavoura, e por quê."),
    ("s15", 108.44, 109.13, "AgroSmart."),
    ("s15", 109.48, 113.31, "O código, as evidências e a documentação\nestão no nosso repositório."),
]


def marca(s: float) -> str:
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


cenas = {c["id"]: c for c in T["cenas"]}
linhas = []
for n, (cid, a, b, texto) in enumerate(FRASES, 1):
    c = cenas[cid]
    base = (arred(c["b0"] * BAT * FPS) + arred(c["fala_em_s"] * FPS)) / FPS - S["narracao"]["trechos"][cid][0]
    linhas.append(f"{n}\n{marca(base + a - 0.05)} --> {marca(base + b + 0.25)}\n{texto}\n")
(RAIZ / "out").mkdir(exist_ok=True)
(RAIZ / "out/legendas.srt").write_text("\n".join(linhas), encoding="utf-8")
print(len(linhas), "legendas;", linhas[0].replace("\n", " | "), "...", linhas[-1].replace("\n", " | "))
