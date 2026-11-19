# Contrato do event log de execução — AgroSmart Fase 7

Contrato **novo**, separado dos schemas agronômicos (sensores, campo, Refined). Implementação: [`02_plataforma/agrosmart/rastreio.py`](../02_plataforma/agrosmart/rastreio.py).

## Unidade de caso

**Um caso (`case_id`) é uma execução da cadeia** disparada por um gatilho real: um ciclo da execução contínua, uma requisição `POST` ou um comando da CLI. Um caso novo tem outro `case_id` mesmo quando reprocessa as mesmas leituras. Uma leitura de sensor **não** é um evento de atividade. O `data_hora` da leitura (relógio do sensor simulado, sem fuso) nunca é usado como horário de atividade.

## Colunas

| Coluna | Significado |
|---|---|
| `event_id` | `case_id` + sequência com 3 dígitos; único |
| `case_id` | `RUN-<UTC AAAAMMDDTHHMMSSZ>-<8 hex>`; correlaciona as atividades da execução |
| `sequence` | ordem dentro do caso (1..n, contígua); desempata timestamps iguais |
| `activity` | nome estável da atividade (tabela abaixo) |
| `lifecycle` | `start` ou `complete`. Atividades instantâneas têm só `complete` |
| `timestamp` | instante UTC **com offset** (`+00:00`) em que o software registrou o evento |
| `status` | resultado técnico: `iniciado`, `sucesso`, `rejeitado`, `falha`, `http_200`, `http_400`, `http_500`. Não é severidade agronômica |
| `duration_ms` | duração medida com `time.perf_counter()` entre start e complete. Vazio nas atividades instantâneas |
| `component` | componente técnico responsável (`operacao`, `web_server`, `pipeline`, `simulador`, `cli`) |
| `trigger` | gatilho do caso: `execucao_continua`, `api_simular`, `api_importar_observacoes`, `cli_processar`, `cli_simular`, `cli_importar_sensores`, `cli_importar_observacoes`, `experimento_escala` |
| `records_in` / `records_out` | contagens, quando a atividade as conhece |
| `detail` | texto curto (até 160 caracteres): motivo de rejeição, tipo de erro ou contexto. Sem caminhos internos ou stack trace |

## Atividades

| Atividade | Tipo | Onde é registrada |
|---|---|---|
| Entrada recebida | instantânea | início de todo caso |
| Validar requisição | medida | envelope HTTP: tamanho, JSON, parâmetros (somente API) |
| Gerar leituras simuladas | medida | simulador (execução contínua, `POST /api/simular`, `simular`) |
| Validar dados de entrada | medida | schema dos eventos ou do CSV de observações, **antes** de gravar |
| Aguardar trava de escrita | medida | tempo esperando o RLock (somente dentro do servidor) |
| Persistir Raw | medida | gravação em `raw/` |
| Publicar Trusted | medida | `processar()`: validação, deduplicação e gravação de Trusted (e diagnósticos) |
| Descartar duplicatas | instantânea, condicional | duplicatas **novas** desde a execução anterior |
| Quarentenar registros inválidos | instantânea, condicional | rejeições **novas** em `trusted/rejeitados.csv` |
| Aplicar regras R1–R7 | medida | motor de regras sobre todas as leituras Trusted |
| Publicar Refined | medida | gravação de Refined e de `estado_pipeline.json` |
| Resposta entregue | instantânea | após o envio da resposta HTTP (status `http_*`) |
| Execução concluída / Entrada rejeitada / Execução falhou | terminal | exatamente um por caso, sempre o último |

Visualizar o dashboard **não** é registrado: escrever Refined não prova que alguém abriu a tela, e o frontend não mede esse evento.

## Garantias e limites

- `processar()` sem caso (comando `demo`, testes de regressão) não grava event log e mantém o comportamento da Fase 6.
- O arquivo fica em `<pasta de dados>/processos/event_log.csv` e é rotacionado ao passar de 20 MB (`event_log.1.csv` … `.3.csv`).
- A gravação é serializada por uma trava dentro do processo. Uma falha de gravação do log não interrompe a operação agronômica e é contada em `GET /api/operacao` (`event_log.falhas_gravacao`).
- Para PM4Py ou ferramentas similares, o mapeamento é: `case_id` → `case:concept:name`, `activity` → `concept:name`, `timestamp` → `time:timestamp`, `lifecycle` → `lifecycle:transition`.
- A validação automática do contrato está em [`analisar_event_log.py`](analisar_event_log.py) (`validar()`): ids únicos, offset UTC, sequência contígua, pares start/complete e terminal único no fim do caso. Os testes ficam em `02_plataforma/tests/test_fase7_event_log.py`.
