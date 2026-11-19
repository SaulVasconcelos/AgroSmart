# Apresentação do produto e vídeos — Fase 7

| Entregável | Situação |
|---|---|
| Slides do pitch (problema, solução, diferencial, público-alvo, proposta de valor) | **Prontos e revisados.** Deck editável: <https://claude.ai/artifact/KqJzpFu9JXSFy71Du9Eukv> (privado da conta que o criou, até ser compartilhado). **PENDENTE:** exportar o arquivo (PowerPoint ou PDF) para esta pasta |
| Roteiro do vídeo final técnico (5–8 min) | **Pronto:** [roteiro_video_tecnico.md](roteiro_video_tecnico.md), 8 cenas, 7 minutos planejados. Os passos da interface foram ensaiados na versão final |
| Roteiro do vídeo pitch (até 5 min) | **Pronto:** [roteiro_video_pitch.md](roteiro_video_pitch.md), uma fala por slide, 4 min 40 s planejados |
| Vídeo final técnico (5–8 min) — MP4 | **PENDENTE** — gravação pela equipe |
| Vídeo pitch (até 5 min) — MP4 | **Gerado com voz sintética:** [video_pitch/video_pitch.mp4](video_pitch/video_pitch.mp4), 4 min 39,5 s, 1920 × 1080, com legendas em [video_pitch.srt](video_pitch/video_pitch.srt). **PENDENTE:** a equipe assistir e aprovar, porque a pronúncia não foi conferida por audição, e confirmar se a disciplina aceita narração sintética. A alternativa é gravar com a voz da equipe, pelo roteiro |

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

## Vídeo do pitch com voz sintética

A pasta [video_pitch/](video_pitch/) tem o vídeo e tudo o que foi usado para montá-lo, em 19/11/2026, no ambiente de trabalho do Claude:

- **Imagem:** um quadro por slide em [video_pitch/quadros/](video_pitch/quadros/), desenhado no Chromium a partir dos arquivos do próprio deck, com as mesmas fontes. Não é uma exportação feita pela página do deck, então pequenos detalhes de desenho podem diferir.
- **Narração:** voz sintética Letícia-F123, do sintetizador RHVoice 1.8.0 (pacotes `rhvoice` e `rhvoice-brazilian-portuguese` do Ubuntu 24.04). A voz é de Olga Yakovleva e Fernando H. F. Botelho, sob licença CC BY-SA 4.0. Ninguém da equipe fala no vídeo.
- **Texto falado:** [video_pitch/narracao.json](video_pitch/narracao.json). Segue o [roteiro](roteiro_video_pitch.md), com três adaptações para a voz sintética: os números são ditos por extenso, "container" vira "contêiner" e os termos em inglês foram trocados ("pipeline" por "esteira de verificação", "GitHub Actions" por "serviço de integração contínua do repositório", "roadmap" por "plano de evolução", "login" por "autenticação de usuários"). O nome "Debian" não é falado. Os slides continuam com os termos originais.
- **Legendas:** uma por frase, com o tempo exato de cada fala ([video_pitch/tempos.json](video_pitch/tempos.json)).

Foi conferido: duração de 279,5 s (limite de 300 s), os 11 slides na ordem, a narração de cada slide começando 0,6 s depois da troca de slide e o volume uniforme entre os slides. **Não foi conferido:** como a voz soa. O ambiente não reproduz áudio nem tem reconhecimento de fala, então pronúncia e entonação precisam ser ouvidas por alguém da equipe.

Para refazer, num Linux com RHVoice e ffmpeg: `python 05_apresentacao/video_pitch/montar_video_pitch.py`. Para corrigir uma palavra mal pronunciada, basta trocar o texto do campo `voz` em `narracao.json` e rodar de novo.

## Capturas usadas nos slides

As telas em [capturas_pitch/](capturas_pitch/) são capturas reais da versão final (`main`, commit `f8732f5`), feitas em 18/11/2026 no ambiente de trabalho do Claude, com execução nativa sobre uma cópia temporária da amostra. A leitura e a observação de campo são **simuladas**. O arquivo [registro.json](capturas_pitch/registro.json) guarda a leitura sorteada e a decisão antes e depois da observação. Não houve exceção JS.

Para refazer (requer Playwright e Chromium): `python 05_apresentacao/capturar_telas_pitch.py`. A leitura sorteada muda a cada execução; se as capturas forem refeitas, os valores do slide 6 precisam ser atualizados para os do novo `registro.json`.

## Insumos já prontos para os vídeos

O script [gerar_observacao_demo.py](gerar_observacao_demo.py) gera o CSV de observação de campo usado na cena 4 do vídeo técnico, com a data do dia da gravação. Também estão prontos: a plataforma em container, o painel de execução contínua, o monitoramento pelo terminal, os relatórios do pipeline, o event log e a análise de processo ([../04_processos/ANALISE_PROCESSO.md](../04_processos/ANALISE_PROCESSO.md)), além das capturas em [../03_evidencias/capturas/](../03_evidencias/capturas/).
