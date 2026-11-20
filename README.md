# AgroSmart — Fase 7

AgroSmart é uma plataforma local de inteligência agrícola. Seu módulo **AgroMonitor** transforma leituras de sensores e observações de campo em prioridades de investigação por talhão. Para isso, usa regras explicáveis (R1–R7), mostra a evidência de cada decisão e dá orientações rastreáveis. A decisão continua sendo humana.

A Fase 7 evolui a Fase 6 consolidada (redesign UX P0/P1) sem reconstruí-la. Ela acrescenta:

- **container** Docker endurecido, com volume persistente;
- **execução contínua** controlada, com **monitoramento** por sinais verdadeiros;
- **event log** das execuções e **análise de processo**;
- **pipeline DevSecOps** (Ruff, Bandit, testes, build, teste ponta a ponta no container e Trivy), local e no GitHub Actions.

As regras, os schemas agronômicos e os contratos de API da Fase 6 continuam iguais. A regressão confere registro por registro.

> Os dados de sensores e de campo são **simulados**. O processamento, as regras, os logs e o event log são execuções reais do software.

## Início rápido

```bash
cd 02_plataforma
docker compose up -d --build      # http://127.0.0.1:8517, com execução contínua a cada 30 s
python devsecops/pipeline.py      # pipeline DevSecOps completo, com relatórios em relatorios/<UTC>/
```

Sem Docker: `python main.py web --porta 8517 --execucao-continua`.

No GitHub, o mesmo pipeline roda pelo workflow [.github/workflows/devsecops.yml](.github/workflows/devsecops.yml) a cada `push` em `main` e a cada pull request ([DEVSECOPS.md](02_plataforma/docs/DEVSECOPS.md)). Detalhes de execução em [02_plataforma/README_EXECUCAO.md](02_plataforma/README_EXECUCAO.md).

## Onde está cada coisa

| Área | Entrada |
|---|---|
| Atendimento aos 6 requisitos | [MATRIZ_RASTREABILIDADE_FASE_7.md](MATRIZ_RASTREABILIDADE_FASE_7.md) |
| Arquitetura final, componentes e fluxo de dados | [01_arquitetura/descricao_componentes.md](01_arquitetura/descricao_componentes.md), [diagrama SVG](01_arquitetura/arquitetura_final.svg) / [PNG](01_arquitetura/arquitetura_final.png) |
| Plataforma (código, testes, Docker) | [02_plataforma/](02_plataforma/README_EXECUCAO.md) |
| Monitoramento e execução contínua | [02_plataforma/docs/MONITORAMENTO.md](02_plataforma/docs/MONITORAMENTO.md) |
| DevSecOps | [02_plataforma/docs/DEVSECOPS.md](02_plataforma/docs/DEVSECOPS.md), workflow [.github/workflows/devsecops.yml](.github/workflows/devsecops.yml) |
| Evidências de execução | [03_evidencias/LEIA_ME.md](03_evidencias/LEIA_ME.md) |
| Event log e mineração de processos | [04_processos/ANALISE_PROCESSO.md](04_processos/ANALISE_PROCESSO.md), [contrato](04_processos/contrato_event_log.md) |
| Pitch, slides e vídeos | [05_apresentacao/LEIA_ME.md](05_apresentacao/LEIA_ME.md) |
| Contratos de API da Fase 6 (vigentes) | [CONTRATOS_UX.txt](CONTRATOS_UX.txt) |
| Protótipo de classificação de imagens (fases anteriores) | [historico/classificador_imagens/](historico/classificador_imagens/LEIA_ME.md) |

## Situação atual (19/11/2026, horário de Brasília)

**Implementado e executado:**

- plataforma, execução contínua, monitoramento e event log;
- 45 testes Python e 18 cenários JS;
- pipeline DevSecOps completo **aprovado em dois ambientes**: no PC da equipe ([devsecops_equipe](03_evidencias/devsecops_equipe/LEIA_ME.md)) e no **GitHub Actions** ([devsecops_ci](03_evidencias/devsecops_ci/LEIA_ME.md), run 44438716927, PR #1);
- Ruff e Bandit;
- build e container ponta a ponta com a imagem oficial `python:3.13-slim`, e Trivy sem bloqueantes, nos dois ambientes;
- análise de processo;
- slides do pitch: 11 slides, aprovados pela equipe, em [05_apresentacao/slides_pitch_agrosmart.pdf](05_apresentacao/slides_pitch_agrosmart.pdf);
- vídeo pitch de até 5 min: filme animado de 2 min 14 s, em [05_apresentacao/video_pitch/](05_apresentacao/video_pitch/LEIA_ME.md), com voz e imagens de abertura feitas por IA; a equipe assistiu ao vídeo pronto e o aprovou em 19/11/2026;
- vídeo final técnico de 5–8 min: gravação da plataforma em execução (container, navegador e terminal reais), com narração gerada por IA, em [05_apresentacao/video_tecnico/](05_apresentacao/video_tecnico/LEIA_ME.md).

Os entregáveis dos seis requisitos da Fase 7 estão no repositório; a [matriz de rastreabilidade](MATRIZ_RASTREABILIDADE_FASE_7.md) liga cada um ao código e à evidência.

**Não existe no produto:** sensores físicos, Kafka ativo, inferência de imagem ao vivo, LLM, autenticação, multiusuário, notificações externas ou acionamento físico.

Origem: a cópia da Fase 6 consolidada fica no pacote de transferência (`AGROSMART_FASE7_PARA_CLAUDE/FASE_6_AGROSMART`, SHA256 do ZIP `69cfa98f…6a08`), preservada sem alterações.
