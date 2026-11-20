# Apresentação do produto e vídeos — Fase 7

| Entregável | Situação |
|---|---|
| Slides do pitch (problema, solução, diferencial, público-alvo, proposta de valor) | **Prontos e aprovados pela equipe:** [slides_pitch_agrosmart.pdf](slides_pitch_agrosmart.pdf), 11 páginas em 16:9, gerado em 19/11/2026 a partir dos arquivos do deck. O deck editável continua em <https://claude.ai/artifact/KqJzpFu9JXSFy71Du9Eukv> (privado da conta que o criou, até ser compartilhado) |
| Roteiro do vídeo final técnico (5–8 min) | **Pronto:** [roteiro_video_tecnico.md](roteiro_video_tecnico.md), 8 cenas, 7 minutos planejados. Os passos da interface foram ensaiados na versão final |
| Roteiro do vídeo pitch (até 5 min) | **Aprovado pela equipe em 19/11/2026:** [roteiro_video_pitch.md](roteiro_video_pitch.md), filme animado narrado com voz gerada pelo Gemini, com imagens de lavoura do Gemini na abertura e telas reais animadas pelo plugin video-shotcraft |
| Vídeo final técnico (5–8 min) — MP4 | **Gravado em 19/11/2026:** [video_tecnico/video_tecnico_agrosmart.mp4](video_tecnico/video_tecnico_agrosmart.mp4), 6 min 4 s, 1920 × 1080: gravação de tela da plataforma em execução (container, navegador e terminal), com narração gerada por IA e legendas à parte. Como foi feito e o que foi conferido: [video_tecnico/LEIA_ME.md](video_tecnico/LEIA_ME.md). **Falta a equipe assistir com som** |
| Vídeo pitch (até 5 min) — MP4 | **Pronto e aprovado pela equipe em 19/11/2026:** [video_pitch/video_pitch_agrosmart.mp4](video_pitch/video_pitch_agrosmart.mp4), 2 min 14 s, 1920 × 1080, com legendas à parte. Como foi feito e o que foi medido: [video_pitch/LEIA_ME.md](video_pitch/LEIA_ME.md). |

São dois vídeos separados. O MP4 prévio da Fase 6 é histórico e não atende aos requisitos da Fase 7.

## Slides do pitch: conteúdo e origem de cada afirmação

São 11 slides, pensados para um pitch de até 5 minutos. O número de slides e o visual são escolhas da equipe, não exigência da rubrica. O visual usa as cores da própria interface do AgroMonitor.

| # | Slide | O que afirma | De onde vem |
|---|---|---|---|
| 1 | AgroSmart (capa) | Nome do produto e do módulo | — |
| 2 | O problema | Dados separados, alerta sem explicação, falta de dado tratada como "normal" | Problema de partida do projeto. **Não foi medido com produtores**, e o slide diz isso |
| 3 | Público-alvo | Produtor rural, agrônomo ou consultor, gestor | Perfis do briefing. São **hipóteses de produto**, sem pesquisa de campo, e o slide diz isso. O que cada um encontra corresponde a telas existentes (Visão Geral, detalhe do talhão, filtros por talhão e período) |
| 4 | A solução | Lista de prioridades por talhão | [capturas_pitch/visao_geral_prioridades.png](capturas_pitch/visao_geral_prioridades.png), recorte de [visao_geral.png](capturas_pitch/visao_geral.png) |
| 5 | Como funciona | Entrada → tratamento → regras → saída; três regras (R1, R4, ND) | [descricao_componentes.md](../01_arquitetura/descricao_componentes.md) e [regras.py](../02_plataforma/agrosmart/regras.py): condições, prioridades e orientações copiadas do código |
| 6 | Um exemplo real | A mesma leitura do Talhão B (umidade 50%, 33 °C) passa de ND para R2 depois da observação de campo (34%, lagarta, 4 dias) | [capturas_pitch/registro.json](capturas_pitch/registro.json), [exemplo_antes_nd.png](capturas_pitch/exemplo_antes_nd.png), [exemplo_depois_r2.png](capturas_pitch/exemplo_depois_r2.png) |
| 7 | Diferencial competitivo | Explicável, honesto com a incerteza, rastreável, leve e local | Demonstrado no produto: regra e justificativa em cada ocorrência, ND em vez de "normal", event log ([04_processos](../04_processos/ANALISE_PROCESSO.md)), container único só com a biblioteca padrão. **Não há comparação medida com concorrentes**, e o slide diz isso |
| 8 | Proposta de valor | "Saber onde olhar primeiro na lavoura, e por quê." | Proposta de valor de partida do briefing. É posicionamento, não prova de impacto |
| 9 | Qualidade e segurança | 63 testes (45 Python + 18 de interface), 22/22 verificações no container, 0 vulnerabilidades críticas ou altas com correção, 2 ambientes; 47 altas sem correção continuam reportadas | [03_evidencias/devsecops_ci](../03_evidencias/devsecops_ci/LEIA_ME.md) (run 44438716927) e [devsecops_equipe](../03_evidencias/devsecops_equipe/LEIA_ME.md) |
| 10 | Entregue, simulado e roadmap | Separa o que é software entregue, o que roda com dados simulados e o que não existe | [README.md](../README.md) e [ANALISE_PROCESSO.md § 6](../04_processos/ANALISE_PROCESSO.md). O roadmap é **proposta**, a ajustar pela equipe |
| 11 | Encerramento | Endereço do repositório | — |

O deck não traz números de mercado, clientes, ganhos de produtividade nem economia, porque o projeto não tem dados para isso.

### Como o PDF dos slides foi gerado

O arquivo [slides_pitch_agrosmart.pdf](slides_pitch_agrosmart.pdf) foi gerado em 19/11/2026, no ambiente de trabalho do Claude, por um script que desenha no Chromium os arquivos do deck, com as fontes do deck e as telas de [capturas_pitch/](capturas_pitch/), e grava uma página de 1920 × 1080 px por slide. Os arquivos usados são os da versão do deck aprovada pela equipe, a mesma que estava no editor em 19/11/2026.

Não é a exportação feita pela página do deck, então pequenos detalhes de desenho podem diferir do que o editor mostra. Foi conferido:

- o PDF tem 11 páginas, na ordem do deck, em 16:9;
- o texto de cada página é igual ao do slide correspondente;
- as cinco fontes usadas (Inter e Space Grotesk) estão embutidas no arquivo;
- o endereço do repositório, no último slide, é um link clicável;
- cada página, comparada com o mesmo slide desenhado na tela, só difere na borda das letras.


## Vídeo pitch

O vídeo pitch está em [video_pitch/](video_pitch/). O [LEIA_ME.md](video_pitch/LEIA_ME.md) da pasta descreve as ferramentas, as diferenças em relação ao roteiro, a origem de cada imagem e de cada número e os avisos de licença.

## Capturas usadas nos slides

As telas em [capturas_pitch/](capturas_pitch/) são capturas reais da versão final (`main`, commit `f8732f5`), feitas em 18/11/2026 no ambiente de trabalho do Claude, com execução nativa sobre uma cópia temporária da amostra. A leitura e a observação de campo são **simuladas**. O arquivo [registro.json](capturas_pitch/registro.json) guarda a leitura sorteada e a decisão antes e depois da observação. Não houve exceção JS.


## Insumos já prontos para os vídeos

O script [gerar_observacao_demo.py](gerar_observacao_demo.py) gera o CSV de observação de campo usado na cena 4 do vídeo técnico, com a data do dia da gravação. Também estão prontos: a plataforma em container, o painel de execução contínua, o monitoramento pelo terminal, os relatórios do pipeline, o event log e a análise de processo ([../04_processos/ANALISE_PROCESSO.md](../04_processos/ANALISE_PROCESSO.md)), além das capturas em [../03_evidencias/capturas/](../03_evidencias/capturas/).
