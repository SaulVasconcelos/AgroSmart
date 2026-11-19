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

**Antes do primeiro push para o GitHub:** mova `WORKFLOW_GITHUB_devsecops.yml` para `.github/workflows/devsecops.yml`. A cópia na raiz existe porque a ferramenta de transferência para o seu computador não grava em pastas `.github`.

No Windows: `mkdir .github\workflows` e depois `move WORKFLOW_GITHUB_devsecops.yml .github\workflows\devsecops.yml`.

O conteúdo é idêntico ao do workflow descrito em [DEVSECOPS.md](02_plataforma/docs/DEVSECOPS.md). Detalhes em [02_plataforma/README_EXECUCAO.md](02_plataforma/README_EXECUCAO.md).

## Onde está cada coisa

| Área | Entrada |
|---|---|
| Atendimento aos 6 requisitos | [MATRIZ_RASTREABILIDADE_FASE_7.md](MATRIZ_RASTREABILIDADE_FASE_7.md) |
| Arquitetura final, componentes e fluxo de dados | [01_arquitetura/descricao_componentes.md](01_arquitetura/descricao_componentes.md), [diagrama SVG](01_arquitetura/arquitetura_final.svg) / [PNG](01_arquitetura/arquitetura_final.png) |
| Plataforma (código, testes, Docker) | [02_plataforma/](02_plataforma/README_EXECUCAO.md) |
| Monitoramento e execução contínua | [02_plataforma/docs/MONITORAMENTO.md](02_plataforma/docs/MONITORAMENTO.md) |
| DevSecOps | [02_plataforma/docs/DEVSECOPS.md](02_plataforma/docs/DEVSECOPS.md), workflow `.github/workflows/devsecops.yml` (entregue como [WORKFLOW_GITHUB_devsecops.yml](WORKFLOW_GITHUB_devsecops.yml)) |
| Evidências de execução | [03_evidencias/LEIA_ME.md](03_evidencias/LEIA_ME.md) |
| Event log e mineração de processos | [04_processos/ANALISE_PROCESSO.md](04_processos/ANALISE_PROCESSO.md), [contrato](04_processos/contrato_event_log.md) |
| Pitch, slides e vídeos | [05_apresentacao/LEIA_ME.md](05_apresentacao/LEIA_ME.md) |
| Contratos de API da Fase 6 (vigentes) | [CONTRATOS_UX_P0_P1.txt](CONTRATOS_UX_P0_P1.txt) |
| Protótipo de classificação de imagens (fases anteriores) | [historico/classificador_imagens/](historico/classificador_imagens/LEIA_ME.md) |

## Situação atual (18/11/2026)

**Implementado e executado:**

- plataforma, execução contínua, monitoramento e event log;
- 45 testes Python e 18 cenários JS;
- pipeline DevSecOps completo aprovado no PC da equipe (`03_evidencias/devsecops_equipe/`);
- Ruff e Bandit;
- build e container ponta a ponta, com a imagem oficial no PC da equipe;
- análise de processo.

**Pendente:**

- run do pipeline no **GitHub Actions**. No PC da equipe, o pipeline completo, com a imagem oficial e o Trivy, já foi **aprovado em todas as etapas** em 19/11/2026;
- slides e roteiros;
- os **dois vídeos**, a gravar pela equipe: o final técnico de 5–8 min e o pitch de até 5 min.

A Fase 7 **ainda não está integralmente concluída**.

**Não existe no produto:** sensores físicos, Kafka ativo, inferência de imagem ao vivo, LLM, autenticação, multiusuário, notificações externas ou acionamento físico.

Origem: a cópia da Fase 6 consolidada fica no pacote de transferência (`AGROSMART_FASE7_PARA_CLAUDE/FASE_6_AGROSMART`, SHA256 do ZIP `69cfa98f…6a08`), preservada sem alterações.
