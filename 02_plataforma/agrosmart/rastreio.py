"""Event log de execuções reais da cadeia AgroSmart (Fase 7).

Contrato NOVO, separado dos schemas agronômicos. Um caso (case_id) é UMA execução
da cadeia disparada por um gatilho real: ciclo da execução contínua, requisição
HTTP ou comando CLI. Uma leitura de sensor NÃO é um evento de atividade; o
timestamp de cada evento é o instante (UTC) em que o software registrou a
atividade, e duration_ms é medido com relógio monotônico (perf_counter).

Colunas: ver COLUNAS e 04_processos/contrato_event_log.md.
"""
from __future__ import annotations

import csv
import logging
import os
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

COLUNAS = ["event_id", "case_id", "sequence", "activity", "lifecycle", "timestamp", "status",
           "duration_ms", "component", "trigger", "records_in", "records_out", "detail"]

TERMINAIS = {"sucesso": "Execução concluída", "rejeitado": "Entrada rejeitada", "falha": "Execução falhou"}

LIMITE_BYTES = int(os.environ.get("AGROSMART_EVENT_LOG_MAX_BYTES", str(20 * 1024 * 1024)))
BACKUPS = 3

_log = logging.getLogger("agrosmart.rastreio")
_TRAVA_ARQUIVO = threading.Lock()
_contadores = {"eventos_gravados": 0, "falhas_gravacao": 0}


def caminho_event_log() -> Path:
    """Resolvido a cada chamada: respeita AGROSMART_DATA_DIR e patches de teste."""
    from . import pipeline as _pipeline  # import tardio evita ciclo pipeline <-> rastreio
    return Path(_pipeline.DATA_DIR) / "processos" / "event_log.csv"


def contadores() -> dict:
    return dict(_contadores)


def _agora_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _rotacionar(caminho: Path):
    """Rotação simples por tamanho: event_log.csv -> .1 -> .2 -> .3 (o mais antigo sai)."""
    if not caminho.exists() or caminho.stat().st_size < LIMITE_BYTES:
        return
    for i in range(BACKUPS - 1, 0, -1):
        origem = caminho.with_name(f"event_log.{i}.csv")
        if origem.exists():
            os.replace(origem, caminho.with_name(f"event_log.{i + 1}.csv"))
    os.replace(caminho, caminho.with_name("event_log.1.csv"))


def _gravar(linha: dict):
    caminho = caminho_event_log()
    try:
        with _TRAVA_ARQUIVO:
            caminho.parent.mkdir(parents=True, exist_ok=True)
            _rotacionar(caminho)
            novo = not caminho.exists() or caminho.stat().st_size == 0
            with caminho.open("a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=COLUNAS)
                if novo:
                    w.writeheader()
                w.writerow(linha)
            _contadores["eventos_gravados"] += 1
    except OSError as exc:
        # A operação agronômica não depende do event log; a falha fica registrada.
        _contadores["falhas_gravacao"] += 1
        _log.warning("falha ao gravar event log: %s", type(exc).__name__)


class Caso:
    """Uma execução da cadeia. Eventos ordenados por sequence dentro do caso."""

    def __init__(self, trigger: str, component: str):
        carimbo = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.case_id = f"RUN-{carimbo}-{uuid.uuid4().hex[:8]}"
        self.trigger = trigger
        self.component = component
        self._seq = 0
        self._lock = threading.Lock()
        self.resultado: str | None = None

    def registrar(self, activity: str, lifecycle: str = "complete", status: str = "sucesso",
                  duration_ms: float | None = None, component: str | None = None,
                  records_in="", records_out="", detail: str = "") -> dict:
        with self._lock:
            self._seq += 1
            seq = self._seq
        linha = {
            "event_id": f"{self.case_id}-{seq:03d}",
            "case_id": self.case_id,
            "sequence": seq,
            "activity": activity,
            "lifecycle": lifecycle,
            "timestamp": _agora_utc(),
            "status": status,
            "duration_ms": "" if duration_ms is None else f"{duration_ms:.3f}",
            "component": component or self.component,
            "trigger": self.trigger,
            "records_in": records_in,
            "records_out": records_out,
            "detail": str(detail).replace("\n", " ")[:160],
        }
        _gravar(linha)
        return linha

    @contextmanager
    def atividade(self, activity: str, component: str | None = None):
        """Registra start/complete e mede a duração. O chamador pode preencher info."""
        info = {"status": "sucesso", "records_in": "", "records_out": "", "detail": ""}
        self.registrar(activity, "start", "iniciado", component=component)
        t0 = time.perf_counter()
        try:
            yield info
        except Exception as exc:
            dur = (time.perf_counter() - t0) * 1000
            rejeicao = isinstance(exc, (ValueError, KeyError))
            self.registrar(activity, "complete", "rejeitado" if rejeicao else "falha", dur, component,
                           info["records_in"], info["records_out"], str(exc) if rejeicao else type(exc).__name__)
            raise
        dur = (time.perf_counter() - t0) * 1000
        self.registrar(activity, "complete", info["status"], dur, component,
                       info["records_in"], info["records_out"], info["detail"])

    def concluir(self, resultado: str = "sucesso", detail: str = "") -> dict:
        if self.resultado is not None:
            raise RuntimeError("Caso já encerrado")
        self.resultado = resultado
        return self.registrar(TERMINAIS[resultado], "complete", resultado, detail=detail)


@contextmanager
def etapa(caso: Caso | None, activity: str, component: str = "pipeline"):
    """Atividade opcional: sem caso, não registra nada (comportamento da Fase 6)."""
    if caso is None:
        yield {"status": "sucesso", "records_in": "", "records_out": "", "detail": ""}
        return
    with caso.atividade(activity, component) as info:
        yield info
