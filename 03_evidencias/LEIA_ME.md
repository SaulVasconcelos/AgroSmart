# Evidências da Fase 7 — índice

Todas as execuções abaixo foram **reais**. Salvo indicação, rodaram em 17–18/11/2026 no ambiente de trabalho do Claude: Linux (Ubuntu 24.04), Python 3.13.18, Node 22.23.4 e Docker Engine 29.9.3. As pastas `devsecops_equipe/` e `devsecops_ci/` registram, respectivamente, o PC da equipe (Windows 11) e o GitHub Actions. Os dados de sensores e de campo são **simulados**.

Para cada item, a coluna Situação diz o que foi executado e o que ainda falta executar no ambiente da equipe.

| Evidência | Arquivo | Situação |
|---|---|---|
| Testes Python e JS, Ruff e Bandit | [devsecops_ambiente_claude/20261118T024453Z/](devsecops_ambiente_claude/20261118T024453Z/RELATORIO_PIPELINE.md): `04_testes_python.txt` (44 OK), `04_testes_js.txt` (18 OK), `02_ruff.json` (0 achados), `03_bandit.json` (0 bloqueantes; 4 B311/LOW) | Executado, commit `6cf04b4` |
| Build e container ponta a ponta | mesma pasta, `05_*` e `06_*`: 22 verificações aprovadas (semente 144/109, POST, 400, ciclos contínuos, UID 10001, fuso −03:00, raiz somente leitura, healthcheck *healthy*, restart com dados preservados e sem nova semeadura, stop com código 0 em 0,66 s) | Executado **com base substituta** (ver nota 1) |
| Pipeline completo com base oficial e Trivy (PC da equipe) | [devsecops_equipe/](devsecops_equipe/LEIA_ME.md):<br>• execução 1: **reprovada pelo gate** (6 HIGH com correção), resolvida com atualização do Debian e remoção do pip;<br>• execução 2: **Trivy aprovado** (0 bloqueantes), mas os testes acharam uma falha intermitente no Windows, corrigida no servidor;<br>• execução 3: **APROVADO em todas as etapas** (45 Py + 18 JS, build, 22/22 no container, Trivy com 0 bloqueantes) | Executado |
| Pipeline completo no **GitHub Actions** | [devsecops_ci/](devsecops_ci/LEIA_ME.md): [run 44438716927](https://github.com/SaulVasconcelos/AgroSmart/actions/runs/44438716927) (PR #1), **APROVADO em todas as etapas** (45 Py + 18 JS, build com a imagem oficial, 22/22 no container, Trivy com 0 bloqueantes). Relatórios do artefato do run, com SHA-256 conferido | Executado |
| Execução ponta a ponta com exemplo rastreado | [execucao/exemplo_entrada_saida.json](execucao/exemplo_entrada_saida.json): `POST /api/simular` → ND/Parcial → importação de campo → R2/Alta/Completa | Executado |
| Execução contínua e monitoramento | [execucao/monitorar_terminal.txt](execucao/monitorar_terminal.txt) (6 consultas, ciclos 1→6, 0 falhas), [api_operacao.json](execucao/api_operacao.json), [api_pronto.json](execucao/api_pronto.json), [api_health.json](execucao/api_health.json), [agrosmart.log](execucao/agrosmart.log), [ciclos.jsonl](execucao/ciclos.jsonl), [encerramento.json](execucao/encerramento.json) (SIGTERM → exit 0) | Executado |
| Regressão visual básica (Chromium) | [execucao/ux_larguras_telas.json](execucao/ux_larguras_telas.json): 5 telas × 4 larguras (1440, 768, 390, 320), sem rolagem horizontal e sem exceções JS | Executado |
| Capturas da interface (Chromium) | [capturas/](capturas/): `21`/`22` painel de execução contínua (desktop/mobile), `23` Visão Geral com leituras novas, `24` detalhe da leitura rastreada (R2). Nenhuma exceção JS ([capturas_erros_js.json](execucao/capturas_erros_js.json)) | Executado |
| Event log e análise de processo | [../04_processos/ANALISE_PROCESSO.md](../04_processos/ANALISE_PROCESSO.md) (40 casos, 600 eventos, 8 variantes, validação sem problemas) e experimento de escala | Executado |
| Event log gerado **dentro do container** | `devsecops_ambiente_claude/20261118T024453Z/06_event_log_container.csv` (4 casos, validação sem problemas) | Executado com base substituta |
| Histórico da Fase 6 | [historico_fase6/](historico_fase6/LEIA_ME.md) | Somente referência |

## Notas

**1. Base substituta (somente no ambiente do Claude).** No PC da equipe, o pipeline rodou com a imagem oficial: veja `devsecops_equipe/`.

Detalhe da base substituta: A política de rede do ambiente do Claude bloqueia o Docker Hub. Para validar o Dockerfile, o compose e o pipeline, foi construída localmente uma base equivalente: Ubuntu 24.04 mínimo com Python 3.12.3 e tzdata, chamada `local/base-substituta:ubuntu24-python3`. Ela foi passada com `--python-image`. Isso valida a lógica do container (usuário, volume, semente, healthcheck, sinais, persistência), mas **não substitui** o build com a imagem oficial `python:3.13-slim`. Esse build precisa rodar na máquina da equipe:

```bash
cd 02_plataforma && python devsecops/pipeline.py
```

**2. Trivy.** O Trivy rodou no PC da equipe. Na execução 3, nenhuma vulnerabilidade CRITICAL/HIGH **com correção disponível** foi encontrada. Isso **não** significa "zero vulnerabilidades": continuam reportadas 47 HIGH sem correção publicada pelo Debian. O run do GitHub Actions chegou ao mesmo resultado ([devsecops_ci/](devsecops_ci/LEIA_ME.md)).

**3. Reproduzir.** Execute a partir da raiz `FASE_7_AGROSMART`:

```bash
python 03_evidencias/coletar_evidencias_execucao.py   # execucao/ e capturas/ (as capturas exigem Playwright)
python 04_processos/coletar_cenarios.py --saida 04_processos/coleta --ciclos 20 --intervalo 5
python 04_processos/analisar_event_log.py 04_processos/coleta/event_log.csv --saida 04_processos/resultado
python 04_processos/medir_escala.py --saida 04_processos/resultado
```

Nas execuções novas, os valores sorteados e os horários serão diferentes. As regras e a amostra de regressão (144 leituras, 109 alertas) não mudam.

**4. Não validado.** Leitores de tela, Firefox/Safari, dispositivos físicos, uso por produtores reais e carga com vários usuários reais.
