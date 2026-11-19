# Análise de processo (mineração de processos) — AgroSmart Fase 7

Esta análise usa o **event log real** gravado pelo software durante execuções controladas em 18/11/2026, entre 02:33:23 e 02:35:00 UTC. As leituras de sensores e as observações de campo são **simuladas**. Os eventos de atividade, porém, são registros reais da execução do programa: instantes, durações e resultados medidos. São dois níveis de realidade diferentes, e o texto abaixo não os mistura.

- Contrato do log: [contrato_event_log.md](contrato_event_log.md)
- Amostra coletada: [coleta/event_log.csv](coleta/event_log.csv). Roteiro do que foi executado: [coleta/roteiro_cenarios.json](coleta/roteiro_cenarios.json)
- Métricas recalculáveis: [resultado/metricas_processo.md](resultado/metricas_processo.md) e [.json](resultado/metricas_processo.json), com um caso por linha em [resultado/casos.csv](resultado/casos.csv)
- Experimento de escala: [resultado/escala_pipeline.csv](resultado/escala_pipeline.csv) e [.json](resultado/escala_pipeline.json)
- Ambiente: sandbox Linux do Claude, Python 3.13.18, execução nativa (sem container), máquina única

## 1. Unidade de caso e cenários

**Caso = uma execução da cadeia** (`case_id`/`run_id`). Os gatilhos foram:

- 20 ciclos da execução contínua (intervalo de 5 s, 3 leituras por ciclo);
- 5 `POST /api/simular` válidos, com 1, 3, 6, 2 e 8 leituras;
- 3 `POST /api/simular` inválidos: quantidade 99, talhão inexistente e JSON malformado;
- 1 importação de observações válida e 2 inválidas: folhas = 150 e colunas erradas;
- uma rajada de 6 `POST /api/simular` simultâneos;
- depois de parar o servidor, pela CLI: uma importação com 1 leitura nova + 1 duplicata, uma importação inválida (umidade 140) e um reprocessamento.

Nenhum limiar das regras foi alterado para provocar variantes. Reproduza com `python 04_processos/coletar_cenarios.py --saida <pasta> --ciclos 20 --intervalo 5` e, em seguida, `python 04_processos/analisar_event_log.py <pasta>/event_log.csv --saida <pasta_resultado>`.

## 2. Números gerais

| Medida | Valor |
|---|---:|
| Eventos / casos / variantes | 600 / 40 / 8 |
| Casos concluídos / rejeitados / com falha | 34 / 6 / 0 |
| Validação do contrato (ids, UTC, sequência, start/complete, terminal) | 0 problemas |
| Ponta a ponta dos concluídos: mediana · p95 · máx (ms) | 25,4 · 115,4 · 134,9 |
| Execução contínua: mediana · máx (ms), n = 20 | 25,2 · 35,1 |
| Tempo não atribuído a atividades medidas, mediana por caso concluído | 1,8 ms |

O p95 usa o método do posto mais próximo. "Ponta a ponta" é o último timestamp do caso menos o primeiro.

## 3. Representação do processo

**Esperado** (modelo de referência por gatilho): [resultado/processo_esperado.svg](resultado/processo_esperado.svg) ([PNG](resultado/processo_esperado.png)).
**Observado** (grafo diretamente-segue, com contagens reais): [resultado/processo_observado.svg](resultado/processo_observado.svg) ([PNG](resultado/processo_observado.png)).

| # | Casos | Variante observada |
|---:|---:|---|
| 1 | 20 (50%) | Entrada recebida → Gerar leituras → Validar dados → Aguardar trava → Persistir Raw → Publicar Trusted → Aplicar regras R1–R7 → Publicar Refined → Execução concluída |
| 2 | 11 (27,5%) | Igual à 1, mas começando por Validar requisição e terminando com Resposta entregue (API) |
| 3 | 3 | Entrada recebida → Validar requisição → Resposta entregue (400) → Entrada rejeitada |
| 4 | 2 | … → Validar requisição → Validar dados de entrada → Resposta entregue (400) → Entrada rejeitada |
| 5 | 1 | Importação de observações válida pela API |
| 6 | 1 | CLI com **Descartar duplicatas** entre Publicar Trusted e Aplicar regras |
| 7 | 1 | CLI: Entrada recebida → Validar dados de entrada → Entrada rejeitada |
| 8 | 1 | CLI processar: Entrada recebida → Publicar Trusted → Aplicar regras → Publicar Refined → Execução concluída |

**Conformidade:**

- Todos os 33 casos bem-sucedidos que vieram do servidor ou do reprocessamento seguiram exatamente o fluxo esperado para o seu gatilho.
- A única variação num caso concluído foi a variante 6, com a atividade adicional "Descartar duplicatas". É o comportamento previsto da deduplicação (o primeiro evento válido vence).
- Nenhum dos 6 casos rejeitados passou por **Persistir Raw**. Isso confirma, no log observado, que as entradas inválidas são barradas antes de qualquer gravação.

## 4. Onde o tempo é gasto (gargalos)

| Atividade | n | Mediana (ms) | p95 (ms) | % do tempo medido |
|---|---:|---:|---:|---:|
| Publicar Trusted | 34 | 14,70 | 19,81 | 49,2 |
| Aguardar trava de escrita | 32 | 0,001 | 72,42 | 26,8 |
| Publicar Refined | 34 | 6,51 | 8,84 | 20,3 |
| Aplicar regras R1–R7 | 34 | 0,84 | 1,15 | 2,7 |
| Demais (gerar, validar, persistir) | — | < 0,2 | < 1,3 | 1,0 |

**Insight 1. O custo está em republicar as camadas, não em decidir.**

- Publicar Trusted e Publicar Refined somam **69,5%** do tempo medido. O motor de regras responde por 2,7%.
- A causa está no código: `processar()` relê todo o Raw e regrava todos os CSVs, inclusive os 766 diagnósticos históricos, que não mudam entre os ciclos.

**Insight 2. A reconstrução completa cresce de forma linear com o volume (hipótese testada, não presumida).** Medimos com `medir_escala.py` a mediana de 3 repetições em cada um de 6 tamanhos de Raw:

| Leituras no Raw | 144 | 500 | 1.000 | 2.000 | 4.000 | 8.000 |
|---|---:|---:|---:|---:|---:|---:|
| Trusted + Regras + Refined (ms) | 20,2 | 28,4 | 41,5 | 67,1 | 121,8 | 219,1 |

- O ajuste linear dá **≈ 25,5 ms por 1.000 leituras** mais **16,5 ms** fixos, com r = 0,9998.
- Extrapolando, o limite padrão de 10.000 leituras levaria ≈ 270 ms por ciclo. Isso continua irrelevante num intervalo de 30 s. Porém, a trava fica retida pelo mesmo tempo, o que alimenta o insight 3.

Na amostra do event log (Raw entre 147 e 232 leituras) a correlação foi fraca (r = 0,28). A faixa era estreita demais para revelar a tendência, e por isso fizemos o experimento separado.

**Insight 3. Há disputa pela trava em rajadas, e a espera cresce em degraus do tempo de uma execução.**

- Em 26 das 32 aquisições a espera foi menor que 1 ms.
- Na rajada de 6 POSTs simultâneos, as esperas foram de 25, 31, 50, 72 e 93 ms. A partir da terceira, os degraus têm cerca de 20 ms, próximo da duração de uma execução da cadeia. Os pedidos são serializados pela autoridade única de escrita, como projetado.
- O primeiro POST (19 ms) coincidiu com o primeiro ciclo contínuo.
- Efeito: os POSTs da API tiveram mediana de 46 ms e máximo de 135 ms ponta a ponta, contra 25 ms dos ciclos sem disputa.
- O comportamento está correto: não houve duplicata nem perda (Raw 232 = Trusted 231 + 1 duplicata). Mesmo assim, é o primeiro ponto que limitaria vários usuários simultâneos.

## 5. Variações na qualidade da decisão (nível agronômico, com dados simulados)

No fim da coleta, o estado do pipeline mostrou:

- 231 leituras válidas;
- **18 decisões ND** ("observação de campo ausente");
- 1 duplicata removida;
- 0 rejeições no Raw.

As leituras novas de 17/11 (data local) do Talhão C não tinham observação de campo para o dia. Por isso, o motor registrou ND ou apenas regras sensoriais (R4/R5), sem afirmar situação normal. Já os talhões A e B receberam observações importadas no próprio dia e tiveram as decisões reavaliadas como completas no reprocessamento seguinte.

**Insight 4.** A completude da decisão depende do registro de campo, não da frequência dos sensores. Gerar mais leituras não reduz ND.

## 6. Oportunidades de melhoria (propostas, não implementadas)

| Oportunidade | Evidência | Como medir o ganho |
|---|---|---|
| Processamento incremental: publicar só as leituras novas e tirar os diagnósticos históricos do ciclo | Insights 1 e 2; 16,5 ms fixos e 25,5 ms/1.000 leituras | Repetir `medir_escala.py` e comparar as medianas por tamanho |
| Encurtar a seção crítica ou agrupar requisições concorrentes num único reprocessamento | Insight 3; degraus de ≈ 20 ms | Repetir a rajada e comparar o p95 de "Aguardar trava" |
| Destacar a falta de observação de campo por área e o dia (lembrete de registro) | Insight 4; 18 ND | Percentual de decisões "Completa" por dia no Refined |
| Medir a abertura do dashboard (evento no frontend) para fechar o ciclo até a decisão humana | O log atual termina na publicação | Novo evento com `case_id` próprio de sessão de uso |

## 7. Limites desta análise

- A amostra é pequena (40 casos em 97 s), coletada numa única máquina, com cenários e rajada provocados de propósito. Não representa carga de campo nem vários usuários reais.
- A rajada mostra o mecanismo de disputa, não a sua frequência no uso real.
- As durações dependem do hardware. A comparação entre tamanhos foi feita na mesma máquina e na mesma sessão.
- O tempo entre o fim de uma atividade e o início da seguinte (mediana de 1,8 ms por caso) não é atribuído a nenhuma atividade. Inclui o próprio registro do log e o tratamento HTTP.
- A execução containerizada gera o mesmo contrato de log. O pipeline exporta esse log do container para `relatorios/<execução>/06_event_log_container.csv`, que pode ser analisado com o mesmo script.
