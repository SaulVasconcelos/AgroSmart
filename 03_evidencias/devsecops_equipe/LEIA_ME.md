# Pipeline DevSecOps executado no PC da equipe

## Execução 1 — 18/11/2026 23:11 UTC — **REPROVADO** (gate de vulnerabilidades)

- **Ambiente:** Windows 11, Python 3.14.2, Node 18.13.0 e Docker 29.9.3.
- **Imagens:** base oficial `python:3.13-slim@sha256:e48f59cd…ed90` (Debian 13.7) e scanner `aquasec/trivy:0.76.1@sha256:790fd66d…c06c`.
- **Pasta:** [20261118T231148Z_reprovado/](20261118T231148Z_reprovado/RELATORIO_PIPELINE.md)

| Etapa | Resultado |
|---|---|
| Ruff / Bandit | APROVADO: 0 achados / 0 bloqueantes (4 B311 LOW) |
| Testes | APROVADO: 44 Python e 18 cenários JS. O relatório mostrou "1" porque o Node 18 agrupa os cenários num subteste; a contagem foi corrigida no pipeline |
| Build com a imagem oficial | APROVADO (177,1 MB, usuário `agrosmart`) |
| Container ponta a ponta | APROVADO: todas as verificações |
| Trivy, Dockerfile | 27 verificações, 0 falhas |
| **Trivy, imagem** | **REPROVADO: 6 vulnerabilidades HIGH com correção disponível** |

### Achados bloqueantes e origem

| CVE / GHSA | Pacote | Onde estava | Correção aplicada |
|---|---|---|---|
| CVE-2026-85091 | zlib1g 1.3.1-1+b1 → 1+deb13u1 | sistema operacional da base (Debian) | `apt-get -y upgrade` no build aplica a atualização de segurança do Debian |
| CVE-2026-114613, GHSA-6v7p-g79w-8964 | msgpack 1.1.2 | dependência **vendorizada do pip 26.2.2**, declarada no SBOM do próprio pip | pip **removido** da imagem de runtime |
| CVE-2025-47273 | setuptools 70.3.0 (pkg_resources) | idem, vendorizada do pip | idem |
| CVE-2026-97687, CVE-2026-97689 | urllib3 2.7.0 | idem, vendorizada do pip | idem |

A aplicação não usa pip nem nenhum pacote de terceiros em tempo de execução, porque só usa a biblioteca padrão. Remover o pip elimina 8 dos 10 achados que têm correção e reduz a superfície de ataque da imagem. O próprio build confere que o pip foi removido, e o pipeline também (`05_pip_ausente.txt`, campo `pip_ausente_no_runtime`).

### Achados sem correção (reportados, não bloqueiam)

Restam 47 HIGH, 103 MEDIUM, 67 LOW e 7 UNKNOWN em pacotes do Debian **sem versão corrigida publicada**: família util-linux (`bsdutils`, `libblkid1`, `libmount1`, `mount`…), `login` e outros. Pela política documentada em [DEVSECOPS.md](../../02_plataforma/docs/DEVSECOPS.md), esses achados aparecem no relatório, mas não reprovam. Não há ação possível além de reconstruir a imagem quando o Debian publicar a correção. Isso acontece automaticamente: a cada execução do pipeline, o `apt-get upgrade` aplica o que já estiver disponível. Reduzir ainda mais exigiria trocar a base (por exemplo, por uma imagem distroless). Isso fica registrado como oportunidade, não como entrega desta fase.

## Execução 2 — 18/11/2026 23:49 UTC — Trivy **APROVADO**; testes **REPROVADOS** (falha intermitente)

Pasta: [20261118T234945Z_trivy_aprovado_teste_intermitente/](20261118T234945Z_trivy_aprovado_teste_intermitente/RELATORIO_PIPELINE.md)

- **Vulnerabilidades:** APROVADO, 0 bloqueantes. O build mostra `zlib1g` atualizado para `1+deb13u1` (`05_build.txt`), e `05_pip_ausente.txt` confirma o pip removido. Restam só os achados sem correção publicada: 47 HIGH, 103 MEDIUM, 67 LOW e 7 UNKNOWN. O Dockerfile continua com 0 falhas.
- **Build, container, Ruff e Bandit:** APROVADOS. A imagem ficou com 177,9 MB.
- **Testes:** 44 executados, **1 erro**. Em `teste_rotas_desconhecidas`, o cliente recebeu `ConnectionAbortedError [WinError 10053]` num `POST` para uma rota inexistente. O mesmo teste tinha passado na execução 1.

**Diagnóstico:** defeito real do servidor, herdado da Fase 6. Nas respostas de erro (404 de rota desconhecida e 400 de corpo acima do limite), o servidor respondia e fechava a conexão **sem ler o corpo** da requisição. No Windows, fechar um socket com dados não lidos aborta a conexão (RST), e o cliente pode descartar a resposta que já tinha chegado. Por isso a falha é intermitente e não aparece no Linux.

**Correção** (`agrosmart/web_server.py`):

- o servidor passou a ler e descartar o corpo, com limite de 1 MB, antes de responder esses erros;
- foi acrescentado um timeout de 30 s por operação de socket, para que um cliente que não envia o corpo declarado não prenda uma thread.

O teste que falhou **não foi alterado**. Um teste novo (`teste_respostas_de_erro_consomem_o_corpo_antes_de_fechar`) confere que o corpo é consumido nos dois casos. Os testes também passaram a ignorar `data/logs`, `data/processos` e `data/operacao`, que podem ter sobrado de uma execução nativa anterior e não fazem parte da amostra. Agora são 45 testes Python.

## Execução 3 — 19/11/2026 00:57 UTC — **APROVADO** em todas as etapas

Pasta: [20261119T005747Z_aprovado/](20261119T005747Z_aprovado/RELATORIO_PIPELINE.md). Mesmo ambiente: Windows 11, Python 3.14.2, Node 18.13.0 e Docker 29.9.3.

| Etapa | Resultado |
|---|---|
| Ruff 0.17.5 | APROVADO: 0 achados em `02_plataforma` e `04_processos` |
| Bandit 1.9.4 | APROVADO: 0 bloqueantes, 4 B311/LOW reportados (`random` na simulação) e 1.374 linhas analisadas |
| Testes | APROVADO: **45 Python** (1 ignorado no Windows, o de SIGTERM, que o container cobre) e **18 cenários JS** |
| Build (`python:3.13-slim@sha256:e48f59cd…ed90`) | APROVADO: imagem de 177,9 MB, usuário `agrosmart`, `/app` = `agrosmart, main.py, semente, web` e **pip ausente** |
| Container ponta a ponta | APROVADO: **22 de 22 verificações** (UID 10001, fuso −03:00, raiz somente leitura, healthcheck *healthy*, 2 ciclos contínuos reais, restart em 0,97 s com dados preservados, stop em 0,76 s com código 0) |
| Trivy 0.76.1 (`sha256:790fd66d…c06c`) | APROVADO: **0 vulnerabilidades CRITICAL/HIGH com correção disponível**; Dockerfile com 0 falhas. Reportados sem bloquear, por não terem correção publicada: 47 HIGH, 103 MEDIUM, 67 LOW e 7 UNKNOWN |

**Histórico das três execuções:**

1. **Execução 1:** o gate barrou 6 vulnerabilidades reais. A correção foi a atualização do Debian no build e a remoção do pip.
2. **Execução 2:** o Trivy passou a aprovar, e os testes acharam um defeito intermitente do servidor no Windows. A correção foi ler o corpo da requisição antes de responder o erro, mais o timeout.
3. **Execução 3:** pipeline inteiro aprovado.

Nenhum gate foi relaxado e nenhum teste foi desativado.
