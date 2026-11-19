# Arquitetura final — componentes e fluxo de dados (Fase 7)

Diagrama: [arquitetura_final.svg](arquitetura_final.svg) ([PNG](arquitetura_final.png)). É uma aplicação modular única, em Python (somente biblioteca padrão) com frontend nativo, que roda **nativa** (`python main.py web`) ou **em container** (`docker compose up`). O desenho segue o que foi executado e testado. Não há microsserviços, Kafka, nuvem nem banco externo, e a rubrica não pede isso.

## Componentes

| Componente | Arquivo | Papel | Origem |
|---|---|---|---|
| CLI / inicialização | `02_plataforma/main.py` | comandos `web`, `simular`, `processar`, `importar-*`, `demo`; novo `monitorar`; semeia o volume vazio | Fase 6, estendido |
| Simulador | `agrosmart/simulador.py` | gera o evento de 9 campos (sorteios inclusivos; 3 talhões/culturas/sensores) | Fase 6, inalterado |
| Pipeline de camadas | `agrosmart/pipeline.py` | valida, deduplica e publica Raw → Trusted → Refined; agrega indicadores. `processar(caso=…)` registra as etapas no event log | Fase 6, instrumentado |
| Motor de regras | `agrosmart/regras.py` | R1–R7/ND determinístico, primeira regra aplicável vence | Fase 6, **inalterado** |
| Consultas | `agrosmart/consultas.py` | alertas paginados e detalhe por talhão, somente leitura | Fase 6, inalterado |
| Servidor HTTP | `agrosmart/web_server.py` | APIs, arquivos estáticos (lista fechada), trava única, SIGTERM, métricas HTTP | Fase 6, estendido |
| Execução contínua | `agrosmart/operacao.py` | worker no mesmo processo; ciclos sem sobreposição; política de falhas e de limite; estado; idade do dado; prontidão | **novo** |
| Event log | `agrosmart/rastreio.py` | casos e atividades com start/complete, duração, status técnico e gatilho | **novo** |
| Logs e métricas | `agrosmart/observabilidade.py` | logs `chave=valor` em stdout e arquivo com rotação; contadores HTTP | **novo** |
| Inicialização do volume | `agrosmart/inicializacao.py` | copia a amostra-semente só para a pasta de dados vazia | **novo** |
| Interface | `web/index.html`, `app.js`, `styles.css`, `icons.svg` | UX P0/P1 preservada; novo painel "Execução contínua e monitoramento" em Ferramentas | Fase 6, estendido |
| Container | `Dockerfile`, `.dockerignore`, `compose.yaml` | imagem enxuta, sem root; raiz somente leitura; volume `/data`; healthcheck de prontidão; porta só no loopback | **novo** |
| DevSecOps | `devsecops/pipeline.py`, `.github/workflows/devsecops.yml`, `pyproject.toml` | Ruff, Bandit, testes, build, E2E no container e Trivy, com relatórios | **novo** |
| Análise de processo | `04_processos/*.py` | coleta controlada, validação do log, variantes, DFG, gargalos e experimento de escala | **novo** (offline) |

## Fluxo de dados: entrada → processamento → saída

### Entrada

1. **Execução contínua.** A cada intervalo, o worker gera N leituras simuladas, em rodízio entre os talhões A, B e C.
2. **`POST /api/simular`.** O botão "Gerar leituras" gera de 1 a 8 leituras simuladas.
3. **`POST /api/importar-observacoes`** ou **`importar-observacoes`** (CLI): CSV `;` de campo (folhas doentes, praga, dias).
4. **`importar-sensores`** (CLI): JSONL com eventos de 9 campos.
5. **Diagnósticos históricos**: o CSV do protótipo de imagem (766 linhas) é só lido.

Toda entrada passa por **validação antes de gravar**: o envelope HTTP e o schema dos dados. Uma entrada inválida retorna HTTP 400 (ou código 2 na CLI) e não grava nada.

### Processamento

1. Com a **trava única de escrita**, a entrada válida é preservada no **Raw**:
   - `sensores.jsonl` guarda o envelope `recebido_em_utc` (UTC), `origem` e `evento`. O `data_hora` do evento é o relógio local do simulador, sem fuso;
   - `observacoes_campo.csv` recebe as observações de campo.
2. `processar()` reconstrói **Trusted** a partir de todo o Raw:
   - tipagem e normalização de timestamp;
   - deduplicação por `data_hora + sensor_id + talhao`, em que o primeiro evento válido vence;
   - quarentena em `rejeitados.csv`.
3. Cada leitura recebe a observação de campo do mesmo dia, talhão e cultura, se existir. O **motor R1–R7** decide a regra, a severidade, o alerta, a ação e a justificativa. Sem observação de campo, a decisão só pode ser R4/R5 (sensorial) ou ND.
4. **Refined** é publicado com gravação atômica (arquivo temporário + `os.replace`): `monitoramento.csv`, `alertas.csv`, `indicadores_talhoes.csv`, `serie_temporal.csv`, `diagnosticos.csv` e `estado_pipeline.json`.
5. Em paralelo, cada execução grava o **event log** (`processos/event_log.csv`), o **log** (`logs/agrosmart.log`) e, quando é um ciclo contínuo, o **histórico de ciclos** (`operacao/ciclos.jsonl`).

### Saída

1. **APIs:**
   - `GET /api/estado`, `/api/alertas`, `/api/talhao` (contratos da Fase 6, preservados);
   - `GET /api/operacao` e `/api/pronto` (novos).
2. **Dashboard AgroMonitor:** prioridades por área, evidência, orientação e justificativa, além do painel de operação.
3. **Decisão humana:** o produtor, agrônomo ou gestor decide. O sistema não executa nenhuma ação no campo.
4. **Arquivos para análise:** o Refined e o event log, este último analisado offline em `04_processos`.

### Exemplo rastreado de entrada e saída (execução real)

Arquivo: [`03_evidencias/execucao/exemplo_entrada_saida.json`](../03_evidencias/execucao/exemplo_entrada_saida.json). A leitura e a observação são simuladas; a execução é real.

1. **Entrada.** `POST /api/simular` com `{"talhao": "Talhao B", "quantidade": 1}` gerou:

   ```json
   {"data_hora": "2026-11-17T23:42:43.301932", "sensor_id": "S-002", "talhao": "Talhao B", "cultura": "Milho",
    "umidade_solo": 62, "temperatura": 26, "probabilidade_praga": 49, "alerta": "Normal", "recomendacao": "Manter monitoramento."}
   ```

2. **Saída sem observação de campo do dia.** Refined registra **ND / Indeterminada**: "Registrar observação de campo para avaliar todas as regras R1–R7", com avaliação **Parcial**. O sistema não afirma situação normal.
3. **Nova entrada.** `POST /api/importar-observacoes` com a observação de 17/11 para o Talhão B: folhas 34%, Lagarta, 4 dias.
4. **Saída após reprocessar.** A mesma leitura passa a **R2 / Alta**: "Realizar inspeção técnica", porque o percentual de folhas doentes é superior a 30%. A avaliação passa a **Completa**. R1 não se aplica, porque a umidade é 62% (≥ 35).

O exemplo R1 da Fase 6 (S-002, 06/10/2026 12:00) continua válido e coberto pela regressão.

## Decisões de arquitetura

- **Autoridade única de escrita:** worker e POSTs no mesmo processo, sob o mesmo RLock. Comandos de CLI escrevem somente com o servidor parado.
- **O contrato agronômico não mudou:** schemas Raw, Trusted e Refined, regras, limiares e campos de API da Fase 6 são idênticos. A regressão confere registro por registro.
- **Mudanças aditivas:** rotas novas e campos novos só em endpoints novos. O `/api/health` legado fica inalterado.
- **Mudanças de comportamento deliberadas e documentadas:**
  - `importar-sensores` (CLI) agora valida o arquivo inteiro antes de gravar; antes podia gravar parcialmente;
  - `POST /api/simular` passou a gerar e validar todas as leituras antes de gravá-las. O resultado é igual para entradas válidas;
  - o cabeçalho HTTP `Server` não expõe mais a versão do Python;
  - nas respostas de erro, o servidor lê e descarta o corpo antes de responder, e cada operação de socket tem timeout de 30 s. Isso corrige o aborto de conexão visto no Windows (`WinError 10053`) no pipeline da equipe;
  - a imagem aplica as atualizações de segurança do Debian e não inclui o pip (correção dos achados do Trivy).
- **Container:** `0.0.0.0` só dentro do container, porta publicada em `127.0.0.1`; usuário 10001; raiz somente leitura; `cap_drop: ALL`; `no-new-privileges`; semente copiada só para o volume vazio; `demo` nunca roda automaticamente.

## O que não existe (para não confundir na apresentação)

Não há sensores físicos, Kafka ativo, inferência de imagem ao vivo, LLM, autenticação, multiusuário, notificações externas, resolução persistente de alertas nem acionamento físico. O Kafka da Fase 4 e o PBIX da fase anterior continuam como **histórico**, na pasta da Fase 6.
