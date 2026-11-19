// Testes funcionais de JS com DOM substituído; não são testes de navegador/layout.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8');

function fixture(empty=false){
  return {
    metadados:{ultimo_registro:empty?null:'2026-10-08T18:00:00'},
    kpis:{leituras:empty?0:144,talhoes:empty?0:3,alertas:empty?0:109,criticos:empty?0:8,umidade_media:empty?0:44,temperatura_media:empty?0:30.2},
    serie:empty?[]:[{data:'2026-10-08',umidade_media:44,temperatura_media:30.2}],
    talhoes:[],ultimas_leituras:[],ultimas_por_talhao:[],distribuicao_regras:{},pipeline:{},
    alertas:empty?[]:Array.from({length:109},()=>({alerta:'Alerta crítico',regra:'R1',severidade:'Crítica',talhao:'Talhao B',cultura:'Milho',data_hora:'2026-10-06T12:00:00',avaliacao:'Completa',justificativa:'Origem <script> não executável',acao:'Intervenção imediata'})),
    diagnosticos:{total:766,confianca_media:91,classes:{'Folha saudável':525},ultimos:[]}
  };
}

function app(){
  const elements = new Map();
  function element(id){
    if(!elements.has(id)){
      const attrs=new Map();
      elements.set(id,{id,value:'',textContent:'',innerHTML:'',hidden:false,disabled:false,files:[],dataset:{},
        classList:{toggle(){}},setAttribute(k,v){attrs.set(k,v);if(k==='hidden')this.hidden=true;},
        removeAttribute(k){attrs.delete(k);if(k==='hidden')this.hidden=false;},getAttribute(k){return attrs.get(k);},addEventListener(){},focus(){},scrollIntoView(){},close(){this.open=false;},open:false});
    }
    return elements.get(id);
  }
  const tabs=['geral','talhoes','alertas','diagnosticos','pipeline'];
  const nav=tabs.map(t=>{const e=element('nav'+t);e.dataset.tab=t;return e;});
  const panes=tabs.map(t=>element('pane'+t));
  const sandbox={Intl,URLSearchParams,document:{getElementById:element,querySelectorAll:s=>s==='.nav-item'?nav:panes},
    window:{addEventListener(){},scrollTo(){}},history:{replaceState(){},pushState(){}},location:{pathname:'/',search:'',hash:''},
    fetch:async()=>({ok:true,json:async()=>fixture()})};
  const context=vm.createContext(sandbox);
  vm.runInContext(source,context);
  return {el:element,nav,panes,context,run:code=>vm.runInContext(code,context),setState:d=>{context.testState=d;vm.runInContext('estado=testState;',context);}};
}

test('no readings show missing averages',()=>{
  const a=app();a.setState(fixture(true));a.run('render()');
  assert.match(a.el('umidadeContexto').textContent,/Sem leituras válidas/);
  assert.doesNotMatch(a.el('umidadeContexto').textContent,/0%|0°C/);
  assert.match(a.el('chartUmidade').innerHTML,/Nenhum registro/);
  assert.match(a.el('dataRef').textContent,/Sem leituras/);
});

test('measured zero remains a valid measurement',()=>{
  const a=app();const d=fixture();d.kpis.umidade_media=0;d.kpis.temperatura_media=0;a.setState(d);a.run('render()');
  assert.match(a.el('umidadeContexto').textContent,/0%/);assert.match(a.el('temperaturaContexto').textContent,/0°C/);
});

test('diagnostics and pipeline use their full scope',()=>{
  const a=app();a.el('fTalhao').value='Talhao B';a.el('fInicio').value='2030-01-01';
  a.run("tab('diagnosticos')");assert.equal(a.el('sensorFilters').hidden,true);
  assert.equal(a.run('urlEstado()'),'/api/estado');assert.match(a.el('scopeNote').textContent,/Todo o CSV/);
  assert.equal(a.nav[3].getAttribute('aria-current'),'page');
  a.run("tab('pipeline')");assert.equal(a.el('sensorFilters').hidden,true);
  a.run("tab('talhoes')");assert.equal(a.el('sensorFilters').hidden,false);
  assert.match(a.run('urlEstado()'),/talhao=Talhao\+B/);assert.equal(a.el('fInicio').value,'2030-01-01');
});

test('alert counts distinguish displayed and total and escape content',()=>{
  const a=app();a.setState(fixture());a.run("tabAtual='alertas';render()");
  a.context.testAlerts={itens:fixture().alertas.slice(0,20),total:109,pagina:1,paginas:6,inicio_exibido:1,fim_exibido:20,severidades:{'Crítica':8,Alta:61,'Média':40}};
  a.run('alertasPagina=testAlerts;render()');
  assert.match(a.el('contagemAlertas').textContent,/1–20 de 109/);
  assert.equal((a.el('alertList').innerHTML.match(/class="occurrence /g)||[]).length,20);
  assert.equal(a.el('btnAnterior').disabled,true);assert.equal(a.el('btnProxima').disabled,false);
  assert.match(a.el('alertList').innerHTML,/&lt;script&gt;/);
  assert.doesNotMatch(a.el('alertList').innerHTML,/<script>/);
});

test('aggregate chart and latest date have explicit context',()=>{
  const a=app();a.setState(fixture());a.run("tabAtual='talhoes';render()");
  assert.match(a.el('talhoesSerieEscopo').textContent,/agregada de todos/);
  assert.match(a.el('chartTalhoes').innerHTML,/Consultar valores diários/);
  assert.match(a.el('dataRef').textContent,/08\/10\/2026 · 18:00/);
});

test('old responses cannot replace the latest filter response',async()=>{
  const a=app();const pending=[];a.context.fetch=()=>new Promise(resolve=>pending.push(resolve));
  const first=a.run('atualizar()');a.el('fTalhao').value='Talhao B';const second=a.run('atualizar()');
  const recent=fixture();recent.kpis.leituras=48;
  pending[1]({ok:true,json:async()=>recent});assert.equal(await second,true);
  pending[0]({ok:true,json:async()=>fixture()});assert.equal(await first,false);
  assert.equal(a.run('estado.kpis.leituras'),48);assert.equal(a.el('btnRefresh').disabled,false);
});

test('invalid interval and HTTP failure hide old results and allow retry',async()=>{
  const a=app();a.setState(fixture());a.el('fInicio').value='2026-10-08';a.el('fFim').value='2026-10-01';
  assert.equal(await a.run('atualizar()'),false);assert.equal(a.run('estado'),null);
  assert.ok(a.panes.every(p=>p.hidden));assert.equal(a.el('btnRefresh').disabled,false);
  a.el('fFim').value='2026-10-09';a.context.fetch=async()=>({ok:false,status:500});
  assert.equal(await a.run('atualizar()'),false);assert.match(a.el('consultaMensagem').textContent,/tentar novamente/);
  assert.equal(a.el('btnRefresh').disabled,false);
});

test('simulation preserves filters and separates mutation and refresh outcomes',async()=>{
  const a=app();a.el('fTalhao').value='Talhao B';a.el('fInicio').value='2026-09-27';a.el('fFim').value='2026-10-08';
  a.el('sQuantidade').value='1';
  a.context.fetch=async(url)=>url==='/api/simular'
    ?{ok:true,json:async()=>({eventos:[{sensor_id:'S-002'}],pipeline:{trusted_sensores:145}})}
    :{ok:false,status:500};
  await a.run('executarSimulacao()');
  assert.equal(a.el('fTalhao').value,'Talhao B');assert.equal(a.el('fInicio').value,'2026-09-27');
  assert.equal(a.el('fFim').value,'2026-10-08');assert.match(a.el('simMensagem').textContent,/145 leituras válidas/);
  assert.match(a.el('simMensagem').textContent,/operação foi concluída/);
  assert.equal(a.el('btnSimular').disabled,false);assert.equal(a.el('btnImportar').disabled,false);
});

test('import disables resubmission and preserves context',async()=>{
  const a=app();a.el('fTalhao').value='Talhao C';let finish,started;
  const requested=new Promise(resolve=>{started=resolve;});
  a.el('inputCSV').files=[{size:200,text:async()=> 'csv'}];
  a.context.fetch=async(url)=>url==='/api/importar-observacoes'
    ?new Promise(resolve=>{finish=resolve;started();})
    :{ok:true,json:async()=>fixture()};
  const operation=a.run('importarCSV()');await requested;
  assert.equal(a.el('btnImportar').disabled,true);assert.equal(a.el('btnSimular').disabled,true);
  finish({ok:true,json:async()=>({observacoes_importadas:1})});await operation;
  assert.equal(a.el('fTalhao').value,'Talhao C');assert.match(a.el('uploadFeedback').textContent,/Filtros mantidos/);
  assert.equal(a.el('btnImportar').disabled,false);
});

test('server import rejection releases buttons and preserves context',async()=>{
  const a=app();a.el('fTalhao').value='Talhao B';
  a.context.fetch=async()=>({ok:false,json:async()=>({erro:'Arquivo excede limite de 100 KB'})});
  a.el('inputCSV').files=[{size:100001,text:async()=> 'csv'}];await a.run('importarCSV()');
  assert.match(a.el('uploadFeedback').textContent,/Erro: Arquivo excede/);
  assert.equal(a.el('btnImportar').disabled,false);assert.equal(a.el('btnSimular').disabled,false);
  assert.equal(a.el('fTalhao').value,'Talhao B');
});

test('reading evidence uses actual schema and ND stays undetermined',()=>{
  const a=app();a.context.row={data_hora:'2026-10-08T18:00:00',regra:'ND',severidade:'Indeterminada',avaliacao:'Parcial',umidade_solo:'0',temperatura:'0',percentual_folhas_doentes:'',praga_detectada:'',dias_mesma_praga:'',acao:'Coletar dados',justificativa:'Faltam campos'};
  const html=a.run('leituraCard(row)');
  assert.match(html,/não significa risco baixo/);assert.match(html,/Não informado/);
  assert.match(html,/0%/);assert.match(html,/0°C/);
  a.context.row.percentual_folhas_doentes='20';a.context.row.praga_detectada='Pulgão';a.context.row.dias_mesma_praga='1';
  assert.match(a.run('evidencia(row,true)'),/20%/);assert.match(a.run('evidencia(row,true)'),/Pulgão/);
});

test('context URLs preserve period severity page and exact reading',()=>{
  const a=app();a.el('fTalhao').value='Talhao A';a.el('fInicio').value='2026-10-01';a.el('fFim').value='2026-10-08';a.el('fSeveridade').value='Crítica';
  a.run("paginaAtual=3;leituraContexto={data_hora:'2026-10-04T18:00:00',sensor_id:'S-001'}");
  const url=a.run("rotaURL('talhoes')");assert.match(url,/data_hora=/);assert.match(url,/sensor_id=S-001/);assert.match(url,/inicio=2026-10-01/);assert.match(url,/pagina=3/);
  const all=a.run("rotaURL('talhoes',{talhao:''})");assert.doesNotMatch(all,/talhao=|data_hora=|sensor_id=/);
  assert.match(all,/severidade=/);assert.match(all,/fim=2026-10-08/);
});

test('new alert API receives filters and can return its actual page',async()=>{
  const a=app();a.el('fTalhao').value='Talhao B';a.el('fSeveridade').value='Crítica';a.el('fOrdem').value='prioridade';a.run("tabAtual='alertas';paginaAtual=99");
  const calls=[];a.context.fetch=async(url)=>{calls.push(url);return {ok:true,json:async()=>url.startsWith('/api/alertas')?{itens:[],total:8,pagina:1,paginas:1,inicio_exibido:0,fim_exibido:0,severidades:{'Crítica':8}}:fixture()};};
  assert.equal(await a.run('atualizar()'),true);
  assert.match(calls[1],/talhao=Talhao\+B/);assert.match(calls[1],/pagina=99/);assert.match(calls[1],/tamanho=20/);
  assert.equal(a.run('paginaAtual'),1);assert.equal(a.el('btnProxima').disabled,true);
});

test('plot lookup failure hides prior detail and reports available retry',async()=>{
  const a=app();a.el('fTalhao').value='Talhao B';a.run("tabAtual='talhoes';leituraContexto={data_hora:'2026-10-01T00:00:00',sensor_id:'S-002'}");
  a.context.fetch=async(url)=>url.startsWith('/api/talhao')?{ok:false,status:404,json:async()=>({erro:'Leitura selecionada não encontrada neste talhão e período'})}:{ok:true,json:async()=>fixture()};
  assert.equal(await a.run('atualizar()'),false);assert.equal(a.run('estado'),null);assert.equal(a.run('detalheTalhao'),null);
  assert.ok(a.panes.every(p=>p.hidden));assert.match(a.el('consultaMensagem').textContent,/Leitura selecionada não encontrada/);
});

// Fase 7: painel de execução contínua (DOM substituído; não é teste de navegador).
function operacaoFixture(ativa=true){
  return {estado_funcional:ativa?'atualizado':'sem_execucao_continua',servidor:{uptime_s:125},
    dados:{ultimo_registro:'2026-11-18T10:15:00.123456',idade_ultimo_registro_s:42,raw_sensores:150},
    execucao_continua:{ativa,estado:ativa?'ativa':'parada',motivo_parada:ativa?'':'solicitado pela interface/API',intervalo_s:30,eventos_por_ciclo:3,
      ciclos_total:2,ciclos_sucesso:2,falhas_total:0,falhas_consecutivas:0,
      ultimo_ciclo:{ciclo:2,resultado:'sucesso',duracao_ms:21.5,inicio_utc:'2026-11-18T13:15:00.000+00:00',aceitos:3},
      historico:[{ciclo:2,resultado:'sucesso',duracao_ms:21.5,inicio_utc:'2026-11-18T13:15:00.000+00:00',aceitos:3},{ciclo:1,resultado:'sucesso',duracao_ms:30,inicio_utc:'2026-11-18T13:14:30.000+00:00',aceitos:3}]}};
}

test('operation panel shows active worker, data age and cycle history',()=>{
  const a=app();a.context.testOp=operacaoFixture(true);a.run('renderOperacao(testOp)');
  const status=a.el('operacaoStatus').innerHTML;
  assert.match(status,/Ativa/);assert.match(status,/há 42 s/);assert.match(status,/2 \(2\)/);assert.match(status,/2 min 5 s/);
  assert.match(a.el('operacaoCiclos').innerHTML,/13:15:00/);
  assert.equal(a.el('btnOperacaoIniciar').disabled,true);assert.equal(a.el('btnOperacaoParar').disabled,false);
  assert.match(a.el('operacaoMensagem').textContent,/ativa/);
});

test('stopped worker explains reason and re-enables start',()=>{
  const a=app();a.context.testOp=operacaoFixture(false);a.run('renderOperacao(testOp)');
  assert.match(a.el('operacaoStatus').innerHTML,/Parada/);
  assert.match(a.el('operacaoStatus').innerHTML,/somente por ação manual/);
  assert.match(a.el('operacaoMensagem').textContent,/solicitado pela interface/);
  assert.equal(a.el('btnOperacaoIniciar').disabled,false);assert.equal(a.el('btnOperacaoParar').disabled,true);
});

test('operation status failure hides previous status instead of showing stale data',async()=>{
  const a=app();a.context.testOp=operacaoFixture(true);a.run('renderOperacao(testOp)');
  a.context.fetch=async()=>({ok:false,status:503,json:async()=>({erro:'indisponível'})});
  const ok=await a.run('atualizarOperacao()');
  assert.equal(ok,false);assert.equal(a.el('operacaoStatus').innerHTML,'');
  assert.match(a.el('operacaoMensagem').textContent,/Não foi possível consultar/);
});

test('server without operation data does not crash the tools page',()=>{
  const a=app();a.run('renderOperacao({})');
  assert.match(a.el('operacaoMensagem').textContent,/indisponível/);
});
