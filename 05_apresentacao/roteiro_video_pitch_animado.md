# Roteiro — vídeo pitch animado

**Aprovado pela equipe em 19/11/2026**, com estas decisões: o Claude operou o Gemini pelo navegador da equipe; a voz escolhida foi a "Nika"; a abertura usa imagens do Gemini; a trilha é a `bgm-tech-house`. O vídeo foi produzido e está em [video_pitch_animado/](video_pitch_animado/). O que mudou na produção (a abertura, a duração e alguns detalhes de cena) está no [LEIA_ME.md](video_pitch_animado/LEIA_ME.md) daquela pasta. O texto abaixo é o roteiro como foi aprovado.

- **Duração planejada:** 2 min 12 s. O limite da entrega é de 5 minutos; um filme curto prende mais do que cinco minutos de narração.
- **Formato:** 1920 × 1080, 30 quadros por segundo, em português do Brasil.
- **Estrutura:** abertura com imagens de lavoura (30 s), filme do produto com telas reais animadas (80 s) e encerramento (22 s). **Narração do começo ao fim**, com voz gerada pelo Gemini.

O que mudou em relação à primeira versão: a voz deixou de ser o problema. Antes, só a abertura tinha fala, e ela dependia de um plugin pago. Agora o vídeo inteiro é narrado com o texto escrito por nós.

## Quem faz o quê

| Ferramenta | Papel no vídeo | Limites que afetam o roteiro |
|---|---|---|
| **Gemini — voz** (geração de fala no Google AI Studio) | A narração de todas as cenas, lendo exatamente o texto deste roteiro, em português do Brasil | É gratuita para qualquer conta Google, com limites de uso; não depende da assinatura. Quem escolhe a voz precisa ouvir, e o Claude não ouve áudio |
| **Gemini — vídeo** (Veo 3.1 Fast, incluído na assinatura) | Três clipes curtos de lavoura para a abertura | O acesso no plano Plus é limitado. As fontes consultadas falam em cerca de 200 créditos por mês, algo como dez clipes; os limites mudam, então vale conferir no aplicativo. Cada clipe é curto, de cerca de 8 s. As imagens são geradas por IA: são ilustração, não registro de uma lavoura real |
| **video-shotcraft** (plugin) | O filme do produto: telas reais do AgroMonitor com movimentos de câmera, texto animado, trilha e efeitos sonoros | Não tem voz. É gratuito e roda no ambiente do Claude. Em 19/11/2026 um quadro e um trecho de 2 s do projeto-modelo do plugin foram renderizados aqui, então a ferramenta funciona; o filme do AgroSmart ainda não foi feito |
| **AI Avatar Presenter** (plugin da ManyMotions) | Fica **fora** desta versão | É pago, limita cada vídeo a 60 s, escreve o próprio texto e declara que não faz apresentação de produto. Com a voz do Gemini, deixou de ser necessário |

O Gemini não tem conector nesta conversa. Para usá-lo há dois caminhos: alguém da equipe gera os arquivos e coloca na pasta do projeto, ou o Claude opera o Gemini pelo navegador da equipe, com autorização. Nos dois casos, a escolha da voz é de quem ouve.

## Onde está cada item exigido no pitch

| Item exigido | Cenas |
|---|---|
| Problema resolvido | 1 |
| Público-alvo | 3 |
| Solução proposta | 2, 4 e 5 |
| Diferencial competitivo | 7, 8, 9 e 11 |
| Proposta de valor | 14 |

## Visual e som

- **Cores e letras:** as do próprio AgroMonitor. Verde-escuro `#0C3028` nos fundos de palco, cinza-claro `#F6F8F6` das páginas, verde `#17633F` e um único destaque em âmbar. Texto em Inter, a fonte da interface; títulos em Space Grotesk, a mesma do deck.
- **Telas:** sempre capturas reais da versão final, com o selo "Dados simulados" visível. Nenhuma tela é redesenhada.
- **Voz:** uma só, do começo ao fim. O tempo de cada cena é ajustado à duração real da fala, então os tempos abaixo podem variar alguns segundos.
- **Trilha:** o plugin traz cinco faixas, com uso liberado segundo a documentação dele (`bgm-tech-house`, `cat-walk`, `g-eazy-nba-type`, `house-vibez`, `tonight-hiphop`). Ela fica baixa, sob a narração, e os cortes seguem a batida da faixa escolhida.
- **Efeitos sonoros:** da biblioteca do plugin, um por movimento importante.
- **Entrega:** duas versões, com trilha e sem trilha.

## Bloco A — Abertura (0:00 a 0:30)

### Cena 1 — O problema

| Tempo | Na tela | Texto na tela | Efeito |
|---|---|---|---|
| 0:00 a 0:08 | Clipe 1: lavoura de milho ao amanhecer, vista de cima, em movimento lento | — | Entrada simples |
| 0:08 a 0:16 | Clipe 2: sensor de umidade cravado no solo, entre as fileiras | "Dados separados" | As três etiquetas entram uma a uma, no ritmo da fala |
| 0:16 a 0:24 | Clipe 3: mão examinando uma folha de milho com manchas | "Alerta sem explicação" | — |
| 0:24 a 0:30 | O clipe 3 escurece até o verde-escuro do palco | "Falta de dado vira “normal”" | Passagem para a marca |

Um aviso pequeno, "Imagens ilustrativas geradas por IA", fica no canto durante os três clipes.

**Pedidos para o Gemini gerar os clipes** (16:9, sem pessoas reconhecíveis, sem texto na imagem, sem fala):

1. "Plano aéreo lento sobre uma lavoura de milho ao amanhecer, névoa baixa, luz dourada, câmera avançando devagar, estilo documentário."
2. "Close de um sensor de umidade cravado no solo entre fileiras de soja jovem, foco raso, câmera deslizando lentamente para o lado, luz natural da manhã."
3. "Close da mão de uma agrônoma segurando uma folha de milho com manchas amareladas e uma pequena lagarta, câmera na mão e estável, luz natural."

**Se a equipe não quiser gastar créditos de vídeo,** a cena vira texto animado sobre o fundo verde-escuro, com a mesma narração e as mesmas três etiquetas. O resto do roteiro não muda.

## Bloco B — Filme do produto (0:30 a 1:50)

Cada cena usa um único efeito do plugin, e nenhum efeito se repete. A coluna "Efeito" traz o nome do cartão do plugin; as amostras animadas de cada um estão em <https://vincentwei1021.github.io/video-shotcraft/library.html>.

| # | Tempo | Item do pitch | O que acontece na tela | Texto na tela | Efeito |
|---|---|---|---|---|---|
| 2 | 0:30 a 0:35,5 | Solução (marca) | Fundo verde-escuro. O nome se desenha letra a letra e fica parado por mais de 1 s | "AgroMonitor" · "módulo do AgroSmart" | `letterspace-materialize` |
| 3 | 0:35,5 a 0:42,5 | Público-alvo | Uma frase fixa; só a etiqueta do final troca, três vezes | "Para quem decide no campo:" + "o produtor rural" → "o agrônomo" → "o gestor da operação" | `pill-slot-cycle` |
| 4 | 0:42,5 a 0:48,5 | Solução | A câmera começa colada no indicador "157 leituras no período" e sobe, revelando a Visão Geral inteira | "Sensores + observações de campo = prioridades por talhão" | `crane-rise-reveal` |
| 5 | 0:48,5 a 0:54,5 | Solução | Um foco de luz percorre a página e para na linha do Talhão B. A câmera se aproxima, a linha se destaca da página e volta ao lugar | "Talhão B · prioridade alta · regra R2" | `spotlight-hero-card` |
| 6 | 0:54,5 a 0:56,5 | (respiro) | Cartão de texto | "E quando falta dado?" | `paper-title-card` |
| 7 | 0:56,5 a 1:05,5 | Diferencial: honesto com a incerteza | As duas capturas reais da mesma leitura ficam sobrepostas. Uma barra vertical atravessa a tela: de um lado "Indeterminada", do outro "Alta" | Antes: "Sem observação de campo: indeterminada" · Depois: "Com a observação: prioridade alta" | `before-after-slider-scrub` |
| 8 | 1:05,5 a 1:13,5 | Diferencial: explicável | Uma linha de luz desce pelo cartão da ocorrência. Onde ela passa, molduras marcam a regra, a evidência e a orientação | "A regra: R2" · "A evidência: 34% de folhas afetadas, lagarta, 4 dias" · "A orientação: realizar inspeção técnica" | `scanline-annotate-focus` |
| 9 | 1:13,5 a 1:22 | Diferencial: rastreável | A câmera corre por uma linha do tempo com as etapas principais de uma execução e freia na última | "Entrada recebida → Validar dados → Persistir Raw → Publicar Trusted → Aplicar regras → Publicar Refined → Execução concluída" | `timeline-travel` |
| 10 | 1:22 a 1:24 | (respiro) | Cartão de texto | "E roda sozinho." | `paper-title-card` |
| 11 | 1:24 a 1:32 | Diferencial: leve e local | Um terminal digita o comando. No Enter, corte para o painel real de execução contínua, com o estado "Ativa" | `docker compose up -d` · "Um container. Um comando." | `typewriter-moves`, variante `terminal-typewriter` |
| 12 | 1:32 a 1:41 | Qualidade e segurança | O número gira dígito a dígito até travar. Depois entram duas linhas menores e uma nota | "63 testes automatizados aprovados" · "22 de 22 verificações no container" · "0 vulnerabilidades críticas ou altas com correção" · nota: "47 altas sem correção publicada seguem no relatório" | `odometer-digit-roll` |
| 13 | 1:41 a 1:50 | Estágio do produto | Três cartões viram de frente, um depois do outro | "Entregue: motor de regras, painel, execução contínua, container, pipeline" · "Simulado: dados de sensores e de campo" · "Roadmap: sensores físicos, login, notificações" | `card-flip-reveal` |

O cartão de respiro `paper-title-card` aparece duas vezes de propósito: ele é a pausa entre blocos de informação, não uma cena de efeito.

## Bloco C — Encerramento (1:50 a 2:12)

| # | Tempo | Item do pitch | O que acontece na tela | Texto na tela | Efeito |
|---|---|---|---|---|---|
| 14 | 1:50 a 2:00 | Proposta de valor | A primeira palavra aparece grande no centro; a frase se completa ao redor dela e fica parada por 2 s | "Saber onde olhar primeiro na lavoura, e por quê." | `lead-word-zoom-assemble` |
| 15 | 2:00 a 2:12 | Encerramento | Elementos das cenas anteriores (a etiqueta "Alta", a regra "R2", um nó da linha do tempo, o terminal, o "63") voam de volta e cercam o nome. Fica parado por 1,5 s e escurece | "AgroSmart" · "AgroMonitor · Fase 7" · "github.com/SaulVasconcelos/AgroSmart" | `outro-group-photo-launch` |

## Narração

Este é o texto que o Gemini vai ler, cena por cena. São cerca de 250 palavras, o que dá entre 1 min 40 s e 1 min 55 s de fala dentro dos 2 min 12 s.

Instrução de estilo para a voz: "Narração de vídeo de produto em português do Brasil, tom calmo, claro e confiante, ritmo natural, sem soar como propaganda."

| Cena | Fala |
|---|---|
| 1 | Uma lavoura monitorada produz dados o tempo todo. Os sensores medem umidade e temperatura, e quem anda pelo campo anota o que vê nas plantas. Mas essas informações ficam separadas, e nenhuma delas diz onde está a urgência. Um alerta sem explicação é difícil de confiar. E, quando falta a observação de campo, o sensor sozinho não prova que está tudo bem. |
| 2 | Este é o AgroMonitor, um módulo do AgroSmart. |
| 3 | Ele foi pensado para quem decide no campo: o produtor rural, o agrônomo e o gestor da operação. |
| 4 | Ele cruza sensores e observações de campo e mostra as prioridades de cada talhão. |
| 5 | Aqui, o Talhão B aparece com prioridade alta, pela regra R2. |
| 6 | E quando falta dado? |
| 7 | Sem observação de campo, a resposta é indeterminada, nunca normal. Registrada a observação, a mesma leitura passa a prioridade alta. |
| 8 | Toda prioridade mostra o porquê: a regra aplicada, a evidência usada e a orientação sugerida. |
| 9 | Cada execução deixa rastro no event log, da entrada recebida até a publicação do resultado. |
| 10 | E roda sozinho. |
| 11 | Um comando sobe a plataforma em um container, e a execução contínua gera e processa leituras em ciclos. |
| 12 | São 63 testes automatizados aprovados, 22 de 22 verificações no container e nenhuma vulnerabilidade crítica ou alta com correção disponível. |
| 13 | O software está entregue e testado. Os dados são simulados. Sensores físicos, login e notificações ficam no roadmap. |
| 14 | A nossa proposta de valor: saber onde olhar primeiro na lavoura, e por quê. |
| 15 | AgroSmart. O código, as evidências e a documentação estão no nosso repositório. |

## De onde vem cada imagem e cada número

| Cena | Origem |
|---|---|
| 1 | Clipes gerados pelo Gemini (Veo). São ilustrativos e levam o aviso na tela |
| 4 e 5 | Tela Visão Geral: captura real em [capturas_pitch/visao_geral.png](capturas_pitch/visao_geral.png). Na produção ela é refeita em alta resolução, com o mesmo fluxo |
| 7 | [capturas_pitch/exemplo_antes_nd.png](capturas_pitch/exemplo_antes_nd.png) e [exemplo_depois_r2.png](capturas_pitch/exemplo_depois_r2.png): a mesma leitura do Talhão B, antes e depois da observação de campo ([registro.json](capturas_pitch/registro.json)) |
| 8 | Cartão da ocorrência R2, da mesma captura |
| 9 | Etapas do event log, como em [../04_processos/ANALISE_PROCESSO.md](../04_processos/ANALISE_PROCESSO.md), seção 3 |
| 11 | Painel "Execução contínua e monitoramento": captura real, a refazer em alta resolução |
| 12 | [../03_evidencias/devsecops_ci/LEIA_ME.md](../03_evidencias/devsecops_ci/LEIA_ME.md): 45 testes Python + 18 de interface, 22 de 22 verificações, 0 bloqueantes, 47 altas sem correção |
| 13 | [../README.md](../README.md) e [LEIA_ME.md](LEIA_ME.md). O roadmap é proposta |

## O que continua fora do vídeo

O projeto não tem dados para sustentar estas afirmações, então elas não entram nem na fala nem no texto da tela:

- que o problema ou os perfis foram validados com produtores;
- ganho de produtividade, economia ou redução de defensivos;
- comparação com concorrentes, ou que o produto é o único do mercado;
- que existem sensores físicos, login, notificações ou inteligência artificial no produto.

A voz e os clipes da abertura são gerados por IA. Isso fica registrado em [LEIA_ME.md](LEIA_ME.md), e convém confirmar se a disciplina aceita.

## Três decisões da equipe antes de produzir

1. **Como o Gemini entra:** alguém da equipe gera a voz e os clipes e salva na pasta do projeto, ou o Claude opera o Gemini pelo navegador da equipe. Nos dois casos, alguém precisa ouvir e escolher a voz.
2. **Abertura:** os três clipes de lavoura do Gemini, ou só texto animado.
3. **Trilha, duração e cenas:** qual das cinco faixas, e se os 2 min 12 s e as 15 cenas estão bons ou se algo deve sair, entrar ou mudar de texto.

## O que acontece depois da aprovação

1. Voz: uma gravação por cena, com a voz escolhida. A duração de cada fala define o tempo final da cena.
2. Clipes da abertura, se aprovados.
3. Captura das telas em alta resolução, com o mesmo fluxo das capturas atuais.
4. Montagem das cenas, uma por vez, conferindo um quadro de cada.
5. Som: narração, trilha baixa com os cortes na batida e efeitos sonoros.
6. Vídeo completo, conferido nos pontos de corte, com duração e áudio verificados. O que não dá para conferir daqui é como o som soa: a equipe precisa ouvir antes de entregar.

A versão anterior do roteiro, com uma fala por slide, continua em [roteiro_video_pitch.md](roteiro_video_pitch.md) como reserva, caso a equipe prefira gravar a apresentação com a própria voz.
