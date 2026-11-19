'use strict';
// AgroSmart: frontend local em JavaScript nativo. Regras calculadas pelo Python.
const $ = id => document.getElementById(id);
const PAGE_META = {
  geral:['Visão Geral','Situação na última leitura registrada de cada talhão.'],
  talhoes:['Talhões','Indicadores, evidências e histórico por área.'],
  alertas:['Central de Alertas','Investigue as ocorrências pela prioridade ou pela recência.'],
  diagnosticos:['Diagnósticos Históricos','O que o CSV histórico de classificação por imagem registra.'],
  pipeline:['Ferramentas de demonstração','Pipeline local, simulação e importação de observações de campo.']
};
let estado = null, alertasPagina = null, detalheTalhao = null;
let tabAtual = 'geral', consultaAtual = 0, paginaAtual = 1, leituraContexto = null;
let operacaoConsulta = 0, operacaoOcupada = false;
const nf = new Intl.NumberFormat('pt-BR',{maximumFractionDigits:1});
const fmt = n => nf.format(Number(n ?? 0));
function esc(x){return String(x ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');}
function data(x){return x ? x.slice(0,10).split('-').reverse().join('/') : '—';}
function hora(x){return x ? `${data(x)} · ${x.slice(11,16)}` : '—';}
function nomeTalhao(x){return String(x || '').replace('Talhao','Talhão');}
function nomeCultura(x){return x==='Cafe'?'Café':x;}
function severidade(x){return `<span class="badge b-${esc(x)}">${esc(x)}</span>`;}
function medida(x,unit){return x===null||x===undefined||x===''?'Não informado':`${fmt(x)}${unit}`;}
function filtros(){const p=new URLSearchParams();for(const [id,key] of [['fTalhao','talhao'],['fInicio','inicio'],['fFim','fim']])if($(id).value)p.set(key,$(id).value);return p;}
function urlEstado(){const p=['diagnosticos','pipeline'].includes(tabAtual)?new URLSearchParams():filtros();return '/api/estado'+(p.toString()?'?'+p:'');}
function rotaURL(nome,opcoes={}){
  const p=filtros();
  if($('fSeveridade').value)p.set('severidade',$('fSeveridade').value);
  if($('fOrdem').value==='recencia')p.set('ordem','recencia');
  if(paginaAtual>1)p.set('pagina',String(paginaAtual));
  if(Object.hasOwn(opcoes,'talhao')){if(opcoes.talhao)p.set('talhao',opcoes.talhao);else p.delete('talhao');}
  const leitura=Object.hasOwn(opcoes,'leitura')?opcoes.leitura:(nome==='talhoes'&&!Object.hasOwn(opcoes,'talhao')?leituraContexto:null);
  if(leitura){p.set('data_hora',leitura.data_hora);p.set('sensor_id',leitura.sensor_id);}
  return location.pathname+(p.toString()?'?'+p:'')+(nome==='geral'?'':'#'+nome);
}
function gravarRota(substituir=false){history[substituir?'replaceState':'pushState'](null,'',rotaURL(tabAtual));}
function configurarPagina(){
  const m=PAGE_META[tabAtual];
  $('breadcrumb').textContent=m[0];$('pageTitle').textContent=m[0];$('pageDesc').textContent=m[1];
  const sensores=!['diagnosticos','pipeline'].includes(tabAtual);
  $('sensorFilters').hidden=!sensores;
  $('alertFilters').hidden=tabAtual!=='alertas';
  $('filterLabel').textContent=tabAtual==='alertas'?'Filtros de ocorrências':'Filtros de talhão e período';
  $('scopeNote').textContent=tabAtual==='diagnosticos'
    ? 'Todo o CSV histórico. Filtros de sensores não se aplicam; não há vínculo com talhões.'
    :tabAtual==='pipeline'?'Toda a base local. Filtros de sensores mantidos ao retornar ao monitoramento.'
      :'Sensores e campo simulados. Datas conforme a origem, sem fuso informado. Filtros aplicam-se às leituras e ocorrências.';
  document.querySelectorAll('.nav-item').forEach(b=>{const active=b.dataset.tab===tabAtual;b.classList.toggle('active',active);if(active)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  document.querySelectorAll('.tabpane').forEach(p=>p.classList.toggle('active',p.id===`pane${tabAtual[0].toUpperCase()}${tabAtual.slice(1)}`));
}
async function tab(nome,opcoes={},gravar=true){
  tabAtual=PAGE_META[nome]?nome:'geral';
  if(Object.hasOwn(opcoes,'talhao'))$('fTalhao').value=opcoes.talhao;
  leituraContexto=tabAtual==='talhoes'?(opcoes.leitura||null):null;
  if($('menuDialog').open)$('menuDialog').close();
  configurarPagina();if(gravar)gravarRota();
  $('pageTitle').focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});
  return atualizar();
}
function restaurarRota(){
  const p=new URLSearchParams(location.search);
  for(const [id,key] of [['fTalhao','talhao'],['fInicio','inicio'],['fFim','fim'],['fSeveridade','severidade']])$(id).value=p.get(key)||'';
  $('fOrdem').value=p.get('ordem')||'prioridade';paginaAtual=Number(p.get('pagina')||1);
  const leitura=p.get('data_hora')&&p.get('sensor_id')?{data_hora:p.get('data_hora'),sensor_id:p.get('sensor_id')}:null;
  return tab(location.hash.slice(1)||'geral',{leitura},false);
}
async function lerJSON(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok){let msg='HTTP '+r.status;try{msg=(await r.json()).erro||msg;}catch{}throw Error(msg);}return r.json();}
async function atualizar(){
  const consulta=++consultaAtual;
  estado=null;alertasPagina=null;detalheTalhao=null;
  document.querySelectorAll('.tabpane').forEach(p=>{p.hidden=true;p.setAttribute('aria-busy','true');});
  $('btnRefresh').disabled=true;$('consultaMensagem').setAttribute('role','status');
  $('consultaMensagem').classList.toggle('sr-only',false);$('consultaMensagem').setAttribute('aria-live','polite');
  $('consultaMensagem').textContent='Consultando os dados locais…';
  const sensores=!['diagnosticos','pipeline'].includes(tabAtual);
  try{
    if(sensores&&$('fInicio').value&&$('fFim').value&&$('fInicio').value>$('fFim').value)throw Error('A data inicial deve ser anterior ou igual à data final.');
    const jobs=[lerJSON(urlEstado())];
    if(tabAtual==='alertas'){
      const p=filtros();p.set('severidade',$('fSeveridade').value);p.set('ordem',$('fOrdem').value||'prioridade');p.set('pagina',String(paginaAtual));p.set('tamanho','20');jobs.push(lerJSON('/api/alertas?'+p));
    }else if(tabAtual==='talhoes'&&$('fTalhao').value){
      const p=filtros();if(leituraContexto){p.set('data_hora',leituraContexto.data_hora);p.set('sensor_id',leituraContexto.sensor_id);}jobs.push(lerJSON('/api/talhao?'+p));
    }
    const [d,extra]=await Promise.all(jobs);if(consulta!==consultaAtual)return false;
    estado=d;
    if(tabAtual==='alertas'){alertasPagina=extra;paginaAtual=extra.pagina;gravarRota(true);}
    if(tabAtual==='talhoes')detalheTalhao=extra||null;
    document.querySelectorAll('.tabpane').forEach(p=>{p.hidden=false;});
    render();if(tabAtual==='pipeline')atualizarOperacao();$('consultaMensagem').textContent=tabAtual==='alertas'?`Consulta concluída. ${extra.total} ocorrências no filtro, página ${extra.pagina} de ${extra.paginas}.`:tabAtual==='diagnosticos'?`Consulta concluída. ${d.diagnosticos.total} diagnósticos históricos.`:tabAtual==='pipeline'?'Consulta concluída. Estatísticas de toda a base local.':`Consulta concluída. ${d.kpis.leituras} leituras no filtro.`;$('consultaMensagem').classList.toggle('sr-only',true);return true;
  }catch(e){
    if(consulta!==consultaAtual)return false;
    $('consultaMensagem').setAttribute('role','alert');
    $('consultaMensagem').setAttribute('aria-live','assertive');
    $('consultaMensagem').textContent='Não foi possível consultar os dados. '+e.message+' Use Atualizar dados para tentar novamente.';
    $('dataRef').textContent='Consulta indisponível';return false;
  }finally{if(consulta===consultaAtual){document.querySelectorAll('.tabpane').forEach(p=>p.setAttribute('aria-busy','false'));$('btnRefresh').disabled=false;}}
}
function indicador(label,value,sub='',kind=''){return `<div class="kpi ${kind}"><div class="kpi-name">${esc(label)}</div><div class="kpi-val">${esc(value)}</div><div class="kpi-sub">${esc(sub)}</div></div>`;}
function tabela(headers,rows){if(!rows.length)return vazio();return `<table><thead><tr>${headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;}
function vazio(){return '<div class="empty"><strong>Nenhum registro neste filtro</strong>Altere o período ou limpe os filtros para consultar outras leituras.</div>';}
function linkTalhao(r,label='Ver talhão',leitura=false){
  const opcoes={talhao:r.talhao,...(leitura?{leitura:r}:{})};
  return `<a class="secondary-btn" href="${esc(rotaURL('talhoes',opcoes))}" data-route="talhoes" data-talhao="${esc(r.talhao)}"${leitura?` data-hora="${esc(r.data_hora)}" data-sensor="${esc(r.sensor_id)}"`:''}>${esc(label)}</a>`;
}
function ultimasPriorizadas(){
  const rank={'Crítica':0,'Alta':1,'Média':2,'Indeterminada':3,'Baixa':4};
  return [...(estado.ultimas_por_talhao||[])].sort((a,b)=>(rank[a.severidade]??3)-(rank[b.severidade]??3)||a.talhao.localeCompare(b.talhao));
}
function prioridades(){
  const rows=ultimasPriorizadas();if(!rows.length)return vazio();
  return `<div class="priority-head" aria-hidden="true"><span>Talhão</span><span>Cultura</span><span>Prioridade</span><span>Principal indício</span><span>Última leitura no filtro</span><span class="priority-rule">Regra</span><span></span></div>`+rows.map((r,i)=>`<div class="priority-row ${i>1?'mobile-additional':''}"><div class="priority-name">${esc(nomeTalhao(r.talhao))}<span class="mobile-culture"> · ${esc(nomeCultura(r.cultura))}</span></div><div class="priority-culture">${esc(nomeCultura(r.cultura))}</div><div class="priority-severity">${severidade(r.severidade)}</div><div class="priority-problem">${esc(r.regra==='ND'?'Dados insuficientes':r.alerta)}</div><div class="priority-reading">${medida(r.umidade_solo,'%')} umidade · ${medida(r.temperatura,'°C')}<span class="priority-time">${esc(hora(r.data_hora))}</span></div><div class="priority-rule">${esc(r.regra)}</div>${linkTalhao(r)}</div>`).join('')+`<a class="mobile-priority-link" href="${esc(rotaURL('talhoes'))}" data-route="talhoes">Ver ${rows.length===1?'o talhão':`os ${rows.length} talhões`} do filtro →</a>`;
}
function evidencia(r,campo=false){
  return `<dl class="evidence-grid">${campo?'':`<div><dt>Umidade do solo</dt><dd>${medida(r.umidade_solo,'%')}</dd></div><div><dt>Temperatura</dt><dd>${medida(r.temperatura,'°C')}</dd></div>`}<div><dt>Folhas afetadas</dt><dd>${medida(r.percentual_folhas_doentes,'%')}</dd></div><div><dt>Praga detectada</dt><dd>${esc(r.praga_detectada||'Não informado')}</dd></div><div><dt>Duração</dt><dd>${medida(r.dias_mesma_praga,' dia(s)')}</dd></div></dl>`;
}
function origem(r,aberta=false){
  return `<details class="origin"${aberta?' open':''}><summary>Justificativa e origem · ${esc(r.regra)} · ${esc(r.avaliacao)}</summary><p><strong>Justificativa:</strong> ${esc(r.justificativa)}</p><p><strong>Sensor:</strong> ${esc(r.sensor_id)} · ${esc(r.origem_sensor)}</p><p><strong>Observação de campo:</strong> ${esc(r.origem_observacao)} · união por data, talhão e cultura.</p><p>A probabilidade de praga do simulador (${medida(r.probabilidade_praga,'%')}) não substitui evidência de campo nas regras.</p></details>`;
}
function recomendacao(r){return `<div class="recommendation"><strong>Orientação sugerida · ${esc(r.regra)}</strong>${esc(r.acao)}<p class="small-note">Avaliação e decisão humana; nenhuma intervenção é executada pelo sistema.</p></div>`;}
function leituraCard(r,selecionada=false){
  if(!r)return vazio();
  return `<section class="panel current-reading ${selecionada?'selected-reading':''}"><div class="reading-heading"><h2>${selecionada?'Ocorrência selecionada':'Última leitura no filtro'}</h2>${severidade(r.severidade)}</div><p class="small-note">${esc(hora(r.data_hora))} · ${esc(r.regra)} · ${esc(r.alerta)}</p><div class="reading-metrics"><div><span>Umidade do solo</span><strong>${medida(r.umidade_solo,'%')}</strong></div><div><span>Temperatura</span><strong>${medida(r.temperatura,'°C')}</strong></div><div><span>Avaliação dos dados</span><strong class="evaluation">${esc(r.avaliacao)}</strong></div></div><p class="completeness">${r.regra==='ND'?'ND: sem evidência suficiente para determinar a condição; não significa risco baixo.':r.avaliacao==='Completa'?'Observação de campo disponível para esta leitura.':'Avaliação parcial: verifique os campos disponíveis na origem.'}</p><div class="reading-detail-grid"><div class="field-evidence"><h3>Evidências de campo</h3>${evidencia(r,true)}</div><div>${recomendacao(r)}<p class="reading-reason">${esc(r.justificativa)}</p></div>${origem(r)}</div></section>`;
}
function renderDetalhe(){
  const d=detalheTalhao;
  $('plotsOverview').hidden=!!d;$('plotDetail').hidden=!d;if(!d)return;
  $('pageTitle').textContent=`${nomeTalhao(d.talhao)} · ${nomeCultura(d.cultura)}`;
  $('pageDesc').textContent='Evidências da leitura e orientação das regras; médias separadas por período.';
  const nav=`<div class="detail-nav"><a href="${esc(rotaURL('talhoes',{talhao:''}))}" data-route="talhoes" data-all="true">← Todos os talhões</a><a class="secondary-btn" href="${esc(rotaURL('alertas'))}" data-route="alertas">Consultar ocorrências deste talhão</a></div>`;
  if(!d.ultima_leitura){$('plotDetail').innerHTML=nav+`<section class="panel">${vazio()}</section>`;return;}
  const r=d.resumo;
  $('plotDetail').innerHTML=nav+(d.leitura_selecionada?leituraCard(d.leitura_selecionada,true):'')+leituraCard(d.ultima_leitura)+`<section class="panel"><div class="panel-head"><div><h2>Histórico do período · ${esc(nomeTalhao(d.talhao))}</h2><p>Médias do período; não são valores da última leitura.</p></div></div><dl class="detail-summary"><div><dt>Umidade média</dt><dd>${medida(r.umidade_media,'%')}</dd></div><div><dt>Temperatura média</dt><dd>${medida(r.temperatura_media,'°C')}</dd></div><div><dt>Leituras</dt><dd>${fmt(r.leituras)}</dd></div><div><dt>Ocorrências / críticas</dt><dd>${fmt(r.alertas)} / ${fmt(r.criticos)}</dd></div></dl></section><section class="panel chart-panel"><div class="panel-head"><div><h2>Umidade média diária · ${esc(nomeTalhao(d.talhao))}</h2><p>Somente as leituras desta área no período selecionado.</p></div></div><div id="chartDetalhe" class="chart-wrap"></div><p class="quality">Qualidade: ${fmt(d.observacoes_ausentes)} leitura(s) sem observação de campo. Avaliações: ${Object.entries(d.avaliacoes).map(([k,v])=>esc(k)+': '+fmt(v)).join(' · ')}. Diagnósticos de imagem permanecem independentes.</p></section>`;
  chartLine($('chartDetalhe'),d.serie,'umidade_media','%','#17633f',0,100);
}
function renderAlertas(){
  const d=alertasPagina;if(!d)return;
  $('contagemAlertas').textContent=`Exibindo ${fmt(d.inicio_exibido)}–${fmt(d.fim_exibido)} de ${fmt(d.total)} ocorrências no filtro`;
  $('severityCounts').textContent=['Crítica','Alta','Média'].map(s=>`${fmt(d.severidades[s]||0)} ${s.toLowerCase()}${s==='Crítica'?'s':s==='Alta'?'s':'s'}`).join(' · ');
  $('paginaAlertas').textContent=`Página ${d.pagina} de ${d.paginas}`;
  $('btnAnterior').disabled=d.pagina<=1;$('btnProxima').disabled=d.pagina>=d.paginas;
  $('alertList').innerHTML=d.itens.length?d.itens.map((r,i)=>`<details class="occurrence ${r.severidade==='Crítica'?'critical':r.severidade==='Alta'?'high':''}"${i===0?' open':''}><summary>${severidade(r.severidade)}<span><span class="occurrence-title">${esc(r.alerta)} · ${esc(r.regra)}</span><span class="occurrence-meta">${esc(nomeTalhao(r.talhao))} · ${esc(nomeCultura(r.cultura))} · ${esc(hora(r.data_hora))} · ${esc(r.avaliacao)}</span></span></summary><div class="occurrence-body">${evidencia(r)}${recomendacao(r)}${origem(r)}${linkTalhao(r,'Ver talhão e esta leitura',true)}</div></details>`).join(''):vazio();
}
function render(){
  if(!estado)return;const d=estado,k=d.kpis;
  $('dataRef').textContent=['diagnosticos','pipeline'].includes(tabAtual)?(tabAtual==='diagnosticos'?'Origem: CSV histórico do protótipo':'Escopo: toda a base local'):k.leituras?`Última leitura no filtro: ${hora(d.metadados.ultimo_registro)}`:'Sem leituras no filtro selecionado';
  $('filterSummary').textContent=$('fTalhao').value?nomeTalhao($('fTalhao').value):$('fInicio').value||$('fFim').value?'Período ativo':'Todos';
  if(tabAtual==='alertas')$('filterSummary').textContent=($('fSeveridade').value||'Todas')+' · '+$('filterSummary').textContent;
  if(tabAtual==='geral'){
    $('kpiCards').innerHTML=indicador('Leituras no período',fmt(k.leituras),'Dados de sensores')+indicador('Talhões no período',fmt(k.talhoes),'Áreas com leituras')+indicador('Ocorrências históricas',fmt(k.alertas),'Regras R1–R6')+indicador('Críticas históricas',fmt(k.criticos),'Regra R1','red');
    $('priorityList').innerHTML=prioridades();
    const scope=$('fTalhao').value?nomeTalhao($('fTalhao').value):'Todos os talhões · média agregada';
    $('umidadeContexto').textContent=`${scope} · Média no período: ${k.leituras?medida(k.umidade_media,'%'):'— · Sem leituras válidas'}`;
    $('temperaturaContexto').textContent=`${scope} · Média no período: ${k.leituras?medida(k.temperatura_media,'°C'):'— · Sem leituras válidas'}`;
    chartLine($('chartUmidade'),d.serie,'umidade_media','%','#17633f',0,100);chartLine($('chartTemperatura'),d.serie,'temperatura_media','°C','#a46515');
    barras('regrasBarras',d.distribuicao_regras,['R1','R2','R3','R4','R5','R6','R7','ND']);
  }
  if(tabAtual==='talhoes'){
    renderDetalhe();
    if(!detalheTalhao){
      const last=new Map((d.ultimas_por_talhao||[]).map(r=>[r.talhao,r]));
      $('plotCards').innerHTML=d.talhoes.length?d.talhoes.map(r=>`<article class="plot-card"><div><h3>${esc(nomeTalhao(r.talhao))} · ${esc(nomeCultura(r.cultura))}</h3><p>Última leitura: ${esc(hora(r.ultima_leitura))}</p>${severidade(r.severidade_atual)} <span class="small-note">${esc(r.regra_atual)} · ${esc(last.get(r.talhao)?.alerta||'')}</span></div>${linkTalhao(r)}</article>`).join(''):vazio();
      $('talhoesSerieEscopo').textContent='Média diária agregada de todos os talhões no período; não representa o histórico de uma área individual.';
      chartLine($('chartTalhoes'),d.serie,'umidade_media','%','#17633f',0,100);
      $('tableTalhoesCompleta').innerHTML=tabela(['Talhão','Cultura','Leituras','Umidade média','Temperatura média','Ocorrências','Críticas','Última regra'],d.talhoes.map(r=>[linkTalhao(r,nomeTalhao(r.talhao)),esc(nomeCultura(r.cultura)),fmt(r.leituras),medida(r.umidade_media,'%'),medida(r.temperatura_media,'°C'),fmt(r.alertas),fmt(r.criticos),esc(r.regra_atual)]));
    }
    const rows=d.ultimas_leituras.slice(0,25);
    $('contagemLeituras').textContent=`Exibindo ${rows.length} de ${k.leituras} leituras do filtro, mais recentes. Role a tabela para consultar todas as colunas.`;
    $('tableLeituras').innerHTML=tabela(['Data/hora','Sensor','Talhão','Umidade','Temperatura','Folhas afetadas','Praga / dias','Regra','Avaliação','Detalhe'],rows.map(r=>[esc(hora(r.data_hora)),esc(r.sensor_id),esc(nomeTalhao(r.talhao)),medida(r.umidade_solo,'%'),medida(r.temperatura,'°C'),medida(r.percentual_folhas_doentes,'%'),esc(r.praga_detectada||'Não informado')+' / '+medida(r.dias_mesma_praga,' dia(s)'),esc(r.regra),esc(r.avaliacao),linkTalhao(r,'Ver leitura',true)]));
  }
  if(tabAtual==='alertas')renderAlertas();
  if(tabAtual==='diagnosticos'){
    const diag=d.diagnosticos;
    $('diagCards').innerHTML=indicador('Registros históricos',fmt(diag.total),'Todo o CSV original')+indicador('Confiança média registrada',diag.confianca_media===null?'—':fmt(diag.confianca_media)+'%','Não representa acurácia comprovada')+indicador('Classes disponíveis',fmt(Object.keys(diag.classes).length),'Categorias padronizadas');
    barras('diagBarras',diag.classes,['Folha saudável','Doença detectada','Outro patógeno','Não classificado'],['#327450','#a26a47','#96732b','#707e76']);
    $('contagemDiagnosticos').textContent=`Exibindo ${diag.ultimos.length} de ${diag.total} registros históricos, mais recentes.`;
    $('diagTabela').innerHTML=tabela(['Data/hora','Arquivo','Diagnóstico','Confiança registrada','Tipo de amostra','Fonte'],diag.ultimos.map(r=>[esc(hora(r.data_hora)),esc(r.nome_imagem),esc(r.diagnostico),medida(r.confianca_pct,'%'),esc(r.tipo_amostra),esc(r.fonte_imagem)]));
  }
  if(tabAtual==='pipeline'){
    const p=d.pipeline,fields=[['Raw / eventos recebidos',p.raw_sensores],['Trusted / sensores validados',p.trusted_sensores],['Duplicidades removidas',p.duplicados_removidos],['Observações de campo',p.observacoes_campo],['Diagnósticos históricos',p.diagnosticos_historicos],['Refined / registros publicados',p.monitoramento_refinado],['Ocorrências produzidas',p.alertas],['Registros rejeitados',p.rejeitados]];
    $('pipelineStats').innerHTML=`<div class="stat-list">${fields.map(([l,v])=>`<div class="stat"><span>${esc(l)}</span><b>${fmt(v)}</b></div>`).join('')}</div>`;
  }
  document.querySelectorAll('a[data-route]').forEach(a=>{const opts={};if(a.dataset.all)opts.talhao='';if(a.dataset.talhao)opts.talhao=a.dataset.talhao;if(a.dataset.hora)opts.leitura={data_hora:a.dataset.hora,sensor_id:a.dataset.sensor};a.href=rotaURL(a.dataset.route,opts);});
}
function filtrosAlterados(){paginaAtual=1;leituraContexto=null;gravarRota();return atualizar();}
window.addEventListener('DOMContentLoaded',()=>{
  $('sensorFilters').open=!window.matchMedia('(max-width: 600px)').matches;
  window.matchMedia('(max-width: 600px)').addEventListener('change',e=>{$('sensorFilters').open=!e.matches;});
  document.querySelectorAll('.nav-item').forEach(b=>b.addEventListener('click',()=>tab(b.dataset.tab)));
  document.addEventListener('click',e=>{
    const a=e.target.closest('a[data-route]');if(!a||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
    e.preventDefault();const opts={};if(a.dataset.all)opts.talhao='';if(a.dataset.talhao)opts.talhao=a.dataset.talhao;if(a.dataset.hora)opts.leitura={data_hora:a.dataset.hora,sensor_id:a.dataset.sensor};tab(a.dataset.route,opts);
  });
  $('btnRefresh').addEventListener('click',atualizar);
  ['fTalhao','fInicio','fFim','fSeveridade','fOrdem'].forEach(id=>$(id).addEventListener('change',filtrosAlterados));
  $('btnLimpar').addEventListener('click',()=>{['fTalhao','fInicio','fFim','fSeveridade'].forEach(id=>$(id).value='');$('fOrdem').value='prioridade';filtrosAlterados();});
  $('btnAnterior').addEventListener('click',()=>{if(paginaAtual>1){paginaAtual--;gravarRota();atualizar().then(ok=>{if(ok)$('contagemAlertas').scrollIntoView({block:'center'});});}});
  $('btnProxima').addEventListener('click',()=>{if(alertasPagina&&paginaAtual<alertasPagina.paginas){paginaAtual++;gravarRota();atualizar().then(ok=>{if(ok)$('contagemAlertas').scrollIntoView({block:'center'});});}});
  $('btnSimular').addEventListener('click',executarSimulacao);$('btnImportar').addEventListener('click',importarCSV);
  $('btnOperacaoIniciar').addEventListener('click',()=>controlarOperacao('iniciar'));$('btnOperacaoParar').addEventListener('click',()=>controlarOperacao('parar'));$('btnOperacaoAtualizar').addEventListener('click',atualizarOperacao);
  setInterval(()=>{if(tabAtual==='pipeline'&&document.visibilityState!=='hidden'&&!operacaoOcupada)atualizarOperacao();},10000);
  $('btnMenu').addEventListener('click',()=>$('menuDialog').showModal());$('btnFecharMenu').addEventListener('click',()=>$('menuDialog').close());
  window.addEventListener('popstate',restaurarRota);restaurarRota();
});

// Gráficos e operações existentes preservados.
function chartLine(el,serie,chave,sufixo,cor,limiteMin=null,limiteMax=null){
  if(!el)return;
  if(!serie || !serie.length){el.innerHTML=vazio();return;}
  let rows=serie;
  if(rows.length>18){const f= Math.ceil(rows.length/18);rows=rows.filter((_,i)=>i%f===0 || i===rows.length-1);}
  const W=620,H=225,ml=45,mt=18,mr=14,mb=36, cw=W-ml-mr,ch=H-mt-mb;
  const nums=rows.map(x=>Number(x[chave]));
  let lo=limiteMin??Math.floor((Math.min(...nums)-3)/5)*5;
  let hi=limiteMax??Math.ceil((Math.max(...nums)+3)/5)*5;
  if(hi<=lo)hi=lo+10;
  const x=i=>ml+(rows.length===1?cw/2:(i*cw/(rows.length-1)));
  const y=v=>mt+ch-(v-lo)/(hi-lo)*ch;
  const pts=nums.map((n,i)=>[x(i),y(n)]);
  const line=pts.map((p,i)=>`${i?'L':'M'} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ');
  const area=line+` L ${pts[pts.length-1][0]} ${mt+ch} L ${pts[0][0]} ${mt+ch} Z`;
  const ticks=Array.from({length:5},(_,i)=>lo+(hi-lo)*i/4);
  const g=ticks.map(t=>`<line x1="${ml}" y1="${y(t)}" x2="${ml+cw}" y2="${y(t)}" stroke="#e7eee7" stroke-dasharray="3 4"/><text x="${ml-11}" y="${y(t)+3}" text-anchor="end" font-size="11" fill="#52695e">${fmt(t)}</text>`).join('');
  const labels=rows.map((v,i)=> {if(i!==0 && i!==rows.length-1 && i%Math.max(1,Math.ceil((rows.length-1)/5))!==0)return '';return `<text x="${x(i)}" y="${H-9}" text-anchor="${rows.length===1?'middle':i===0?'start':i===rows.length-1?'end':'middle'}" font-size="10" fill="#52695e">${data(v.data).slice(0,5)}</text>`;}).join('');
  const circles=pts.map((p,i)=>`<circle cx="${p[0]}" cy="${p[1]}" r="3.5" fill="${cor}" stroke="white" stroke-width="1.3"><title>${rows[i].data}: ${fmt(nums[i])}${sufixo}</title></circle>`).join('');
  const nome=chave==='umidade_media'?'Umidade média diária':'Temperatura média diária';
  const escopo=$('fTalhao').value||'todos os talhões';
  const resumo=`${nome} de ${escopo}. ${serie.length} dias; primeiro: ${serie[0].data}, ${fmt(serie[0][chave])}${sufixo}; último: ${serie.at(-1).data}, ${fmt(serie.at(-1)[chave])}${sufixo}.`;
  const gradiente=`area_${el.id}_${chave}`;
  el.innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(resumo)}"> <defs><linearGradient id="${esc(gradiente)}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${cor}" stop-opacity=".19"/><stop offset="1" stop-color="${cor}" stop-opacity="0"/></linearGradient></defs>${g}<path d="${area}" fill="url(#${esc(gradiente)})"/><path d="${line}" stroke="${cor}" stroke-width="3" fill="none" stroke-linejoin="round" stroke-linecap="round"/>${circles}${labels}</svg><details class="chart-data"><summary>Consultar valores diários de ${esc(escopo)}</summary>${tabela(['DATA','MÉDIA'],serie.map(r=>[esc(r.data),esc(fmt(r[chave])+sufixo)]))}</details>`;
}
function barras(el,counts,labels,colors=null){
  const entries=labels.map((l,i)=>[l,Number(counts[l]||0),i]);
  const max=Math.max(1,...entries.map(r=>r[1]));
  $(el).innerHTML=`<div class="bars">${entries.map(([l,v,i])=>`<div class="bar-row"><div class="bar-title">${esc(l)}</div><div class="bar-bg"><div class="bar-fill" style="width:${(v/max)*100}%;${colors?'background:'+colors[i]:''}"></div></div><div class="bar-count">${fmt(v)}</div></div>`).join('')}</div>`;
}

async function executarSimulacao(){
  const btn=$('btnSimular');btn.disabled=true;btn.textContent='Processando...';
  $('btnImportar').disabled=true;
  $('simMensagem').textContent='Gerando novos eventos, validando e aplicando as regras R1–R7...';
  try{
    const r=await fetch('/api/simular',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({talhao:$('sTalhao').value,quantidade:Number($('sQuantidade').value)})});
    const j=await r.json();if(!r.ok)throw Error(j.erro||'Falha na simulação');
    $('sampleJSON').textContent=JSON.stringify(j.eventos.at(-1),null,2);
    $('simMensagem').textContent=`${j.eventos.length} leitura(s) simulada(s) gerada(s) e processada(s). ${j.pipeline.trusted_sensores} leituras válidas na base. Filtros mantidos; novas leituras podem estar fora do período selecionado.`;
    const ok=await atualizar();
    if(!ok)$('simMensagem').textContent+=' A operação foi concluída, mas a consulta da tela não foi atualizada. Use Atualizar dados.';
  } catch(e){ $('simMensagem').textContent='Erro: '+e.message; }
  finally{btn.disabled=false;btn.textContent='Gerar leituras';$('btnImportar').disabled=false;}
}
async function importarCSV(){
  const input=$('inputCSV');if(!input.files.length){$('uploadFeedback').textContent='Escolha um arquivo CSV.';return;}
  $('btnImportar').disabled=true;$('btnSimular').disabled=true;
  try {
    $('uploadFeedback').textContent='Validando o arquivo e reconstruindo as camadas...';
    const csv=await input.files[0].text();
    const r=await fetch('/api/importar-observacoes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({csv})});
    const j=await r.json();if(!r.ok)throw Error(j.erro||'Falha');
    $('uploadFeedback').textContent=`Importação concluída: ${j.observacoes_importadas} observação(ões) validadas. Filtros mantidos.`;
    const ok=await atualizar();
    if(!ok)$('uploadFeedback').textContent+=' A operação foi concluída, mas a consulta da tela não foi atualizada. Use Atualizar dados.';
  } catch(e){ $('uploadFeedback').textContent='Erro: '+e.message; }
  finally{$('btnImportar').disabled=false;$('btnSimular').disabled=false;}
}

// Fase 7: execução contínua e monitoramento (seção técnica secundária das Ferramentas).
function duracaoTexto(seg){
  if(seg===null||seg===undefined||!Number.isFinite(Number(seg)))return 'Não disponível';
  const s=Math.max(0,Math.round(Number(seg)));
  if(s<60)return `${s} s`;if(s<3600)return `${Math.floor(s/60)} min ${s%60} s`;
  if(s<86400)return `${Math.floor(s/3600)} h ${Math.floor((s%3600)/60)} min`;return `${Math.floor(s/86400)} dia(s)`;
}
const ESTADOS_OPERACAO={ativa:'Ativa',parada:'Parada',nunca_iniciada:'Não iniciada',concluida:'Concluída',limite_atingido:'Parada: limite de leituras',interrompida_por_falhas:'Parada por falhas consecutivas'};
const ESTADO_FUNCIONAL={atualizado:'Dados sendo atualizados no intervalo esperado',atrasado:'Atenção: último ciclo bem-sucedido acima do esperado',sem_execucao_continua:'Sem execução contínua: dados atualizam somente por ação manual'};
function renderOperacao(op){
  const ex=op&&op.execucao_continua;
  if(!ex||typeof ex!=='object'){
    $('operacaoStatus').innerHTML='';$('operacaoCiclos').innerHTML='';
    $('operacaoMensagem').textContent='Estado da operação indisponível neste servidor.';return false;
  }
  const dados=op.dados||{},ult=ex.ultimo_ciclo,classe=ex.ativa?'estado-ativa':(['interrompida_por_falhas','limite_atingido'].includes(ex.estado)?'estado-alerta':'estado-parada');
  const linhas=[
    ['Execução contínua',`<span class="estado-operacao ${classe}">${esc(ESTADOS_OPERACAO[ex.estado]||ex.estado)}</span>`],
    ['Situação dos dados',esc(ESTADO_FUNCIONAL[op.estado_funcional]||op.estado_funcional||'—')],
    ['Intervalo / leituras por ciclo',`${esc(fmt(ex.intervalo_s))} s · ${esc(fmt(ex.eventos_por_ciclo))}`],
    ['Ciclos executados (sucesso)',`${esc(fmt(ex.ciclos_total))} (${esc(fmt(ex.ciclos_sucesso))})`],
    ['Falhas (consecutivas)',`${esc(fmt(ex.falhas_total))} (${esc(fmt(ex.falhas_consecutivas))})`],
    ['Último ciclo',ult?`${esc(ult.resultado==='sucesso'?'Sucesso':ult.resultado==='falha'?'Falha':'Não executado')} · ${esc(fmt(ult.duracao_ms))} ms`:'Nenhum ciclo nesta execução do servidor'],
    ['Leitura mais recente',dados.ultimo_registro?`${esc(hora(dados.ultimo_registro))} · há ${esc(duracaoTexto(dados.idade_ultimo_registro_s))}`:'Sem leituras'],
    ['Leituras na base (Raw)',esc(fmt(dados.raw_sensores))],
    ['Servidor no ar há',esc(duracaoTexto(op.servidor&&op.servidor.uptime_s))]
  ];
  $('operacaoStatus').innerHTML=`<div class="stat-list">${linhas.map(([l,v])=>`<div class="stat"><span>${esc(l)}</span><b>${v}</b></div>`).join('')}</div>`;
  const hist=Array.isArray(ex.historico)?ex.historico.slice(0,8):[];
  $('operacaoCiclos').innerHTML=hist.length?tabela(['CICLO','INÍCIO (UTC)','DURAÇÃO','RESULTADO','ACEITAS'],hist.map(r=>[esc(r.ciclo),esc(String(r.inicio_utc||'').slice(11,19)),esc(fmt(r.duracao_ms)+' ms'),esc(r.resultado),esc(fmt(r.aceitos))])):'<div class="empty"><strong>Nenhum ciclo executado</strong>Inicie a execução contínua para acompanhar os ciclos.</div>';
  $('btnOperacaoIniciar').disabled=!!ex.ativa;$('btnOperacaoParar').disabled=!ex.ativa;
  if(ex.motivo_parada&&!ex.ativa)$('operacaoMensagem').textContent=`Execução contínua parada: ${ex.motivo_parada}.`;
  else $('operacaoMensagem').textContent=ex.ativa?'Execução contínua ativa. Estado consultado agora; atualização automática a cada 10 s nesta tela.':'Execução contínua parada. Escolha o intervalo e inicie quando quiser.';
  return true;
}
async function atualizarOperacao(){
  const n=++operacaoConsulta;
  try{const op=await lerJSON('/api/operacao');if(n!==operacaoConsulta)return false;return renderOperacao(op);}
  catch(e){if(n!==operacaoConsulta)return false;$('operacaoStatus').innerHTML='';$('operacaoCiclos').innerHTML='';$('operacaoMensagem').textContent='Não foi possível consultar o estado da operação. '+e.message+' Use Atualizar estado.';return false;}
}
async function controlarOperacao(acao){
  if(operacaoOcupada)return;operacaoOcupada=true;
  $('btnOperacaoIniciar').disabled=true;$('btnOperacaoParar').disabled=true;
  $('operacaoMensagem').textContent=acao==='iniciar'?'Iniciando a execução contínua…':'Parando a execução contínua…';
  try{
    const corpo=acao==='iniciar'?JSON.stringify({intervalo_s:Number($('oIntervalo').value),eventos_por_ciclo:Number($('oEventos').value)}):'';
    const r=await fetch('/api/operacao/'+acao,{method:'POST',headers:{'Content-Type':'application/json'},body:corpo});
    const j=await r.json();if(!r.ok)throw Error(j.erro||'Falha na operação');
    operacaoConsulta++;renderOperacao({execucao_continua:j.execucao_continua,estado_funcional:j.execucao_continua.ativa?'atualizado':'sem_execucao_continua',dados:{},servidor:{}});
    await atualizarOperacao();
  }catch(e){await atualizarOperacao();$('operacaoMensagem').textContent='Erro: '+e.message;}
  finally{operacaoOcupada=false;}
}
