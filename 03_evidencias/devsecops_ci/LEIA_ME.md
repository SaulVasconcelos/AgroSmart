# Pipeline DevSecOps executado no GitHub Actions

## Run 44438716927 — 19/11/2026 01:41 UTC — **APROVADO** em todas as etapas

| Item | Valor |
|---|---|
| Repositório | [SaulVasconcelos/AgroSmart](https://github.com/SaulVasconcelos/AgroSmart) |
| Run | [actions/runs/44438716927](https://github.com/SaulVasconcelos/AgroSmart/actions/runs/44438716927), workflow `devsecops`, run #1, job `pipeline` (1 min 17 s; 1 min 21 s no total) |
| Gatilho | `pull_request`: [PR #1](https://github.com/SaulVasconcelos/AgroSmart/pull/1) (`fase-7` → `main`) |
| Commit testado | `c164eec` = `refs/pull/1/merge`. Num `pull_request`, o `actions/checkout` testa o **resultado do merge** de `fase-7` (`3573ac9`) sobre `main` (`02bc9c5`), não o commit do branch isolado. Conferido com `git ls-remote` |
| Árvore com alterações? | Não (`arvore_com_alteracoes: false`) |
| Ambiente | runner `ubuntu-24.04`, Python 3.13.18, Node v24.22.2, Docker 28.0.4 |
| Artefato | `relatorios-devsecops-44438716927` (171 KB), digest `sha256:a02ec74a93149b58d2504dd957e6df06f11abb85fa316d55213c0434a8417b36`. O zip baixado pela equipe tem exatamente esse SHA-256. O conteúdo está, sem alteração, em [20261119T014111Z_github_actions_aprovado/](20261119T014111Z_github_actions_aprovado/RELATORIO_PIPELINE.md) |

| Etapa | Resultado |
|---|---|
| Ruff 0.17.5 | APROVADO: 0 achados em `02_plataforma` e `04_processos` |
| Bandit 1.9.4 | APROVADO: 0 bloqueantes, 4 B311/LOW reportados (`random` na simulação), 1.374 linhas analisadas |
| Testes | APROVADO: **45 Python** (nenhum ignorado; no Linux o teste de SIGTERM também roda) e **18 cenários JS** (`ℹ pass 18`, `ℹ fail 0` em `04_testes_js.txt`) |
| Build (`python:3.13-slim@sha256:e48f59cd…ed90`) | APROVADO: usuário `agrosmart`, `/app` = `agrosmart, main.py, semente, web`, **pip ausente**, `zlib1g` atualizado pelo `apt-get upgrade` (`05_build.txt`) |
| Container ponta a ponta | APROVADO: **22 de 22 verificações** (UID 10001, fuso −03:00, raiz somente leitura, healthcheck *healthy*, 2 ciclos contínuos reais, restart em 0,66 s com 151 leituras preservadas, stop em 0,59 s com código 0) |
| Trivy 0.76.1 (`aquasec/trivy@sha256:790fd66d…c06c`) | APROVADO: imagem Debian 13.7 com **0 bloqueantes** (CRITICAL/HIGH com correção); Dockerfile com 0 falhas |

É a mesma base oficial e o mesmo scanner, fixados por digest, da execução 3 no PC da equipe ([devsecops_equipe/](../devsecops_equipe/LEIA_ME.md)). O pipeline agora foi aprovado em dois ambientes independentes: Windows 11 com Docker 29.9.3 e Linux do GitHub com Docker 28.0.4.

### Diferenças em relação à execução 3 (PC da equipe) e explicação

- **Trivy, UNKNOWN 7 → 10.** Os pacotes inventariados nas duas imagens são idênticos. Os 3 achados novos são o mesmo CVE, **CVE-2026-95690** (`openssl`, `libssl3t64`, `openssl-provider-legacy` 3.5.7-1~deb13u3), ainda sem severidade nem versão corrigida. Ele entrou na base de vulnerabilidades do Trivy entre as duas execuções. Pela política, é reportado e não bloqueia. As demais contagens não mudaram: 47 HIGH, 103 MEDIUM e 67 LOW, todas sem correção publicada.
- **Tamanho da imagem: 120,3 MB no CI e 177,9 MB no PC.** O conteúdo instalado é o mesmo (inventário do Trivy e `05_conteudo_app.txt`). Com o mesmo conteúdo, a diferença deve vir da forma de medir de cada instalação do Docker. Por exemplo, o Docker Desktop recente usa o *image store* do containerd, que contabiliza camadas de outro jeito. Não indica mudança no que roda na imagem.
- **Contagem de testes JS mostrada como `?` no relatório.** O Node 24 usa por padrão o reporter `spec` (`ℹ pass 18`), e o pipeline só reconhecia o formato TAP (`# pass 18`). Os testes passaram (exit code 0, 18/18 na saída bruta). Só a contagem no resumo falhou. Isso foi corrigido em `devsecops/pipeline.py` (`_contar_js`), conferido com as saídas do Node 18 (PC), do Node 22 (ambiente do Claude) e do Node 24 (este run).
- **Aviso do Trivy sobre a versão 0.76.2.** O scanner continua fixado em 0.76.1 por digest, de propósito (ver [DEVSECOPS.md](../../02_plataforma/docs/DEVSECOPS.md), incidente de cadeia de suprimentos de março de 2026). Uma atualização deve ser uma decisão explícita, com o novo digest conferido.

## Runs seguintes

| Run | Gatilho | Commit | Resultado |
|---|---|---|---|
| [#2, 44440403415](https://github.com/SaulVasconcelos/AgroSmart/actions/runs/44440403415) | `pull_request` (PR #1, depois do commit com esta evidência e a correção da contagem JS) | `3705e6d` | **Success**, 1 min 0 s |
| [#3, 44440765313](https://github.com/SaulVasconcelos/AgroSmart/actions/runs/44440765313) | `push` em `main` (merge do PR #1) | `f8732f5` | **Success**, 1 min 22 s |

Destes dois runs, só o status foi lido na página pública do GitHub em 19/11/2026. Os artefatos (`relatorios-devsecops-<run>`, 171 KB cada) não foram baixados nem versionados aqui. Como o workflow só termina com sucesso quando o pipeline devolve APROVADO, o status indica que todas as etapas passaram, mas os números de cada etapa estão apenas nos artefatos do GitHub, guardados por 30 dias.

### Como reproduzir

O workflow roda sozinho a cada `push` em `main`, a cada `pull_request` e manualmente (**Actions → devsecops → Run workflow**). Os relatórios ficam como artefato do run por 30 dias. Para guardá-los no repositório, baixe o zip e descompacte numa nova pasta aqui.
