#!/usr/bin/env python3
"""Análise de processo do AgroSmart a partir do event log REAL (Fase 7).

Somente biblioteca padrão. Lê um ou mais CSVs no contrato de
04_processos/contrato_event_log.md, valida a integridade, descobre variantes,
calcula durações e o grafo diretamente-segue (DFG) observado e compara com o
fluxo esperado por gatilho. Nada é inventado: toda métrica sai do log lido.

Uso:
  python analisar_event_log.py event_log.csv [mais.csv ...] --saida pasta_resultado
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

OBRIGATORIAS = ["event_id", "case_id", "sequence", "activity", "lifecycle", "timestamp", "status"]
TERMINAIS = {"Execução concluída", "Entrada rejeitada", "Execução falhou"}
NUCLEO = ["Publicar Trusted", "Aplicar regras R1–R7", "Publicar Refined"]
ENTRADA_SENSOR = ["Gerar leituras simuladas", "Validar dados de entrada", "Aguardar trava de escrita", "Persistir Raw"]

# Fluxo esperado (modelo de referência) por gatilho, apenas para comparação com o observado.
ESPERADO = {
    "execucao_continua": ["Entrada recebida", *ENTRADA_SENSOR, *NUCLEO, "Execução concluída"],
    "api_simular": ["Entrada recebida", "Validar requisição", *ENTRADA_SENSOR, *NUCLEO, "Resposta entregue", "Execução concluída"],
    "api_importar_observacoes": ["Entrada recebida", "Validar requisição", "Validar dados de entrada", "Aguardar trava de escrita",
                                 "Persistir Raw", *NUCLEO, "Resposta entregue", "Execução concluída"],
    "cli_processar": ["Entrada recebida", *NUCLEO, "Execução concluída"],
    "cli_importar_sensores": ["Entrada recebida", "Validar dados de entrada", "Persistir Raw", *NUCLEO, "Execução concluída"],
}


def carregar(caminhos) -> list[dict]:
    eventos = []
    for caminho in caminhos:
        with Path(caminho).open(newline="", encoding="utf-8") as f:
            eventos.extend(csv.DictReader(f))
    return eventos


def _ts(texto: str) -> datetime:
    return datetime.fromisoformat(texto)


def validar(eventos: list[dict]) -> list[str]:
    problemas: list[str] = []
    ids = Counter(e.get("event_id") for e in eventos)
    for event_id, n in ids.items():
        if n > 1:
            problemas.append(f"event_id duplicado: {event_id} ({n}x)")
    casos: dict[str, list[dict]] = defaultdict(list)
    for i, e in enumerate(eventos, start=2):
        faltando = [c for c in OBRIGATORIAS if not str(e.get(c, "")).strip()]
        if faltando:
            problemas.append(f"linha {i}: campos vazios {faltando}")
            continue
        try:
            t = _ts(e["timestamp"])
            if t.utcoffset() is None or t.utcoffset().total_seconds() != 0:
                problemas.append(f"linha {i}: timestamp sem fuso UTC explícito")
                continue
        except ValueError:
            problemas.append(f"linha {i}: timestamp inválido")
            continue
        if e["lifecycle"] not in ("start", "complete"):
            problemas.append(f"linha {i}: lifecycle inválido {e['lifecycle']}")
        try:
            int(e["sequence"])
        except ValueError:
            problemas.append(f"linha {i}: sequence não inteiro")
            continue
        casos[e["case_id"]].append(e)
    for case_id, lista in casos.items():
        lista.sort(key=lambda e: int(e["sequence"]))
        seqs = [int(e["sequence"]) for e in lista]
        if seqs != list(range(1, len(lista) + 1)):
            problemas.append(f"{case_id}: sequence não contígua {seqs[:5]}…")
        tempos = [_ts(e["timestamp"]) for e in lista]
        if tempos != sorted(tempos):
            problemas.append(f"{case_id}: timestamps fora da ordem de sequence")
        terminais = [e for e in lista if e["activity"] in TERMINAIS]
        if len(terminais) != 1 or lista[-1]["activity"] not in TERMINAIS:
            problemas.append(f"{case_id}: caso sem evento terminal único no final")
        abertos: Counter = Counter()
        for e in lista:
            if e["lifecycle"] == "start":
                abertos[e["activity"]] += 1
            elif e.get("duration_ms"):
                if abertos[e["activity"]] <= 0:
                    problemas.append(f"{case_id}: complete com duração sem start ({e['activity']})")
                abertos[e["activity"]] -= 1
        pendentes = [a for a, n in abertos.items() if n > 0]
        if pendentes:
            problemas.append(f"{case_id}: start sem complete {pendentes}")
    return problemas


def _percentil(valores: list[float], p: float) -> float:
    """Percentil por posto mais próximo (nearest-rank); declarado no relatório."""
    ordenados = sorted(valores)
    k = max(1, math.ceil(p / 100 * len(ordenados)))
    return ordenados[k - 1]


def _estat(valores: list[float]) -> dict:
    if not valores:
        return {"n": 0}
    return {"n": len(valores), "media": round(statistics.fmean(valores), 3), "mediana": round(statistics.median(valores), 3),
            "p95": round(_percentil(valores, 95), 3), "max": round(max(valores), 3), "soma": round(sum(valores), 3)}


def _pearson(xs: list[float], ys: list[float]):
    if len(xs) < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    return round(statistics.correlation(xs, ys), 3)


def _inclinacao(xs: list[float], ys: list[float]):
    if len(xs) < 3 or len(set(xs)) < 2:
        return None
    return round(statistics.linear_regression(xs, ys).slope, 6)


def analisar(eventos: list[dict]) -> dict:
    casos: dict[str, list[dict]] = defaultdict(list)
    for e in eventos:
        casos[e["case_id"]].append(e)
    for lista in casos.values():
        lista.sort(key=lambda e: int(e["sequence"]))

    variantes: Counter = Counter()
    exemplos: dict = {}
    por_caso = []
    duracoes_atividade: dict[str, list[float]] = defaultdict(list)
    dfg: Counter = Counter()
    dfg_gap: dict = defaultdict(list)
    trusted_xy: list[tuple[float, float]] = []
    for case_id, lista in casos.items():
        completos = [e for e in lista if e["lifecycle"] == "complete"]
        trace = tuple(e["activity"] for e in completos)
        variantes[trace] += 1
        exemplos.setdefault(trace, case_id)
        for a, b in zip(completos, completos[1:], strict=False):
            dfg[(a["activity"], b["activity"])] += 1
            dfg_gap[(a["activity"], b["activity"])].append((_ts(b["timestamp"]) - _ts(a["timestamp"])).total_seconds() * 1000)
        medido = 0.0
        for e in completos:
            if e.get("duration_ms"):
                d = float(e["duration_ms"])
                duracoes_atividade[e["activity"]].append(d)
                medido += d
                if e["activity"] == "Publicar Trusted" and e.get("records_in"):
                    trusted_xy.append((float(e["records_in"]), d))
        inicio, fim = _ts(lista[0]["timestamp"]), _ts(lista[-1]["timestamp"])
        e2e = (fim - inicio).total_seconds() * 1000
        gatilho = lista[0].get("trigger", "")
        esperado = ESPERADO.get(gatilho)
        por_caso.append({
            "case_id": case_id, "trigger": gatilho, "resultado": lista[-1]["activity"], "eventos": len(lista),
            "inicio_utc": lista[0]["timestamp"], "fim_utc": lista[-1]["timestamp"],
            "duracao_ponta_a_ponta_ms": round(e2e, 3), "duracao_medida_atividades_ms": round(medido, 3),
            "tempo_nao_atribuido_ms": round(e2e - medido, 3),
            "conforme_fluxo_esperado": None if esperado is None else list(trace) == esperado,
            "variante": " → ".join(trace),
        })

    por_gatilho = {}
    for gatilho in sorted({c["trigger"] for c in por_caso}):
        cs = [c for c in por_caso if c["trigger"] == gatilho]
        conformes = [c["conforme_fluxo_esperado"] for c in cs if c["conforme_fluxo_esperado"] is not None]
        por_gatilho[gatilho] = {
            "casos": len(cs),
            "resultados": dict(Counter(c["resultado"] for c in cs)),
            "duracao_ponta_a_ponta_ms": _estat([c["duracao_ponta_a_ponta_ms"] for c in cs]),
            "conformes_ao_esperado": None if not conformes else f"{sum(conformes)}/{len(conformes)}",
        }

    atividades = {a: _estat(v) for a, v in duracoes_atividade.items()}
    total_medido = sum(sum(v) for v in duracoes_atividade.values()) or 1.0
    participacao = sorted(((a, round(100 * sum(v) / total_medido, 1)) for a, v in duracoes_atividade.items()),
                          key=lambda x: -x[1])
    xs, ys = [x for x, _ in trusted_xy], [y for _, y in trusted_xy]
    concluidos = [c for c in por_caso if c["resultado"] == "Execução concluída"]
    return {
        "resumo": {
            "eventos": len(eventos), "casos": len(casos), "variantes": len(variantes),
            "resultados": dict(Counter(c["resultado"] for c in por_caso)),
            "inicio_utc": min((e["timestamp"] for e in eventos), default=None),
            "fim_utc": max((e["timestamp"] for e in eventos), default=None),
            "duracao_ponta_a_ponta_ms_concluidos": _estat([c["duracao_ponta_a_ponta_ms"] for c in concluidos]),
        },
        "por_gatilho": por_gatilho,
        "variantes": [{"casos": n, "percentual": round(100 * n / len(casos), 1), "atividades": list(v), "exemplo_case_id": exemplos[v]}
                      for v, n in variantes.most_common()],
        "atividades": atividades,
        "participacao_no_tempo_medido_pct": participacao,
        "dfg": [{"de": a, "para": b, "contagem": n, "intervalo_medio_ms": round(statistics.fmean(dfg_gap[(a, b)]), 3)}
                for (a, b), n in dfg.most_common()],
        "crescimento_publicar_trusted": {
            "n": len(trusted_xy), "registros_min": min(xs, default=None), "registros_max": max(xs, default=None),
            "pearson_r": _pearson(xs, ys), "ms_por_registro": _inclinacao(xs, ys),
        },
        "casos": por_caso,
    }


def _mermaid(resultado: dict, minimo: int = 1) -> str:
    nomes: dict[str, str] = {}

    def no(nome: str) -> str:
        if nome not in nomes:
            nomes[nome] = f"A{len(nomes)}"
        return nomes[nome]

    linhas = ["flowchart TD"]
    arestas = []
    for t in resultado["dfg"]:
        if t["contagem"] >= minimo:
            arestas.append(f"  {no(t['de'])} -->|{t['contagem']}| {no(t['para'])}")
    for nome, ident in nomes.items():
        n = resultado["atividades"].get(nome, {})
        rotulo = nome if not n.get("n") else f"{nome}<br/>mediana {n['mediana']:.2f} ms"
        forma = f'(["{rotulo}"])' if nome in TERMINAIS or nome == "Entrada recebida" else f'["{rotulo}"]'
        linhas.append(f"  {ident}{forma}")
    linhas.extend(arestas)
    return "\n".join(linhas) + "\n"


def _markdown(resultado: dict, fontes: list[str]) -> str:
    r = resultado["resumo"]
    md = ["# Resultado da análise do event log (gerado automaticamente)", "",
          f"Fontes: {', '.join(fontes)}  ", f"Janela: {r['inicio_utc']} → {r['fim_utc']} (UTC)  ",
          f"Eventos: {r['eventos']} · Casos: {r['casos']} · Variantes: {r['variantes']}  ",
          f"Resultados: {r['resultados']}", "",
          "Percentis por posto mais próximo; durações de atividade medidas com relógio monotônico; ponta a ponta = último − primeiro timestamp do caso.", "",
          "## Por gatilho", "", "| Gatilho | Casos | Resultados | Ponta a ponta mediana (ms) | p95 (ms) | Conformes ao esperado |", "|---|---:|---|---:|---:|---|"]
    for g, d in resultado["por_gatilho"].items():
        e = d["duracao_ponta_a_ponta_ms"]
        md.append(f"| {g} | {d['casos']} | {d['resultados']} | {e.get('mediana', '—')} | {e.get('p95', '—')} | {d['conformes_ao_esperado'] or '—'} |")
    md += ["", "## Variantes", "", "| # | Casos | % | Sequência de atividades |", "|---:|---:|---:|---|"]
    for i, v in enumerate(resultado["variantes"], start=1):
        md.append(f"| {i} | {v['casos']} | {v['percentual']} | {' → '.join(v['atividades'])} |")
    md += ["", "## Atividades com duração medida", "", "| Atividade | n | Média (ms) | Mediana (ms) | p95 (ms) | Máx (ms) | % do tempo medido |", "|---|---:|---:|---:|---:|---:|---:|"]
    part = dict(resultado["participacao_no_tempo_medido_pct"])
    for a, s in sorted(resultado["atividades"].items(), key=lambda x: -x[1].get("soma", 0)):
        md.append(f"| {a} | {s['n']} | {s['media']} | {s['mediana']} | {s['p95']} | {s['max']} | {part.get(a, 0)} |")
    c = resultado["crescimento_publicar_trusted"]
    md += ["", "## Publicar Trusted × tamanho do Raw", "",
           f"n={c['n']}; registros de {c['registros_min']} a {c['registros_max']}; r de Pearson={c['pearson_r']}; inclinação={c['ms_por_registro']} ms/registro.", "",
           "## Grafo diretamente-segue (observado)", "", "| De | Para | Contagem | Intervalo médio (ms) |", "|---|---|---:|---:|"]
    for t in resultado["dfg"]:
        md.append(f"| {t['de']} | {t['para']} | {t['contagem']} | {t['intervalo_medio_ms']} |")
    return "\n".join(md) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("arquivos", nargs="+", type=Path)
    ap.add_argument("--saida", type=Path, default=Path("resultado_analise"))
    args = ap.parse_args()
    eventos = carregar(args.arquivos)
    problemas = validar(eventos)
    resultado = analisar(eventos)
    resultado["validacao"] = {"problemas": problemas, "aprovado": not problemas}
    args.saida.mkdir(parents=True, exist_ok=True)
    (args.saida / "metricas_processo.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.saida / "metricas_processo.md").write_text(_markdown(resultado, [p.name for p in args.arquivos]), encoding="utf-8")
    (args.saida / "processo_observado.mmd").write_text(_mermaid(resultado), encoding="utf-8")
    with (args.saida / "casos.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(resultado["casos"][0].keys()) if resultado["casos"] else ["case_id"])
        w.writeheader()
        w.writerows(resultado["casos"])
    print(json.dumps({"eventos": len(eventos), "casos": resultado["resumo"]["casos"], "variantes": resultado["resumo"]["variantes"],
                      "validacao_aprovada": not problemas, "problemas": problemas[:10]}, ensure_ascii=False))
    raise SystemExit(0 if not problemas else 1)


if __name__ == "__main__":
    main()
