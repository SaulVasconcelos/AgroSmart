"""Motor deterministico AgroMonitor R1-R7, fiel ao PDF historico.

Fonte: definicao_logica_decisao_agromonitor.pdf, paginas 3-7.
Dados de observacao ausentes NAO sao inferidos de probabilidade_praga.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Decisao:
    regra: str
    severidade: str
    alerta: str
    acao: str
    justificativa: str
    avaliacao: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def avaliar(sensor: dict[str, Any], campo: dict[str, Any] | None) -> Decisao:
    umidade = float(sensor["umidade_solo"])
    temperatura = float(sensor["temperatura"])
    folhas = None
    dias = None
    praga = None
    if campo is not None:
        folhas = float(campo["percentual_folhas_doentes"])
        dias = int(campo["dias_mesma_praga"])
        praga = str(campo["praga_detectada"]).strip()

    # Ordem de precedencia identica ao documento (R1 -> ... -> R7).
    if folhas is not None and folhas > 30 and dias >= 3 and umidade < 35:
        return Decisao("R1", "Crítica", "Alerta crítico", "Intervenção imediata, controle de praga e irrigação prioritária", "Folhas doentes acima de 30%, praga recorrente e umidade abaixo de 35%.", "Completa")
    if folhas is not None and folhas > 30:
        return Decisao("R2", "Alta", "Alerta de infestação", "Realizar inspeção técnica", "Percentual de folhas doentes superior a 30%.", "Completa")
    if folhas is not None and dias >= 3 and folhas > 20:
        return Decisao("R3", "Alta", "Praga recorrente", "Acionar plano de controle de praga", "Praga persistente por três dias ou mais com folhas doentes acima de 20%.", "Completa")
    if umidade < 35 and temperatura > 30:
        return Decisao("R4", "Alta", "Estresse hídrico", "Priorizar irrigação", "Umidade inferior a 35% e temperatura superior a 30 °C.", "Sensorial; campos opcionais" if campo is None else "Completa")
    if umidade < 35:
        return Decisao("R5", "Média", "Recomendação de irrigação", "Programar irrigação do talhão", "Umidade do solo inferior a 35%.", "Sensorial; campos opcionais" if campo is None else "Completa")
    if folhas is not None and (folhas >= 15 or (praga.casefold() != "nenhuma" and dias < 3)):
        return Decisao("R6", "Média", "Monitoramento preventivo", "Acompanhar evolução do talhão", "Folhas doentes a partir de 15% ou ocorrência recente de praga.", "Completa")
    # R7 so e afirmada se temos todas as variaveis necessarias.
    if campo is None:
        return Decisao("ND", "Indeterminada", "Observação de campo ausente", "Registrar observação de campo para avaliar todas as regras R1–R7", "Sensores não comprovam ausência de infestação.", "Parcial")
    return Decisao("R7", "Baixa", "Situação normal", "Manter monitoramento de rotina", "Nenhuma condição de risco R1–R6 atendida.", "Completa")
