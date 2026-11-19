import numpy as np, librosa, json, sys
from scipy.signal import butter, sosfilt
src = sys.argv[1]
y, sr = librosa.load(src, sr=None, mono=True)
dur = len(y)/sr
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, tightness=400, units="time")
i = np.arange(len(beats)); A = np.vstack([i, np.ones_like(i)]).T
(T, t0), *_ = np.linalg.lstsq(A, beats, rcond=None)
res = beats - (t0 + i*T)
print(f"dur={dur:.2f}s sr={sr} tempo_scalar={float(np.atleast_1d(tempo)[0]):.2f} BPM_fit={60/T:.3f} t0={t0:.4f} T={T:.5f} resid_max={np.abs(res).max()*1000:.0f}ms resid_mean={np.abs(res).mean()*1000:.1f}ms nbeats={len(beats)}")
def band_env(lo, hi):
    sos = butter(4, [lo, hi], btype="band", fs=sr, output="sos")
    env = librosa.onset.onset_strength(y=sosfilt(sos, y), sr=sr)
    return env, librosa.times_like(env, sr=sr)
kenv, times = band_env(40, 160)
# refine grid on kick onsets: detect kick onsets and fit
on = librosa.onset.onset_detect(onset_envelope=kenv, sr=sr, units="time", backtrack=False)
def score(T_, t0_):
    n = np.round((on - t0_)/T_); err = on - (t0_ + n*T_)
    grid = t0_ + np.arange(0, int((dur - t0_)/T_))*T_
    d = np.array([np.min(np.abs(on - g)) for g in grid])
    return dict(match=float((d < 0.035).mean()), mean_abs_ms=float(d[d<0.035].mean()*1000) if (d<0.035).any() else None)
cands = {}
for name, f in (("0.5x", 2.0), ("1x", 1.0), ("2x", 0.5)):
    cands[name] = score(T*f, t0)
print("grid candidates:", json.dumps(cands))
# refit using kick onsets near 1x grid for precision
n = np.round((on - t0)/T); err = on - (t0 + n*T); m = np.abs(err) < 0.04
A2 = np.vstack([n[m], np.ones(m.sum())]).T
(T2, t02), *_ = np.linalg.lstsq(A2, on[m], rcond=None)
r2 = on[m] - (t02 + n[m]*T2)
print(f"kick refit: BPM={60/T2:.3f} t0={t02:.4f} T={T2:.5f} n={m.sum()} resid_max={np.abs(r2).max()*1000:.0f}ms mean={np.abs(r2).mean()*1000:.1f}ms drift_ms={np.polyfit(on[m], r2, 1)[0]*dur*1000:.2f}")
# rms per bar (4 beats)
rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]; rt = librosa.times_like(rms, sr=sr, hop_length=512)
bars = []
nb = int((dur - t02)/T2)
for b in range(0, nb, 4):
    a, e = t02 + b*T2, t02 + (b+4)*T2
    seg = rms[(rt>=a)&(rt<e)]
    kk = kenv[(times>=a)&(times<e)]
    bars.append((b, round(a,2), round(float(seg.mean()) if len(seg) else 0,4), round(float(kk.max()) if len(kk) else 0,1)))
print("bar: beat, t, rms, kickmax")
for b in bars[:80]: print(b)
json.dump(dict(src=src, dur=dur, bpm=60/T2, t0=t02, T=T2, beats=[float(t02+k*T2) for k in range(nb)], bars=bars, candidates=cands, beat_track=dict(bpm=60/T, t0=float(t0), T=float(T), resid_max_ms=float(np.abs(res).max()*1000))), open("beat_data.json","w"), indent=1)
