"""Consultas locais somente de leitura. Não classifica nem grava dados."""
from __future__ import annotations

import re
from collections import Counter
from datetime import date, datetime

from .pipeline import carregar_refinado, estado_dashboard
from .simulador import TALHOES

SEVERIDADES = ("Crítica", "Alta", "Média")
PRIORIDADE = {nome: indice for indice, nome in enumerate(SEVERIDADES)}


def validar_filtros(talhao: str = "", inicio: str = "", fim: str = ""):
    if talhao and talhao not in TALHOES:
        raise ValueError("Talhão não cadastrado")
    for nome, valor in (("inicio", inicio), ("fim", fim)):
        if valor:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
                raise ValueError(f"{nome}: use data no formato AAAA-MM-DD")
            try:
                date.fromisoformat(valor)
            except ValueError as error:
                raise ValueError(f"{nome}: data inválida") from error
    if inicio and fim and inicio > fim:
        raise ValueError("A data inicial deve ser anterior ou igual à data final")


def filtrar_monitoramento(talhao: str = "", inicio: str = "", fim: str = "") -> list[dict]:
    validar_filtros(talhao, inicio, fim)
    return [r for r in carregar_refinado()
            if (not talhao or r["talhao"] == talhao)
            and (not inicio or r["data_hora"][:10] >= inicio)
            and (not fim or r["data_hora"][:10] <= fim)]


def consultar_alertas(talhao: str = "", inicio: str = "", fim: str = "",
                     severidade: str = "", ordem: str = "prioridade",
                     pagina: int = 1, tamanho: int = 20) -> dict:
    if severidade and severidade not in SEVERIDADES:
        raise ValueError("Severidade deve ser Crítica, Alta ou Média")
    if ordem not in ("prioridade", "recencia"):
        raise ValueError("Ordenação deve ser prioridade ou recencia")
    if isinstance(pagina, bool) or not isinstance(pagina, int) or not 1 <= pagina <= 1_000_000:
        raise ValueError("Página deve ser um inteiro entre 1 e 1000000")
    if isinstance(tamanho, bool) or not isinstance(tamanho, int) or not 1 <= tamanho <= 100:
        raise ValueError("Tamanho de página deve ser um inteiro entre 1 e 100")
    rows = [r for r in filtrar_monitoramento(talhao, inicio, fim) if r["regra"] not in ("R7", "ND")]
    if severidade:
        rows = [r for r in rows if r["severidade"] == severidade]
    # Chave estável para empates; severidade é aplicada depois da recência.
    rows.sort(key=lambda r: (r["data_hora"], r["talhao"], r["sensor_id"]), reverse=True)
    if ordem == "prioridade":
        rows.sort(key=lambda r: PRIORIDADE.get(r["severidade"], len(PRIORIDADE)))
    total = len(rows)
    paginas = max(1, (total + tamanho - 1) // tamanho)
    # Contextos podem perder páginas após reprocessar; devolve a última válida.
    efetiva = min(pagina, paginas)
    offset = (efetiva - 1) * tamanho
    items = rows[offset:offset + tamanho]
    return {"itens": items, "total": total, "pagina": efetiva, "paginas": paginas,
            "tamanho": tamanho, "inicio_exibido": offset + 1 if items else 0,
            "fim_exibido": offset + len(items),
            "severidades": dict(Counter(r["severidade"] for r in rows)),
            "filtros": {"talhao": talhao, "inicio": inicio, "fim": fim,
                        "severidade": severidade, "ordem": ordem},
            "escopo": "Ocorrências históricas R1–R6; sem registro de resolução"}


def consultar_talhao(talhao: str, inicio: str = "", fim: str = "",
                    data_hora: str = "", sensor_id: str = "") -> dict:
    if not talhao:
        raise ValueError("Selecione um talhão")
    rows = filtrar_monitoramento(talhao, inicio, fim)
    selected = None
    if bool(data_hora) != bool(sensor_id):
        raise ValueError("Informe data_hora e sensor_id juntos para identificar a leitura")
    if data_hora:
        try:
            datetime.fromisoformat(data_hora.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("Data/hora da leitura inválida") from error
        selected = next((r for r in rows if r["data_hora"] == data_hora and r["sensor_id"] == sensor_id), None)
        if selected is None:
            raise LookupError("Leitura selecionada não encontrada neste talhão e período")
    state = estado_dashboard(talhao, inicio, fim)
    return {"talhao": talhao, "cultura": TALHOES[talhao],
            "resumo": state["talhoes"][0] if state["talhoes"] else None,
            "ultima_leitura": max(rows, key=lambda r: (r["data_hora"], r["sensor_id"]), default=None),
            "serie": state["serie"], "avaliacoes": dict(Counter(r["avaliacao"] for r in rows)),
            "observacoes_ausentes": sum(r["origem_observacao"] == "Ausente" for r in rows),
            "leitura_selecionada": selected,
            "filtros": {"talhao": talhao, "inicio": inicio, "fim": fim},
            "escopo": "Última leitura no período selecionado; diagnósticos de imagem independentes"}
