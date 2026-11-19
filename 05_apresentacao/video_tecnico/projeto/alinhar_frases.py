"""Instantes de início de cada frase na narração do Gemini (DTW contra leitura de referência frase a frase)."""
import json, re, subprocess, sys, tempfile, os
import numpy as np, librosa
SR = 16000; HOP = 320
arq = sys.argv[1]
tempos = [t for t in json.load(open("tempos_falas.json")) if t["arquivo"] == arq]
def feats(y):
    m = librosa.feature.mfcc(y=y, sr=SR, n_mfcc=13, hop_length=HOP, n_fft=640)[1:]
    return (m - m.mean(axis=1, keepdims=True)) / (m.std(axis=1, keepdims=True) + 1e-6)
def tts(txt):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as t: t.write(txt)
    out = t.name + ".wav"; subprocess.run(["RHVoice-test","-p","Leticia-F123","-R",str(SR),"-i",t.name,"-o",out], check=True)
    y, _ = librosa.load(out, sr=SR); y, _ = librosa.effects.trim(y, top_db=40); os.unlink(t.name); os.unlink(out); return y
yg, _ = librosa.load(arq, sr=SR); res = []
for t in tempos:   # alinha parágrafo a parágrafo (fronteiras do parágrafo já conhecidas)
    frases = [f.strip() for f in re.split(r"(?<=[.!?])\s+", t["texto"]) if f.strip()]
    refs = [tts(f) for f in frases]; lim = np.cumsum([0] + [len(r) / SR for r in refs])
    seg = yg[int(t["ini"] * SR):int(t["fim"] * SR)]
    D, wp = librosa.sequence.dtw(X=feats(np.concatenate(refs)), Y=feats(seg)); wp = wp[::-1]
    tr, tg = wp[:, 0] * HOP / SR, wp[:, 1] * HOP / SR
    ini = [t["ini"]] + [float(t["ini"] + np.median(tg[(tr >= b - 0.03) & (tr <= b + 0.03)])) for b in lim[1:-1]]
    for f, a in zip(frases, ini): res.append({"cena": t["cena"], "fala": t["fala"], "ini": round(a, 2), "frase": f})
json.dump(res, open(f"frases_{arq}.json", "w"), ensure_ascii=False, indent=1)
for r in res: print(r["cena"], r["fala"], f'{r["ini"]:7.2f}', r["frase"][:70])
