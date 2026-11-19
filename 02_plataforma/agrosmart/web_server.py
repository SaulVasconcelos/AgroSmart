"""Dashboard web sem dependencias externas (http.server + JS/SVG).

Servidor em 127.0.0.1 por padrão. Não recomendado exposição publica.
Fase 7 (aditivo): execução contínua no mesmo processo e com a mesma trava,
/api/operacao (estado funcional), /api/pronto (prontidão), controle de início/parada,
event log das execuções e encerramento limpo por SIGTERM (docker stop).
"""
from __future__ import annotations

import json
import logging
import random
import signal
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from urllib.parse import parse_qs, urlsplit

from . import __version__
from . import pipeline as _pipeline
from .consultas import consultar_alertas, consultar_talhao
from .observabilidade import MetricasHTTP, configurar_logs
from .operacao import ExecucaoContinua, resumo_dados, validar_parametros, verificar_prontidao
from .pipeline import DATA_DIR, estado_dashboard, gravar_observacoes, processar, validar_observacoes_csv, validar_sensor
from .rastreio import Caso
from .rastreio import contadores as contadores_event_log
from .simulador import TALHOES, gerar_leitura

ASSETS = Path(__file__).resolve().parents[1] / 'web'
TRAVA=RLock()
_log = logging.getLogger('agrosmart.http')


class Handler(BaseHTTPRequestHandler):
    server_version = 'AgroSmart'
    sys_version = ''
    timeout = 30  # segundos por operação de socket: cliente que não envia o corpo declarado não prende a thread

    def _descartar_corpo(self, limite: int = 1_048_576) -> int:
        """Lê e descarta o corpo ainda não lido antes de responder um erro.

        Fechar o socket com dados não lidos faz o Windows abortar a conexão (RST), e o
        cliente pode perder a resposta (WinError 10053). Encontrado no pipeline da equipe
        em 18/11/2026. Limite de leitura para não aceitar volume arbitrário.
        """
        try:
            restante = min(max(int(self.headers.get('Content-Length', '0')), 0), limite)
        except ValueError:
            return 0
        lidos = 0
        try:
            while restante > 0:
                bloco = self.rfile.read(min(65_536, restante))
                if not bloco:
                    break
                lidos += len(bloco)
                restante -= len(bloco)
        except OSError:
            pass
        return lidos

    def responder(self, status, body: bytes, content_type: str, extra_headers=None):
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cache-Control','no-store')
        if extra_headers:
            for k,v in extra_headers.items():self.send_header(k,v)
        self.end_headers(); self.wfile.write(body)

    def json_resp(self,status,obj):
        self.responder(status,json.dumps(obj,ensure_ascii=False,default=str).encode('utf-8'),'application/json; charset=utf-8')

    # ------------------------------------------------------------ Fase 7: estado
    def _operacao(self) -> ExecucaoContinua | None:
        return getattr(self.server, 'operacao', None)

    def _estado_operacao(self) -> dict:
        op = self._operacao()
        metricas = getattr(self.server, 'metricas', None)
        execucao = op.status() if op else None
        with TRAVA:
            dados = resumo_dados()
        prontidao = verificar_prontidao()
        if execucao is None or not execucao['ativa']:
            funcional = 'sem_execucao_continua'
        else:
            desde = execucao['segundos_desde_ultimo_sucesso']
            tolerancia = max(2 * execucao['intervalo_s'], 60)
            funcional = 'atualizado' if desde is not None and desde <= tolerancia else 'atrasado'
        return {
            'servidor': {'status': 'ok', 'versao': __version__,
                         'iniciado_em_utc': metricas.iniciado_em_utc if metricas else None,
                         'uptime_s': metricas.uptime_s() if metricas else None,
                         'requisicoes': metricas.resumo() if metricas else None},
            'prontidao': prontidao,
            'estado_funcional': funcional,
            'execucao_continua': execucao,
            'dados': dados,
            'event_log': contadores_event_log(),
            'escopo': 'Ambiente acadêmico local; leituras simuladas. Estado do processo atual, não de equipamento de campo.',
        }

    def do_GET(self):
        parsed=urlsplit(self.path)
        path=parsed.path
        if path in ('/','/index.html','/app.js','/styles.css','/icons.svg'):
            arquivo=ASSETS/({'/':'index.html','/index.html':'index.html','/app.js':'app.js','/styles.css':'styles.css','/icons.svg':'icons.svg'}[path])
            if not arquivo.is_file(): self.json_resp(404,{'erro':'Frontend ausente'});return
            tipo='image/svg+xml' if path=='/icons.svg' else ('text/html; charset=utf-8' if path in ('/','/index.html') else ('text/javascript; charset=utf-8' if path=='/app.js' else 'text/css; charset=utf-8'))
            self.responder(200,arquivo.read_bytes(),tipo);return
        if path=='/api/health':self.json_resp(200,{'status':'ok','tipo':'ambiente acadêmico local','persistencia':str(DATA_DIR)});return
        if path=='/api/pronto':
            p=verificar_prontidao();self.json_resp(200 if p['pronto'] else 503,p);return
        if path=='/api/operacao':
            self.json_resp(200,self._estado_operacao());return
        if path=='/api/estado':
            filtros=parse_qs(parsed.query)
            with TRAVA:
                dados=estado_dashboard((filtros.get('talhao') or [''])[0],(filtros.get('inicio') or [''])[0],(filtros.get('fim') or [''])[0])
            self.json_resp(200,dados);return
        if path in ('/api/alertas','/api/talhao'):
            try:
                filtros=parse_qs(parsed.query,keep_blank_values=True)
                permitidos={'talhao','inicio','fim'} | ({'severidade','ordem','pagina','tamanho'} if path=='/api/alertas' else {'data_hora','sensor_id'})
                if any(k not in permitidos or len(v)!=1 for k,v in filtros.items()):
                    raise ValueError('Parâmetro desconhecido ou repetido')
                params={k:v[0] for k,v in filtros.items()}
                if path=='/api/alertas':
                    for nome in ('pagina','tamanho'):
                        if nome in params:
                            valor=params[nome]
                            if not valor.isascii() or not valor.isdigit():raise ValueError(nome+': use um inteiro positivo')
                            params[nome]=int(valor)
                    with TRAVA:dados=consultar_alertas(**params)
                else:
                    with TRAVA:dados=consultar_talhao(**params)
                self.json_resp(200,dados)
            except ValueError as exc:self.json_resp(400,{'erro':str(exc)})
            except (LookupError,TypeError) as exc:self.json_resp(404 if isinstance(exc,LookupError) else 400,{'erro':str(exc)})
            return
        self.json_resp(404,{'erro':'Rota desconhecida'})

    def _ler_json(self, permitir_vazio=False) -> dict:
        tamanho=int(self.headers.get('Content-Length','0'))
        if permitir_vazio and tamanho==0:return {}
        if tamanho<=0 or tamanho>150_000:
            self._descartar_corpo()
            raise ValueError('Corpo excede limite de 150 KB ou está vazio')
        payload=json.loads(self.rfile.read(tamanho).decode('utf-8'))
        if not isinstance(payload,dict):raise ValueError('Corpo JSON inválido')
        return payload

    def _post_operacao(self):
        op=self._operacao()
        if op is None:
            self._descartar_corpo()
            self.json_resp(404,{'erro':'Execução contínua indisponível neste servidor'});return
        try:
            payload=self._ler_json(permitir_vazio=True)
            if self.path=='/api/operacao/iniciar':
                desconhecidos=set(payload)-{'intervalo_s','eventos_por_ciclo'}
                if desconhecidos:raise ValueError('Parâmetro desconhecido: '+', '.join(sorted(desconhecidos)))
                validar_parametros(payload.get('intervalo_s'),payload.get('eventos_por_ciclo'))
                status=op.iniciar(payload.get('intervalo_s'),payload.get('eventos_por_ciclo'))
            else:
                if payload:raise ValueError('Parar não recebe parâmetros')
                status=op.parar('solicitado pela interface/API')
            self.json_resp(200,{'ok':True,'execucao_continua':status})
        except (ValueError,UnicodeDecodeError,json.JSONDecodeError) as e:
            self.json_resp(400,{'erro':str(e)})

    def do_POST(self):
        if self.path in ('/api/operacao/iniciar','/api/operacao/parar'):
            self._post_operacao();return
        if self.path not in ('/api/simular','/api/importar-observacoes'):
            self._descartar_corpo()
            self.json_resp(404,{'erro':'Rota desconhecida'});return
        simular=self.path=='/api/simular'
        caso=Caso('api_simular' if simular else 'api_importar_observacoes','web_server')
        caso.registrar('Entrada recebida',records_in=self.headers.get('Content-Length','0'),detail='POST '+self.path)
        try:
            with caso.atividade('Validar requisição') as info:
                payload=self._ler_json()
                if simular:
                    qtd=int(payload.get('quantidade',1))
                    if not 1<=qtd<=8:raise ValueError('Quantidade entre 1 e 8')
                    talhao=str(payload.get('talhao') or '').strip()
                    if talhao and talhao not in TALHOES:raise ValueError('Talhão não cadastrado')
                    info['records_in']=qtd
                else:
                    csv_texto=payload.get('csv','')
                    if not isinstance(csv_texto,str):raise ValueError('CSV inválido')
            if simular:
                with caso.atividade('Gerar leituras simuladas','simulador') as info:
                    rng=random.Random()  # simulação didática; não é uso criptográfico
                    novos=[gerar_leitura(talhao or rng.choice(list(TALHOES)),datetime.now(),rng) for _ in range(qtd)]
                    info['records_out']=len(novos)
                with caso.atividade('Validar dados de entrada','pipeline') as info:
                    for evento in novos:validar_sensor(evento)
                    info['records_in']=info['records_out']=len(novos)
            else:
                with caso.atividade('Validar dados de entrada','pipeline') as info:
                    observacoes=validar_observacoes_csv(csv_texto)
                    info['records_in']=info['records_out']=len(observacoes)
            with caso.atividade('Aguardar trava de escrita','web_server'):
                TRAVA.acquire()
            try:
                with caso.atividade('Persistir Raw','pipeline') as info:
                    if simular:
                        for evento in novos:_pipeline.adicionar_evento(evento)
                        info['records_out']=len(novos)
                    else:
                        info['records_out']=gravar_observacoes(observacoes)
                estado=processar(caso=caso)
            finally:
                TRAVA.release()
            corpo={'ok':True,'eventos':novos,'pipeline':estado} if simular else {'ok':True,'observacoes_importadas':len(observacoes),'pipeline':estado}
            self.json_resp(200,corpo)
            caso.registrar('Resposta entregue',status='http_200',component='web_server')
            caso.concluir('sucesso')
        except (ValueError,KeyError,UnicodeDecodeError,json.JSONDecodeError) as e:
            self.json_resp(400,{'erro':str(e)})
            caso.registrar('Resposta entregue',status='http_400',component='web_server')
            caso.concluir('rejeitado',str(e))
        except Exception as e:
            _log.error('erro interno rota=%s case_id=%s tipo=%s', self.path, caso.case_id, type(e).__name__)
            self.json_resp(500,{'erro':'Falha interna do servidor'})
            caso.registrar('Resposta entregue',status='http_500',component='web_server')
            caso.concluir('falha',type(e).__name__)

    def log_request(self, code='-', size='-'):
        metricas=getattr(self.server,'metricas',None)
        if metricas is not None:metricas.registrar(code)
        super().log_request(code,size)

    def log_message(self, fmt, *args):
        _log.info('requisicao cliente=%s %s', self.address_string(), fmt%args)


def criar_servidor(host='127.0.0.1', porta=8501, operacao: ExecucaoContinua | None = None) -> ThreadingHTTPServer:
    servidor=ThreadingHTTPServer((host,porta),Handler)
    servidor.daemon_threads=True
    servidor.operacao=operacao
    servidor.metricas=MetricasHTTP()
    return servidor


def iniciar(host='127.0.0.1',porta=8501,execucao_continua=False,intervalo_s=30.0,eventos_por_ciclo=3,limite_leituras=10_000):
    arquivo_log=configurar_logs(Path(_pipeline.DATA_DIR))
    operacao=ExecucaoContinua(TRAVA,intervalo_s=intervalo_s,eventos_por_ciclo=eventos_por_ciclo,limite_leituras=limite_leituras)
    servidor=criar_servidor(host,porta,operacao)

    def encerrar(signum, _frame):
        _log.info('sinal recebido sinal=%s; encerrando', signal.Signals(signum).name)
        threading.Thread(target=servidor.shutdown,daemon=True).start()

    try:
        signal.signal(signal.SIGTERM,encerrar)
    except (ValueError,AttributeError):
        pass  # fora da thread principal ou plataforma sem SIGTERM
    _log.info('servidor iniciado versao=%s host=%s porta=%s log_arquivo=%s', __version__, host, porta, 'sim' if arquivo_log else 'nao')
    if execucao_continua:
        operacao.iniciar()
    print(f'AgroSmart/AgroMonitor em http://{host}:{porta} (CTRL+C encerra)',flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        operacao.parar('encerramento do servidor')
        servidor.server_close()
        _log.info('servidor encerrado ciclos_total=%s', operacao.ciclos_total)
