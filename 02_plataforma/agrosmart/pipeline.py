"""Pipeline local Raw -> Trusted -> Refined do AgroSmart (Fase 6, instrumentado na Fase 7).

Todas as gravacoes sao locais; idempotencia no trusted e processamento reconstruivel.
A simulacao nao depende de internet, Docker, Kafka nem APIs pagas.
Fase 7: processar(caso=...) registra etapas no event log; sem caso, o comportamento
e as saidas sao identicos aos da Fase 6 (coberto pelos testes de regressao).
"""
from __future__ import annotations

import csv
import io
import json
import os
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from .rastreio import etapa
from .regras import avaliar
from .simulador import TALHOES, simular_campo, simular_historico

PASTA_PROJETO = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("AGROSMART_DATA_DIR", PASTA_PROJETO / "data"))
RAW = DATA_DIR / "raw"
TRUSTED = DATA_DIR / "trusted"
REFINED = DATA_DIR / "refined"

SENSOR_FIELDS = ["data_hora", "sensor_id", "talhao", "cultura", "umidade_solo", "temperatura", "probabilidade_praga", "alerta", "recomendacao"]
CAMPO_FIELDS = ["data", "talhao", "cultura", "percentual_folhas_doentes", "praga_detectada", "dias_mesma_praga", "origem_dados"]
DIAG_FIELDS = ["Data_Hora", "Nome_Imagem", "Diagnostico", "Confianca", "Fonte_Imagem"]
MONITOR_FIELDS = ["data_hora", "sensor_id", "talhao", "cultura", "umidade_solo", "temperatura", "probabilidade_praga", "alerta_origem", "recomendacao_origem", "percentual_folhas_doentes", "praga_detectada", "dias_mesma_praga", "origem_observacao", "regra", "severidade", "alerta", "acao", "justificativa", "avaliacao", "origem_sensor"]


def garantir_pastas():
    for p in (RAW, TRUSTED, REFINED): p.mkdir(parents=True, exist_ok=True)


def gravar_csv(path: Path, colunas: list[str], linhas: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+".tmp")
    with tmp.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=colunas, delimiter=';')
        w.writeheader()
        for linha in linhas:
            w.writerow({c: linha.get(c, "") for c in colunas})
    os.replace(tmp, path)


def ler_csv(path: Path, sep: str = ';') -> list[dict]:
    if not path.exists(): return []
    with path.open('r', newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter=sep))


def data_iso(valor: Any) -> str:
    v = str(valor).strip()
    if not v: raise ValueError("Data ou timestamp vazio")
    try:
        dt = datetime.fromisoformat(v.replace('Z','+00:00'))
    except ValueError as e:
        raise ValueError("Data/hora inválida") from e
    return dt.isoformat(timespec="seconds") if dt.microsecond == 0 else dt.isoformat(timespec="microseconds")


def numero(valor: Any, nome: str, minimo: float, maximo: float) -> float:
    try:
        x = float(str(valor).strip().replace(',', '.'))
    except (ValueError, TypeError): raise ValueError(f"{nome}: número inválido") from None
    if not minimo <= x <= maximo: raise ValueError(f"{nome}: fora do intervalo [{minimo};{maximo}]")
    return x


def validar_sensor(evento: dict) -> dict:
    if not isinstance(evento, dict): raise ValueError('Sensor precisa ser objeto JSON')
    for x in SENSOR_FIELDS:
        if x not in evento or evento[x] is None: raise ValueError('Campo sensor ausente: '+x)
    row = {x:evento[x] for x in SENSOR_FIELDS}
    row['data_hora'] = data_iso(row['data_hora'])
    for x in ('sensor_id','talhao','cultura'):
        row[x] = str(row[x]).strip()
        if not row[x]: raise ValueError(x+' obrigatório')
    # Controle de referencia usado para a demonstracao, derivado do simulador F4.
    if row['talhao'] not in TALHOES: raise ValueError('Talhão não cadastrado: '+row['talhao'])
    if row['cultura'] != TALHOES[row['talhao']]: raise ValueError('Cultura não corresponde ao talhão da simulação')
    row['umidade_solo'] = numero(row['umidade_solo'], 'umidade_solo', 0, 100)
    row['temperatura'] = numero(row['temperatura'], 'temperatura', -50, 70)
    row['probabilidade_praga'] = numero(row['probabilidade_praga'], 'probabilidade_praga', 0, 100)
    row['alerta'] = str(row['alerta'])
    row['recomendacao'] = str(row['recomendacao'])
    return row


def validar_campo(dados: dict) -> dict:
    for x in CAMPO_FIELDS[:-1]:
        if x not in dados or dados[x] is None or str(dados[x]).strip() == '': raise ValueError('Observação sem '+x)
    v = {x: str(dados.get(x, '')).strip() for x in CAMPO_FIELDS}
    try: v['data'] = datetime.fromisoformat(v['data']).date().isoformat()
    except ValueError: raise ValueError('Data da observação inválida') from None
    if v['talhao'] not in TALHOES or v['cultura'] != TALHOES[v['talhao']]: raise ValueError('Talhão/cultura incompatíveis')
    v['percentual_folhas_doentes'] = numero(v['percentual_folhas_doentes'], 'folhas', 0, 100)
    d = numero(v['dias_mesma_praga'], 'dias_mesma_praga', 0, 366)
    if int(d) != d: raise ValueError('dias_mesma_praga precisa ser inteiro')
    v['dias_mesma_praga'] = int(d)
    v['origem_dados'] = v['origem_dados'] or 'arquivo do usuário'
    return v


def normalizar_diagnostico(valor: str) -> str:
    nome = unicodedata.normalize('NFKD',str(valor)).encode('ascii','ignore').decode().casefold()
    if 'saudavel' in nome: return 'Folha saudável'
    if 'doenca' in nome: return 'Doença detectada'
    if 'patogeno' in nome: return 'Outro patógeno'
    return 'Não classificado'


def validar_diagnostico(dados: dict) -> dict:
    for x in DIAG_FIELDS:
        if x not in dados: raise ValueError('Diagnóstico sem '+x)
    confianca = numero(str(dados['Confianca']).replace('%',''), 'Confianca', 0, 100)
    data = data_iso(dados['Data_Hora'])
    nome = str(dados['Nome_Imagem']).strip()
    return {'data_hora':data, 'nome_imagem':nome, 'diagnostico_original':str(dados['Diagnostico']), 'diagnostico':normalizar_diagnostico(dados['Diagnostico']), 'confianca_pct':confianca, 'fonte_imagem':str(dados['Fonte_Imagem']), 'tipo_amostra':'Simulada (nome do arquivo)' if nome.lower().startswith('simulado_') else 'Outra origem no CSV histórico', 'talhao':'', 'cultura':''}


def adicionar_evento(evento: dict, origem: str = 'simulador_local'):
    """Preserva dado recebido na raw, mesmo quando houver falha de validacao.

    A validacao e feita primeiro na interface para devolver erro, mas o fluxo bruto
    continua auditavel e o trusted pode ser reconstruido.
    """
    garantir_pastas()
    envelope = {'recebido_em_utc':datetime.now(timezone.utc).isoformat(), 'origem':origem, 'evento':evento}
    with (RAW / 'sensores.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps(envelope,ensure_ascii=False)+'\n')


def validar_observacoes_csv(texto: str) -> list[dict]:
    """Valida TODO o CSV de observacoes antes de qualquer gravacao (Fase 6, separado na Fase 7)."""
    if len(texto) > 100_000: raise ValueError('Arquivo excede limite de 100 KB')
    reader = csv.DictReader(io.StringIO(texto.lstrip('\ufeff')), delimiter=';')
    if not reader.fieldnames or any(x not in reader.fieldnames for x in CAMPO_FIELDS[:-1]):
        raise ValueError('CSV deve conter colunas: '+', '.join(CAMPO_FIELDS[:-1]))
    novas = [validar_campo(r) for r in reader]
    if not novas: raise ValueError('CSV sem registros')
    return novas


def gravar_observacoes(novas: list[dict]) -> int:
    garantir_pastas()
    arquivo = RAW/'observacoes_campo.csv'
    antigas = ler_csv(arquivo)
    gravar_csv(arquivo, CAMPO_FIELDS, antigas+novas)
    return len(novas)


def adicionar_observacoes_csv(texto: str) -> int:
    """Importa CSV de observacoes com validacao atomica e cabecalho existente."""
    return gravar_observacoes(validar_observacoes_csv(texto))


def reset_demo(origem_diagnosticos: Path | None = None) -> dict:
    """Regera amostras com semente fixa; nao sobrescreve fases anteriores."""
    garantir_pastas()
    inicio = datetime(2026, 9, 27)
    eventos = simular_historico(inicio=inicio, dias=12, por_dia=4, semente=96)
    with (RAW/'sensores.jsonl').open('w',encoding='utf-8') as f:
        for e in eventos:
            f.write(json.dumps({'recebido_em_utc':datetime.now(timezone.utc).isoformat(), 'origem':'simulacao_historica_fase6','evento':e},ensure_ascii=False)+'\n')
    gravar_csv(RAW/'observacoes_campo.csv', CAMPO_FIELDS, simular_campo(inicio, dias=12))
    if origem_diagnosticos and origem_diagnosticos.is_file():
        (RAW/'diagnosticos_historicos.csv').write_bytes(origem_diagnosticos.read_bytes())
    return processar()


def _estado_anterior() -> dict:
    caminho = REFINED/'estado_pipeline.json'
    try:
        return json.loads(caminho.read_text(encoding='utf-8')) if caminho.is_file() else {}
    except (OSError, ValueError):
        return {}


def processar(caso=None) -> dict:
    """Reconstroi Trusted/Refined a partir de todo o Raw.

    caso (rastreio.Caso, opcional): registra as etapas no event log da Fase 7.
    As instrucoes de transformacao e a ordem de gravacao sao as da Fase 6.
    """
    garantir_pastas()
    anterior = _estado_anterior() if caso is not None else {}
    with etapa(caso, 'Publicar Trusted') as info:
        rejeitados = []
        sensores_dict = {}
        raw_path = RAW/'sensores.jsonl'
        raw_count = 0
        for idx,linha in enumerate(raw_path.read_text(encoding='utf-8').splitlines() if raw_path.exists() else [], start=1):
            if not linha.strip(): continue
            raw_count += 1
            try:
                env=json.loads(linha)
                dado = validar_sensor(env['evento'])
                dado['origem_sensor'] = env.get('origem', 'não informada')
                chave=(dado['data_hora'], dado['sensor_id'], dado['talhao'])
                # Primeiro evento valido vence: reconstruir nao duplica.
                sensores_dict.setdefault(chave, dado)
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                rejeitados.append({'fonte':'sensores','linha':idx,'motivo':str(exc)})
        sensores=list(sensores_dict.values())
        sensores.sort(key=lambda x:(x['data_hora'],x['talhao']))
        gravar_csv(TRUSTED/'sensores.csv', SENSOR_FIELDS+['origem_sensor'],sensores)

        campo_dict={}
        for idx, row in enumerate(ler_csv(RAW/'observacoes_campo.csv'),start=2):
            try:
                v=validar_campo(row)
                campo_dict[(v['data'],v['talhao'],v['cultura'])]=v
            except ValueError as exc:
                rejeitados.append({'fonte':'observacoes_campo','linha':idx,'motivo':str(exc)})
        campos=list(campo_dict.values()); campos.sort(key=lambda x:(x['data'],x['talhao']))
        gravar_csv(TRUSTED/'observacoes_campo.csv', CAMPO_FIELDS,campos)

        diagnosticos_dict={}
        for idx, row in enumerate(ler_csv(RAW/'diagnosticos_historicos.csv'),start=2):
            try:
                v=validar_diagnostico(row)
                diagnosticos_dict[(v['data_hora'],v['nome_imagem'])]=v
            except ValueError as exc:
                rejeitados.append({'fonte':'diagnosticos','linha':idx,'motivo':str(exc)})
        diagn=list(diagnosticos_dict.values()); diagn.sort(key=lambda x:x['data_hora'])
        diagcols=['data_hora','nome_imagem','diagnostico_original','diagnostico','confianca_pct','fonte_imagem','tipo_amostra','talhao','cultura']
        gravar_csv(TRUSTED/'diagnosticos.csv',diagcols,diagn)
        gravar_csv(REFINED/'diagnosticos.csv',diagcols,diagn)
        info['records_in'] = raw_count
        info['records_out'] = len(sensores)

    if caso is not None:
        duplicados = raw_count-len(sensores)-sum(e['fonte']=='sensores' for e in rejeitados)
        novos_dup = duplicados - int(anterior.get('duplicados_removidos', 0) or 0)
        novos_rej = len(rejeitados) - int(anterior.get('rejeitados', 0) or 0)
        if novos_dup > 0:
            caso.registrar('Descartar duplicatas', component='pipeline', records_in=novos_dup,
                           detail='chave data_hora+sensor_id+talhao; primeiro evento valido vence')
        if novos_rej > 0:
            caso.registrar('Quarentenar registros inválidos', status='rejeitado', component='pipeline',
                           records_in=novos_rej, detail='trusted/rejeitados.csv')

    with etapa(caso, 'Aplicar regras R1–R7') as info:
        rows=[]
        for s in sensores:
            campo=campo_dict.get((s['data_hora'][:10],s['talhao'],s['cultura']))
            decisao=avaliar(s,campo).to_dict()
            rows.append({
                'data_hora':s['data_hora'], 'sensor_id':s['sensor_id'], 'talhao':s['talhao'], 'cultura':s['cultura'],
                'umidade_solo':s['umidade_solo'], 'temperatura':s['temperatura'], 'probabilidade_praga':s['probabilidade_praga'],
                'alerta_origem':s['alerta'], 'recomendacao_origem':s['recomendacao'],
                'percentual_folhas_doentes':campo['percentual_folhas_doentes'] if campo else '',
                'praga_detectada':campo['praga_detectada'] if campo else '',
                'dias_mesma_praga':campo['dias_mesma_praga'] if campo else '',
                'origem_observacao':campo['origem_dados'] if campo else 'Ausente',
                **decisao, 'origem_sensor':s['origem_sensor'],
            })
        info['records_in'] = len(sensores)
        info['records_out'] = sum(r['regra'] not in ('R7','ND') for r in rows)

    with etapa(caso, 'Publicar Refined') as info:
        gravar_csv(REFINED/'monitoramento.csv',MONITOR_FIELDS,rows)
        gravar_csv(REFINED/'alertas.csv',MONITOR_FIELDS,[r for r in rows if r['regra'] not in ('R7','ND')])

        por_talhao=defaultdict(list)
        por_data=defaultdict(list)
        for r in rows:
            por_talhao[(r['talhao'],r['cultura'])].append(r)
            por_data[(r['data_hora'][:10],r['talhao'])].append(r)
        agregados=[]
        for (t,c),rs in por_talhao.items():
            agregados.append({'talhao':t,'cultura':c,'leituras':len(rs),'umidade_media':round(mean(float(r['umidade_solo']) for r in rs),1),'temperatura_media':round(mean(float(r['temperatura']) for r in rs),1),'alertas':sum(r['regra'] not in ('R7','ND') for r in rs),'criticos':sum(r['regra']=='R1' for r in rs),'ultima_leitura':rs[-1]['data_hora'],'ultima_regra':rs[-1]['regra']})
        aggcols=['talhao','cultura','leituras','umidade_media','temperatura_media','alertas','criticos','ultima_leitura','ultima_regra']
        gravar_csv(REFINED/'indicadores_talhoes.csv',aggcols,agregados)
        serie=[]
        for (dia,t),rs in sorted(por_data.items()):
            serie.append({'data':dia,'talhao':t,'leituras':len(rs),'umidade_media':round(mean(float(r['umidade_solo']) for r in rs),1),'temperatura_media':round(mean(float(r['temperatura']) for r in rs),1),'alertas':sum(r['regra'] not in ('R7','ND') for r in rs)})
        gravar_csv(REFINED/'serie_temporal.csv',['data','talhao','leituras','umidade_media','temperatura_media','alertas'],serie)
        gravar_csv(TRUSTED/'rejeitados.csv',['fonte','linha','motivo'],rejeitados)
        estatisticas = {'raw_sensores':raw_count,'trusted_sensores':len(sensores),'duplicados_removidos':raw_count-len(sensores)-sum(e['fonte']=='sensores' for e in rejeitados),'observacoes_campo':len(campos),'diagnosticos_historicos':len(diagn),'monitoramento_refinado':len(rows),'alertas':sum(r['regra'] not in ('R7','ND') for r in rows),'rejeitados':len(rejeitados),'regras':dict(Counter(r['regra'] for r in rows)),'modo':'Simulação acadêmica / processamento local'}
        (REFINED/'estado_pipeline.json').write_text(json.dumps(estatisticas,ensure_ascii=False,indent=2),encoding='utf-8')
        info['records_in'] = len(rows)
        info['records_out'] = len(rows)
    return estatisticas


def carregar_refinado() -> list[dict]:
    return ler_csv(REFINED/'monitoramento.csv')


def carregar_diagnosticos() -> list[dict]:
    return ler_csv(REFINED/'diagnosticos.csv')


def estado_dashboard(talhao: str = '', inicio: str = '', fim: str = '') -> dict:
    linhas=carregar_refinado()
    if talhao: linhas=[x for x in linhas if x['talhao']==talhao]
    if inicio: linhas=[x for x in linhas if x['data_hora'][:10]>=inicio]
    if fim: linhas=[x for x in linhas if x['data_hora'][:10]<=fim]
    todas=len(linhas)
    criticas=sum(x['regra']=='R1' for x in linhas)
    em_alerta=[x for x in linhas if x['regra'] not in ('R7','ND')]
    medias=(round(mean(float(x['umidade_solo']) for x in linhas),1),round(mean(float(x['temperatura']) for x in linhas),1)) if linhas else (0,0)
    ultimo={}
    por_dia=defaultdict(list)
    contagem=Counter()
    for r in linhas:
        ultimo[r['talhao']]=r
        por_dia[r['data_hora'][:10]].append(r)
        contagem[r['regra']]+=1
    serie=[]
    for dia,arr in sorted(por_dia.items()):
        serie.append({'data':dia,'umidade_media':round(mean(float(r['umidade_solo']) for r in arr),1),'temperatura_media':round(mean(float(r['temperatura']) for r in arr),1),'alertas':sum(r['regra'] not in ('R7','ND') for r in arr)})
    talhoes=[]
    for t,arr in sorted(((t,[x for x in linhas if x['talhao']==t]) for t in ultimo),key=lambda a:a[0]):
        u=arr[-1]
        talhoes.append({'talhao':t,'cultura':u['cultura'],'leituras':len(arr),'umidade_media':round(mean(float(x['umidade_solo']) for x in arr),1),'temperatura_media':round(mean(float(x['temperatura']) for x in arr),1),'alertas':sum(x['regra'] not in ('R7','ND') for x in arr),'criticos':sum(x['regra']=='R1' for x in arr),'regra_atual':u['regra'],'severidade_atual':u['severidade'],'ultima_leitura':u['data_hora']})
    diagn=carregar_diagnosticos()
    counts=Counter(x['diagnostico'] for x in diagn)
    classificacao_tipos=Counter(x['tipo_amostra'] for x in diagn)
    pipeline={}
    p=REFINED/'estado_pipeline.json'
    if p.is_file():pipeline=json.loads(p.read_text(encoding='utf-8'))
    return {'metadados':{'projeto':'AgroSmart','modulo':'AgroMonitor','origem':'Dados simulados para fins acadêmicos','ultimo_registro':linhas[-1]['data_hora'] if linhas else None,'filtro_talhao':talhao},
        'kpis':{'leituras':todas,'talhoes':len(ultimo),'alertas':len(em_alerta),'criticos':criticas,'umidade_media':medias[0],'temperatura_media':medias[1], 'cobertura_campo_pct':round(100*sum(x['avaliacao']=='Completa' for x in linhas)/todas,1) if todas else 0},
        'serie':serie,'distribuicao_regras':dict(contagem),'talhoes':talhoes,'alertas':list(reversed(em_alerta))[:120],'ultimas_leituras':list(reversed(linhas))[:120],
        'ultimas_por_talhao':list(ultimo.values()),
        'diagnosticos':{'total':len(diagn),'classes':dict(counts),'tipos':dict(classificacao_tipos),'confianca_media':round(mean(float(x['confianca_pct']) for x in diagn),1) if diagn else None,'ultimos':list(reversed(diagn))[:12], 'observacao':'Diagnósticos históricos não possuem identificação de talhão e não são vinculados automaticamente aos sensores.'},
        'pipeline':pipeline,'filtros':{'talhoes':list(TALHOES),'data_minima':min((x['data_hora'][:10] for x in carregar_refinado()), default=''),'data_maxima':max((x['data_hora'][:10] for x in carregar_refinado()), default='')},
    }
