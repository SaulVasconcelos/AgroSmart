"""Fase 7: rotas de operação/prontidão, compatibilidade do health legado e casos HTTP."""
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from agrosmart import web_server as ws
from agrosmart.operacao import ExecucaoContinua

from apoio_fase7 import PLATAFORMA, DadosIsolados, ler_event_log, por_caso


class TestarHTTPFase7(unittest.TestCase):
    def setUp(self):
        self.dados = DadosIsolados(self)
        self.op = ExecucaoContinua(ws.TRAVA, intervalo_s=5)
        self.srv = ws.criar_servidor("127.0.0.1", 0, self.op)
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.addCleanup(self.op.parar, "fim do teste")

    def req(self, caminho, corpo=None):
        dados = None if corpo is None else (corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode())
        r = urllib.request.Request(self.base + caminho, data=dados, method="POST" if corpo is not None else "GET",
                                   headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def casos_encerrados(self, quantidade, limite=5.0):
        """O servidor registra 'Resposta entregue' e o terminal DEPOIS de enviar a resposta."""
        terminais = {"Execução concluída", "Entrada rejeitada", "Execução falhou"}
        fim = time.monotonic() + limite
        while True:
            casos = list(por_caso(ler_event_log()).values())
            prontos = len(casos) == quantidade and all(c[-1]["activity"] in terminais for c in casos)
            if prontos or time.monotonic() > fim:
                return casos

    def teste_health_legado_inalterado(self):
        status, corpo = self.req("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(set(corpo), {"status", "tipo", "persistencia"})
        self.assertEqual(corpo["status"], "ok")

    def teste_operacao_sem_caminhos_internos_e_prontidao(self):
        status, corpo = self.req("/api/operacao")
        self.assertEqual(status, 200)
        self.assertEqual(corpo["estado_funcional"], "sem_execucao_continua")
        self.assertEqual(corpo["dados"]["raw_sensores"], 144)
        self.assertEqual(corpo["dados"]["ultimo_registro"], "2026-10-08T18:00:00")
        self.assertGreater(corpo["dados"]["idade_ultimo_registro_s"], 0)
        self.assertNotIn(str(self.dados.root), json.dumps(corpo, ensure_ascii=False))
        self.assertEqual(self.req("/api/pronto"), (200, {"pronto": True, "verificacoes": {"pasta_dados_gravavel": True, "refined_disponivel": True}}))
        (self.dados.root / "refined" / "monitoramento.csv").unlink()
        status, corpo = self.req("/api/pronto")
        self.assertEqual((status, corpo["pronto"]), (503, False))

    def teste_controle_da_execucao_continua(self):
        self.assertEqual(self.req("/api/operacao/iniciar", {"intervalo_s": 1})[0], 400)
        self.assertEqual(self.req("/api/operacao/iniciar", {"eventos_por_ciclo": 9})[0], 400)
        self.assertEqual(self.req("/api/operacao/iniciar", {"x": 1})[0], 400)
        status, corpo = self.req("/api/operacao/iniciar", {"intervalo_s": 5, "eventos_por_ciclo": 1})
        self.assertEqual((status, corpo["execucao_continua"]["ativa"]), (200, True))
        fim = time.monotonic() + 5
        while self.op.ciclos_total < 1 and time.monotonic() < fim:
            time.sleep(0.02)
        status, corpo = self.req("/api/operacao")
        self.assertEqual(corpo["estado_funcional"], "atualizado")
        self.assertEqual(corpo["dados"]["raw_sensores"], 145)
        self.assertLess(corpo["dados"]["idade_ultimo_registro_s"], 60)
        status, corpo = self.req("/api/operacao/parar", b"")
        self.assertEqual((status, corpo["execucao_continua"]["estado"]), (200, "parada"))

    def teste_post_simular_registra_caso_completo_e_rejeicao(self):
        status, corpo = self.req("/api/simular", {"talhao": "Talhao A", "quantidade": 2})
        self.assertEqual((status, corpo["pipeline"]["raw_sensores"]), (200, 146))
        self.assertEqual(self.req("/api/simular", {"quantidade": 99})[0], 400)
        self.assertEqual(self.req("/api/simular", b"{nao json")[0], 400)
        casos = self.casos_encerrados(3)
        sucesso = [e["activity"] for e in casos[0] if e["lifecycle"] == "complete"]
        self.assertEqual(sucesso, ["Entrada recebida", "Validar requisição", "Gerar leituras simuladas",
                                   "Validar dados de entrada", "Aguardar trava de escrita", "Persistir Raw",
                                   "Publicar Trusted", "Aplicar regras R1–R7", "Publicar Refined",
                                   "Resposta entregue", "Execução concluída"])
        for rejeitado in casos[1:]:
            self.assertEqual([e["activity"] for e in rejeitado if e["lifecycle"] == "complete"],
                             ["Entrada recebida", "Validar requisição", "Resposta entregue", "Entrada rejeitada"])
            self.assertEqual(rejeitado[-2]["status"], "http_400")
        # Rejeição não grava nada além do primeiro POST.
        self.assertEqual(self.req("/api/operacao")[1]["dados"]["raw_sensores"], 146)

    def teste_importacao_valida_antes_de_gravar(self):
        cab = "data;talhao;cultura;percentual_folhas_doentes;praga_detectada;dias_mesma_praga\n"
        ruim = cab + "2026-11-18;Talhao A;Soja;10;Nenhuma;0\n2026-11-18;Talhao A;Soja;-1;Nenhuma;0\n"
        antes = (self.dados.root / "raw" / "observacoes_campo.csv").read_bytes()
        self.assertEqual(self.req("/api/importar-observacoes", {"csv": ruim})[0], 400)
        self.assertEqual((self.dados.root / "raw" / "observacoes_campo.csv").read_bytes(), antes)
        status, corpo = self.req("/api/importar-observacoes", {"csv": cab + "2026-11-18;Talhao A;Soja;10;Nenhuma;0\n"})
        self.assertEqual((status, corpo["observacoes_importadas"]), (200, 1))

    def teste_respostas_de_erro_consomem_o_corpo_antes_de_fechar(self):
        """Regressão do WinError 10053 visto no Windows: 404/400 sem ler o corpo abortava a conexão."""
        lidos = []
        original = ws.Handler._descartar_corpo

        def espiao(handler, *args, **kwargs):
            n = original(handler, *args, **kwargs)
            lidos.append(n)
            return n

        with mock.patch.object(ws.Handler, "_descartar_corpo", espiao):
            self.assertEqual(self.req("/api/operacao/reiniciar", b"x" * 2048)[0], 404)
            self.assertEqual(self.req("/api/simular", b"x" * 200_000)[0], 400)
        self.assertEqual(lidos, [2048, 200_000])

    def teste_rotas_desconhecidas(self):
        self.assertEqual(self.req("/api/operacao/reiniciar", {})[0], 404)
        self.assertEqual(self.req("/api/inexistente")[0], 404)


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@unittest.skipIf(os.name == "nt", "semântica de SIGTERM validada em Linux/container")
class TestarEncerramentoPorSinal(unittest.TestCase):
    def teste_sigterm_encerra_com_codigo_zero_e_preserva_dados(self):
        with tempfile.TemporaryDirectory() as tmp:
            dados = Path(tmp) / "volume"
            env = dict(os.environ, AGROSMART_DATA_DIR=str(dados), AGROSMART_SEED_DIR=str(PLATAFORMA / "data"))
            porta = porta_livre()
            proc = subprocess.Popen([sys.executable, "main.py", "web", "--porta", str(porta), "--execucao-continua", "--intervalo", "5"],
                                    cwd=PLATAFORMA, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            try:
                fim = time.monotonic() + 15
                while time.monotonic() < fim:
                    try:
                        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/api/pronto", timeout=1) as r:
                            if r.status == 200:
                                break
                    except OSError:
                        time.sleep(0.1)
                time.sleep(0.5)
                t0 = time.monotonic()
                proc.send_signal(signal.SIGTERM)
                codigo = proc.wait(timeout=10)
                self.assertEqual(codigo, 0)
                self.assertLess(time.monotonic() - t0, 5)
            finally:
                if proc.poll() is None:
                    proc.kill()
                saida = proc.stdout.read()
                proc.stdout.close()
            self.assertIn("semeado=True", saida)
            self.assertIn("servidor encerrado", saida)
            self.assertTrue((dados / "processos" / "event_log.csv").exists())
            # Segundo início: volume existente preservado (sem nova semeadura).
            with mock.patch.dict(os.environ, env):
                from agrosmart.inicializacao import semear_se_vazio
                self.assertFalse(semear_se_vazio(dados, PLATAFORMA / "data")["semeado"])


class TestarInicializacaoVolume(unittest.TestCase):
    def teste_semeia_somente_pasta_vazia(self):
        from agrosmart.inicializacao import semear_se_vazio
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "dados"
            (destino / "lost+found").mkdir(parents=True)
            r = semear_se_vazio(destino, PLATAFORMA / "data")
            self.assertTrue(r["semeado"])
            original = (PLATAFORMA / "data" / "refined" / "monitoramento.csv").read_bytes()
            self.assertEqual((destino / "refined" / "monitoramento.csv").read_bytes(), original)
            (destino / "raw" / "sensores.jsonl").write_text("alterado\n", encoding="utf-8")
            r2 = semear_se_vazio(destino, PLATAFORMA / "data")
            self.assertFalse(r2["semeado"])
            self.assertEqual((destino / "raw" / "sensores.jsonl").read_text(encoding="utf-8"), "alterado\n")
            vazio = Path(tmp) / "outro"
            self.assertFalse(semear_se_vazio(vazio, Path(tmp) / "sem_semente")["semeado"])


if __name__ == "__main__":
    unittest.main()
