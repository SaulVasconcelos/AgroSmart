"""Fase 7: event log de execuções reais — ids, correlação, ordem, durações e variantes."""
import importlib.util
import random
import unittest
from datetime import datetime
from pathlib import Path

from agrosmart import pipeline as p
from agrosmart import rastreio
from agrosmart.rastreio import COLUNAS, Caso
from agrosmart.simulador import gerar_leitura

from apoio_fase7 import DadosIsolados, ler_event_log, por_caso

ANALISE = Path(__file__).resolve().parents[2] / "04_processos" / "analisar_event_log.py"


def carregar_analise():
    spec = importlib.util.spec_from_file_location("analisar_event_log", ANALISE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestarEventLog(unittest.TestCase):
    def setUp(self):
        self.dados = DadosIsolados(self)

    def _executar(self, evento, gatilho="teste_fluxo"):
        caso = Caso(gatilho, "teste")
        caso.registrar("Entrada recebida")
        with caso.atividade("Validar dados de entrada", "pipeline"):
            p.validar_sensor(evento)
        with caso.atividade("Persistir Raw", "pipeline"):
            p.adicionar_evento(evento)
        p.processar(caso=caso)
        caso.concluir("sucesso")
        return caso.case_id

    def teste_processar_sem_caso_nao_grava_event_log(self):
        p.processar()
        self.assertFalse(rastreio.caminho_event_log().exists())

    def teste_estrutura_ordem_e_duracoes_de_um_caso(self):
        evento = gerar_leitura("Talhao A", datetime(2026, 11, 18, 9, 0), random.Random(7))
        case_id = self._executar(evento)
        eventos = ler_event_log()
        self.assertEqual(list(eventos[0].keys()), COLUNAS)
        caso = por_caso(eventos)[case_id]
        self.assertEqual([int(e["sequence"]) for e in caso], list(range(1, len(caso) + 1)))
        self.assertEqual(len({e["event_id"] for e in eventos}), len(eventos))
        self.assertEqual(caso[0]["activity"], "Entrada recebida")
        self.assertEqual(caso[-1]["activity"], "Execução concluída")
        timestamps = [datetime.fromisoformat(e["timestamp"]) for e in caso]
        self.assertTrue(all(t.utcoffset().total_seconds() == 0 for t in timestamps))
        self.assertEqual(timestamps, sorted(timestamps))
        completos = [e["activity"] for e in caso if e["lifecycle"] == "complete" and e["duration_ms"]]
        iniciados = [e["activity"] for e in caso if e["lifecycle"] == "start"]
        self.assertEqual(completos, iniciados, "cada start tem exatamente um complete com duração")
        self.assertEqual(iniciados, ["Validar dados de entrada", "Persistir Raw", "Publicar Trusted",
                                     "Aplicar regras R1–R7", "Publicar Refined"])
        self.assertTrue(all(float(e["duration_ms"]) >= 0 for e in caso if e["duration_ms"]))
        trusted = next(e for e in caso if e["activity"] == "Publicar Trusted" and e["lifecycle"] == "complete")
        self.assertEqual((trusted["records_in"], trusted["records_out"]), ("145", "145"))

    def teste_duplicata_gera_variante_observada(self):
        evento = gerar_leitura("Talhao B", datetime(2026, 11, 18, 10, 0), random.Random(8))
        primeiro = self._executar(evento)
        segundo = self._executar(dict(evento))
        casos = por_caso(ler_event_log())
        atividades = lambda c: [e["activity"] for e in casos[c] if e["lifecycle"] == "complete"]  # noqa: E731
        self.assertNotIn("Descartar duplicatas", atividades(primeiro))
        self.assertIn("Descartar duplicatas", atividades(segundo))
        self.assertEqual(p._estado_anterior()["duplicados_removidos"], 1)

    def teste_rejeicao_e_falha_tem_status_tecnico_distinto(self):
        caso = Caso("teste_rejeicao", "teste")
        caso.registrar("Entrada recebida")
        with self.assertRaises(ValueError):
            with caso.atividade("Validar dados de entrada"):
                p.validar_sensor({"sensor_id": "S-001"})
        caso.concluir("rejeitado", "campo ausente")
        falha = Caso("teste_falha", "teste")
        with self.assertRaises(OSError):
            with falha.atividade("Persistir Raw"):
                raise OSError("simulada")
        falha.concluir("falha", "OSError")
        casos = por_caso(ler_event_log())
        rej = casos[caso.case_id]
        self.assertEqual(rej[2]["status"], "rejeitado")
        self.assertEqual(rej[-1]["activity"], "Entrada rejeitada")
        self.assertEqual(casos[falha.case_id][1]["status"], "falha")
        self.assertEqual(casos[falha.case_id][-1]["activity"], "Execução falhou")
        with self.assertRaises(RuntimeError):
            caso.concluir("sucesso")

    def teste_analise_recalcula_metricas_a_partir_do_log(self):
        for i in range(3):
            self._executar(gerar_leitura("Talhao C", datetime(2026, 11, 18, 11, i), random.Random(i)))
        analise = carregar_analise()
        eventos = analise.carregar([rastreio.caminho_event_log()])
        problemas = analise.validar(eventos)
        self.assertEqual(problemas, [])
        resultado = analise.analisar(eventos)
        self.assertEqual(resultado["resumo"]["casos"], 3)
        self.assertEqual(resultado["resumo"]["eventos"], len(eventos))
        self.assertEqual(len(resultado["variantes"]), 1)
        self.assertEqual(resultado["variantes"][0]["casos"], 3)
        dfg = {(t["de"], t["para"]): t["contagem"] for t in resultado["dfg"]}
        self.assertEqual(dfg[("Publicar Trusted", "Aplicar regras R1–R7")], 3)

    def teste_validador_detecta_linhas_invalidas(self):
        analise = carregar_analise()
        base = {"event_id": "X-001", "case_id": "X", "sequence": "1", "activity": "Entrada recebida", "lifecycle": "complete",
                "timestamp": "2026-11-18T10:00:00+00:00", "status": "sucesso", "duration_ms": "", "component": "t",
                "trigger": "t", "records_in": "", "records_out": "", "detail": ""}
        repetido = dict(base)
        sem_fuso = dict(base, event_id="X-002", sequence="2", timestamp="2026-11-18T10:00:01")
        problemas = analise.validar([base, repetido, sem_fuso])
        self.assertTrue(any("duplicado" in pr for pr in problemas))
        self.assertTrue(any("fuso" in pr for pr in problemas))
        self.assertTrue(any("terminal" in pr for pr in problemas))


if __name__ == "__main__":
    unittest.main()
