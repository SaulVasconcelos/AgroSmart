"""Testes sem dependencias externas, cobrindo regras e estado do pipeline."""
from __future__ import annotations

import unittest

from agrosmart.pipeline import (validar_sensor, validar_campo, normalizar_diagnostico)
from agrosmart.regras import avaliar

BASE={'data_hora':'2026-10-05T12:00:00','sensor_id':'S-001','talhao':'Talhao A','cultura':'Soja','umidade_solo':55,'temperatura':27,'probabilidade_praga':10,'alerta':'Normal','recomendacao':'Rotina'}
CAMPO={'data':'2026-10-05','talhao':'Talhao A','cultura':'Soja','percentual_folhas_doentes':5,'praga_detectada':'Nenhuma','dias_mesma_praga':0}

class TestarRegras(unittest.TestCase):
    def teste_cada_regra(self):
        cenarios={
            'R1':({'umidade_solo':30},{'percentual_folhas_doentes':35,'dias_mesma_praga':3,'praga_detectada':'Lagarta'}),
            'R2':({'umidade_solo':50},{'percentual_folhas_doentes':35,'dias_mesma_praga':1,'praga_detectada':'Lagarta'}),
            'R3':({'umidade_solo':50},{'percentual_folhas_doentes':25,'dias_mesma_praga':3,'praga_detectada':'Lagarta'}),
            'R4':({'umidade_solo':30,'temperatura':31},{'percentual_folhas_doentes':5,'dias_mesma_praga':0}),
            'R5':({'umidade_solo':30,'temperatura':27},{'percentual_folhas_doentes':5,'dias_mesma_praga':0}),
            'R6':({'umidade_solo':50},{'percentual_folhas_doentes':16,'dias_mesma_praga':0}),
            'R7':({'umidade_solo':55,'temperatura':27},{'percentual_folhas_doentes':5,'dias_mesma_praga':0}),
        }
        for regra,(alter_s,alter_c) in cenarios.items():
            with self.subTest(regra=regra):
                s={**BASE,**alter_s};c={**CAMPO,**alter_c}
                self.assertEqual(avaliar(s,c).regra,regra)

    def teste_prioridade_R1_sobre_R2(self):
        self.assertEqual(avaliar({**BASE,'umidade_solo':30},{**CAMPO,'percentual_folhas_doentes':50,'dias_mesma_praga':4}).regra,'R1')

    def teste_R6_parenteses(self):
        c={**CAMPO,'percentual_folhas_doentes':16,'praga_detectada':'Nenhuma','dias_mesma_praga':5}
        self.assertEqual(avaliar(BASE,c).regra,'R6')

    def teste_falta_campo_nao_afirma_normal(self):
        r=avaliar(BASE,None)
        self.assertEqual(r.regra,'ND')
        self.assertEqual(r.avaliacao,'Parcial')
        self.assertEqual(avaliar({**BASE,'umidade_solo':30,'temperatura':31},None).regra,'R4')

    def teste_limites_exatos(self):
        self.assertEqual(avaliar({**BASE,'umidade_solo':35,'temperatura':30},{**CAMPO,'percentual_folhas_doentes':14}).regra,'R7')
        self.assertEqual(avaliar({**BASE,'umidade_solo':34.99,'temperatura':30},CAMPO).regra,'R5')

class TestarQualidade(unittest.TestCase):
    def teste_sensor_original_preservado(self):
        self.assertEqual(len(validar_sensor(BASE)),9)
        self.assertEqual(validar_sensor(BASE)['cultura'],'Soja')
    def teste_sensor_proba_fora_escala(self):
        with self.assertRaises(ValueError): validar_sensor({**BASE,'probabilidade_praga':101})
    def teste_sensor_talhao_cultura_incompativeis(self):
        with self.assertRaises(ValueError): validar_sensor({**BASE,'cultura':'Cafe'})
    def teste_observacao_invalida(self):
        with self.assertRaises(ValueError):validar_campo({**CAMPO,'percentual_folhas_doentes':-1})
    def teste_diagnosticos_equivalentes(self):
        self.assertEqual(normalizar_diagnostico('Folha_Saudavel'),normalizar_diagnostico('Folha_Saudável'))
        self.assertEqual(normalizar_diagnostico('Doenca_Detectada (Ex: Ferrugem/Mancha)'), 'Doença detectada')

if __name__=='__main__':unittest.main()
