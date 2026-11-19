# Executar o AgroSmart / AgroMonitor (Fase 7)

A plataforma usa Python 3.10+ só com a biblioteca padrão, e o frontend nativo é servido pelo próprio Python. Há duas formas de execução, ambas sobre a mesma aplicação:

## A. Container (recomendado para a demonstração)

Requisito: Docker Desktop (Windows/macOS) ou Docker Engine com o plugin Compose. Nesta pasta (`02_plataforma`):

```bash
docker compose up -d --build        # constrói a imagem e sobe com execução contínua (30 s)
docker compose ps                   # aguarde STATUS "(healthy)"
```

Abra http://127.0.0.1:8517.

- **Primeira subida:** o volume `agrosmart-dados` está vazio e recebe a amostra determinística da Fase 6 (144 leituras). A partir daí a execução contínua acrescenta leituras simuladas a cada 30 s.
- **Reinícios** (`docker compose restart` ou reiniciar o computador): o volume é **preservado**. Não há nova semeadura e o `demo` nunca roda automaticamente.

**Acompanhar:** `docker compose logs -f agrosmart` ou a tela **Ferramentas de demonstração → Execução contínua e monitoramento**. Outras opções estão em [docs/MONITORAMENTO.md](docs/MONITORAMENTO.md).

**Parar:** `docker compose stop` (encerramento limpo em cerca de 1 s).

**Recomeçar do zero:** `docker compose down -v`. Isso **apaga o volume** com as leituras geradas.

**Exportar o event log:** `docker compose cp agrosmart:/data/processos/event_log.csv .`

Para mudar o intervalo ou desligar a execução contínua, edite `environment` em [compose.yaml](compose.yaml) ou use os controles da tela. A porta só é publicada em `127.0.0.1`, ou seja, o servidor não fica exposto na rede.

## B. Nativa (sem Docker)

```bash
python main.py web --porta 8517                                  # como na Fase 6: sem execução contínua
python main.py web --porta 8517 --execucao-continua --intervalo 30
```

No Windows, `py -3` substitui `python`; no Linux ou macOS, use `python3` se necessário. CTRL+C encerra.

O comando `web` **não reprocessa nem reinicializa** a base. Por padrão, os dados ficam em `02_plataforma/data`, a amostra versionada; logs, event log e histórico de ciclos vão para `data/logs`, `data/processos` e `data/operacao`, que estão no `.gitignore`. Para não alterar a amostra, aponte `AGROSMART_DATA_DIR` para uma cópia **antes** de iniciar o Python.

> **Uma autoridade de escrita por vez.** Com o servidor no ar, não rode `simular`, `processar` ou `importar-*` pela CLI sobre a mesma pasta de dados. O servidor sincroniza as próprias threads, mas não sincroniza outros processos.

## Comandos

| Comando | Efeito |
|---|---|
| `python main.py web [--host] [--porta] [--execucao-continua] [--intervalo S] [--eventos-por-ciclo N] [--limite-leituras N]` | servidor e dashboard |
| `python main.py monitorar --url http://127.0.0.1:8517 [--intervalo 5] [--vezes 0]` | acompanha `/api/operacao` no terminal |
| `python main.py simular --quantidade 3 [--talhao "Talhao A"]` | gera de 1 a 300 leituras e reprocessa |
| `python main.py processar` | reconstrói Trusted e Refined |
| `python main.py importar-observacoes arquivo.csv` | CSV `;` de campo, validado antes de gravar |
| `python main.py importar-sensores arquivo.jsonl` | eventos de 9 campos. **Fase 7: valida o arquivo inteiro antes de gravar** (exit 2 se houver erro) |
| `python main.py demo` | **sobrescreve** a base selecionada com a amostra determinística. Faça backup antes |

Os formatos dos dados estão em [descricao_sensores_simulados.md](descricao_sensores_simulados.md) e os indicadores em [indicadores_dashboard.md](indicadores_dashboard.md).

## APIs

- **Contratos da Fase 6, preservados:** `/api/health`, `/api/estado`, `/api/alertas`, `/api/talhao`, `POST /api/simular` e `POST /api/importar-observacoes`. Ver [../CONTRATOS_UX_P0_P1.txt](../CONTRATOS_UX_P0_P1.txt).
- **Rotas novas da Fase 7:** `GET /api/operacao`, `GET /api/pronto`, `POST /api/operacao/iniciar` e `POST /api/operacao/parar`. Ver [docs/MONITORAMENTO.md](docs/MONITORAMENTO.md).

## Testes e pipeline

```bash
python -m unittest discover -s tests -v      # 45 testes (23 da Fase 6 + 22 da Fase 7)
node --test tests/test_frontend.cjs          # 18 cenários JS (14 + 4)
node --check web/app.js
python devsecops/pipeline.py                 # pipeline DevSecOps completo (requer Docker)
```

Detalhes e políticas: [docs/DEVSECOPS.md](docs/DEVSECOPS.md). Os testes usam pastas temporárias e não alteram `data/`. O teste de SIGTERM é ignorado no Windows.

## Limites

Os dados de sensores e de campo são simulados. Não há autenticação, TLS, multiusuário ou acionamento físico. É uma demonstração local; não publique a porta em rede pública.
