# Sensores virtuais e coleta simulada — AgroSmart (Fase 6, válido na Fase 7)

> **Fase 7:** além da geração sob demanda descrita abaixo, a **execução contínua** chama `gerar_leitura` em ciclos de intervalo configurável (rodízio A → B → C, 1–8 leituras por ciclo) dentro do servidor. Schema, intervalos de geração e validação não mudaram. Ver [docs/MONITORAMENTO.md](docs/MONITORAMENTO.md). As evidências de coleta abaixo são da Fase 6 e estão preservadas em `03_evidencias/historico_fase6/`.

Esta implementação **não conecta sensores físicos**. São eventos produzidos por [simulador.py](agrosmart/simulador.py), para demonstrar coleta, persistência, processamento e apresentação. Não há fabricante, modelo, precisão, calibração ou protocolo de dispositivo alegado.

## Sensores representados

Cada talhão tem um identificador de sensor virtual e uma cultura fixa, conforme `TALHOES` e `SENSORES`:

| Talhão | Cultura registrada | Sensor virtual |
|---|---|---|
| Talhao A | Soja | S-001 |
| Talhao B | Milho | S-002 |
| Talhao C | Cafe | S-003 |

Os identificadores representam fontes virtuais de umidade/temperatura e atributos auxiliares no mesmo evento, sem afirmar três equipamentos físicos distintos por variável. O simulador gera essa associação fixa. A validação verifica talhão/cultura e sensor_id não vazio; **não exige** que um evento importado use exatamente S-001/S-002/S-003.

## Schema do evento e intervalos

| Campo bruto | Tipo gerado / unidade | Geração e finalidade | Validação efetiva |
|---|---|---|---|
| data_hora | string ISO 8601 | Instante do evento; histórico ou relógio local na geração sob demanda | Timestamp interpretável; normalizado pelo pipeline |
| sensor_id | string / identificador | Identifica a fonte virtual associada ao talhão | Obrigatório, convertido em texto e sem espaços externos |
| talhao | string | Localiza a área | Deve existir em TALHOES |
| cultura | string | Cultura configurada para a área | Deve corresponder ao talhão |
| umidade_solo | inteiro / % | Sorteio inclusivo de 22 a 67; apoio às regras hídricas | Número de 0 a 100 |
| temperatura | inteiro / °C | Sorteio inclusivo de 23 a 38; apoio às regras sensoriais | Número de -50 a 70 |
| probabilidade_praga | inteiro / % | Sorteio inclusivo de 0 a 100; indicador auxiliar **simulado**, sem modelo preditivo validado | Número de 0 a 100 |
| alerta | string | Heurística de origem do simulador | Campo presente e convertido para texto |
| recomendacao | string | Orientação correspondente à heurística de origem | Campo presente e convertido para texto |

Unidades são as usadas pelos rótulos do produto e pelas regras. Os intervalos de sorteio vêm de `gerar_leitura`; os limites de validação vêm de `validar_sensor` em [pipeline.py](agrosmart/pipeline.py). Limites técnicos de importação não são especificações de um sensor físico nem novos limiares agronômicos. Todos os nove campos são exigidos; campos com valor None são rejeitados.

`alerta` e `recomendacao` **já pertencem ao evento bruto**. A heurística inicia em “Normal”; umidade <30 indica irrigação, temperatura >35 com umidade <35 indica risco alto, e probabilidade >70 substitui o resultado anterior por alerta de praga. Essas condições são executadas na ordem do código. No Refined, esses textos são preservados como `alerta_origem` e `recomendacao_origem`; `alerta`, `acao`, `regra`, `severidade`, `justificativa` e `avaliacao` passam a registrar a decisão determinística R1–R7/ND. Não são campos intercambiáveis.

## Frequência representada e execução real

`simular_historico(inicio, dias=12, por_dia=4, semente=96)` usa Random com semente fixa. O reset demo começa em 27/09/2026 às 00:00 e percorre 12 dias. O instante é `inicio + dias(i) + horas(6*j)`: no padrão, 00:00, 06:00, 12:00 e 18:00 por talhão. 12 × 4 × 3 = 144 eventos. Os parâmetros são configuráveis; o passo de 6 horas é explícito, não calculado por 24/por_dia. Mudar parâmetros não configura um agendamento real.

`simular_campo` produz uma observação manual **simulada** por dia/talhão: 12 × 3 = 36. Ela vem de padrões independentes de folhas/praga/duração e não da probabilidade de praga. É armazenada em CSV e unida ao sensor por data + talhão + cultura.

Na geração sob demanda, CLI ou API chamam `gerar_leitura` com `datetime.now()` e Random sem semente fixa. API aceita 1–8 eventos por requisição; CLI aceita 1–300; UI oferece 1, 3 e 6. Cada evento recebe o instante de sua geração, sem periodicidade automática ou intervalo fixo entre eventos. Não há timer, cron, streaming ou leitura contínua de dispositivo no runtime.

`data_hora` é registrado sem informação de fuso no gerador atual; não atribua UTC ou America/Sao_Paulo ao evento por hipótese. O envelope de ingestão possui, separadamente, `recebido_em_utc` com offset UTC.

## Armazenamento e processamento

O evento é validado na entrada de simulação e entregue a `adicionar_evento`. Raw mantém um JSON por linha com envelope `recebido_em_utc`, `origem`, `evento` em [sensores.jsonl](data/raw/sensores.jsonl). `processar` reconstrói Trusted e Refined: normaliza timestamps/tipos, valida, deduplica, associa campo, aplica regras e grava CSV/JSON.

Sensor virtual é a fonte simulada; observação de campo é uma fonte CSV independente; probabilidade de praga é um número sorteado; regra, severidade e orientação final são **campos calculados**. Diagnósticos históricos são outra fonte, sem junção com talhões.

## Evento real de uma execução simulada

[evento_simulado.json](../03_evidencias/historico_fase6/coleta/evento_simulado.json) contém os nove campos realmente gerados pelo botão do AgroMonitor. [Envelope Raw capturado](../03_evidencias/historico_fase6/coleta/evento_raw_simulado.jsonl), [Trusted](../03_evidencias/historico_fase6/coleta/trusted_sensores.csv) e [Refined](../03_evidencias/historico_fase6/coleta/refined_monitoramento.csv) preservam suas respectivas estruturas. O campo `acao` do refinado não foi artificialmente acrescentado ao evento bruto.

[Registro da execução](../03_evidencias/historico_fase6/coleta/execucao.json) e [resposta HTTP](../03_evidencias/historico_fase6/coleta/resposta_simulacao.json) comprovam a geração. A sequência foi executada com cópia temporária: 144 leituras antes, uma leitura para Talhao A e 145 depois. Os números da base distribuída não foram alterados. Alertas e médias podem mudar ou permanecer iguais, conforme o evento sorteado e o arredondamento; consulte os valores efetivos do registro.

[Índice com capturas antes/depois e reprodução](../03_evidencias/LEIA_ME.md). [Transformação e exemplo R1](../01_arquitetura/descricao_componentes.md).
