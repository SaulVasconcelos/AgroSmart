"""Fase 7: execução contínua real (vários ciclos), sem sobreposição, falhas e limites."""
import threading
import time
import unittest
from threading import RLock
from unittest import mock

from agrosmart import operacao as op_mod
from agrosmart import pipeline as p
from agrosmart.operacao import ExecucaoContinua, validar_parametros

from apoio_fase7 import DadosIsolados, ler_event_log, por_caso


def aguardar(cond, limite=10.0):
    fim = time.monotonic() + limite
    while time.monotonic() < fim:
        if cond():
            return True
        time.sleep(0.01)
    return False


class TestarExecucaoContinua(unittest.TestCase):
    def setUp(self):
        self.dados = DadosIsolados(self)

    def teste_multiplos_ciclos_reais_sem_sobreposicao(self):
        op = ExecucaoContinua(RLock(), intervalo_s=0.05, eventos_por_ciclo=3, max_ciclos=4)
        op.iniciar()
        self.assertTrue(aguardar(lambda: not op.ativa))
        st = op.status()
        self.assertEqual((st["estado"], st["ciclos_total"], st["ciclos_sucesso"], st["falhas_total"]), ("concluida", 4, 4, 0))
        hist = list(reversed(st["historico"]))  # cronológico
        for anterior, atual in zip(hist, hist[1:], strict=False):
            self.assertGreaterEqual(atual["inicio_utc"], anterior["fim_utc"], "ciclos não podem se sobrepor")
        self.assertTrue(all(r["aceitos"] == 3 and r["duplicados"] == 0 for r in hist))
        estado = p._estado_anterior()
        self.assertEqual((estado["raw_sensores"], estado["trusted_sensores"]), (144 + 12, 144 + 12))
        self.assertEqual(len(p.carregar_refinado()), 156)
        casos = por_caso(ler_event_log())
        self.assertEqual(len(casos), 4)
        self.assertTrue(all(ev[-1]["activity"] == "Execução concluída" for ev in casos.values()))
        self.assertEqual({r["case_id"] for r in hist}, set(casos))
        linhas = (self.dados.root / "operacao" / "ciclos.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(linhas), 4)

    def teste_amostra_historica_preservada_por_registro(self):
        antes = {(r["data_hora"], r["sensor_id"]): r for r in p.carregar_refinado()}
        ExecucaoContinua(RLock(), eventos_por_ciclo=3).executar_ciclo()
        depois = {(r["data_hora"], r["sensor_id"]): r for r in p.carregar_refinado()}
        self.assertEqual(len(depois), len(antes) + 3)
        self.assertTrue(all(depois[k] == v for k, v in antes.items()), "decisões históricas não podem mudar")

    def teste_falha_controlada_e_parada_por_falhas_consecutivas(self):
        op = ExecucaoContinua(RLock(), intervalo_s=0.01, max_falhas_consecutivas=2)
        with mock.patch.object(op_mod.pipeline, "processar", side_effect=OSError("disco indisponível")):
            op.iniciar()
            self.assertTrue(aguardar(lambda: not op.ativa))
        st = op.status()
        self.assertEqual((st["estado"], st["falhas_total"], st["ciclos_sucesso"]), ("interrompida_por_falhas", 2, 0))
        self.assertIn("OSError", st["ultimo_ciclo"]["erro"])
        casos = por_caso(ler_event_log())
        self.assertTrue(all(ev[-1]["activity"] == "Execução falhou" for ev in casos.values()))
        # A trava foi liberada mesmo com falha: um novo ciclo funciona e zera a sequência de falhas.
        self.assertEqual(op.executar_ciclo()["resultado"], "sucesso")
        self.assertEqual(op.status()["falhas_consecutivas"], 0)

    def teste_limite_de_leituras_para_sem_gravar(self):
        op = ExecucaoContinua(RLock(), intervalo_s=0.01, limite_leituras=144)
        op.iniciar()
        self.assertTrue(aguardar(lambda: not op.ativa))
        self.assertEqual(op.status()["estado"], "limite_atingido")
        self.assertEqual(p._estado_anterior()["raw_sensores"], 144)
        ultimo = por_caso(ler_event_log())
        self.assertEqual([e["activity"] for e in next(iter(ultimo.values()))], ["Entrada recebida", "Entrada rejeitada"])

    def teste_parar_interrompe_a_espera_e_reinicia(self):
        op = ExecucaoContinua(RLock(), intervalo_s=30)
        op.iniciar()
        self.assertTrue(aguardar(lambda: op.ciclos_total >= 1))
        t0 = time.monotonic()
        st = op.parar("teste")
        self.assertLess(time.monotonic() - t0, 3)
        self.assertEqual((st["estado"], st["ativa"], st["motivo_parada"]), ("parada", False, "teste"))
        op.iniciar(intervalo_s=5)
        self.assertTrue(op.status()["ativa"])
        self.assertEqual(op.status()["intervalo_s"], 5.0)
        op.parar("fim do teste")

    def teste_worker_e_posts_concorrentes_com_mesma_trava(self):
        trava = RLock()
        op = ExecucaoContinua(trava, intervalo_s=0.01, max_ciclos=6)
        erros = []

        def post_simulado():
            try:
                from agrosmart.rastreio import Caso
                from agrosmart.simulador import gerar_leitura
                import random
                from datetime import datetime
                caso = Caso("teste_concorrencia", "teste")
                with trava:
                    p.adicionar_evento(gerar_leitura("Talhao C", datetime.now(), random.Random()))
                    p.processar(caso=caso)
                caso.concluir("sucesso")
            except Exception as exc:  # pragma: no cover - falha reportada pelo assert
                erros.append(exc)

        op.iniciar()
        threads = [threading.Thread(target=post_simulado) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertTrue(aguardar(lambda: not op.ativa))
        self.assertEqual(erros, [])
        estado = p._estado_anterior()
        self.assertEqual(estado["raw_sensores"], 144 + 6 * 3 + 5)
        self.assertEqual(estado["trusted_sensores"], estado["raw_sensores"])
        self.assertEqual(len(p.carregar_refinado()), estado["raw_sensores"])

    def teste_parametros_invalidos(self):
        for args in ((4, None), (3601, None), ("x", None), (True, None), (None, 0), (None, 9), (None, 2.5)):
            with self.assertRaises(ValueError):
                validar_parametros(*args)
        self.assertEqual(validar_parametros(5, 8), (5.0, 8))


if __name__ == "__main__":
    unittest.main()
