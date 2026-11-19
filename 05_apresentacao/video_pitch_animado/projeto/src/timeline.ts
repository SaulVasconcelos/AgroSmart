// Linha do tempo única do filme. Tudo é escrito em batidas da trilha (bgm-tech-house, 124 BPM):
// as fronteiras de cena caem em tempos fortes e os quadros saem daqui, nunca de números soltos.
// O mesmo timeline.json é lido pelo script de som (scripts/montar_som.py).
import dados from './timeline.json';

export const FPS = dados.fps;
export const W = dados.largura;
export const H = dados.altura;
export const BATIDA_S = dados.batida_s;

export const batidaT = (n: number) => n * BATIDA_S;                    // batida -> segundos
export const batidaF = (n: number) => Math.round(batidaT(n) * FPS);    // batida -> quadro
export const seg = (s: number) => Math.round(s * FPS);                 // segundos -> quadros

export type CenaId = 's01' | 's02' | 's03' | 's04' | 's05' | 's06' | 's07' | 's08' | 's09' | 's10' | 's11' | 's12' | 's13' | 's14' | 's15';

export const CENAS = dados.cenas.map((c) => ({
  ...c,
  id: c.id as CenaId,
  de: batidaF(c.b0),
  ate: batidaF(c.b1),
  quadros: batidaF(c.b1) - batidaF(c.b0),
  falaEm: seg(c.fala_em_s), // quadro, dentro da cena, em que a narração da cena começa
}));

export const cena = (id: CenaId) => CENAS.find((c) => c.id === id)!;
export const TOTAL = CENAS[CENAS.length - 1].ate;
