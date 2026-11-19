#!/usr/bin/env bash
# Junta as cenas renderizadas (out/cenas/sNN.mp4) e põe o som, sem recodificar a imagem.
# Saídas: out/video_pitch_agrosmart.mp4 (com trilha) e out/video_pitch_agrosmart_sem_trilha.mp4.
set -euo pipefail
cd "$(dirname "$0")/.."
: > out/lista.txt
for f in out/cenas/s*.mp4; do echo "file '$(basename "$f")'" >> out/lista.txt; done
mv out/lista.txt out/cenas/lista.txt
ffmpeg -v error -y -f concat -safe 0 -i out/cenas/lista.txt -c copy out/_imagem.mp4
for v in com_trilha sem_trilha; do
  nome="video_pitch_agrosmart"; [ "$v" = "sem_trilha" ] && nome="video_pitch_agrosmart_sem_trilha"
  ffmpeg -v error -y -i out/_imagem.mp4 -i "out/som_$v.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 \
    -movflags +faststart -metadata title="AgroSmart — vídeo pitch (AgroMonitor, Fase 7)" -metadata comment="Voz e imagens da abertura geradas por IA. Dados simulados." "out/$nome.mp4"
done
rm -f out/_imagem.mp4
ls -la out/*.mp4
