"""Inicialização do volume de dados do container (Fase 7).

A semente (amostra determinística da Fase 6) só é copiada quando a pasta de dados
está REALMENTE vazia. Um volume com qualquer conteúdo é preservado; `demo` nunca
é executado automaticamente.
"""
from __future__ import annotations

import shutil
from pathlib import Path

CAMADAS = ("raw", "trusted", "refined")
IGNORAR = {"lost+found"}


def semear_se_vazio(destino: Path, semente: Path) -> dict:
    destino = Path(destino)
    semente = Path(semente)
    destino.mkdir(parents=True, exist_ok=True)
    existentes = sorted(p.name for p in destino.iterdir() if p.name not in IGNORAR)
    if existentes:
        return {"semeado": False, "motivo": "pasta de dados com conteúdo existente; preservada", "itens": existentes}
    faltando = [c for c in CAMADAS if not (semente / c).is_dir()]
    if faltando:
        return {"semeado": False, "motivo": "semente incompleta: " + ", ".join(faltando), "itens": []}
    for camada in CAMADAS:
        shutil.copytree(semente / camada, destino / camada)
    return {"semeado": True, "motivo": "pasta vazia inicializada com a amostra determinística", "itens": list(CAMADAS)}
