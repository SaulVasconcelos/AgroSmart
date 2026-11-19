# Roteiro — vídeo pitch por slides (reserva)

> O vídeo pitch entregue é o filme animado de [video_pitch_animado/](video_pitch_animado/LEIA_ME.md), feito a partir de [roteiro_video_pitch_animado.md](roteiro_video_pitch_animado.md) e aprovado pela equipe em 19/11/2026. Este roteiro, com uma fala por slide, fica como reserva, para uma apresentação ao vivo dos slides.

Duração planejada: **4 min 40 s**. O limite é de 5 minutos, então há 20 segundos de folga.

O pitch segue os 11 slides do deck: <https://claude.ai/artifact/KqJzpFu9JXSFy71Du9Eukv>. Os cinco itens exigidos pelo requisito 6 estão nestes slides:

| Item exigido | Slide |
|---|---|
| Problema resolvido | 2 |
| Público-alvo | 3 |
| Solução proposta | 4, 5 e 6 |
| Diferencial competitivo | 7 |
| Proposta de valor | 8 |

As falas são proposta: ajustem as palavras ao jeito de quem for apresentar, mas mantenham os números e os limites. A origem de cada afirmação está em [LEIA_ME.md](LEIA_ME.md).

Já existe uma versão montada com **voz sintética**: [video_pitch/video_pitch.mp4](video_pitch/video_pitch.mp4). Ela usa estas falas, com as adaptações descritas em [LEIA_ME.md](LEIA_ME.md). As instruções abaixo valem se a equipe preferir gravar com a própria voz.

## Antes de gravar

1. Abram o deck em modo de apresentação, em tela cheia.
2. Usem um gravador que capture a tela com o microfone, em 1920 × 1080.
3. Ensaiem uma vez com cronômetro. Se a fala completa passar de 4 min 50 s, usem os cortes indicados no fim.

## O que não dizer

O projeto não tem dados para sustentar estas afirmações, então elas ficam fora da fala:

- que o problema ou os perfis foram validados com produtores;
- ganho de produtividade, economia ou redução de defensivos;
- comparação com concorrentes, ou que o produto é o único do mercado;
- que existem sensores físicos, login, notificações ou inteligência artificial no produto.

## Falas por slide

### Slide 1 — AgroSmart (0:00 a 0:15)

> Olá, somos a equipe do AgroSmart. Vamos apresentar o AgroMonitor, o módulo que ajuda quem cuida da lavoura a saber onde olhar primeiro, e por quê.

### Slide 2 — O problema (0:15 a 0:45)

> Uma lavoura monitorada produz muitos dados. Os sensores medem umidade e temperatura o tempo todo, e quem anda pelo campo anota o que vê nas plantas. O problema é que essas informações ficam separadas e não dizem onde está a urgência. Quando chega um alerta sem explicação, é difícil confiar nele. E existe um risco silencioso: quando falta informação, o sistema pode tratar a situação como se estivesse tudo normal.

### Slide 3 — Público-alvo (0:45 a 1:10)

> Pensamos em três perfis. O produtor rural, que quer saber o que merece atenção hoje e em qual talhão. O agrônomo ou consultor, que precisa ver a evidência por trás de cada recomendação. E o gestor da operação, que acompanha onde as ocorrências se concentram ao longo do tempo. São hipóteses de produto, que ainda precisam ser validadas com usuários.

### Slide 4 — A solução (1:10 a 1:40)

> A nossa solução é o AgroMonitor. Ele cruza as leituras dos sensores com as observações de campo e devolve uma lista de prioridades por talhão. Esta é a tela real do produto, com dados simulados. O Talhão B, de milho, está com prioridade alta por alerta de infestação. O Talhão C, de café, com prioridade alta por estresse hídrico. E o Talhão A, de soja, está indeterminado, porque faltam dados.

### Slide 5 — Como funciona (1:40 a 2:15)

> Por dentro são quatro passos. As leituras e as observações entram e são validadas antes de gravar. Depois são tratadas: duplicatas removidas, e o que é inválido vai para quarentena. Em seguida, sete regras definem prioridade, alerta e orientação, e vale a primeira que se aplica. Por exemplo, pouca umidade com temperatura alta indica estresse hídrico, e a orientação é priorizar a irrigação. A saída é o painel, e a decisão final é sempre de uma pessoa.

### Slide 6 — Um exemplo real (2:15 a 2:50)

> Um exemplo real. O sensor do Talhão B mediu 50% de umidade e 33 graus. Sem observação de campo, o AgroMonitor responde "indeterminada" e pede o registro da observação. Ele não diz que está tudo bem. Quando registramos a observação, com 34% de folhas afetadas e lagarta há quatro dias, a mesma leitura passa a prioridade alta, pela regra R2, com orientação de inspeção técnica. A leitura do sensor não mudou. O que mudou foi a evidência disponível.

### Slide 7 — Diferencial competitivo (2:50 a 3:20)

> O nosso diferencial está em quatro pontos. É explicável: toda prioridade mostra a regra, a evidência e a justificativa. É honesto com a incerteza: sem dado de campo, a resposta é "indeterminada", nunca "normal". É rastreável: cada execução fica registrada do começo ao fim. E é leve: roda em um único container, sem depender de nuvem. São diferenciais que demonstramos no próprio produto.

### Slide 8 — Proposta de valor (3:20 a 3:35)

> A nossa proposta de valor cabe em uma frase: saber onde olhar primeiro na lavoura, e por quê. Para produtores, consultores e gestores, os dados viram prioridades de investigação, com regras explicáveis e evidência por talhão.

### Slide 9 — Qualidade e segurança (3:35 a 4:05)

> E o produto se sustenta tecnicamente. São 63 testes automatizados aprovados. A aplicação em container passa em 22 de 22 verificações. A análise de vulnerabilidades não encontrou nenhuma falha crítica ou alta que tenha correção disponível. E o mesmo pipeline foi aprovado em dois ambientes: no nosso computador e no GitHub Actions. Isso não significa zero vulnerabilidades: 47 de severidade alta, ainda sem correção do Debian, continuam no relatório.

### Slide 10 — Entregue, simulado e roadmap (4:05 a 4:30)

> Para sermos claros sobre o estágio do produto. O motor de regras, o painel, a execução contínua, o container, o pipeline e a análise de processo estão entregues e testados. Os dados de sensores e de campo são simulados. E o que ainda não existe está no roadmap: sensores físicos, login, notificações, processamento incremental e a validação com produtores.

### Slide 11 — Encerramento (4:30 a 4:40)

> O código, as evidências e a documentação estão no nosso repositório. Obrigado.

## Se passar do tempo

Cortem nesta ordem, até caber em 4 min 50 s:

1. No slide 5, a frase do exemplo ("Por exemplo, pouca umidade…").
2. No slide 9, a última frase. O aviso sobre as 47 vulnerabilidades continua escrito no slide.
3. No slide 4, a descrição dos talhões C e A.

## Depois de gravar

- Confiram a duração: no máximo 5 minutos.
- Confiram que cada fala bate com o slide que está na tela, principalmente os números dos slides 6 e 9.
- Registrem em [LEIA_ME.md](LEIA_ME.md) onde o vídeo foi entregue. O GitHub recusa arquivos com mais de 100 MB.
