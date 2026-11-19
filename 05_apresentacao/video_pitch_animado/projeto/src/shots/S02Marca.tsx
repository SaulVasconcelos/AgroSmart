// Cena 2 — A marca. Cartão `letterspace-materialize` do video-shotcraft
// (demos/opening/letterspace-materialize/LetterspaceMaterialize.tsx): todas as letras começam e
// terminam de se desenhar no mesmo quadro (START 16, DUR 52, easeInOut, pathLength 1). Mantidos
// os tempos e a curva do cartão; trocados a palavra, as cores e o fundo. As letras G, O, I e T
// foram desenhadas no mesmo esqueleto de 78x64 das letras originais.
import React from 'react';
import { Easing, interpolate, useCurrentFrame } from 'remotion';
import { COR, FONTE } from '../tema';
import { Palco } from '../lib/ui';

const GLIFOS: Record<string, string> = {
  A: 'M 7 59 L 39 5 L 71 59 M 17 41 L 61 41',
  G: 'M 64 17 C 55 3, 14 2, 12 32 C 10 62, 58 64, 66 44 L 66 33 L 42 33',
  R: 'M 12 59 L 12 5 L 44 5 C 64 5, 64 31, 44 31 L 12 31 M 42 31 L 64 59',
  O: 'M 39 5 C 9 5, 9 59, 39 59 C 69 59, 69 5, 39 5',
  M: 'M 8 59 L 8 6 L 39 38 L 70 6 L 70 59',
  N: 'M 12 59 L 12 5 L 66 59 L 66 5',
  I: 'M 13 5 L 13 59',
  T: 'M 10 5 L 68 5 M 39 5 L 39 59',
};
const LARGURA: Record<string, number> = { I: 26 };
const PALAVRA = 'AGROMONITOR';
const START = 16; // todas as letras começam juntas (cartão: sem defasagem)
const DUR = 52;   // e terminam juntas
const ESCALA = 1.3;

export const S02Marca: React.FC<{ quadros: number }> = ({ quadros }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [START, START + DUR], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const e = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
  const doneGlow = interpolate(frame, [START + DUR, START + DUR + 8], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const glowAmt = p >= 1 ? doneGlow : p > 0.7 ? (p - 0.7) / 0.3 : 0;
  // linha de apoio: entra depois que a palavra fecha, junto de "um módulo do AgroSmart" na fala
  const sub = interpolate(frame, [START + DUR + 6, START + DUR + 22], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.2, 0.75, 0.3, 1) });
  const sai = interpolate(frame, [quadros - 10, quadros], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <Palco>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', opacity: sai }}>
        <div style={{ display: 'flex', gap: 34 * ESCALA, alignItems: 'center' }}>
          {PALAVRA.split('').map((ch, i) => {
            const w = LARGURA[ch] ?? 78;
            return (
              <svg key={i} width={w * ESCALA} height={64 * ESCALA} viewBox={`0 0 ${w} 64`} style={{ overflow: 'visible', display: 'block' }}>
                {p > 0 && (
                  <path d={GLIFOS[ch]} fill="none" stroke="#f3f8f4" strokeWidth={5.5} strokeLinecap="round" strokeLinejoin="round"
                    pathLength={1} strokeDasharray={1} strokeDashoffset={1 - e}
                    style={{ filter: `drop-shadow(0 0 ${6 + glowAmt * 10}px rgba(216,240,226,${0.35 + glowAmt * 0.35}))` }} />
                )}
              </svg>
            );
          })}
        </div>
        <div style={{ marginTop: 54, height: 3, width: 150 * sub, background: COR.ambar, borderRadius: 2 }} />
        <div style={{ marginTop: 30, fontFamily: FONTE.ui, fontWeight: 500, fontSize: 42, letterSpacing: '0.02em', color: COR.menta, opacity: sub, transform: `translateY(${(1 - sub) * 16}px)` }}>
          módulo do <span style={{ fontFamily: FONTE.titulo, fontWeight: 700, color: COR.branco, letterSpacing: '-0.01em' }}>AgroSmart</span>
        </div>
      </div>
    </Palco>
  );
};
