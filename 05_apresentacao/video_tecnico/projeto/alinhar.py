"""Acha as fronteiras entre parágrafos na narração do Gemini por alinhamento (DTW) com uma leitura de referência
feita parágrafo a parágrafo com RHVoice (fronteiras conhecidas). Depois ajusta cada fronteira à pausa mais próxima."""
import json, subprocess, tempfile, os
import numpy as np, librosa
import sys
SR = 16000; HOP = 320
n = json.load(open("narracao.json"))
falas = [(c["id"], k, f) for c in n["cenas"] for k, f in enumerate(c["falas"])]
partes = {"parte1.wav": [f for f in falas if f[0] in ("c1","c2","c3","c4")], "parte2.wav": [f for f in falas if f[0] not in ("c1","c2","c3","c4")]}
def feats(y):
    m = librosa.feature.mfcc(y=y, sr=SR, n_mfcc=13, hop_length=HOP, n_fft=640)[1:]
    m = (m - m.mean(axis=1, keepdims=True)) / (m.std(axis=1, keepdims=True) + 1e-6)
    return m
def pausas(y, sr, minimo=0.2):
    hop = int(sr*0.01); env = np.array([np.sqrt(np.mean(y[i:i+hop]**2)+1e-12) for i in range(0,len(y)-hop,hop)])
    sil = 20*np.log10(env+1e-9) < -45; tr=[]; i=0
    while i < len(sil):
        if sil[i]:
            j=i
            while j<len(sil) and sil[j]: j+=1
            if (j-i)*0.01>=minimo: tr.append((i*0.01,j*0.01))
            i=j
        else: i+=1
    return tr
saida = []
for arq, fs in [(a, partes[a]) for a in sys.argv[1:]]:
    ref = []; lim = [0.0]
    for cid, k, txt in fs:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as t: t.write(txt)
        out = t.name + ".wav"
        subprocess.run(["RHVoice-test","-p","Leticia-F123","-R",str(SR),"-i",t.name,"-o",out], check=True)
        y, _ = librosa.load(out, sr=SR); y, _ = librosa.effects.trim(y, top_db=40)
        ref.append(y); lim.append(lim[-1] + len(y)/SR); os.unlink(t.name); os.unlink(out)
    yr = np.concatenate(ref); yg, _ = librosa.load(arq, sr=SR)
    D, wp = librosa.sequence.dtw(X=feats(yr), Y=feats(yg), metric="euclidean", subseq=False)
    wp = wp[::-1]; tr_ref = wp[:,0]*HOP/SR; tr_gem = wp[:,1]*HOP/SR
    ps = pausas(yg, SR); total = len(yg)/SR
    ini = ps[0][1] if ps[0][0] < 0.05 else 0.0; fim = ps[-1][0] if ps[-1][1] > total-0.05 else total
    cortes = []
    for b in lim[1:-1]:
        idx = np.where((tr_ref >= b-0.02) & (tr_ref <= b+0.02))[0]
        tg = float(np.median(tr_gem[idx]))
        cand = min(ps[1:-1], key=lambda p: 0 if p[0]-0.1 <= tg <= p[1]+0.1 else min(abs(tg-p[0]), abs(tg-p[1])))
        dist = 0 if cand[0]-0.1 <= tg <= cand[1]+0.1 else min(abs(tg-cand[0]), abs(tg-cand[1]))
        cortes.append((cand, tg, dist))
    edges = [ini] + [c for (p, tg, d) in cortes for c in p] + [fim]
    print(f"{arq}: gemini {total:.1f}s, referência {lim[-1]:.1f}s")
    for k, (cid, kk, txt) in enumerate(fs):
        a, b = edges[2*k], edges[2*k+1]; pal = len(txt.split())
        extra = f" | fronteira alinhada em {cortes[k][1]:.2f}s, pausa escolhida {cortes[k][0][0]:.2f}–{cortes[k][0][1]:.2f} (dist {cortes[k][2]:.2f}s)" if k < len(cortes) else ""
        print(f"  {cid}.{kk} {a:7.2f}–{b:7.2f} dur {b-a:6.2f}s {pal/(b-a):.2f} pal/s  ref {lim[k+1]-lim[k]:5.1f}s razão {(b-a)/(lim[k+1]-lim[k]):.2f}{extra}")
        saida.append({"cena": cid, "fala": kk, "arquivo": arq, "ini": round(a,3), "fim": round(b,3), "texto": txt})
json.dump(saida, open("tempos_" + sys.argv[1] + ".json","w"), ensure_ascii=False, indent=1)
