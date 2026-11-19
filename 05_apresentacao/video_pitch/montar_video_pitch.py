#!/usr/bin/env python3
"""Monta o vídeo do pitch: quadros dos slides + narração por voz sintética + legendas.

Requisitos (Linux): RHVoice com a voz brasileira Leticia-F123 e ffmpeg.
    sudo apt-get install rhvoice rhvoice-brazilian-portuguese ffmpeg

Entradas, nesta pasta:
    narracao.json      texto falado em cada slide, frase por frase
    quadros/NN_id.png  um quadro 1920x1080 por slide, na ordem do deck

Saídas, nesta pasta:
    video_pitch.mp4    H.264 1920x1080 a 30 fps, com áudio AAC estéreo
    video_pitch.srt    legendas, uma por frase
    tempos.json        duração de cada slide e de cada frase

Uso:  python montar_video_pitch.py [--velocidade 100]

Cada frase é sintetizada separadamente, para controlar as pausas e marcar o tempo exato das
legendas. Cada slide vira um arquivo de vídeo; os arquivos são unidos sem recodificar.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess  # nosec B404 - chama apenas RHVoice-test, ffmpeg e ffprobe
import sys
import tempfile
import wave
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TAXA = 24000            # Hz, mono, 16 bits: formato de saída da voz
FPS = 30
ENTRADA_S = 0.6         # silêncio entre a troca de slide e a primeira frase
PAUSA_FRASE_S = 0.32    # silêncio entre frases do mesmo slide
SAIDA_S = 0.7           # silêncio depois da última frase do slide
FINAL_S = 1.5           # tempo extra no último slide
TRANSICAO_S = 0.5       # fusão a partir do slide anterior
CODEC = ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def rodar(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)  # nosec B603
    if r.returncode != 0:
        sys.exit(f"Falhou ({r.returncode}): {' '.join(cmd[:4])} …\n{r.stderr[-1500:]}")
    return r.stdout


def silencio(segundos: float) -> bytes:
    return b"\x00\x00" * round(segundos * TAXA)


def sintetizar(texto: str, velocidade: int, pasta: Path, nome: str) -> bytes:
    """Devolve o PCM da frase, sem o silêncio que o sintetizador põe no começo e no fim."""
    txt, bruto, limpo = pasta / f"{nome}.txt", pasta / f"{nome}_bruto.wav", pasta / f"{nome}.wav"
    txt.write_text(texto + "\n", encoding="utf-8")
    rodar(["RHVoice-test", "-p", "Leticia-F123", "-r", str(velocidade), "-R", str(TAXA), "-i", str(txt), "-o", str(bruto)])
    corte = "silenceremove=start_periods=1:start_threshold=-45dB:detection=peak"
    rodar(["ffmpeg", "-y", "-v", "error", "-i", str(bruto), "-af", f"{corte},areverse,{corte},areverse",
           "-ar", str(TAXA), "-ac", "1", "-c:a", "pcm_s16le", str(limpo)])
    with wave.open(str(limpo), "rb") as w:
        if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (TAXA, 1, 2):
            sys.exit(f"Formato inesperado em {limpo}")
        pcm = w.readframes(w.getnframes())
    if len(pcm) < TAXA * 2 * 0.2:
        sys.exit(f"Áudio vazio ou curto demais para: {texto!r}")
    return pcm


def tempo_srt(s: float) -> str:
    ms = round(s * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    ap = argparse.ArgumentParser(description="Monta o vídeo do pitch com voz sintética")
    ap.add_argument("--velocidade", type=int, default=100, help="velocidade da fala em %% (100 = padrão da voz)")
    args = ap.parse_args()
    for exe in ("RHVoice-test", "ffmpeg", "ffprobe"):
        if not shutil.which(exe):
            sys.exit(f"{exe} não encontrado. Veja os requisitos no início deste arquivo.")
    roteiro = json.loads((AQUI / "narracao.json").read_text(encoding="utf-8"))
    quadros = sorted((AQUI / "quadros").glob("*.png"))
    slides = roteiro["slides"]
    if [q.stem.split("_", 1)[1] for q in quadros] != [s["id"] for s in slides]:
        sys.exit("Os quadros em quadros/ não batem com a ordem dos slides em narracao.json")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        trilha, legendas, tempos, cenas, inicio = b"", [], [], [], 0.0
        for n, slide in enumerate(slides):
            audio = silencio(ENTRADA_S)
            frases = []
            for k, frase in enumerate(slide["frases"]):
                if k:
                    audio += silencio(PAUSA_FRASE_S)
                pcm = sintetizar(frase["voz"], args.velocidade, tmp, f"s{n:02d}_{k:02d}")
                t0 = inicio + len(audio) / 2 / TAXA
                audio += pcm
                t1 = inicio + len(audio) / 2 / TAXA
                legendas.append((t0, t1, frase.get("legenda", frase["voz"])))
                frases.append({"inicio_s": round(t0, 3), "fim_s": round(t1, 3), "voz": frase["voz"]})
            audio += silencio(SAIDA_S + (FINAL_S if n == len(slides) - 1 else 0))
            n_quadros = -(-len(audio) * FPS // (2 * TAXA))          # arredonda para cima, em quadros de vídeo
            duracao = n_quadros / FPS
            audio += b"\x00\x00" * (round(duracao * TAXA) - len(audio) // 2)
            trilha += audio
            tempos.append({"slide": n + 1, "id": slide["id"], "inicio_s": round(inicio, 3), "duracao_s": round(duracao, 3), "frases": frases})

            # Um arquivo por slide, todos com o mesmo codificador; a fusão fica dentro do arquivo.
            parcial, cena = tmp / f"cena{n:02d}.parcial.mp4", tmp / f"cena{n:02d}.mp4"
            segura = f"format=yuv420p,loop=-1:1,trim=duration={duracao:.6f},setpts=PTS-STARTPTS"
            if n == 0:
                cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(quadros[0]),
                       "-vf", f"{segura},fade=t=in:st=0:d={TRANSICAO_S}"]
            else:
                fim = f",fade=t=out:st={duracao - 0.8:.3f}:d=0.8" if n == len(slides) - 1 else ""
                cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(quadros[n - 1]),
                       "-framerate", str(FPS), "-i", str(quadros[n]), "-filter_complex",
                       f"[0:v]format=yuv420p,loop=-1:1,trim=duration={TRANSICAO_S},setpts=PTS-STARTPTS[a];[1:v]{segura}[b];"
                       f"[a][b]xfade=transition=fade:duration={TRANSICAO_S}:offset=0{fim}[v]", "-map", "[v]"]
            rodar(cmd + CODEC + ["-frames:v", str(n_quadros), str(parcial)])
            parcial.rename(cena)
            cenas.append(cena)
            inicio += duracao

        with wave.open(str(tmp / "narracao.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(TAXA)
            w.writeframes(trilha)
        (tmp / "lista.txt").write_text("".join(f"file '{c}'\n" for c in cenas), encoding="utf-8")
        rodar(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(tmp / "lista.txt"), "-c", "copy", str(tmp / "mudo.mp4")])
        parcial = AQUI / "video_pitch.parcial.mp4"
        rodar(["ffmpeg", "-y", "-v", "error", "-i", str(tmp / "mudo.mp4"), "-i", str(tmp / "narracao.wav"), "-map", "0:v", "-map", "1:a",
               "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-ac", "2", "-c:a", "aac", "-b:a", "160k",
               "-movflags", "+faststart", str(parcial)])
        parcial.rename(AQUI / "video_pitch.mp4")

    (AQUI / "video_pitch.srt").write_text(
        "".join(f"{i}\n{tempo_srt(a)} --> {tempo_srt(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(legendas, 1)), encoding="utf-8")
    total = inicio
    (AQUI / "tempos.json").write_text(json.dumps(
        {"velocidade_pct": args.velocidade, "duracao_total_s": round(total, 3), "limite_s": 300, "slides": tempos},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"video_pitch.mp4: {int(total // 60)} min {total % 60:04.1f} s (limite: 5 min)")
    if total > 300:
        sys.exit("O vídeo passou de 5 minutos: aumente --velocidade ou encurte narracao.json")


if __name__ == "__main__":
    main()
