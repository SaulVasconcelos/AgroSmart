"""Apoio aos testes da Fase 7: cópia isolada da amostra e leitura do event log."""
import csv
import shutil
import tempfile
from pathlib import Path
from unittest import mock

from agrosmart import pipeline as p
from agrosmart import rastreio

PLATAFORMA = Path(__file__).resolve().parents[1]


class DadosIsolados:
    """Copia data/ para pasta temporária e redireciona o pipeline (como test_consultas)."""

    def __init__(self, testcase, copiar_amostra=True):
        self.tmp = tempfile.TemporaryDirectory()
        testcase.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "data"
        if copiar_amostra:
            # Só as camadas da amostra: uma execução nativa anterior pode ter deixado logs,
            # event log e histórico de ciclos em data/, que não pertencem à amostra.
            shutil.copytree(PLATAFORMA / "data", self.root, ignore=shutil.ignore_patterns("logs", "processos", "operacao"))
        else:
            self.root.mkdir(parents=True)
        patch = mock.patch.multiple(p, DATA_DIR=self.root, RAW=self.root / "raw",
                                    TRUSTED=self.root / "trusted", REFINED=self.root / "refined")
        patch.start()
        testcase.addCleanup(patch.stop)


def ler_event_log() -> list[dict]:
    caminho = rastreio.caminho_event_log()
    if not caminho.exists():
        return []
    with caminho.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def por_caso(eventos: list[dict]) -> dict[str, list[dict]]:
    casos: dict[str, list[dict]] = {}
    for e in eventos:
        casos.setdefault(e["case_id"], []).append(e)
    for lista in casos.values():
        lista.sort(key=lambda e: int(e["sequence"]))
    return casos
