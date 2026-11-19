# Roteiro — vídeo final técnico (5 a 8 minutos)

Duração planejada: **7 minutos**. A exigência é ficar entre 5 e 8 minutos.

O requisito 5 pede que o vídeo mostre quatro coisas. Cada uma tem sua cena:

| O que o vídeo precisa conter | Cenas |
|---|---|
| Demonstração da plataforma | 3, 4 e 5 |
| Explicação do fluxo (entrada → processamento → saída) | 2 e 4 |
| Análise do processo | 7 |
| Funcionamento completo da solução | 3 a 6 |

Os passos da interface (cenas 4 e 5) e o comando `monitorar` foram ensaiados em 18/11/2026 na versão que está na `main`, em execução nativa, sem Docker. Os textos entre aspas são os que a tela mostrou. Os comandos de Docker são os do [README_EXECUCAO.md](../02_plataforma/README_EXECUCAO.md) e não foram repetidos nesse ensaio: confiram no ensaio de vocês. Os dados de sensores e de campo são simulados. Tempos e divisão de falas são proposta: ajustem ao ritmo de quem for narrar.

## Antes de gravar

Façam a preparação e a gravação **no mesmo dia**: a observação de campo importada na cena 4 vale para a data do dia.

1. **Gravador.** Usem um programa que capture a tela inteira com o microfone, porque o vídeo alterna entre navegador e terminal. Gravem em 1920 × 1080. Se preferirem gravar cena por cena, juntem os trechos depois num editor.
2. **Legibilidade.** Zoom do navegador entre 110% e 125%, fonte do terminal maior, notificações desligadas.
3. **Repositório atualizado.** No PowerShell:

   ```powershell
   cd D:\AgroSmart\AgroSmart
   git pull
   ```

4. **Plataforma do zero.** O primeiro comando apaga o volume com os dados de demonstração, para a gravação começar da amostra original (144 leituras):

   ```powershell
   cd D:\AgroSmart\AgroSmart\02_plataforma
   docker compose down -v
   docker compose up -d --build
   docker compose ps
   ```

   Repitam o `docker compose ps` até a coluna STATUS mostrar `healthy`. Pode levar cerca de 30 segundos.
5. **Pausar a execução contínua.** Abram <http://127.0.0.1:8517>, entrem em **Pipeline e Simulação** e, no painel "Execução contínua e monitoramento", cliquem em **Parar**. A mensagem deve ser "Execução contínua parada: solicitado pela interface/API." Isso evita que leituras novas entrem no meio da cena 4.
6. **Conferir o Talhão B.** Em **Visão Geral**, a linha do Talhão B precisa estar como **Indeterminada** (regra ND). Se estiver com outra prioridade, vão em **Pipeline e Simulação**, escolham "Talhao B" e "1 leitura", cliquem em **Gerar leituras** e confiram de novo. Cerca de uma em cada quatro leituras sai com umidade baixa e cai em R4 ou R5, então pode ser preciso repetir.
7. **Arquivo da observação de campo.** Gera o CSV com a data de hoje:

   ```powershell
   python ..\05_apresentacao\gerar_observacao_demo.py
   ```

   O arquivo fica em `05_apresentacao\observacao_demo.csv`.
8. **Abas abertas, nesta ordem:**
   1. `01_arquitetura/arquitetura_final.png` (no GitHub ou no visualizador de imagens);
   2. a plataforma, em <http://127.0.0.1:8517>;
   3. <https://github.com/SaulVasconcelos/AgroSmart/actions>;
   4. `03_evidencias/devsecops_ci/20261119T014111Z_github_actions_aprovado/RELATORIO_PIPELINE.md`, no GitHub;
   5. `03_evidencias/devsecops_equipe/LEIA_ME.md`, no GitHub, na seção "Execução 1";
   6. `04_processos/coleta/event_log.csv`, no GitHub (ele mostra o CSV como tabela);
   7. `04_processos/resultado/processo_observado.png`;
   8. `04_processos/ANALISE_PROCESSO.md`, no GitHub;
   9. `MATRIZ_RASTREABILIDADE_FASE_7.md`, no GitHub.
9. **Terminal** aberto em `D:\AgroSmart\AgroSmart\02_plataforma`, com a tela limpa (`cls`).

**O ensaio gasta a demonstração.** Depois de importar a observação uma vez, o Talhão B não volta a ficar indeterminado naquele dia. Se ensaiarem a cena 4 de verdade, refaçam os passos 4 a 6 antes de gravar.

## Cenas

### Cena 1 — Abertura (0:00 a 0:20)

**Na tela:** página inicial do repositório no GitHub, com o README.

**Fala:**

> Este é o vídeo final do AgroSmart, Fase 7. Vamos mostrar a arquitetura, a plataforma funcionando de ponta a ponta em container, a execução contínua com monitoramento, o pipeline DevSecOps e a análise do processo. Os dados de sensores e de campo são simulados; o software e as execuções são reais.

### Cena 2 — Arquitetura e fluxo de dados (0:20 a 1:15)

**Na tela:** aba 1, o diagrama da arquitetura. Acompanhem a fala com o cursor, de cima para baixo.

**Fala:**

> A solução é uma aplicação única em Python, que roda em um container. No topo estão as entradas: leituras de sensores, que são simuladas, e observações de campo, importadas em CSV. Toda entrada é validada antes de gravar, e uma trava única garante uma escrita por vez. O dado bruto fica na camada Raw. A camada Trusted confere os tipos, remove duplicatas e separa o que é inválido. O motor de regras, de R1 a R7, define a prioridade de cada leitura, e a camada Refined publica o resultado. A saída são as APIs e o painel AgroMonitor, e quem decide o que fazer no campo é sempre uma pessoa. À direita, cada execução gera logs e um event log, usados na análise de processo. Embaixo fica o pipeline DevSecOps.

### Cena 3 — Plataforma no ar, em container (1:15 a 1:45)

**Na tela:** terminal.

**Ação:** digitem os dois comandos. O primeiro responde que o container já está rodando; o segundo mostra `healthy`.

```powershell
docker compose up -d
docker compose ps
```

**Fala:**

> A plataforma sobe com um comando, docker compose up. A imagem parte do Python 3.13 slim e roda com um usuário sem privilégios, com o sistema de arquivos somente leitura e um volume para os dados. O healthcheck do Docker consulta a rota de prontidão da aplicação, e por isso o container aparece como healthy. A porta fica exposta só nesta máquina.

### Cena 4 — Entrada, processamento e decisão (1:45 a 3:15)

**Na tela:** aba 2, a plataforma.

| Passo | Ação | O que a tela mostra |
|---|---|---|
| a | Abrir **Visão Geral** | Lista "Prioridades de investigação"; Talhão B como "Indeterminada", regra ND |
| b | **Pipeline e Simulação** → "Gerar novas leituras": escolher "Talhao A" e "1 leitura" → **Gerar leituras** | "1 leitura(s) simulada(s) gerada(s) e processada(s)…", o JSON da leitura e as contagens em "Auditoria das camadas" |
| c | **Talhões** → Talhão B | Cartão "Última leitura no filtro": "Indeterminada", "ND · Observação de campo ausente", avaliação "Parcial" |
| d | **Pipeline e Simulação** → "Importar observações de campo" → escolher `observacao_demo.csv` → **Importar observações** | "Importação concluída: 1 observação(ões) validadas. Filtros mantidos." |
| e | **Talhões** → Talhão B | O mesmo cartão agora mostra "Alta", "R2 · Alerta de infestação", avaliação "Completa", folhas afetadas 34%, Lagarta, 4 dia(s), orientação "Realizar inspeção técnica" |
| f | **Central de Alertas** | Lista de ocorrências com evidência e orientação |

**Fala:**

> Esta é a Visão Geral do AgroMonitor. Para cada talhão, a lista de prioridades mostra a última leitura e a regra aplicada.
>
> A entrada de dados é simulada. Quando geramos uma leitura, o evento em JSON é validado e gravado na camada Raw, e as camadas e as regras são reprocessadas. A auditoria mostra as contagens de cada camada.
>
> No Talhão B, a última leitura está como indeterminada. Não há observação de campo para hoje e, só com os sensores, o sistema não afirma que está tudo normal. A orientação é registrar a observação.
>
> Agora importamos a observação de campo do dia: 34% de folhas afetadas e lagarta há quatro dias.
>
> A mesma leitura foi reavaliada. Com mais de 30% de folhas doentes, vale a regra R2: prioridade alta e orientação de inspeção técnica, com a evidência e a justificativa na tela. Esta é a automação baseada em decisão. O sistema recomenda, e nenhuma ação é executada no campo.
>
> A ocorrência também entra na Central de Alertas.

### Cena 5 — Execução contínua e monitoramento (3:15 a 4:05)

**Na tela:** aba 2, depois o terminal.

**Ação:**

1. Em **Pipeline e Simulação**, no painel "Execução contínua e monitoramento", escolher "15 segundos" e clicar em **Iniciar execução contínua**. O painel passa a mostrar "Execução contínua Ativa", "Dados sendo atualizados no intervalo esperado" e a tabela "Últimos ciclos".
2. No terminal:

   ```powershell
   python main.py monitorar --url http://127.0.0.1:8517 --intervalo 5 --vezes 3
   docker compose logs --tail 10
   ```

**Fala:**

> A plataforma também roda sozinha. Na execução contínua, cada ciclo gera leituras, reprocessa as camadas e aplica as regras, e um ciclo nunca se sobrepõe a outro. O painel mostra se a execução está ativa, a idade do dado mais recente e quantos ciclos tiveram sucesso ou falha.
>
> Pelo terminal, o comando monitorar consulta o mesmo estado, e os logs do container registram cada ciclo. São sinais diferentes: uma rota diz se o processo está vivo, outra diz se a aplicação está pronta, e o estado da operação diz se os dados estão sendo atualizados.

### Cena 6 — Pipeline DevSecOps (4:05 a 5:05)

**Na tela:** aba 3 (os três runs verdes), depois aba 4 (tabela de etapas, "Resultado geral: APROVADO"), depois aba 5 (tabela "Achados bloqueantes e origem").

**Fala:**

> O pipeline DevSecOps é um único script, que roda igual no nosso computador e no GitHub Actions. São oito etapas. Entre elas, a qualidade de código com Ruff, a segurança estática com Bandit, 45 testes em Python e 18 de interface, o build da imagem, um teste de ponta a ponta com o container rodando, com 22 verificações, e a análise de vulnerabilidades com Trivy.
>
> O gate funcionou de verdade. A primeira execução foi reprovada: o Trivy encontrou seis vulnerabilidades altas que já tinham correção. Corrigimos aplicando as atualizações do Debian e removendo o pip da imagem, que a aplicação não usa. Hoje o pipeline está aprovado nos dois ambientes. Continuam no relatório 47 vulnerabilidades altas que ainda não têm correção publicada.

### Cena 7 — Análise de processo (5:05 a 6:35)

**Na tela:** aba 6 (event log), depois aba 7 (processo observado), depois aba 8 (rolando as seções 3 a 6 da análise).

**Fala:**

> Cada execução vira um caso no event log, com as atividades, o horário, a duração e o resultado de cada uma. Para a análise, coletamos 40 casos e 600 eventos em cenários controlados: ciclos contínuos, chamadas válidas e inválidas e uma rajada de requisições simultâneas.
>
> Este é o processo observado. Encontramos oito variantes. Os casos bem-sucedidos seguiram o fluxo esperado, e nenhuma das seis entradas rejeitadas chegou a ser gravada.
>
> O gargalo não está nas regras, que usam menos de 3% do tempo. Quase 70% vai para republicar as camadas Trusted e Refined, porque cada execução reprocessa a base inteira. Medimos esse custo: ele cresce de forma linear, cerca de 25 milissegundos a cada mil leituras.
>
> Na rajada, as requisições esperaram até 93 milissegundos pela trava de escrita. E 18 decisões ficaram indeterminadas por falta de observação de campo; gerar mais leituras não resolve isso.
>
> As melhorias propostas são o processamento incremental, uma seção crítica mais curta e um lembrete de registro de campo por talhão.

### Cena 8 — Encerramento (6:35 a 7:00)

**Na tela:** aba 9, a matriz de rastreabilidade.

**Fala:**

> Resumindo: a plataforma roda de ponta a ponta em container, com execução contínua, monitoramento, pipeline aprovado e processo analisado. O que ainda não existe está declarado, como sensores físicos, login e notificações. A matriz de rastreabilidade, no repositório, liga cada requisito ao código e à evidência. Obrigado.

## Se algo sair diferente

| Situação | O que fazer |
|---|---|
| O Talhão B não está indeterminado no começo da cena 4 | Não gravem a cena assim. Refaçam o passo 6 da preparação |
| Depois da importação, o Talhão B aparece como "Crítica", regra R1 | A leitura usada tinha umidade abaixo de 35%. Refaçam os passos 4 a 6 e gravem de novo, para a fala bater com a tela |
| A importação responde com erro | Confiram se o arquivo é o gerado hoje pelo passo 7. Uma entrada inválida não grava nada, então basta importar o arquivo certo |
| `docker compose ps` mostra `starting` | Esperem alguns segundos e repitam o comando antes de gravar a cena 3 |
| O vídeo passou de 8 minutos | Cortem o passo f da cena 4 e o segundo comando da cena 5 |
| O vídeo ficou com menos de 5 minutos | Não acelerem a fala. Na cena 4, mostrem com calma o JSON e a auditoria das camadas |

## Depois de gravar

- Confiram a duração: entre 5 e 8 minutos.
- Confiram que as falas batem com o que aparece na tela, principalmente os números das cenas 6 e 7.
- Registrem em [LEIA_ME.md](LEIA_ME.md) onde o vídeo foi entregue. O GitHub recusa arquivos com mais de 100 MB.
- Para desligar a plataforma: `docker compose down`. Os dados ficam no volume.
