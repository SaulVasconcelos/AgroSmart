"""Consultas novas: conjunto integral, contexto exato e nenhuma gravação."""
import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agrosmart import consultas as c, pipeline as p


class TestarConsultas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'data'
        shutil.copytree(Path(__file__).resolve().parents[1] / 'data', self.root)
        patch = mock.patch.multiple(p, DATA_DIR=self.root, RAW=self.root / 'raw',
                                    TRUSTED=self.root / 'trusted', REFINED=self.root / 'refined')
        patch.start()
        self.addCleanup(patch.stop)

    def hashes(self):
        return {str(f.relative_to(self.root)): hashlib.sha256(f.read_bytes()).hexdigest()
                for f in self.root.rglob('*') if f.is_file()}

    def teste_paginas_completas_sem_repeticao_e_prioridade(self):
        before = self.hashes()
        first = c.consultar_alertas()
        self.assertEqual((first['total'], first['paginas'], len(first['itens'])), (109, 6, 20))
        self.assertEqual(first['severidades'], {'Crítica': 8, 'Alta': 61, 'Média': 40})
        all_rows = [r for page in range(1, 7) for r in c.consultar_alertas(pagina=page)['itens']]
        self.assertEqual(len(all_rows), 109)
        self.assertEqual(len({(r['talhao'], r['sensor_id'], r['data_hora']) for r in all_rows}), 109)
        self.assertEqual([r['severidade'] for r in all_rows[:8]], ['Crítica'] * 8)
        self.assertEqual(first['itens'][0]['talhao'], 'Talhao B')
        self.assertEqual(first['itens'][0]['data_hora'], '2026-10-06T12:00:00')
        self.assertEqual(self.hashes(), before)

    def teste_critica_antiga_fora_do_limite_120_permanece_primeira(self):
        source = p.carregar_refinado()
        old = dict(source[0], data_hora='2000-01-01T00:00:00', regra='R1', severidade='Crítica')
        newer = [dict(source[0], data_hora=f'2026-10-08T{i // 60:02}:{i % 60:02}:00',
                      regra='R6', severidade='Média') for i in range(150)]
        with mock.patch.object(c, 'carregar_refinado', return_value=[old] + newer):
            result = c.consultar_alertas(tamanho=1)
            self.assertEqual(result['total'], 151)
            self.assertEqual(result['itens'][0], old)
            self.assertEqual(c.consultar_alertas(ordem='recencia', tamanho=1)['itens'][0], newer[-1])

    def teste_filtros_recencia_e_pagina_fora_intervalo(self):
        rows = c.consultar_alertas(talhao='Talhao B', inicio='2026-10-01', fim='2026-10-02', ordem='recencia')
        self.assertEqual(rows['total'], 8)
        self.assertTrue(all(r['talhao'] == 'Talhao B' for r in rows['itens']))
        dates = [r['data_hora'] for r in rows['itens']]
        self.assertEqual(dates, sorted(dates, reverse=True))
        critical = c.consultar_alertas(severidade='Crítica')
        self.assertEqual(critical['total'], 8)
        self.assertEqual(critical['severidades'], {'Crítica': 8})
        last = c.consultar_alertas(pagina=999)
        self.assertEqual((last['pagina'], last['inicio_exibido'], last['fim_exibido']), (6, 101, 109))

    def teste_vazio_nao_inventa_ultima_leitura(self):
        args = dict(inicio='2030-01-01', fim='2030-01-02')
        alerts = c.consultar_alertas(**args)
        self.assertEqual((alerts['total'], alerts['inicio_exibido'], alerts['fim_exibido']), (0, 0, 0))
        detail = c.consultar_talhao('Talhao A', **args)
        self.assertIsNone(detail['ultima_leitura'])
        self.assertIsNone(detail['resumo'])
        self.assertEqual(detail['serie'], [])

    def teste_detalhe_separa_ocorrencia_e_ultima_leitura(self):
        before = self.hashes()
        r = c.consultar_alertas()['itens'][0]
        detail = c.consultar_talhao(r['talhao'], data_hora=r['data_hora'], sensor_id=r['sensor_id'])
        self.assertEqual(detail['leitura_selecionada'], r)
        self.assertEqual(detail['ultima_leitura']['regra'], 'R3')
        self.assertEqual(detail['ultima_leitura']['data_hora'], '2026-10-08T18:00:00')
        self.assertEqual(detail['resumo']['umidade_media'], 45.4)
        self.assertEqual(detail['observacoes_ausentes'], 0)
        with self.assertRaises(LookupError):
            c.consultar_talhao('Talhao A', data_hora=r['data_hora'], sensor_id=r['sensor_id'])
        with self.assertRaises(LookupError):
            c.consultar_talhao(r['talhao'], inicio='2026-10-07', data_hora=r['data_hora'], sensor_id=r['sensor_id'])
        self.assertEqual(self.hashes(), before)

    def teste_parametros_invalidos(self):
        for args in [dict(talhao='Outra'), dict(inicio='2026-02-30'), dict(inicio='2026-1-01'),
                     dict(inicio='2026-10-08', fim='2026-10-01'), dict(severidade='Baixa'),
                     dict(ordem='nome'), dict(pagina=0), dict(pagina=True), dict(pagina=1.5),
                     dict(pagina=1_000_001), dict(tamanho=101), dict(tamanho=0)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                c.consultar_alertas(**args)
        for args in [dict(talhao=''), dict(talhao='Talhao A', data_hora='x'),
                     dict(talhao='Talhao A', data_hora='x', sensor_id='S-001')]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                c.consultar_talhao(**args)

    def teste_nd_e_avaliacao_parcial_nao_sao_reclassificados(self):
        source = p.carregar_refinado()
        row = dict(source[0], regra='ND', severidade='Indeterminada', avaliacao='Parcial',
                   origem_observacao='Ausente', percentual_folhas_doentes='', dias_mesma_praga='', praga_detectada='')
        with mock.patch.object(c, 'carregar_refinado', return_value=[row]):
            self.assertEqual(c.consultar_alertas()['total'], 0)
            detail = c.consultar_talhao(row['talhao'])
            self.assertEqual(detail['ultima_leitura'], row)
            self.assertEqual(detail['observacoes_ausentes'], 1)

    def teste_campo_aditivo_ultima_leitura_respeita_talhao_periodo(self):
        state = p.estado_dashboard()
        self.assertEqual(len(state['ultimas_por_talhao']), 3)
        filtered = p.estado_dashboard('Talhao A', '2026-10-01', '2026-10-02')
        self.assertEqual(len(filtered['ultimas_por_talhao']), 1)
        row = filtered['ultimas_por_talhao'][0]
        self.assertEqual((row['talhao'], row['data_hora']), ('Talhao A', '2026-10-02T18:00:00'))
        self.assertEqual(filtered['diagnosticos'], state['diagnosticos'])
