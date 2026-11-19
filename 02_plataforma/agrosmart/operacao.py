"""Execução contínua controlada e estado de operação (Fase 7).

Decisão de concorrência: uma ÚNICA autoridade de escrita. O worker roda como
thread DENTRO do processo do servidor e usa a mesma trava (RLock) das rotas
POST; nenhum outro processo escreve nos JSONL/CSV enquanto o servidor está no ar.
O RLock não sincroniza processos: não rode `main.py simular/processar` em paralelo
com o servidor sobre a mesma pasta de dados.

O intervalo é o tempo entre o FIM de um ciclo e o INÍCIO do próximo (sem
sobreposição por construção: um único laço). É parâmetro de demonstração, não
frequência de sensor físico.
"""
from __future__ import annotations

import json
import logging
import os
import random
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from . import pipeline
from .rastreio import Caso
from .simulador import TALHOES, gerar_leitura

INTERVALO_MIN_S, INTERVALO_MAX_S = 5.0, 3600.0
EVENTOS_MIN, EVENTOS_MAX = 1, 8
CICLOS_MAX_BYTES = 5 * 1024 * 1024

_log = logging.getLogger("agrosmart.operacao")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def validar_parametros(intervalo_s=None, eventos_por_ciclo=None) -> tuple[float | None, int | None]:
    if intervalo_s is not None:
        if isinstance(intervalo_s, bool):
            raise ValueError("intervalo_s inválido")
        try:
            intervalo_s = float(intervalo_s)
        except (TypeError, ValueError) as exc:
            raise ValueError("intervalo_s deve ser numérico") from exc
        if not INTERVALO_MIN_S <= intervalo_s <= INTERVALO_MAX_S:
            raise ValueError(f"intervalo_s entre {INTERVALO_MIN_S:g} e {INTERVALO_MAX_S:g} segundos")
    if eventos_por_ciclo is not None:
        if isinstance(eventos_por_ciclo, bool) or not isinstance(eventos_por_ciclo, int):
            raise ValueError("eventos_por_ciclo deve ser inteiro")
        if not EVENTOS_MIN <= eventos_por_ciclo <= EVENTOS_MAX:
            raise ValueError(f"eventos_por_ciclo entre {EVENTOS_MIN} e {EVENTOS_MAX}")
    return intervalo_s, eventos_por_ciclo


class ExecucaoContinua:
    def __init__(self, trava, intervalo_s: float = 30.0, eventos_por_ciclo: int = 3,
                 max_falhas_consecutivas: int = 5, limite_leituras: int = 10_000,
                 max_ciclos: int | None = None):
        self.trava = trava
        self.intervalo_s = float(intervalo_s)
        self.eventos_por_ciclo = int(eventos_por_ciclo)
        self.max_falhas_consecutivas = int(max_falhas_consecutivas)
        self.limite_leituras = int(limite_leituras)
        self.max_ciclos = max_ciclos
        self._rng = random.Random()  # simulação didática; não é uso criptográfico
        self._parar = threading.Event()
        self._thread: threading.Thread | None = None
        self._estado_lock = threading.Lock()
        self.estado = "nunca_iniciada"
        self.motivo_parada = ""
        self.iniciada_em_utc = ""
        self.ciclos_total = 0
        self.ciclos_sucesso = 0
        self.falhas_total = 0
        self.falhas_consecutivas = 0
        self.ultimo_ciclo: dict | None = None
        self.ultimo_sucesso_utc = ""
        self._ultimo_sucesso_mono: float | None = None
        self.historico: deque = deque(maxlen=20)
        self._proximo_talhao = 0

    # ------------------------------------------------------------------ controle
    @property
    def ativa(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._parar.is_set()

    def iniciar(self, intervalo_s=None, eventos_por_ciclo=None) -> dict:
        intervalo_s, eventos_por_ciclo = validar_parametros(intervalo_s, eventos_por_ciclo)
        with self._estado_lock:
            if intervalo_s is not None:
                self.intervalo_s = intervalo_s
            if eventos_por_ciclo is not None:
                self.eventos_por_ciclo = eventos_por_ciclo
            if self.ativa:
                _log.info("execucao_continua ja ativa intervalo_s=%s eventos_por_ciclo=%s", self.intervalo_s, self.eventos_por_ciclo)
                return self.status()
            if self._thread is not None:
                self._thread.join(timeout=5)
            self._parar = threading.Event()
            self.estado, self.motivo_parada, self.iniciada_em_utc = "ativa", "", _utc()
            self.falhas_consecutivas = 0
            self._thread = threading.Thread(target=self._laco, name="agrosmart-execucao-continua", daemon=True)
            self._thread.start()
        _log.info("execucao_continua iniciada intervalo_s=%s eventos_por_ciclo=%s", self.intervalo_s, self.eventos_por_ciclo)
        return self.status()

    def parar(self, motivo: str = "solicitado", aguardar: bool = True, timeout: float = 30.0) -> dict:
        self._parar.set()
        thread = self._thread
        if aguardar and thread is not None and thread is not threading.current_thread():
            thread.join(timeout=timeout)
        with self._estado_lock:
            if self.estado == "ativa":
                self.estado, self.motivo_parada = "parada", motivo
        _log.info("execucao_continua parada motivo=%s ciclos_total=%s", motivo, self.ciclos_total)
        return self.status()

    # ------------------------------------------------------------------- laço
    def _encerrar_por(self, estado: str, motivo: str):
        with self._estado_lock:
            self.estado, self.motivo_parada = estado, motivo
        self._parar.set()
        _log.warning("execucao_continua encerrada estado=%s motivo=%s", estado, motivo)

    def _laco(self):
        while not self._parar.is_set():
            registro = self.executar_ciclo()
            if self.max_ciclos is not None and self.ciclos_total >= self.max_ciclos:
                self._encerrar_por("concluida", f"max_ciclos={self.max_ciclos}")
                break
            if registro["resultado"] == "limite":
                self._encerrar_por("limite_atingido", registro["erro"])
                break
            if self.falhas_consecutivas >= self.max_falhas_consecutivas:
                self._encerrar_por("interrompida_por_falhas", f"{self.falhas_consecutivas} falhas consecutivas")
                break
            self._parar.wait(self.intervalo_s)

    def _talhoes_do_ciclo(self) -> list[str]:
        nomes = list(TALHOES)
        escolhidos = []
        for _ in range(self.eventos_por_ciclo):
            escolhidos.append(nomes[self._proximo_talhao % len(nomes)])
            self._proximo_talhao += 1
        return escolhidos

    def executar_ciclo(self) -> dict:
        """Um ciclo completo: gerar → validar → persistir Raw → processar camadas."""
        numero = self.ciclos_total + 1
        caso = Caso("execucao_continua", "operacao")
        inicio_utc, t0 = _utc(), time.perf_counter()
        registro = {"ciclo": numero, "case_id": caso.case_id, "inicio_utc": inicio_utc, "fim_utc": "",
                    "duracao_ms": None, "resultado": "", "recebidos": 0, "aceitos": 0,
                    "duplicados": 0, "rejeitados": 0, "raw_total": None, "erro": ""}
        caso.registrar("Entrada recebida", component="operacao", records_in=self.eventos_por_ciclo,
                       detail=f"ciclo {numero}; intervalo {self.intervalo_s:g}s")
        try:
            antes = pipeline._estado_anterior()
            if int(antes.get("raw_sensores", 0) or 0) >= self.limite_leituras:
                registro["resultado"] = "limite"
                registro["erro"] = f"limite de {self.limite_leituras} leituras Raw atingido"
                caso.concluir("rejeitado", registro["erro"])
            else:
                with caso.atividade("Gerar leituras simuladas", "simulador") as info:
                    eventos = [gerar_leitura(t, datetime.now(), self._rng) for t in self._talhoes_do_ciclo()]
                    info["records_out"] = len(eventos)
                registro["recebidos"] = len(eventos)
                with caso.atividade("Validar dados de entrada", "pipeline") as info:
                    for e in eventos:
                        pipeline.validar_sensor(e)
                    info["records_in"] = info["records_out"] = len(eventos)
                with caso.atividade("Aguardar trava de escrita", "operacao"):
                    self.trava.acquire()
                try:
                    antes = pipeline._estado_anterior()
                    with caso.atividade("Persistir Raw", "pipeline") as info:
                        for e in eventos:
                            pipeline.adicionar_evento(e, origem="execucao_continua")
                        info["records_out"] = len(eventos)
                    estado = pipeline.processar(caso=caso)
                finally:
                    self.trava.release()
                registro["aceitos"] = estado["trusted_sensores"] - int(antes.get("trusted_sensores", 0) or 0)
                registro["duplicados"] = estado["duplicados_removidos"] - int(antes.get("duplicados_removidos", 0) or 0)
                registro["rejeitados"] = estado["rejeitados"] - int(antes.get("rejeitados", 0) or 0)
                registro["raw_total"] = estado["raw_sensores"]
                registro["resultado"] = "sucesso"
                caso.concluir("sucesso")
        except Exception as exc:  # política: o laço sobrevive a erro controlado e contabiliza a falha
            registro["resultado"] = "falha"
            registro["erro"] = f"{type(exc).__name__}: {str(exc)[:120]}"
            if caso.resultado is None:
                caso.concluir("falha", type(exc).__name__)
            _log.error("ciclo=%s case_id=%s resultado=falha erro=%s", numero, caso.case_id, registro["erro"])
        registro["fim_utc"] = _utc()
        registro["duracao_ms"] = round((time.perf_counter() - t0) * 1000, 3)
        with self._estado_lock:
            self.ciclos_total = numero
            if registro["resultado"] == "sucesso":
                self.ciclos_sucesso += 1
                self.falhas_consecutivas = 0
                self.ultimo_sucesso_utc = registro["fim_utc"]
                self._ultimo_sucesso_mono = time.monotonic()
            elif registro["resultado"] == "falha":
                self.falhas_total += 1
                self.falhas_consecutivas += 1
            self.ultimo_ciclo = registro
            self.historico.append(registro)
        self._persistir(registro)
        if registro["resultado"] == "sucesso":
            _log.info("ciclo=%s case_id=%s resultado=sucesso duracao_ms=%s recebidos=%s aceitos=%s duplicados=%s rejeitados=%s raw_total=%s",
                      numero, caso.case_id, registro["duracao_ms"], registro["recebidos"], registro["aceitos"],
                      registro["duplicados"], registro["rejeitados"], registro["raw_total"])
        return registro

    def _persistir(self, registro: dict):
        caminho = Path(pipeline.DATA_DIR) / "operacao" / "ciclos.jsonl"
        try:
            caminho.parent.mkdir(parents=True, exist_ok=True)
            if caminho.exists() and caminho.stat().st_size > CICLOS_MAX_BYTES:
                os.replace(caminho, caminho.with_name("ciclos.1.jsonl"))
            with caminho.open("a", encoding="utf-8") as f:
                f.write(json.dumps(registro, ensure_ascii=False) + "\n")
        except OSError as exc:
            _log.warning("falha ao gravar historico de ciclos: %s", type(exc).__name__)

    # ----------------------------------------------------------------- status
    def status(self) -> dict:
        with self._estado_lock:
            idade_sucesso = None if self._ultimo_sucesso_mono is None else round(time.monotonic() - self._ultimo_sucesso_mono, 1)
            return {
                "ativa": self.ativa,
                "estado": "ativa" if self.ativa else self.estado,
                "motivo_parada": self.motivo_parada,
                "iniciada_em_utc": self.iniciada_em_utc,
                "intervalo_s": self.intervalo_s,
                "eventos_por_ciclo": self.eventos_por_ciclo,
                "ciclos_total": self.ciclos_total,
                "ciclos_sucesso": self.ciclos_sucesso,
                "falhas_total": self.falhas_total,
                "falhas_consecutivas": self.falhas_consecutivas,
                "max_falhas_consecutivas": self.max_falhas_consecutivas,
                "limite_leituras": self.limite_leituras,
                "ultimo_ciclo": dict(self.ultimo_ciclo) if self.ultimo_ciclo else None,
                "ultimo_sucesso_utc": self.ultimo_sucesso_utc,
                "segundos_desde_ultimo_sucesso": idade_sucesso,
                "historico": [dict(r) for r in reversed(self.historico)],
            }


def resumo_dados() -> dict:
    """Idade e volume do dado publicado, lidos do Refined (sem caminhos internos)."""
    linhas = pipeline.carregar_refinado()
    estado = pipeline._estado_anterior()
    agora = datetime.now()  # mesmo relógio local (naive) usado por gerar_leitura
    ultimos: dict[str, str] = {}
    for r in linhas:
        ultimos[r["talhao"]] = r["data_hora"]

    def idade(texto: str | None):
        if not texto:
            return None
        try:
            return round((agora - datetime.fromisoformat(texto)).total_seconds(), 1)
        except ValueError:
            return None

    ultimo = max(ultimos.values()) if ultimos else None
    return {
        "ultimo_registro": ultimo,
        "idade_ultimo_registro_s": idade(ultimo),
        "por_talhao": [{"talhao": t, "ultima_leitura": v, "idade_s": idade(v)} for t, v in sorted(ultimos.items())],
        "raw_sensores": estado.get("raw_sensores"),
        "trusted_sensores": estado.get("trusted_sensores"),
        "duplicados_removidos": estado.get("duplicados_removidos"),
        "rejeitados": estado.get("rejeitados"),
        "alertas": estado.get("alertas"),
        "relogio_local": agora.isoformat(timespec="seconds"),
        "fuso_utc_offset": time.strftime("%z"),
    }


def verificar_prontidao() -> dict:
    pasta = Path(pipeline.DATA_DIR)
    refinado = pipeline.REFINED / "monitoramento.csv"
    checks = {
        "pasta_dados_gravavel": pasta.is_dir() and os.access(pasta, os.W_OK),
        "refined_disponivel": refinado.is_file() and os.access(refinado, os.R_OK),
    }
    return {"pronto": all(checks.values()), "verificacoes": checks}
