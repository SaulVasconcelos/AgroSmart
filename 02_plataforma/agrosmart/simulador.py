"""Simulacao compatível com o esquema de eventos da Fase 4.

Uma mesma cultura e associada a cada talhao, para permitir chaves coerentes.
Dados estritamente simulados; nenhuma leitura e de dispositivo fisico.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

TALHOES = {"Talhao A": "Soja", "Talhao B": "Milho", "Talhao C": "Cafe"}
SENSORES = {"Talhao A": "S-001", "Talhao B": "S-002", "Talhao C": "S-003"}


def gerar_leitura(talhao: str, instante: datetime, rng: random.Random) -> dict:
    """Preserva nove campos exatos do JSON da Fase 4."""
    if talhao not in TALHOES:
        raise ValueError(f"Talhão não cadastrado: {talhao}")
    umidade = rng.randint(22, 67)
    temperatura = rng.randint(23, 38)
    probabilidade = rng.randint(0, 100)
    alerta, recomendacao = "Normal", "Manter monitoramento."
    if umidade < 30:
        alerta, recomendacao = "Alerta de irrigacao", "Verificar irrigacao do talhao."
    if temperatura > 35 and umidade < 35:
        alerta, recomendacao = "Risco alto", "Priorizar irrigacao e vistoria tecnica."
    if probabilidade > 70:
        alerta, recomendacao = "Alerta de praga", "Realizar inspecao fitossanitaria."
    return {
        "data_hora": instante.isoformat(timespec="microseconds"),
        "sensor_id": SENSORES[talhao],
        "talhao": talhao,
        "cultura": TALHOES[talhao],
        "umidade_solo": umidade,
        "temperatura": temperatura,
        "probabilidade_praga": probabilidade,
        "alerta": alerta,
        "recomendacao": recomendacao,
    }


def simular_historico(inicio: datetime, dias: int = 12, por_dia: int = 4, semente: int = 96) -> list[dict]:
    rng = random.Random(semente)
    eventos = []
    for i in range(dias):
        for j in range(por_dia):
            momento = inicio + timedelta(days=i, hours=6*j)
            for talhao in TALHOES:
                eventos.append(gerar_leitura(talhao, momento, rng))
    return eventos


def simular_campo(inicio: datetime, dias: int = 12) -> list[dict]:
    """Observacoes manuais SIMULADAS. Nunca derivar 'folhas' da chance de praga."""
    padroes = [
        (35.0, "Lagarta", 4), # R1 quando umidade baixa
        (36.0, "Lagarta", 1), # R2
        (25.0, "Lagarta", 4), # R3
        (10.0, "Nenhuma", 0), # R4/R5/R7 dependem do sensor
        (16.0, "Nenhuma", 0), # R6
        (9.0, "Pulgão", 2),  # R6
        (8.0, "Nenhuma", 0), # R7 se sensores normais
        (33.0, "Lagarta", 4), # R1 ou R2
        (22.0, "Pulgão", 3), # R3
        (0.0, "Nenhuma", 0), # R7 se sensores normais
        (14.0, "Nenhuma", 0), # R4/R5/R7
        (20.0, "Pulgão", 1), # R6
    ]
    saida = []
    for d in range(dias):
        for idx, (talhao, cultura) in enumerate(TALHOES.items()):
            folhas, praga, duracao = padroes[(d+idx*3) % len(padroes)]
            saida.append({"data":(inicio + timedelta(days=d)).date().isoformat(),"talhao":talhao,"cultura":cultura,"percentual_folhas_doentes":folhas,"praga_detectada":praga,"dias_mesma_praga":duracao,"origem_dados":"SIMULADO - observacao de campo"})
    return saida
