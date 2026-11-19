"""Teste end-to-end em pasta temporaria isolada; sem alterar datasets entregues."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from agrosmart import pipeline as p
from agrosmart.simulador import gerar_leitura
from datetime import datetime
import random

class TestarPipeline(unittest.TestCase):
    def teste_reprocessamento_deduplicacao_e_ausencia_campo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with mock.patch.multiple(p,DATA_DIR=root,RAW=root/'raw',TRUSTED=root/'trusted',REFINED=root/'refined'):
                evt=gerar_leitura('Talhao A',datetime(2026,10,3,9,0),random.Random(3))
                p.adicionar_evento(evt)
                p.adicionar_evento(evt)
                resultado=p.processar()
                self.assertEqual(resultado['raw_sensores'],2)
                self.assertEqual(resultado['trusted_sensores'],1)
                self.assertEqual(resultado['duplicados_removidos'],1)
                self.assertEqual(p.carregar_refinado()[0]['origem_observacao'],'Ausente')
                # Garantia: sem observacao, apenas R4/R5 ou ND; R1/R2/R3/R6/R7 nao sao afirmadas.
                self.assertIn(p.carregar_refinado()[0]['regra'],('R4','R5','ND'))
                depois=p.processar()
                self.assertEqual(depois['trusted_sensores'],1)
                self.assertEqual(len(p.carregar_refinado()),1)

    def teste_registro_invalido_foi_quarentenado(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with mock.patch.multiple(p,DATA_DIR=root,RAW=root/'raw',TRUSTED=root/'trusted',REFINED=root/'refined'):
                p.adicionar_evento({'sensor_id':'S-001'})
                s=p.processar()
                self.assertEqual(s['raw_sensores'],1)
                self.assertEqual(s['rejeitados'],1)
                self.assertEqual(s['trusted_sensores'],0)
                self.assertIn('Campo sensor ausente',p.ler_csv(root/'trusted'/'rejeitados.csv')[0]['motivo'])

if __name__=='__main__':unittest.main()
