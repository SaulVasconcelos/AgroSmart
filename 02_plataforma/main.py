#!/usr/bin/env python3
"""Executavel AgroSmart. Requer apenas Python 3.10+ (biblioteca padrao)."""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

from agrosmart.pipeline import (
    DATA_DIR,
    adicionar_evento,
    gravar_observacoes,
    processar,
    reset_demo,
    validar_observacoes_csv,
    validar_sensor,
)
from agrosmart.rastreio import Caso
from agrosmart.simulador import TALHOES, gerar_leitura


def _env_bool(nome: str) -> bool:
    return os.environ.get(nome, '').strip().lower() in ('1', 'true', 'sim', 'yes', 'on')


def _cli_caso(gatilho: str) -> Caso:
    caso = Caso(gatilho, 'cli')
    _CASO_ATUAL['caso'] = caso
    caso.registrar('Entrada recebida', component='cli', detail=' '.join(sys.argv[1:])[:160])
    return caso


def _monitorar(url: str, intervalo: float, vezes: int) -> int:
    """Acompanha GET /api/operacao no terminal (uma linha por consulta)."""
    from urllib.error import URLError
    from urllib.parse import urlsplit
    from urllib.request import urlopen
    alvo = url.rstrip('/') + '/api/operacao'
    if urlsplit(alvo).scheme not in ('http', 'https'):
        print('URL deve usar http ou https', file=sys.stderr)
        return 2
    n = 0
    while vezes == 0 or n < vezes:
        n += 1
        try:
            with urlopen(alvo, timeout=5) as resp:  # nosec B310 - esquema restrito a http/https acima
                op = json.loads(resp.read().decode('utf-8'))
            ex = op.get('execucao_continua') or {}
            ult = ex.get('ultimo_ciclo') or {}
            dados = op.get('dados') or {}
            print(f"{datetime.now().isoformat(timespec='seconds')} estado={op.get('estado_funcional')} "
                  f"execucao={ex.get('estado')} ciclos={ex.get('ciclos_total')} falhas={ex.get('falhas_total')} "
                  f"ultimo_ciclo={ult.get('resultado', '-')}/{ult.get('duracao_ms', '-')}ms "
                  f"raw={dados.get('raw_sensores')} alertas={dados.get('alertas')} "
                  f"idade_dado_s={dados.get('idade_ultimo_registro_s')} http={op.get('servidor', {}).get('requisicoes')}", flush=True)
        except (URLError, OSError, ValueError) as exc:
            print(f"{datetime.now().isoformat(timespec='seconds')} indisponivel erro={type(exc).__name__}", flush=True)
        if vezes == 0 or n < vezes:
            time.sleep(intervalo)
    return 0


def main():
    try:
        _main()
    except Exception as exc:
        caso=_CASO_ATUAL.get('caso')
        if caso is not None and caso.resultado is None:
            caso.concluir('falha',type(exc).__name__)
        raise


_CASO_ATUAL: dict = {}


def _main():
    parser=argparse.ArgumentParser(description='AgroSmart Fase 7: simulação, pipeline, regras R1-R7, dashboard, execução contínua e monitoramento')
    sub=parser.add_subparsers(dest='comando',required=True)
    p=sub.add_parser('demo',help='Restaura base didática de simulação e reprocessa')
    p.add_argument('--diagnosticos',type=Path, help='CSV historico do prototipo de imagem')
    p=sub.add_parser('processar',help='Reexecuta todas as camadas do pipeline')
    p=sub.add_parser('simular',help='Gera eventos adicionais e atualiza o dashboard')
    p.add_argument('--quantidade',type=int,default=3)
    p.add_argument('--talhao',choices=list(TALHOES))
    p=sub.add_parser('importar-observacoes',help='Carrega observações de campo a partir de CSV ;')
    p.add_argument('arquivo',type=Path)
    p=sub.add_parser('importar-sensores',help='Carrega JSONL contendo eventos do schema da Fase 4 (valida tudo antes de gravar)')
    p.add_argument('arquivo',type=Path)
    p=sub.add_parser('web',help='Inicia o dashboard integrado em http://127.0.0.1:8501')
    p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--porta',type=int,default=8501)
    p.add_argument('--execucao-continua',action='store_true',default=_env_bool('AGROSMART_EXECUCAO_CONTINUA'),
                   help='Gera leituras simuladas automaticamente (env AGROSMART_EXECUCAO_CONTINUA=1)')
    p.add_argument('--intervalo',type=float,default=float(os.environ.get('AGROSMART_INTERVALO_S','30')),
                   help='Segundos entre o fim de um ciclo e o início do próximo (5-3600)')
    p.add_argument('--eventos-por-ciclo',type=int,default=int(os.environ.get('AGROSMART_EVENTOS_POR_CICLO','3')))
    p.add_argument('--limite-leituras',type=int,default=int(os.environ.get('AGROSMART_LIMITE_LEITURAS','10000')),
                   help='A execução contínua para quando o Raw atinge este total')
    p=sub.add_parser('monitorar',help='Acompanha o estado de operação de um servidor em execução')
    p.add_argument('--url',default='http://127.0.0.1:8501')
    p.add_argument('--intervalo',type=float,default=5.0)
    p.add_argument('--vezes',type=int,default=0,help='0 = até CTRL+C')
    args=parser.parse_args()
    if args.comando=='demo':
        default=Path(__file__).resolve().parent/'origens'/'resultados_agrosmart.csv'
        d=args.diagnosticos or (default if default.exists() else None)
        resultado=reset_demo(d)
    elif args.comando=='processar':
        caso=_cli_caso('cli_processar')
        resultado=processar(caso=caso);caso.concluir('sucesso')
    elif args.comando=='simular':
        if args.quantidade<1 or args.quantidade>300:parser.error('--quantidade precisa ficar entre 1 e 300')
        caso=_cli_caso('cli_simular')
        rng=random.Random()  # simulação didática; não é uso criptográfico
        with caso.atividade('Gerar leituras simuladas','simulador') as info:
            eventos=[gerar_leitura(args.talhao or rng.choice(list(TALHOES)),datetime.now(),rng) for _ in range(args.quantidade)]
            info['records_out']=len(eventos)
        with caso.atividade('Validar dados de entrada','pipeline') as info:
            for e in eventos:validar_sensor(e)
            info['records_in']=info['records_out']=len(eventos)
        with caso.atividade('Persistir Raw','pipeline') as info:
            for e in eventos:
                adicionar_evento(e)
                print(json.dumps(e,ensure_ascii=False))
            info['records_out']=len(eventos)
        resultado=processar(caso=caso);caso.concluir('sucesso')
    elif args.comando=='importar-observacoes':
        caso=_cli_caso('cli_importar_observacoes')
        try:
            with caso.atividade('Validar dados de entrada','pipeline'):
                novas=validar_observacoes_csv(args.arquivo.read_text(encoding='utf-8-sig'))
        except ValueError as exc:
            caso.concluir('rejeitado',str(exc));parser.exit(2,f'Importação rejeitada: {exc}\n')
        with caso.atividade('Persistir Raw','pipeline') as info:
            n=gravar_observacoes(novas);info['records_out']=n
        resultado=processar(caso=caso);resultado['importadas']=n;caso.concluir('sucesso')
    elif args.comando=='importar-sensores':
        caso=_cli_caso('cli_importar_sensores')
        eventos=[]
        try:
            with caso.atividade('Validar dados de entrada','pipeline') as info:
                for numero,linha in enumerate(args.arquivo.read_text(encoding='utf-8').splitlines(),start=1):
                    if not linha.strip():continue
                    try:
                        evento=json.loads(linha)
                        validar_sensor(evento)
                    except (ValueError,TypeError) as exc:
                        raise ValueError(f'linha {numero}: {exc}') from exc
                    eventos.append(evento)
                info['records_in']=info['records_out']=len(eventos)
        except ValueError as exc:
            caso.concluir('rejeitado',str(exc));parser.exit(2,f'Importação rejeitada (nada foi gravado): {exc}\n')
        with caso.atividade('Persistir Raw','pipeline') as info:
            for evento in eventos:adicionar_evento(evento,origem='arquivo_jsonl')
            info['records_out']=len(eventos)
        resultado=processar(caso=caso);resultado['importados']=len(eventos);caso.concluir('sucesso')
    elif args.comando=='web':
        from agrosmart.operacao import validar_parametros
        try:
            validar_parametros(args.intervalo,args.eventos_por_ciclo)
        except ValueError as exc:
            parser.error(str(exc))
        semente=os.environ.get('AGROSMART_SEED_DIR')
        if semente:
            from agrosmart.inicializacao import semear_se_vazio
            r=semear_se_vazio(DATA_DIR,Path(semente))
            print(f"inicializacao_dados semeado={r['semeado']} motivo={r['motivo']}",flush=True)
        from agrosmart.web_server import iniciar
        iniciar(args.host,args.porta,execucao_continua=args.execucao_continua,intervalo_s=args.intervalo,
                eventos_por_ciclo=args.eventos_por_ciclo,limite_leituras=args.limite_leituras);return
    elif args.comando=='monitorar':
        sys.exit(_monitorar(args.url,args.intervalo,args.vezes))
    else:parser.error('Comando não reconhecido')
    print(json.dumps(resultado,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
