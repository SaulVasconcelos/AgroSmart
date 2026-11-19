# Vídeo pitch animado — AgroSmart, Fase 7

Vídeo do pitch de 2 min 14 s (o limite da entrega é de 5 minutos), montado em 19/11/2026 no ambiente de trabalho do Claude a partir do [roteiro aprovado pela equipe](../roteiro_video_pitch_animado.md).

| Arquivo | O que é |
|---|---|
| [video_pitch_agrosmart.mp4](video_pitch_agrosmart.mp4) | Versão com trilha. 133,57 s, 1920 × 1080, 30 quadros por segundo, H.264 e áudio AAC estéreo de 48 kHz |
| [video_pitch_agrosmart_sem_trilha.mp4](video_pitch_agrosmart_sem_trilha.mp4) | A mesma imagem, com narração e efeitos sonoros, sem a música |
| [legendas.srt](legendas.srt) | O texto da narração, frase a frase, nos tempos do vídeo. É um arquivo à parte: não está gravado na imagem |
| [projeto/](projeto/) | Tudo o que gera o vídeo: código das cenas, capturas das telas, imagens da abertura, narração, trilha, efeitos e scripts |
| [conferencia/](conferencia/) | O que foi medido depois da montagem: quadros de cada cena, quadros em volta de cada corte e o relatório do som |

**A equipe assistiu ao vídeo pronto e o aprovou em 19/11/2026.** O ambiente em que ele foi montado não reproduz áudio: ali, posição, duração e volume de cada som foram medidos, mas não ouvidos. Antes da montagem, a equipe já tinha ouvido e aprovado a voz na gravação solta da narração.

## Como foi feito

| Parte | Ferramenta | Observação |
|---|---|---|
| Narração | Geração de fala do Google AI Studio, modelo Gemini 3.8 Flash TTS, voz "Nika" | Voz sintética, escolhida pela equipe entre duas opções. Uma única gravação com o texto das 15 cenas e a instrução de estilo do roteiro. Ninguém da equipe fala no vídeo |
| Imagens da abertura | Aplicativo Gemini: ferramenta de vídeo (plano aéreo e dois planos de sensor) e ferramenta de imagem (mão com a folha de milho) | **Ilustrações geradas por IA**, não registros de uma lavoura real. O aviso "Imagens ilustrativas geradas por IA" fica na tela durante toda a abertura |
| Telas do produto | Capturas reais do AgroMonitor (`main`, commit `f8732f5`), com dados simulados | Nenhuma tela foi redesenhada. O que aparece é a captura inteira ou um recorte dela |
| Animação | Remotion 4.0.484, com os cartões de movimento do plugin [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | Cada cena parte do código de exemplo do cartão indicado no roteiro. O cabeçalho de cada arquivo em [projeto/src/shots/](projeto/src/shots/) diz o que foi mantido e o que foi adaptado |
| Trilha e efeitos | Biblioteca de áudio do plugin (Mixkit) | Faixa `bgm-tech-house`, escolhida pela equipe. Ver "Licenças e avisos" |
| Montagem do som e do arquivo final | Python (numpy) e ffmpeg | [montar_som.py](projeto/scripts/montar_som.py) e [juntar.sh](projeto/scripts/juntar.sh) |

## O que mudou em relação ao roteiro

- **Abertura.** O roteiro previa três clipes de vídeo. O aplicativo Gemini gerou o plano aéreo e o plano do sensor; numa nova tentativa devolveu o mesmo plano aéreo seguido de um segundo plano de sensor; depois disso a opção de criar vídeo ficou desabilitada na conta. A mão com a folha de milho foi então gerada como **imagem parada**, que entra com uma aproximação lenta. A cena ficou assim: plano aéreo, sensor, folha, tela dividida entre sensor e folha ("Dados separados") e o segundo plano de sensor, que escurece até o palco da marca. As três etiquetas do roteiro e o texto da fala não mudaram.
- **Duração.** 2 min 14 s, contra 2 min 12 s planejados. O tempo de cada cena foi ajustado à fala real e arredondado para um número inteiro de batidas da trilha.
- **Cena 9.** Os cartões levam o nome da etapa e uma descrição ("camada Raw", "regras R1–R7"), sem número de ordem: o caminho completo no event log tem outras atividades entre essas sete ([ANALISE_PROCESSO.md](../../04_processos/ANALISE_PROCESSO.md), seção 3).
- **Cenas 7 e 8.** O cartão da ocorrência aparece enquadrado na parte esquerda (título, medidas, evidências e orientação), para o texto ficar legível em vídeo. A coluna "Justificativa e origem" fica fora do quadro.
- **Passagens entre cenas.** Cortes secos no tempo forte da trilha. As cenas 4 e 5 emendam na mesma imagem da Visão Geral, e as cenas 7 e 8, no mesmo cartão.

## Cena a cena

| # | Tempo | Cartão do video-shotcraft | Texto na tela |
|---|---|---|---|
| 1 | 0:00 a 0:27 | — (montagem simples das imagens da abertura) | "Dados separados" · "Alerta sem explicação" · "Falta de dado vira “normal”" · "Imagens ilustrativas geradas por IA" |
| 2 | 0:27 a 0:33 | `letterspace-materialize` | "AGROMONITOR" · "módulo do AgroSmart" |
| 3 | 0:33 a 0:41 | `pill-slot-cycle` | "Para quem decide no campo:" + "o produtor rural" → "o agrônomo" → "o gestor da operação" |
| 4 | 0:41 a 0:48 | `crane-rise-reveal` | "Sensores + observações de campo = prioridades por talhão" |
| 5 | 0:48 a 0:54 | `spotlight-hero-card` | "Talhão B · prioridade alta · regra R2" |
| 6 | 0:54 a 0:56 | `paper-title-card` | "E quando falta dado?" |
| 7 | 0:56 a 1:06 | `before-after-slider-scrub` | "ANTES · Sem observação de campo: indeterminada" · "DEPOIS · Com a observação: prioridade alta" |
| 8 | 1:06 a 1:14 | `scanline-annotate-focus` | "A regra: R2" · "A evidência: 34% de folhas afetadas, lagarta, 4 dias" · "A orientação: realizar inspeção técnica" |
| 9 | 1:14 a 1:21 | `timeline-travel` | Entrada recebida · Validar dados · Persistir Raw · Publicar Trusted · Aplicar regras · Publicar Refined · Execução concluída |
| 10 | 1:21 a 1:23 | `paper-title-card` | "E roda sozinho." |
| 11 | 1:23 a 1:31 | `typewriter-moves`, variante `terminal-typewriter` | `docker compose up -d` · "Um container. Um comando." |
| 12 | 1:31 a 1:43 | `odometer-digit-roll` | "63 testes automatizados aprovados" (45 em Python + 18 de interface) · "22 de 22 verificações no container" · "0 vulnerabilidades críticas ou altas com correção disponível" · "47 altas sem correção publicada seguem no relatório" |
| 13 | 1:43 a 1:52 | `card-flip-reveal` | Entregue · Simulado · Roadmap, com os itens de cada um, e "O roadmap é proposta: nada dele existe no produto hoje." |
| 14 | 1:52 a 2:02 | `lead-word-zoom-assemble` | "Saber onde olhar primeiro na lavoura, e por quê." |
| 15 | 2:02 a 2:14 | `outro-group-photo-launch` | "AgroSmart" · "AgroMonitor · Fase 7" · "github.com/SaulVasconcelos/AgroSmart" |

O cartão `paper-title-card` aparece duas vezes de propósito, como pausa entre blocos. A fala de cada cena está no [roteiro](../roteiro_video_pitch_animado.md) e em [legendas.srt](legendas.srt).

## De onde vem cada imagem e cada número

| Cena | Origem |
|---|---|
| 1 | Imagens geradas por IA no aplicativo Gemini, em [projeto/public/clips/](projeto/public/clips/). São ilustração |
| 4, 5 e 15 | Tela Visão Geral: [visao_geral.png](projeto/public/tex/visao_geral.png), com os recortes [kpis_4x.png](projeto/public/tex/kpis_4x.png) e [linha_talhao_b_4x.png](projeto/public/tex/linha_talhao_b_4x.png) tirados da mesma foto. Mostra 157 leituras, 3 talhões, 116 ocorrências históricas, 11 críticas e o Talhão B com prioridade Alta pela regra R2 |
| 7 e 8 | [cartao_antes_nd.png](projeto/public/tex/cartao_antes_nd.png) e [cartao_depois_r2.png](projeto/public/tex/cartao_depois_r2.png): a mesma leitura simulada do Talhão B (umidade 40%, 26 °C), antes e depois da observação de campo (34% de folhas afetadas, lagarta, 4 dias). O texto da cena 8 é lido de [registro.json](projeto/public/tex/registro.json) |
| 9 | Nomes das atividades do event log, como em [ANALISE_PROCESSO.md](../../04_processos/ANALISE_PROCESSO.md), seção 3 |
| 11 | [painel_operacao.png](projeto/public/tex/painel_operacao.png): painel "Execução contínua e monitoramento" com o estado "Ativa" e cinco ciclos executados |
| 12 | [03_evidencias/devsecops_ci/LEIA_ME.md](../../03_evidencias/devsecops_ci/LEIA_ME.md): 45 testes em Python e 18 de interface, 22 de 22 verificações, nenhuma vulnerabilidade bloqueante e 47 altas sem correção publicada |
| 13 | [README.md](../../README.md) e [../LEIA_ME.md](../LEIA_ME.md). O roadmap é proposta |

As capturas foram refeitas para o vídeo em 19/11/2026, em escala 2x e 4x, por [capturar_telas_filme.py](projeto/scripts/capturar_telas_filme.py), com o mesmo fluxo das capturas dos slides. A leitura do simulador é sorteada a cada execução: o script repete a execução até a leitura cair no caso contado no roteiro (ND sem observação, R2 com ela) e registra a tentativa usada. Nesta captura foi a primeira. Por isso os valores do vídeo (40%, 26 °C) diferem dos do slide 6 (50%, 33 °C): são duas leituras simuladas diferentes do mesmo caso.

O vídeo não afirma validação com produtores, ganho de produtividade, economia, comparação com concorrentes nem a existência de sensores físicos, login, notificações ou inteligência artificial no produto.

## Som

A trilha entra a partir de 96,55 s da faixa, ponto escolhido para a batida mais forte voltar exatamente quando a marca aparece (0:27). Ela toca cerca de 15 dB abaixo da voz durante a fala e sobe nas pausas. Cada efeito sonoro está preso a uma ação da imagem e foi alinhado pelo pico do som, não pelo início do arquivo. A lista completa, com o instante e o volume de cada um, está em [projeto/src/som.json](projeto/src/som.json) e, medida, em [conferencia/som_relatorio.json](conferencia/som_relatorio.json).

## O que foi conferido

- **Duração e formato:** 4.007 quadros, 133,57 s, nos dois arquivos. A imagem das duas versões é a mesma.
- **Imagem:** quadros de todas as cenas e de todos os 14 cortes, tirados do arquivo final ([conferencia/](conferencia/)). Os textos da tela foram comparados com o roteiro e com as evidências do repositório.
- **Narração:** presente nas 15 cenas, começando no quadro previsto e terminando antes do fim de cada cena; a menor folga é de 0,43 s, na cena 7. A primeira montagem saiu **sem narração da cena 8 em diante**, por um erro na leitura do arquivo de voz; a medição do nível, cena a cena, mostrou a falha, que foi corrigida.
- **Cortes e trilha:** os 14 cortes caem a menos de 1 quadro do ataque grave mais próximo da trilha (maior diferença: 0,92 quadro).
- **Volume:** −16,2 LUFS com trilha e −16,1 LUFS sem trilha, com pico de −1,5 dBFS. O som do MP4 está em sincronia com a mixagem (diferença medida: 0 ms).
- **Efeitos:** os 32 efeitos caem no quadro da ação e ficam de 12 a 25 dB acima da trilha naquele instante.

## O que a montagem não conferiu

Os itens abaixo ficaram fora da conferência feita no ambiente de montagem. A aprovação da equipe, em 19/11/2026, veio depois, com o vídeo pronto.

- **Como soa.** Voz, música e efeitos não foram ouvidos no ambiente de montagem. Quem ouviu foi a equipe, ao assistir ao vídeo pronto.
- **A divisão da narração por cena.** A gravação é uma só. Os trechos foram separados pelas pausas da fala, e a duração de cada trecho bate com o número de palavras, mas isso não substitui ouvir. Se uma frase aparecer cortada ou fora da cena, os tempos de cada trecho estão em [projeto/src/som.json](projeto/src/som.json).
- **Os instantes de palavras no meio de uma frase.** Onde a imagem acompanha uma palavra sem pausa antes dela (as três etiquetas da cena 3, as três molduras da cena 8), o instante foi estimado pela proporção de sílabas. Pode haver diferença de alguns décimos de segundo.
- **Revisão por outra pessoa.** A conferência acima foi feita por quem montou o vídeo. A revisão independente foi a da equipe, que aprovou o vídeo.

## Licenças e avisos

- **Voz e imagens geradas por IA.** Convém confirmar se a disciplina aceita. O aviso das imagens está na tela; o da voz está neste arquivo.
- **Trilha `bgm-tech-house`.** Vem da biblioteca do plugin, que a registra como material do Mixkit **sem identificação da faixa de origem** e recomenda conferir antes de uso comercial. Para a entrega acadêmica o risco é baixo. Se o vídeo for publicado em plataforma aberta, use a versão sem trilha ou troque a faixa: as outras quatro da biblioteca têm autor e endereço registrados. Trocar a trilha não exige refazer a imagem.
- **Efeitos sonoros.** Mixkit, pela biblioteca do plugin. Três deles (`keyboard`, `riser-cine`, `sparkle`) também não têm endereço de origem registrado.
- **Fontes.** Inter, Space Grotesk e JetBrains Mono, licença SIL Open Font 1.1 (textos em [projeto/public/fonts/](projeto/public/fonts/)).
- **Remotion.** Gratuito para pessoas e equipes pequenas; empresas maiores precisam de licença ([termos](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)).
- **video-shotcraft.** Código sob licença Apache 2.0. O autor pede, sem obrigar, que seja citado se o vídeo for publicado.

## Para refazer

Requer Node.js 22, ffmpeg, Python 3 com `numpy` e `soundfile` e, só para refazer as capturas, Playwright com Chromium.

```bash
cd 05_apresentacao/video_pitch_animado/projeto
npm ci
node scripts/renderizar.mjs          # imagem, cena a cena, em out/cenas/
python scripts/montar_som.py         # som com e sem trilha, em out/
python scripts/gerar_legendas.py     # out/legendas.srt
bash scripts/juntar.sh               # os dois MP4, em out/
```

Para mudar um texto ou um tempo, edite a cena em `src/shots/` ou a linha do tempo em `src/timeline.json` e renderize só essa cena (`node scripts/renderizar.mjs s12`). Para conferir um quadro sem renderizar a cena: `node scripts/quadros.mjs s12:100`. Se as capturas forem refeitas (`python scripts/capturar_telas_filme.py`), os valores da leitura mudam; a cena 8 acompanha sozinha, e a tabela deste arquivo precisa ser atualizada. O arquivo final versionado foi renderizado com qualidade 21 na abertura (`CRF=21 node scripts/renderizar.mjs s01`) e 16 nas demais cenas.
