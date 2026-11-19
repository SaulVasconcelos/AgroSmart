# Execução contínua e monitoramento — AgroSmart Fase 7

## O que foi implementado

| Sinal | Onde | O que prova |
|---|---|---|
| **Liveness** | `GET /api/health` (contrato legado, inalterado) | o processo HTTP responde. **Não** prova dados atualizados nem worker ativo |
| **Prontidão** | `GET /api/pronto` → 200 ou 503 | a pasta de dados aceita gravação e o Refined está legível. É usada pelo `HEALTHCHECK` do Docker |
| **Estado funcional** | `GET /api/operacao` → `estado_funcional` | `atualizado`: worker ativo e último sucesso dentro de 2× o intervalo (mínimo de 60 s). `atrasado`: worker ativo, mas sem sucesso recente. `sem_execucao_continua`: os dados só mudam por ação manual |
| Execução contínua | `GET /api/operacao` → `execucao_continua` | estado, intervalo, ciclos (total/sucesso), falhas (total/consecutivas), último ciclo com duração e contagens, últimos 20 ciclos |
| Idade do dado | `GET /api/operacao` → `dados` | última leitura geral e por talhão e a idade em segundos (mesmo relógio local do simulador). Também Raw/Trusted/duplicados/rejeitados/alertas |
| Tráfego HTTP | `GET /api/operacao` → `servidor.requisicoes` | total e quantidade por classe 2xx/4xx/5xx desde o início do processo, além de uptime e versão |
| Event log | `GET /api/operacao` → `event_log` | eventos gravados e falhas de gravação |
| Logs | stdout (`docker compose logs`) e `<dados>/logs/agrosmart.log` | uma linha `chave=valor` por evento: requisições, ciclos, erros e sinais. Rotação a cada 2 MB, com 5 arquivos |
| Histórico de ciclos | `<dados>/operacao/ciclos.jsonl` | um JSON por ciclo (UTC, duração, resultado, contagens). Rotação a cada 5 MB |
| Painel | Ferramentas de demonstração → **Execução contínua e monitoramento** | os mesmos sinais acima, atualizados a cada 10 s enquanto a tela está aberta, com Iniciar/Parar |

`GET /api/operacao` não expõe caminhos internos. O `/api/health` legado continua expondo `persistencia`, para manter compatibilidade com a Fase 6.

## Execução contínua: decisões

- **Uma única autoridade de escrita.** O worker é uma thread dentro do processo do servidor e usa o mesmo `RLock` das rotas `POST`. Os dois não competem por arquivos a partir de processos diferentes. O RLock **não** sincroniza processos: não rode `main.py simular/processar/importar-*` sobre a mesma pasta enquanto o servidor estiver no ar.
- **Sem sobreposição.** Um único laço executa os ciclos em sequência. O intervalo conta do fim de um ciclo até o início do próximo.
- **Ciclo** = gerar N leituras simuladas (rodízio A/B/C) → validar → aguardar a trava → persistir no Raw → `processar()` (Trusted, regras, Refined). Cada ciclo é um caso no event log.
- **Política de erro.** Uma falha num ciclo é registrada (log, histórico, event log com "Execução falhou") e o laço continua. Depois de 5 falhas consecutivas, o worker para com o estado `interrompida_por_falhas`.
- **Limite.** Quando o Raw atinge `AGROSMART_LIMITE_LEITURAS` (padrão 10.000), o worker para (`limite_atingido`) sem gravar mais nada.
- **Encerramento.** O servidor trata SIGTERM e CTRL+C: para o worker, aguarda o ciclo em andamento e fecha o socket. Por isso o `docker stop` termina em menos de 1 s, com código 0, e não precisa esperar o SIGKILL.
- **Parâmetros de demonstração** (não são frequência de sensor físico): intervalo de 5 a 3.600 s e 1 a 8 leituras por ciclo.

| Configuração | CLI (`main.py web`) | Variável de ambiente | Padrão |
|---|---|---|---|
| Ligar ao iniciar | `--execucao-continua` | `AGROSMART_EXECUCAO_CONTINUA=1` | desligada (compose: ligada) |
| Intervalo (s) | `--intervalo` | `AGROSMART_INTERVALO_S` | 30 |
| Leituras por ciclo | `--eventos-por-ciclo` | `AGROSMART_EVENTOS_POR_CICLO` | 3 |
| Limite do Raw | `--limite-leituras` | `AGROSMART_LIMITE_LEITURAS` | 10.000 |

Controle em tempo de execução: `POST /api/operacao/iniciar` com `{"intervalo_s": 30, "eventos_por_ciclo": 3}` (os dois campos são opcionais) e `POST /api/operacao/parar` sem corpo. Parâmetro inválido ou desconhecido retorna 400. A configuração feita pela API não sobrevive ao reinício do servidor; ao reiniciar, valem a CLI e as variáveis de ambiente.

## Como acompanhar o sistema

**1. Pelo navegador.** Abra Ferramentas de demonstração (lateral; no celular, Menu) → Execução contínua e monitoramento.

**2. Pelo terminal, com uma linha por consulta:**

```bash
python main.py monitorar --url http://127.0.0.1:8517 --intervalo 5
# 2026-11-18T... estado=atualizado execucao=ativa ciclos=12 falhas=0 ultimo_ciclo=sucesso/23.4ms raw=180 alertas=131 idade_dado_s=3.2 http={...}
```

**3. Container:**

```bash
docker compose ps                                  # STATUS mostra (healthy) quando /api/pronto responde 200
docker compose logs -f agrosmart                   # logs ao vivo (requisições, ciclos, erros, sinais)
docker compose exec agrosmart python main.py monitorar --url http://127.0.0.1:8501 --vezes 1
docker compose cp agrosmart:/data/processos/event_log.csv .   # exportar o event log para análise
docker inspect --format '{{json .State.Health}}' agrosmart-agrosmart-1
```

**4. Como interpretar:**

- `estado_funcional=atrasado` ou `falhas_consecutivas>0`: consulte o log.
- `idade_dado_s` alta com a execução contínua parada é esperada, porque a amostra da Fase 6 é histórica (outubro/2026).
- 5xx em `requisicoes`: há erro interno registrado no log, sem stack trace na interface.

## Limites

É uma demonstração local, de um único processo. Não há alertas enviados para fora (e-mail, push), métricas em formato Prometheus, autenticação nos controles de iniciar/parar ou persistência da configuração entre reinícios. Os controles não têm autenticação, assim como os demais POSTs da Fase 6. Por isso o servidor publica a porta só em `127.0.0.1`.
