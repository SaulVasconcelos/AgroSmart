# Indicadores do AgroMonitor — semântica P0/P1

Fontes: [pipeline.py](agrosmart/pipeline.py), [consultas.py](agrosmart/consultas.py), [app.js](web/app.js) e [monitoramento refinado](data/refined/monitoramento.csv). Todos os sensores/observações da base de demonstração são simulados. Um indicador numérico não comprova medição física, problema aberto ou ação executada.

## Monitoramento e priorização

Os rótulos abaixo correspondem às áreas e métricas da interface; os nomes técnicos entre parênteses identificam o campo da API. Talhão e datas inclusivas delimitam o conjunto de leituras. Médias e contagens desse conjunto são históricas, não valores da última leitura.

| Indicador / finalidade | Origem, unidade e cálculo | Interpretação para decisão e limitação |
|---|---|---|
| Leituras no período (leituras) | Contagem de linhas válidas filtradas em monitoramento.csv; leituras | Volume de evidência disponível; reprocessamento não cria leituras duplicadas |
| Talhões no período (talhoes) | Número de áreas distintas com leituras no conjunto; talhões | Abrangência do monitoramento; não conta áreas sem registros no período |
| Ocorrências históricas (alertas) | Contagem de linhas cuja regra é R1–R6; ocorrências | Localiza histórico para investigação; não é quantidade de incidentes ainda abertos |
| Críticas históricas (criticos) | Contagem de R1 no período; ocorrências | Destaca registros de maior severidade; não substitui a condição da última leitura |
| Prioridade por talhão | Última leitura de cada área **dentro do filtro**; regra/severidade/data, sem unidade | Investigação ordenada por Crítica, Alta, Média, Indeterminada, Baixa; não é risco inferido em tempo real; mobile mostra duas prioridades e acesso às demais |
| Umidade média do período | Média aritmética das umidades filtradas, arredondada a 1 decimal; % | Contextualiza histórico; não equivale ao valor instantâneo, calibração ou limiar novo |
| Temperatura média do período | Média aritmética das temperaturas filtradas, arredondada a 1 decimal; °C | Contextualiza variação; interpretação agronômica vem das regras preservadas |
| Última leitura / situação mais recente | Registro mais recente do conjunto ou do talhão; data/hora, regra e severidade | Informa recência e condição registrada; mantém o timestamp da origem sem atribuir fuso ausente |
| Umidade e temperatura da leitura | Valores do registro indicado; % e °C | Sustentam a decisão daquela leitura; separados das médias do período |
| Cobertura de campo (cobertura_campo_pct; disponível na API, sem card próprio na UI atual) | 100 × quantidade com avaliacao='Completa' / leituras, arredondada a 1 decimal; % | Indica completude associada, não qualidade/calibração ou acurácia. Com zero leituras a API devolve 0, mas a interface informa ausência de dados |
| Qualidade no detalhe do talhão | Contagem por avaliacao e observacoes_ausentes (origem_observacao='Ausente'); leituras | Explicita lacunas. R4/R5 podem ser sensoriais; ND permanece Indeterminada |
| Histórico diário de umidade/temperatura | Média por dia do conjunto filtrado, 1 decimal; % / °C; API agrega as leituras | Em Todos os talhões é agregado; no detalhe é série individual. Não interpole medições ausentes; gráficos oferecem tabela |
| Distribuição das avaliações | Contagem por regra R1–R7 e ND em monitoramento filtrado; leituras | Mostra decisões históricas; R7 e ND não são alertas R1–R6 |
| Comparação entre áreas | Por talhão: leituras, médias, ocorrências e críticos; última regra é da última leitura | Compara contexto histórico sem confundir a última condição com média |
| Folhas doentes, praga e duração | Observação de campo do mesmo dia/talhão/cultura; %, texto e dias | Evidência complementar às regras; não calculada a partir de probabilidade ou imagem |
| Probabilidade de praga | Número sorteado/importado no sensor; % | Indicador auxiliar simulado; não é predição validada e não aciona diretamente R1–R7 |

Sem leituras, a interface comunica ausência e não exibe 0%/0 °C como médias medidas; zero efetivamente medido é preservado. O contrato legado de /api/estado retorna médias zero no vazio: o frontend trata o estado sem alterar o contrato.

## Central de Alertas

`/api/alertas` aplica talhão/datas, exclui R7/ND, aplica severidade e ordenação ao conjunto completo e só então pagina. A UI usa 20 por página. Total, faixa “exibindo X–Y de Z” e páginas correspondem ao resultado dessa consulta; contagens de severidade são calculadas após os filtros, incluindo severidade. Prioridade usa Crítica → Alta → Média e desempata por recência; “Mais recentes” usa recência.

O GET legado /api/estado mantém listas de alertas/leituras limitadas a 120; a central utiliza o GET paginado para não perder ocorrências antigas. Últimas leituras na tabela de Talhões são uma amostra de até 25, com contagem explícita, tanto na comparação agregada quanto no detalhe, a partir do retorno legado. [Contratos](../CONTRATOS_UX.txt).

Ocorrência selecionada, regra, alerta, evidência, origem, completude e orientação são atributos do registro. Não há persistência de resolução: gravidade não significa incidente aberto, confirmado ou tratado.

## Diagnósticos históricos — escopo independente

Fonte: [refined/diagnosticos.csv](data/refined/diagnosticos.csv), normalizado a partir do CSV histórico; filtros de sensores não se aplicam. Não há filtro de talhão nem associação inventada.

| Indicador | Unidade / cálculo e finalidade | Limitação |
|---|---|---|
| Registros históricos | Contagem de registros normalizados; diagnósticos | Volume do histórico, não novas inferências |
| Classes disponíveis | Número de classes presentes em diagnosticos.classes; classes | Não é quantidade de categorias possíveis; uma categoria de contagem zero pode aparecer nas barras |
| Distribuição das classificações | Contagem por diagnóstico normalizado; registros; barras proporcionais à maior contagem | Nomes são padronizados por texto no pipeline, não reclassificação por modelo; largura não representa porcentagem do total |
| Confiança média registrada | Média de confianca_pct, arredondada a 1 decimal; % | Confiança informada pelo CSV, **não acurácia comprovada** |
| Tipo de amostra / contagem por tipos | Tipo exibido por registro; agregado de tipos disponível na API, sem card próprio | Prefixo simulado_ no nome é usado para identificar o tipo; outras origens não provam sensores físicos |
| Amostras recentes | Últimos 12 registros em ordem inversa; timestamp e atributos históricos | Amostra visível não equivale ao total; nenhum vínculo com cultura/talhão |

Base inicial: 766 diagnósticos; classes 525 Folha saudável, 180 Doença detectada e 61 Outro patógeno; confiança média 91,0%; 746 nomes simulado_* e 20 de outra origem. Valores de referência, não metas a forçar.

## Ferramentas — estatísticas globais

`estado_pipeline.json` fornece raw_sensores, trusted_sensores, duplicados_removidos, observacoes_campo, diagnosticos_historicos, monitoramento_refinado, alertas, rejeitados e distribuição de regras da **base inteira**. Unidade: registros/ocorrências. Essas contagens auditam geração e processamento e não seguem os filtros de sensores; não são novas medições ou indicadores de execução contínua.

[Evidência da atualização real após gerar uma leitura](../03_evidencias/historico_fase6/coleta/execucao.json). [QA e evidências da Fase 7](../03_evidencias/LEIA_ME.md).
