#!/usr/bin/env python3
"""Monta o som do filme a partir de src/timeline.json e src/som.json.

Três camadas: narração (um trecho por cena, no quadro `fala_em` da cena), trilha (a partir da
batida indicada em timeline.json, abaixando sob a fala) e efeitos (cada um preso a uma ação da
imagem). Saídas, em out/: som_com_trilha.wav e som_sem_trilha.wav (48 kHz, estéreo), mais
som_relatorio.json com os tempos e os níveis medidos.

Uso:  python scripts/montar_som.py        (precisa de ffmpeg, numpy e soundfile)
"""
from __future__ import annotations

import json
import math
import re
import subprocess  # nosec B404 - chama o ffmpeg
from pathlib import Path

import numpy as np
import soundfile as sf

RAIZ = Path(__file__).resolve().parents[1]
SR = 48000
T = json.loads((RAIZ / "src/timeline.json").read_text(encoding="utf-8"))
S = json.loads((RAIZ / "src/som.json").read_text(encoding="utf-8"))
FPS, BAT = T["fps"], T["batida_s"]


def arred(x: float) -> int:
    """Mesmo arredondamento do Math.round do JavaScript."""
    return math.floor(x + 0.5)


def quadro(b: float) -> int:
    return arred(b * BAT * FPS)


CENAS = {c["id"]: {**c, "de": quadro(c["b0"]), "ate": quadro(c["b1"]), "fala_em": arred(c["fala_em_s"] * FPS)} for c in T["cenas"]}
TOTAL_S = max(c["ate"] for c in CENAS.values()) / FPS
N = int(round(TOTAL_S * SR))


_cache: dict[Path, np.ndarray] = {}


def ler(caminho: Path, inicio: float | None = None, dur: float | None = None) -> np.ndarray:
    """Decodifica o arquivo inteiro uma vez e devolve o trecho pedido.

    (Pedir o trecho ao ffmpeg com -ss antes de -i devolveu vazio para o WAV da narração depois
    de ~59 s; decodificar tudo e recortar aqui não depende de busca no arquivo.)
    """
    if caminho not in _cache:
        bruto = subprocess.run(["ffmpeg", "-v", "error", "-i", str(caminho), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],  # nosec B603 B607
                               capture_output=True, check=True).stdout
        _cache[caminho] = np.frombuffer(bruto, dtype=np.float32).reshape(-1, 2).astype(np.float64)
    som = _cache[caminho]
    i = int(round((inicio or 0.0) * SR))
    f = len(som) if dur is None else min(len(som), i + int(round(dur * SR)))
    antes = np.zeros((max(0, -i), 2))  # pedido que começa antes do início do arquivo: completa com silêncio
    i = max(0, i)
    if i >= len(som) or f <= i:
        raise SystemExit(f"Trecho vazio em {caminho.name}: {inicio}–{dur}")
    return np.vstack([antes, som[i:f]])


def lufs(x: np.ndarray) -> tuple[float, float]:
    tmp = RAIZ / "out" / "_medida.wav"
    sf.write(tmp, x, SR, subtype="FLOAT")
    saida = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(tmp), "-af", "ebur128=peak=true", "-f", "null", "-"],  # nosec B603 B607
                           capture_output=True, text=True).stderr
    tmp.unlink()
    resumo = saida[saida.rindex("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", resumo).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", resumo).group(1))


def por(dest: np.ndarray, som: np.ndarray, em_s: float, ganho: float = 1.0) -> None:
    i = int(round(em_s * SR))
    if i < 0:
        som, i = som[-i:], 0
    fim = min(len(dest), i + len(som))
    if fim > i:
        dest[i:fim] += som[: fim - i] * ganho


def rampas(som: np.ndarray, ent: float = 0.012, sai: float = 0.04) -> np.ndarray:
    som = som.copy()
    a, b = int(ent * SR), int(sai * SR)
    if a and len(som) > a:
        som[:a] *= np.linspace(0, 1, a)[:, None]
    if b and len(som) > b:
        som[-b:] *= np.linspace(1, 0, b)[:, None]
    return som


def main() -> None:
    (RAIZ / "out").mkdir(exist_ok=True)
    rel: dict = {"total_s": round(TOTAL_S, 3), "cenas": [], "efeitos": []}

    # 1) narração: um trecho por cena
    fala = np.zeros((N, 2))
    arq = RAIZ / S["narracao"]["arquivo"]
    for cid, (a, b) in S["narracao"]["trechos"].items():
        c = CENAS[cid]
        trecho = rampas(ler(arq, a - 0.03, (b - a) + 0.03 + 0.22), 0.02, 0.12)
        em = (c["de"] + c["fala_em"]) / FPS - 0.03
        por(fala, trecho, em)
        fim_fala = em + 0.03 + (b - a)
        rel["cenas"].append({"cena": cid, "cena_de_s": round(c["de"] / FPS, 3), "cena_ate_s": round(c["ate"] / FPS, 3),
                             "fala_de_s": round(em + 0.03, 3), "fala_ate_s": round(fim_fala, 3), "folga_no_fim_s": round(c["ate"] / FPS - fim_fala, 3)})
        if fim_fala > c["ate"] / FPS:
            raise SystemExit(f"A fala da cena {cid} passa do fim da cena.")
    i_fala, _ = lufs(fala)
    fala *= 10 ** ((S["fala"]["alvo_lufs"] - i_fala) / 20)

    # 2) efeitos: o quadro indicado é onde o pico do som deve cair
    def pico_de(som: np.ndarray) -> float:
        w = int(0.01 * SR)
        env = np.sqrt(np.convolve(som.mean(axis=1) ** 2, np.ones(w) / w, mode="same"))
        return float(env.argmax()) / SR

    efx = np.zeros((N, 2))
    for e in S["efeitos"]:
        c = CENAS[e["cena"]]
        q = c["de"] + (e["quadro"] if "quadro" in e else c["fala_em"] + arred(e["fala_s"] * FPS))
        som = ler(RAIZ / "public/audio/sfx" / e["arquivo"], dur=(e["duracao_quadros"] / FPS if "duracao_quadros" in e else None))
        adianta = 0.0 if e.get("alinhar") == "inicio" else pico_de(som)
        por(efx, rampas(som, 0.003, 0.06 if "duracao_quadros" in e else 0.02), q / FPS - adianta, e["volume"])
        rel["efeitos"].append({"pico_em_s": round(q / FPS, 3), "quadro": q, "cena": e["cena"], "arquivo": e["arquivo"], "volume": e["volume"],
                               "inicio_do_arquivo_em_s": round(q / FPS - adianta, 3), "acao": e["acao"]})

    # 3) trilha: começa na batida da faixa que cai no quadro 0 do filme
    tr = T["trilha"]
    inicio = tr["batida0_fonte_s"] + tr["batida_fonte_no_quadro0"] * BAT
    trilha = ler(RAIZ / "public/audio" / tr["arquivo"], inicio, TOTAL_S + 0.5)[:N]
    trilha = np.vstack([trilha, np.zeros((N - len(trilha), 2))]) if len(trilha) < N else trilha
    i_tr, _ = lufs(trilha)
    trilha *= 10 ** ((S["trilha"]["alvo_lufs"] - i_tr) / 20)
    # abaixa sob a fala: envoltória da narração com subida rápida e descida lenta
    env = np.abs(fala).max(axis=1)
    janela = int(0.02 * SR)
    env = np.convolve(env, np.ones(janela) / janela, mode="same")
    pres = np.clip((20 * np.log10(env + 1e-9) + 50) / 12, 0, 1)  # 0 abaixo de -50 dBFS, 1 acima de -38
    at, rl = math.exp(-1 / (0.05 * SR)), math.exp(-1 / (0.45 * SR))
    suave = np.empty_like(pres)
    v = 0.0
    passo = 48  # atualiza o ganho a cada 1 ms
    for i in range(0, N, passo):
        alvo = pres[i:i + passo].max()
        k = at if alvo > v else rl
        v = alvo + (v - alvo) * (k ** passo)
        suave[i:i + passo] = v
    ganho = 10 ** (-S["trilha"]["reducao_sob_fala_db"] * suave / 20)
    t = np.arange(N) / SR
    ganho *= np.clip(t / S["trilha"]["entrada_s"], 0, 1) ** 1.5
    ganho *= np.clip((TOTAL_S - 0.15 - t) / S["trilha"]["saida_s"], 0, 1) ** 1.5
    trilha *= ganho[:, None]

    # 4) mistura e nível final: ganho linear até o alvo e limitador do ffmpeg para os picos
    def finalizar(mix: np.ndarray, destino: Path) -> tuple[float, float]:
        i, _ = lufs(mix)
        mix = mix * 10 ** ((S["mestre"]["alvo_lufs"] - i) / 20)
        tmp = RAIZ / "out" / "_mix.wav"
        sf.write(tmp, mix, SR, subtype="FLOAT")
        teto = 10 ** ((S["mestre"]["teto_dbfs"] - 0.5) / 20)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af", f"alimiter=limit={teto:.4f}:attack=5:release=60:level=false",  # nosec B603 B607
                        "-ar", str(SR), "-c:a", "pcm_s16le", str(destino)], check=True)
        tmp.unlink()
        return lufs(ler(destino))

    def nivel(x: np.ndarray, t0: float, t1: float, pico: bool = False) -> float:
        tr = np.abs(x[max(0, int(t0 * SR)):int(t1 * SR)]).max(axis=1)
        v = tr.max() if pico else np.sqrt((tr ** 2).mean())
        return round(20 * math.log10(v + 1e-9), 1)

    for e in rel["efeitos"]:
        tq = e["pico_em_s"]
        e["pico_do_efeito_dbfs"] = nivel(efx, tq - 0.08, tq + 0.12, True)
        e["trilha_no_momento_db"] = nivel(trilha, tq - 0.15, tq + 0.15)
        e["fala_no_momento_db"] = nivel(fala, tq - 0.15, tq + 0.15)

    saida_fim = np.clip((TOTAL_S - t) / 0.4, 0, 1)[:, None]  # garante silêncio no último quadro
    i_com, p_com = finalizar((fala + efx + trilha) * saida_fim, RAIZ / "out/som_com_trilha.wav")
    i_sem, p_sem = finalizar((fala + efx) * saida_fim, RAIZ / "out/som_sem_trilha.wav")
    i_fala2, _ = lufs(fala)
    i_tr2, _ = lufs(trilha)
    rel["niveis"] = {"fala_lufs": i_fala2, "trilha_lufs_ja_abaixada": i_tr2, "com_trilha": {"lufs": i_com, "pico_dbfs": p_com}, "sem_trilha": {"lufs": i_sem, "pico_dbfs": p_sem}}
    rel["trilha"] = {"arquivo": tr["arquivo"], "inicio_na_faixa_s": round(inicio, 4), "bpm": tr["bpm"]}
    (RAIZ / "out/som_relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rel["niveis"], ensure_ascii=False))
    for c in rel["cenas"]:
        print(c)


if __name__ == "__main__":
    main()
