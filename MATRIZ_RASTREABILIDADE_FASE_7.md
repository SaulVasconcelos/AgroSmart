# Matriz de rastreabilidade — Fase 7

Situação em 18/11/2026 (horário de Brasília). As colunas são independentes:

- **Implementado:** existe no código ou em arquivo;
- **Executado:** rodou de verdade;
- **Evidência:** artefato gerado pela execução;
- **Pendência.**

"Base substituta" significa que o container foi testado com uma base Ubuntu 24.04 + Python 3.12 construída localmente, porque o Docker Hub está bloqueado no ambiente do Claude (ver [03_evidencias/LEIA_ME.md](03_evidencias/LEIA_ME.md)).

| Req. | Exigência / artefato | Implementado | Executado | Evidência | Pendência |
|---|---|---|---|---|---|
| 1 | Diagrama da arquitetura final | [arquitetura_final.svg](01_arquitetura/arquitetura_final.svg) | Renderizado (PNG) | [arquitetura_final.png](01_arquitetura/arquitetura_final.png) | — |
| 1 | Descrição dos componentes | [descricao_componentes.md](01_arquitetura/descricao_componentes.md) | Conferida com o código | — | — |
| 1 | Fluxo de dados (entrada → processamento → saída) | [descricao_componentes.md § Fluxo](01_arquitetura/descricao_componentes.md) | Exemplo real rastreado | [exemplo_entrada_saida.json](03_evidencias/execucao/exemplo_entrada_saida.json) | — |
| 2 | Entrada (simulação), processamento, automação por decisão, saída | `simulador.py`, `pipeline.py`, `regras.py`, `operacao.py`, `web_server.py`, `web/` | Sim: nativo, e em container com a imagem oficial no PC da equipe e no GitHub Actions | [execucao/](03_evidencias/execucao/agrosmart.log), [capturas/](03_evidencias/capturas/), `06_*` em [devsecops_equipe](03_evidencias/devsecops_equipe/LEIA_ME.md) e [devsecops_ci](03_evidencias/devsecops_ci/LEIA_ME.md) | — |
| 2 | Descrição do funcionamento | [README_EXECUCAO.md](02_plataforma/README_EXECUCAO.md), [descricao_componentes.md](01_arquitetura/descricao_componentes.md) | — | — | — |
| 2 | Exemplo de entrada e saída | [exemplo_entrada_saida.json](03_evidencias/execucao/exemplo_entrada_saida.json) | Sim: ND → R2 após observação de campo | idem | — |
| 3 | Build da aplicação | [Dockerfile](02_plataforma/Dockerfile), [.dockerignore](02_plataforma/.dockerignore) | Sim, com a base oficial `python:3.13-slim` no PC da equipe e no GitHub Actions (e com base substituta no ambiente do Claude) | [devsecops_equipe](03_evidencias/devsecops_equipe/LEIA_ME.md), [devsecops_ci](03_evidencias/devsecops_ci/LEIA_ME.md), [devsecops_ambiente_claude](03_evidencias/devsecops_ambiente_claude/20261118T024453Z/RELATORIO_PIPELINE.md) | — |
| 3 | Execução via container | [compose.yaml](02_plataforma/compose.yaml) | Sim: 22 de 22 verificações aprovadas com a imagem oficial (PC da equipe e GitHub Actions) e com a base substituta | `06_*` nos relatórios | — |
| 3 | Análise de qualidade de código | Ruff 0.17.5 ([pyproject.toml](02_plataforma/pyproject.toml)) | Sim: 0 achados | `02_ruff.json` | — |
| 3 | Análise de vulnerabilidades | Bandit (SAST) e Trivy (imagem + Dockerfile) em [pipeline.py](02_plataforma/devsecops/pipeline.py) | Bandit: sim (0 bloqueantes). Trivy no PC da equipe: a execução 1 reprovou 6 HIGH com correção; corrigido no [Dockerfile](02_plataforma/Dockerfile); as execuções 2 e 3 e o run do GitHub Actions foram **aprovados** (0 bloqueantes; 47 HIGH sem correção publicada, só reportados) | `03_bandit.json`, `07_trivy_imagem.json` em [devsecops_equipe](03_evidencias/devsecops_equipe/LEIA_ME.md) e [devsecops_ci](03_evidencias/devsecops_ci/LEIA_ME.md) | — |
| 3 | Pipeline automatizado e descrição | [pipeline.py](02_plataforma/devsecops/pipeline.py), [workflow GitHub](.github/workflows/devsecops.yml), [DEVSECOPS.md](02_plataforma/docs/DEVSECOPS.md) | Local: sim, **APROVADO em todas as etapas** no PC da equipe (execução 3, depois de corrigir os achados das execuções 1 e 2). CI: sim, **APROVADO em todas as etapas** no GitHub Actions ([run 44438716927](https://github.com/SaulVasconcelos/AgroSmart/actions/runs/44438716927), disparado pelo PR #1) | [devsecops_equipe](03_evidencias/devsecops_equipe/LEIA_ME.md), [devsecops_ci](03_evidencias/devsecops_ci/LEIA_ME.md) (relatório e artefato do run) | — |
| 4 | Logs, status e indicadores de funcionamento | `observabilidade.py`, `operacao.py`, `/api/operacao`, `/api/pronto`, painel | Sim | [monitorar_terminal.txt](03_evidencias/execucao/monitorar_terminal.txt), [api_operacao.json](03_evidencias/execucao/api_operacao.json), [agrosmart.log](03_evidencias/execucao/agrosmart.log), captura 21/22 | — |
| 4 | Execução contínua | `operacao.py` (worker, sem sobreposição, falhas, limite, parada) | Sim: 20 ciclos sem falha na coleta; 7 testes dedicados | [ciclos.jsonl](03_evidencias/execucao/ciclos.jsonl), `tests/test_fase7_operacao.py` | — |
| 4 | Descrição e como acompanhar | [MONITORAMENTO.md](02_plataforma/docs/MONITORAMENTO.md) | — | — | — |
| 5 | Exemplo de event log | [rastreio.py](02_plataforma/agrosmart/rastreio.py), [contrato](04_processos/contrato_event_log.md) | Sim | [event_log.csv](04_processos/coleta/event_log.csv) (600 eventos / 40 casos) | — |
| 5 | Representação do processo | [analisar_event_log.py](04_processos/analisar_event_log.py) | Sim | [processo_observado.svg](04_processos/resultado/processo_observado.svg), [processo_esperado.svg](04_processos/resultado/processo_esperado.svg) | — |
| 5 | Análise com insights (gargalos, variações, melhorias) | [ANALISE_PROCESSO.md](04_processos/ANALISE_PROCESSO.md) | Sim, incluindo o experimento de escala | [metricas_processo.md](04_processos/resultado/metricas_processo.md), [escala_pipeline.csv](04_processos/resultado/escala_pipeline.csv) | — |
| 5 | Vídeo final de 5–8 min | — | — | — | **PENDENTE: roteiro (Claude) e gravação (equipe)** |
| 6 | Apresentação (slides): problema, solução, diferencial, público, proposta de valor | — | — | — | **PENDENTE: próxima etapa** |
| 6 | Vídeo pitch de até 5 min | — | — | — | **PENDENTE: roteiro (Claude) e gravação (equipe)** |

## Regressão e UX preservadas

- R1–R7/ND sem alteração de condição, limiar ou texto. Isso é conferido por `tests/test_regressao_demo.py` (144 registros iguais à fixture da Fase 6) e por `test_fase7_operacao.teste_amostra_historica_preservada_por_registro`.
- Os contratos da Fase 6 continuam íntegros: `/api/health` tem os mesmos campos, e `/api/estado`, `/api/alertas` e `/api/talhao` estão iguais.
- Navegação agrícola inalterada. O painel novo fica só em Ferramentas de demonstração. No Chromium, as 5 telas foram abertas em 1440, 768, 390 e 320 px (20 combinações), com execução contínua ativa: 0 rolagem horizontal e 0 exceções JS ([ux_larguras_telas.json](03_evidencias/execucao/ux_larguras_telas.json)). Os 14 cenários JS da Fase 6 continuam aprovados.
- Mudanças deliberadas estão listadas em [descricao_componentes.md § Decisões](01_arquitetura/descricao_componentes.md).

## Não validado

Leitor de tela, outros navegadores, dispositivos físicos, uso por produtores reais, carga com vários usuários e certificação de segurança.
