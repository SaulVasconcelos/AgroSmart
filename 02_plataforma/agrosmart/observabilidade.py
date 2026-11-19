"""Logs da aplicação e métricas simples de funcionamento (Fase 7).

Formato texto chave=valor, uma linha por evento, em stdout (visível em
`docker compose logs`) e em arquivo com rotação por tamanho dentro do volume
de dados (<dados>/logs/agrosmart.log). Sem caminhos internos ou stack traces
na interface; detalhes técnicos ficam no log.
"""
from __future__ import annotations

import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_MAX_BYTES = int(os.environ.get("AGROSMART_LOG_MAX_BYTES", str(2 * 1024 * 1024)))
LOG_BACKUPS = int(os.environ.get("AGROSMART_LOG_BACKUPS", "5"))


class FormatoChaveValor(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        instante = datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds")
        base = f"{instante} {record.levelname:<7} {record.name.removeprefix('agrosmart.') or 'agrosmart'} {record.getMessage()}"
        if record.exc_info:
            base += " | " + self.formatException(record.exc_info).replace("\n", " | ")
        return base


_configurado = False
_trava = threading.Lock()


def configurar_logs(pasta_dados: Path | None = None, nivel: str | None = None) -> Path | None:
    """Idempotente. Retorna o caminho do arquivo de log (ou None se só stdout)."""
    global _configurado
    with _trava:
        raiz = logging.getLogger("agrosmart")
        if _configurado:
            return getattr(raiz, "_arquivo_log", None)
        raiz.setLevel(getattr(logging, (nivel or os.environ.get("AGROSMART_LOG_NIVEL", "INFO")).upper(), logging.INFO))
        raiz.propagate = False
        formato = FormatoChaveValor()
        saida = logging.StreamHandler(sys.stdout)
        saida.setFormatter(formato)
        raiz.addHandler(saida)
        arquivo = None
        if pasta_dados is not None:
            try:
                (pasta_dados / "logs").mkdir(parents=True, exist_ok=True)
                arquivo = pasta_dados / "logs" / "agrosmart.log"
                rot = RotatingFileHandler(arquivo, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUPS, encoding="utf-8")
                rot.setFormatter(formato)
                raiz.addHandler(rot)
            except OSError as exc:
                raiz.warning("log em arquivo indisponivel motivo=%s", type(exc).__name__)
                arquivo = None
        raiz._arquivo_log = arquivo  # type: ignore[attr-defined]
        _configurado = True
        return arquivo


class MetricasHTTP:
    """Contadores de requisições por classe de status, desde o início do processo."""

    def __init__(self):
        self._trava = threading.Lock()
        self.iniciado_em_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._t0 = time.monotonic()
        self.total = 0
        self.por_classe = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}

    def registrar(self, codigo) -> None:
        try:
            classe = f"{int(codigo) // 100}xx"
        except (TypeError, ValueError):
            return
        with self._trava:
            self.total += 1
            if classe in self.por_classe:
                self.por_classe[classe] += 1

    def uptime_s(self) -> float:
        return round(time.monotonic() - self._t0, 1)

    def resumo(self) -> dict:
        with self._trava:
            return {"total": self.total, **self.por_classe}
