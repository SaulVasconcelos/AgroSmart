# Pipeline DevSecOps — AgroSmart Fase 7

Um único script, [`devsecops/pipeline.py`](../devsecops/pipeline.py), roda igual na máquina local (Windows, Linux ou macOS com Docker) e no GitHub Actions ([`.github/workflows/devsecops.yml`](../../.github/workflows/devsecops.yml)). Ferramentas de CI ficam fora da imagem de runtime.

## Etapas e gates

| # | Etapa | Ferramenta | O que faz | Gate (reprova quando…) |
|---|---|---|---|---|
| 0 | ambiente | — | registra SO, Python, Node, Docker, commit Git e se a árvore tem alterações | — |
| 1 | ferramentas | pip + venv `.venv-devsecops` | instala [requirements-dev.txt](../devsecops/requirements-dev.txt): Ruff 0.17.5 e Bandit 1.9.4 | a instalação falha (FALHA DE FERRAMENTA) |
| 2 | qualidade | **Ruff** | `ruff check` nas regras E4/E7/E9/F/B em `02_plataforma` e `04_processos` | há qualquer achado |
| 3 | segurança estática (SAST) | **Bandit** | analisa `agrosmart/` e `main.py` (código de runtime) | há achado com severidade **e** confiança ≥ MEDIUM. LOW é reportado |
| 4 | testes | unittest + `node --test` | 45 testes Python (23 da Fase 6 + 22 novos), `node --check` e 18 cenários JS (14 da Fase 6 + 4 novos). Sem Node local, roda os testes JS no container `node:24-slim` | qualquer teste falha |
| 5 | build | **Docker** | `docker build` com a base `python:3.13-slim` (registra o digest efetivamente usado), aplicando as atualizações de segurança do Debian e removendo o pip; confere usuário `agrosmart`, conteúdo de `/app` = `agrosmart, main.py, semente, web` e pip ausente | o build falha, o usuário é root, o pip está presente ou há material além do runtime |
| 6 | container ponta a ponta | Docker + HTTP | volume novo, raiz somente leitura, `cap-drop ALL`, `no-new-privileges`. Ver a lista abaixo | qualquer verificação falha |
| 7 | vulnerabilidades | **Trivy 0.76.1** (container) | `trivy image` na imagem salva (SO + pacotes Python) e `trivy config` no Dockerfile | vulnerabilidade **CRITICAL/HIGH com correção disponível**, ou misconfig HIGH/CRITICAL no Dockerfile. As demais são reportadas. Trivy que não roda = FALHA DE FERRAMENTA, nunca "zero vulnerabilidades" |

**Verificações da etapa 6:**

- prontidão pelo host (127.0.0.1) e de dentro do container;
- semente com 144 leituras e 109 alertas;
- `POST /api/simular` passa o Raw para 145, e uma entrada inválida retorna 400;
- execução contínua com 2 ou mais ciclos reais e `estado_funcional=atualizado`;
- UID diferente de 0;
- fuso −03:00;
- gravação negada em `/app`;
- `HEALTHCHECK` do Docker = `healthy`;
- `docker restart` mantém os dados e o volume não é semeado de novo;
- encerramento limpo no log;
- `docker stop` com exit code 0 em menos de 14 s;
- exportação do event log, dos logs e do histórico de ciclos.

O resultado geral é **APROVADO** somente se todas as etapas executarem e passarem. Quando só uma parte das etapas é selecionada, o resultado vira **APROVADO (PARCIAL)**. Não há `|| true`, testes desativados ou ignore global.

## Achados reais e correção (18/11/2026)

A primeira execução no PC da equipe, com a base oficial, foi **reprovada pelo gate**: o Trivy encontrou 6 vulnerabilidades HIGH com correção disponível. A origem estava em dois lugares:

- `zlib1g` do Debian, ainda sem a atualização `deb13u1` na tag `python:3.13-slim`;
- dependências vendorizadas do **pip** (urllib3, msgpack e pkg_resources/setuptools), declaradas no SBOM do próprio pip.

O Dockerfile passou a fazer duas coisas: (1) rodar `apt-get -y upgrade` no build e (2) **remover o pip da imagem de runtime**. A aplicação não usa o pip. O build e o pipeline conferem a remoção. Os 47 HIGH restantes não têm correção publicada pelo Debian, por isso são reportados e não bloqueiam. Detalhes em [03_evidencias/devsecops_equipe/LEIA_ME.md](../../03_evidencias/devsecops_equipe/LEIA_ME.md).

Na segunda execução, o Trivy foi **aprovado** (0 bloqueantes), e a terceira execução foi **aprovada em todas as etapas**. Em compensação, os testes revelaram uma falha intermitente no Windows (`WinError 10053`): o servidor respondia erros sem ler o corpo da requisição. O servidor foi corrigido, o teste que falhou não foi alterado, e um teste novo cobre o caso. Detalhes no mesmo LEIA_ME.

Consequência: o `apt-get upgrade` torna o build dependente do momento em que roda, porque aplica as correções publicadas até aquele dia. Por isso o relatório registra o digest da base e o resultado do Trivy da imagem efetivamente construída.

No **GitHub Actions** (run 44438716927, disparado pelo PR #1, 19/11/2026 01:41 UTC), o pipeline foi **aprovado em todas as etapas**, com a mesma base e o mesmo scanner fixados por digest, em Linux com Docker 28.0.4 e Node 24. O run revelou um defeito só de relatório: o Node 24 imprime o resumo dos testes no formato `spec` (`ℹ pass 18`), e o resumo mostrava `?` em vez de 18. A função `_contar_js` passou a reconhecer os dois formatos. Detalhes em [03_evidencias/devsecops_ci/LEIA_ME.md](../../03_evidencias/devsecops_ci/LEIA_ME.md).

## Exceções escopadas (com justificativa)

- **Ruff E701/E702 em 5 arquivos legados** (`pipeline.py`, `web_server.py`, `main.py`, `tests/test_integracao.py` e `tests/test_pipeline.py`). São várias instruções por linha, estilo herdado da Fase 6, sem efeito funcional. Reformatar esses arquivos ampliaria o diff de regras e do pipeline já validados por regressão. Os módulos novos não têm exceção. Pendência: reformatar numa mudança dedicada, com a regressão por registro.
- **Bandit `# nosec B310`** em `main.py monitorar`: o esquema da URL é restrito a http/https antes do `urlopen`.
- **Bandit B311** (`random`, LOW): a simulação é didática e não tem uso criptográfico. Fica reportado, sem bloquear.

## Fixação de versões

- **Python:** `ruff==0.17.5` e `bandit==1.9.4`, conferidos no PyPI em 17/11/2026. Os hashes não estão fixados; é uma pendência, porque os pacotes de plataforma do Ruff variam entre Windows e Linux.
- **GitHub Actions:** fixadas por **SHA de commit**, conferido com `git ls-remote` em 17/11/2026: `actions/checkout` v7.0.1, `setup-python` v7.1.0, `setup-node` v7.1.0 e `upload-artifact` v7.0.2. O workflow tem `permissions: contents: read` e `persist-credentials: false`.
- **Imagens:** `python:3.13-slim` e `aquasec/trivy:0.76.1` são fixadas por tag. **O digest efetivamente usado é registrado em cada relatório** (`base_digest` e `scanner_digest`). Para fixar por digest, defina `AGROSMART_PYTHON_IMAGE=python:3.13-slim@sha256:…` ou `AGROSMART_TRIVY_IMAGE=aquasec/trivy:0.76.1@sha256:…`.
- **Atenção.** Em março/2026 o ecossistema Trivy sofreu um ataque de cadeia de suprimentos: o release v0.69.4, as imagens 0.69.5/0.69.6 no Docker Hub e tags da `trivy-action` foram adulterados ([aviso oficial GHSA-69fq-xp46-6x23](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)). Por isso o pipeline **não usa a `trivy-action`**, usa uma versão posterior conferida na página de releases e registra o digest. A verificação de assinatura com `cosign`, descrita no aviso, é recomendada antes de fixar o digest.

## Como executar

```bash
cd 02_plataforma
python devsecops/pipeline.py                                   # tudo (requer Docker em execução)
python devsecops/pipeline.py --etapas qualidade,seguranca,testes   # sem Docker
python devsecops/pipeline.py --manter-container                # não remove o container e o volume de teste
```

No Windows, use `py -3` se `python` não estiver no PATH. Os relatórios ficam em `02_plataforma/relatorios/<UTC>/`:

- `RELATORIO_PIPELINE.md` e `resumo.json`: decisão por etapa;
- saídas brutas de cada comando (`02_ruff.json`, `03_bandit.json`, `04_testes_*.txt`, `05_build.txt`, `06_*`, `07_trivy_imagem.json`, `07_trivy_config.json`);
- o event log e os logs exportados do container.

No GitHub, a pasta inteira é publicada como artefato do run.

## Limites

O pipeline demonstra práticas e controles. Ele não certifica a segurança do produto. O Trivy enxerga os pacotes conhecidos da imagem, mas não falhas lógicas. O Bandit é análise estática de padrões e não substitui testes nem revisão. A imagem não é publicada em registry, e nenhum segredo é necessário.
