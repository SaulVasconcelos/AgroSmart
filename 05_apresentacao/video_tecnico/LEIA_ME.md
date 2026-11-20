# Vídeo final técnico — AgroSmart, Fase 7

Vídeo de 6 min 4 s (a exigência é de 5 a 8 minutos), gravado e montado em 19/11/2026 no ambiente de trabalho do Claude, seguindo o [roteiro](../roteiro_video_tecnico.md).

| Arquivo | O que é |
|---|---|
| [video_tecnico_agrosmart.mp4](video_tecnico_agrosmart.mp4) | O vídeo. 364,2 s, 1920 × 1080, 30 quadros por segundo, H.264 e áudio AAC |
| [legendas.srt](legendas.srt) | O texto da narração, frase a frase, nos tempos do vídeo. É um arquivo à parte |

> Os arquivos de produção deste vídeo (scripts, capturas em alta, áudios separados e quadros de conferência) não fazem parte da entrega. Onde este texto cita um desses arquivos pelo nome, é só para registrar de onde veio cada coisa.

**A equipe ainda precisa assistir ao vídeo com som.** O ambiente em que ele foi montado não reproduz áudio: a presença e a posição de cada fala foram medidas, mas a pronúncia e a entonação não foram ouvidas.

## O que é real e o que não é

- **A imagem é uma gravação de tela.** Uma tela virtual de 1920 × 1080 foi gravada com o ffmpeg enquanto um Chromium com janela abria a plataforma e um terminal (xterm) recebia os comandos, digitados tecla a tecla. Nenhuma tela foi redesenhada. A única coisa sobreposta à página é a seta do cursor, desenhada pelo script porque o navegador automatizado não move o cursor do sistema.
- **A plataforma estava em execução de verdade**, em container, com o `compose.yaml` do repositório. As leituras, a importação da observação de campo, a mudança de ND para R2, os ciclos da execução contínua, o comando `monitorar` e os logs aconteceram durante a gravação. O que a plataforma respondeu está resumido abaixo.
- **Os dados de sensores e de campo são simulados**, como em todo o projeto.
- **A narração é voz sintética**: voz "Nika" do Gemini 3.8 Flash TTS (Google AI Studio), a mesma do vídeo pitch. Ninguém da equipe fala no vídeo. O cartão de abertura avisa isso.
- **O container da gravação usa a base substituta.** O ambiente do Claude não acessa o Docker Hub, então a imagem `agrosmart:fase7` foi construída antes da gravação sobre `local/base-substituta:ubuntu24-python3` (Ubuntu 24.04 com Python 3.12), com `docker build --build-arg PYTHON_IMAGE=...`. A narração diz isso na cena 3, e o terminal mostra a lista de imagens e a linha do Dockerfile com a base oficial. O container com a base oficial `python:3.13-slim` foi aprovado no PC da equipe e no GitHub Actions: ver [03_evidencias/](../../03_evidencias/LEIA_ME.md).

## Cenas

| # | Tempo | O que aparece | Requisito do vídeo |
|---|---|---|---|
| — | 0:00 a 0:03 | Cartão de abertura | — |
| 1 | 0:03 a 0:24 | README do repositório | — |
| 2 | 0:24 a 1:10 | Diagrama da arquitetura, com o cursor acompanhando a fala | Explicação do fluxo |
| 3 | 1:10 a 1:45 | Terminal: `docker compose up -d`, `docker inspect`, `docker compose ps` (healthy), `docker image ls`, `grep PYTHON_IMAGE Dockerfile` | Funcionamento completo |
| 4 | 1:45 a 2:55 | Plataforma: Visão Geral, geração de uma leitura, Talhão B em ND, importação da observação, a mesma leitura em R2, Central de Alertas | Demonstração e fluxo |
| 5 | 2:55 a 3:35 | Painel da execução contínua (15 s por ciclo) e, no terminal, `python3 main.py monitorar` e `docker compose logs` | Demonstração |
| 6 | 3:35 a 4:25 | Relatório do pipeline no GitHub Actions (aprovado) e histórico das execuções no PC da equipe | Funcionamento completo |
| 7 | 4:25 a 5:39 | Event log, processo observado e a análise (gargalo, escala, rajada, decisões ND, melhorias) | Análise do processo |
| 8 | 5:39 a 6:04 | README (situação atual e o que não existe) e matriz de rastreabilidade | — |

## O que mudou em relação ao roteiro

- **Quem gravou.** O roteiro foi escrito para a equipe gravar no próprio PC. A equipe pediu que o Claude gravasse e narrasse com a voz do Gemini.
- **Arquivos do repositório em vez de páginas do GitHub.** O navegador do ambiente de gravação não acessa o github.com. O README, os relatórios, o event log, os diagramas e a matriz aparecem num visualizador local simples, que mostra o caminho do arquivo no topo. São os mesmos arquivos do repositório. Por isso a lista de execuções do GitHub Actions (os "três runs verdes" do roteiro) não aparece; no lugar dela está o relatório do run aprovado.
- **Cena 3.** A fala sobre a base da imagem foi trocada pelo aviso da base substituta, e entraram três comandos que mostram o que a fala afirma: usuário sem privilégios, raiz somente leitura, volume e imagens.
- **Comandos.** `docker compose ps` e `docker compose logs` foram usados com opções de formato, para caber na largura da tela. O terminal é Linux (bash), não PowerShell.
- **Cena 4.** Na Central de Alertas, a lista foi filtrada por severidade "Alta" para a ocorrência nova aparecer no topo.
- **Cena 6.** "No nosso computador" virou "no computador da equipe".
- **Duração.** 6 min 4 s, e não os 7 minutos planejados: a voz fala mais rápido do que a estimativa do roteiro.

## O que a gravação registrou

Do registro feito pelo script de gravação:

- antes da importação, a última leitura do Talhão B (sensor S-002, 19/11/2026 20:17, umidade 37%, 26 °C) estava em **ND**, "Observação de campo ausente", avaliação "Parcial";
- a importação respondeu "Importação concluída: 1 observação(ões) validadas. Filtros mantidos.";
- depois dela, **a mesma leitura** passou a **R2**, "Alerta de infestação", prioridade Alta, avaliação "Completa", com 34% de folhas afetadas, Lagarta, 4 dias, orientação "Realizar inspeção técnica";
- a execução contínua foi iniciada pela interface com intervalo de 15 s e seguiu sem falhas;
- nenhuma exceção de JavaScript na página.

A leitura do simulador é sorteada. A preparação para a execução contínua e gera leituras do Talhão B até a última cair em ND com umidade de pelo menos 35%, que é o caso contado no roteiro. Nenhum valor é digitado nem editado.

## Como a narração foi encaixada

O texto é o do [roteiro](../roteiro_video_tecnico.md), com os ajustes listados acima. Foi gerado em dois áudios (cenas 1 a 4 e 5 a 8). Para saber onde cada parágrafo e cada frase começam, cada áudio foi alinhado com uma leitura de referência do mesmo texto, feita parágrafo a parágrafo com o RHVoice (`alinhar.py` e `alinhar_frases.py`): todas as 18 fronteiras caíram dentro de uma pausa da fala. As ações da tela foram agendadas por esses instantes.

## O que foi conferido

- **Duração:** 364,2 s, dentro de 5 a 8 minutos.
- **Narração:** as 20 falas estão no vídeo, cada uma no instante previsto, com silêncio entre elas. Volume de −14,9 LUFS.
- **Imagem e fala juntas:** um quadro do arquivo final por fala, comparado com o texto da fala. Em todos, a tela mostra o que a fala descreve.
- **Números falados:** 45 testes Python e 18 de interface, 22 verificações, 6 vulnerabilidades com correção e 47 sem, 40 casos e 600 eventos, 8 variantes, 6 entradas rejeitadas, menos de 3% e quase 70% do tempo, 25 ms por mil leituras, 93 ms e 18 decisões ND conferem com os documentos do repositório ([ANALISE_PROCESSO.md](../../04_processos/ANALISE_PROCESSO.md) e [devsecops_equipe](../../03_evidencias/devsecops_equipe/LEIA_ME.md)).

## O que não foi conferido

- **Como soa.** Pronúncia de termos como "healthcheck", "healthy", "Raw", "Trusted", "Refined", "Ruff", "Bandit" e "Trivy" precisa ser ouvida pela equipe.
- **Os instantes das frases** vêm do alinhamento automático, não de audição. Pode haver diferença de alguns décimos de segundo entre a fala e o movimento do cursor.
- **Revisão por outra pessoa.** A conferência acima foi feita por quem montou o vídeo.

## Licenças e avisos

- **Voz:** gerada pelo Gemini 3.8 Flash TTS no Google AI Studio, na conta de um integrante da equipe. Confirmem se a disciplina aceita narração sintética.
- **Fontes da tela:** as da plataforma e do sistema (Inter, DejaVu).
- Os arquivos de mídia que saem do ambiente do Claude levam, embutida, uma marca de procedência dizendo que foram fornecidos pelo Claude.
