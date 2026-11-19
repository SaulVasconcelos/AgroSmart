"""Regressão determinística contra os arquivos distribuídos no ZIP original."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agrosmart import pipeline as p


class TestarRegressaoDemo(unittest.TestCase):
    def teste_demo_preserva_resultados_por_registro(self):
        platform = Path(__file__).resolve().parents[1]
        originals = p.ler_csv(Path(__file__).parent / "fixtures" / "monitoramento_original.csv")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.multiple(p, DATA_DIR=root, RAW=root / "raw",
                                     TRUSTED=root / "trusted", REFINED=root / "refined"):
                result = p.reset_demo(platform / "origens" / "resultados_agrosmart.csv")
                self.assertEqual(result["trusted_sensores"], 144)
                self.assertEqual(result["observacoes_campo"], 36)
                self.assertEqual(result["diagnosticos_historicos"], 766)
                self.assertEqual(result["alertas"], 109)
                self.assertEqual(result["regras"], {"R1": 8, "R2": 28, "R3": 24,
                                                  "R4": 9, "R5": 12, "R6": 28, "R7": 35})
                self.assertEqual(p.carregar_refinado(), originals)
                state = p.estado_dashboard()
                self.assertEqual(state["kpis"]["criticos"], 8)
                self.assertTrue(all(not r["talhao"] and not r["cultura"] for r in p.carregar_diagnosticos()))

    def teste_filtros_e_diagnosticos_independentes(self):
        platform = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.multiple(p, DATA_DIR=root, RAW=root / "raw",
                                     TRUSTED=root / "trusted", REFINED=root / "refined"):
                p.reset_demo(platform / "origens" / "resultados_agrosmart.csv")
                all_state = p.estado_dashboard()
                filtered = p.estado_dashboard("Talhao B", "2026-10-01", "2026-10-02")
                self.assertEqual(filtered["kpis"]["leituras"], 8)
                self.assertEqual([r["talhao"] for r in filtered["talhoes"]], ["Talhao B"])
                self.assertEqual(len(filtered["serie"]), 2)
                self.assertEqual(filtered["diagnosticos"], all_state["diagnosticos"])
                empty = p.estado_dashboard("", "2030-01-01", "2030-01-02")
                self.assertEqual(empty["kpis"]["leituras"], 0)
                self.assertEqual(empty["serie"], [])
                self.assertEqual(empty["diagnosticos"], all_state["diagnosticos"])

    def teste_importacao_atomica_valida_invalida_e_reprocessamento(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.multiple(p, DATA_DIR=root, RAW=root / "raw",
                                     TRUSTED=root / "trusted", REFINED=root / "refined"):
                header = "data;talhao;cultura;percentual_folhas_doentes;praga_detectada;dias_mesma_praga\n"
                valid = "2026-10-01;Talhao A;Soja;10;Nenhuma;0\n"
                self.assertEqual(p.adicionar_observacoes_csv(header + valid), 1)
                before = (p.RAW / "observacoes_campo.csv").read_bytes()
                with self.assertRaises(ValueError):
                    p.adicionar_observacoes_csv(header + valid + "2026-10-02;Talhao A;Soja;-1;Nenhuma;0\n")
                with self.assertRaises(ValueError):
                    p.adicionar_observacoes_csv("x" * 100_001)
                self.assertEqual((p.RAW / "observacoes_campo.csv").read_bytes(), before)
                p.adicionar_observacoes_csv(header + valid)
                result = p.processar()
                self.assertEqual(result["observacoes_campo"], 1)
                self.assertEqual(p.processar(), result)
