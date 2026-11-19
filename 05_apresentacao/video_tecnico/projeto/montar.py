"""Monta o vídeo final técnico: cartão de abertura + 8 cenas gravadas + narração nos instantes da agenda + legendas."""
import json, re, subprocess, wave
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright

AQUI = Path(__file__).resolve().parent
OUT = AQUI / "out"; OUT.mkdir(exist_ok=True)
REG = json.loads((AQUI / "registro_gravacao.json").read_text(encoding="utf-8"))
TEMPOS = json.loads((AQUI / "tempos_falas.json").read_text(encoding="utf-8"))
FRASES = json.loads((AQUI / "frases_parte1.wav.json").read_text(encoding="utf-8")) + json.loads((AQUI / "frases_parte2.wav.json").read_text(encoding="utf-8"))
CENAS = ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"]
ABERTURA_S = 3.5
SR = 48000

# 1) cartão de abertura (página local desenhada no Chromium)
html = """<!DOCTYPE html><html lang="pt-BR"><meta charset="utf-8"><style>
body{margin:0;width:1920px;height:1080px;background:#0c3028;color:#e6efe9;font-family:Inter,'DejaVu Sans',sans-serif;display:flex;flex-direction:column;justify-content:center;padding:0 150px;box-sizing:border-box}
hr{width:120px;height:6px;border:0;background:#f2c66d;margin:0 0 34px} .e{font-size:26px;letter-spacing:4px;color:#f2c66d;font-weight:600}
h1{font-size:112px;margin:26px 0 12px;font-weight:700;letter-spacing:-2px} .s{font-size:40px;color:#c1d9cb} .n{font-size:24px;color:#9fb8aa;margin-top:90px;line-height:1.5;max-width:1300px}
</style><hr><div class="e">FASE 7 · VÍDEO FINAL TÉCNICO</div><h1>AgroSmart</h1><div class="s">Demonstração da plataforma, fluxo de dados e análise do processo</div>
<div class="n">Gravação real da plataforma em execução, com navegador e terminal. Dados de sensores e de campo simulados.<br>Narração com voz sintética (Gemini). Novembro de 2026.</div></html>"""
with sync_playwright() as pw:
    b = pw.chromium.launch(); p = b.new_page(viewport={"width": 1920, "height": 1080}); p.set_content(html); p.wait_for_timeout(400)
    p.screenshot(path=str(OUT / "abertura.png")); b.close()
subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-i", str(OUT / "abertura.png"), "-t", str(ABERTURA_S),
                "-vf", f"fade=t=out:st={ABERTURA_S - 0.4}:d=0.4,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "17", str(OUT / "c0.mp4")], check=True)

# 2) imagem: concatena (mesmo codec e formato em todos os trechos)
partes = [OUT / "c0.mp4"] + [AQUI / "cenas" / f"{c}.mp4" for c in CENAS]
def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)
durs = [dur(p) for p in partes]
(OUT / "lista.txt").write_text("".join(f"file '{p}'\n" for p in partes))
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(OUT / "lista.txt"), "-c", "copy", str(OUT / "imagem.mp4")], check=True)
inicio = {}; t = durs[0]
for c, d in zip(CENAS, durs[1:]): inicio[c] = t; t += d
total = t

# 3) narração: cada fala entra no instante previsto da sua cena
def ler(arq):
    w = wave.open(str(AQUI / arq)); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768; return x, w.getframerate()
audios = {a: ler(a) for a in ("parte1.wav", "parte2.wav")}
mix = np.zeros(int(total * SR) + SR, dtype=np.float32); agenda = []
for f in TEMPOS:
    x, sr = audios[f["arquivo"]]; a = max(0, int((f["ini"] - 0.06) * sr)); b = min(len(x), int((f["fim"] + 0.10) * sr)); seg = x[a:b].copy()
    n = int(0.03 * sr); seg[:n] *= np.linspace(0, 1, n); seg[-n:] *= np.linspace(1, 0, n)
    seg = np.interp(np.arange(0, len(seg), sr / SR), np.arange(len(seg)), seg).astype(np.float32)
    t0 = inicio[f["cena"]] + REG["falas"][f["cena"]][str(f["fala"])] - 0.06
    i = int(t0 * SR); mix[i:i + len(seg)] += seg
    agenda.append({"cena": f["cena"], "fala": f["fala"], "inicio_s": round(t0 + 0.06, 3), "fim_s": round(t0 + 0.06 + f["fim"] - f["ini"], 3), "texto": f["texto"]})
w = wave.open(str(OUT / "narracao_bruta.wav"), "w"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix[:int(total * SR)], -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(OUT / "narracao_bruta.wav"), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.84", "-ar", "48000", "-ac", "2", str(OUT / "narracao.wav")], check=True)

# 4) legendas: uma por frase (frases longas divididas na vírgula mais central)
def hhmm(s): h = int(s // 3600); m = int(s % 3600 // 60); return f"{h:02d}:{m:02d}:{s % 60:06.3f}".replace(".", ",")
cues = []
for ag in agenda:
    fr = [x for x in FRASES if x["cena"] == ag["cena"] and x["fala"] == ag["fala"]]
    base = next(x["ini"] for x in TEMPOS if x["cena"] == ag["cena"] and x["fala"] == ag["fala"])
    for k, x in enumerate(fr):
        a = ag["inicio_s"] + x["ini"] - base; b = (ag["inicio_s"] + fr[k + 1]["ini"] - base - 0.08) if k + 1 < len(fr) else ag["fim_s"]
        txt = x["frase"]
        if len(txt) > 105 and "," in txt:
            pos = min((m.start() for m in re.finditer(r"[,;:] ", txt)), key=lambda i: abs(i - len(txt) / 2)); corte = a + (b - a) * (pos + 1) / len(txt)
            cues += [(a, corte - 0.05, txt[:pos + 1]), (corte, b, txt[pos + 2:])]
        else: cues.append((a, b, txt))
(OUT / "legendas.srt").write_text("".join(f"{i}\n{hhmm(a)} --> {hhmm(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(cues, 1)), encoding="utf-8")

# 5) arquivo final
final = OUT / "video_tecnico_agrosmart.mp4"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(OUT / "imagem.mp4"), "-i", str(OUT / "narracao.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", "-metadata", "title=AgroSmart — vídeo final técnico (Fase 7)",
                "-metadata", "comment=Gravação real da plataforma. Narração com voz sintética (Gemini). Dados simulados.", str(final)], check=True)
json.dump({"total_s": round(total, 2), "inicio_cenas_s": {k: round(v, 2) for k, v in inicio.items()}, "falas": agenda, "legendas": len(cues)},
          open(OUT / "agenda_final.json", "w"), ensure_ascii=False, indent=1)
print("total", round(total, 2), "s =", f"{int(total // 60)}:{total % 60:04.1f}", "| cenas:", {k: round(v, 1) for k, v in inicio.items()}, "| legendas:", len(cues))
