// Cenas 6 e 10 — respiro. Cartão `paper-title-card` do video-shotcraft
// (demos/typography/paper-title-card/PaperTitleCard.tsx): cada palavra é "prensada" no papel
// (atraso 4 + i·4, 9 quadros, escala 1,28→1, desfoque 7→0), uma única palavra em destaque,
// traço que cresce de 16 a 34 e saída em 8 quadros. Adaptado: letra e cores do AgroSmart, sem a
// linha de números do exemplo.
import React from 'react';
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from 'remotion';
import { COR, FONTE } from '../tema';

const cl = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;

export const CartaoTexto: React.FC<{ palavras: { texto: string; destaque?: boolean }[]; quadros: number }> = ({ palavras, quadros }) => {
  const frame = useCurrentFrame();
  const fadeOut = interpolate(frame, [quadros - 8, quadros], [1, 0], cl);
  const fadeIn = interpolate(frame, [0, 4], [0, 1], cl);
  const underline = interpolate(frame, [16, 34], [0, 1], { ...cl, easing: Easing.bezier(0.3, 0, 0.2, 1) });
  return (
    <AbsoluteFill style={{ backgroundColor: COR.tela }}>
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', opacity: fadeOut * fadeIn,
        backgroundImage: 'radial-gradient(1100px 750px at 50% 42%, rgba(255,255,255,0.95), transparent 65%)' }}>
        <div style={{ textAlign: 'center', maxWidth: 1500 }}>
          <div style={{ fontFamily: FONTE.titulo, fontSize: 124, fontWeight: 700, lineHeight: 1.14, color: COR.tinta, letterSpacing: '-0.03em', display: 'flex', flexWrap: 'wrap', justifyContent: 'center', columnGap: '0.26em' }}>
            {palavras.map((w, i) => {
              const delay = 4 + i * 4;
              const t = interpolate(frame, [delay, delay + 9], [0, 1], { ...cl, easing: Easing.bezier(0.2, 0.75, 0.3, 1) });
              return (
                <span key={i} style={{ opacity: t, transform: `scale(${1.28 - 0.28 * t})`, filter: `blur(${(1 - t) * 7}px)`, display: 'inline-block', color: w.destaque ? COR.verde : undefined }}>{w.texto}</span>
              );
            })}
          </div>
          <div style={{ height: 6, width: 220, margin: '38px auto 0', borderRadius: 3, background: COR.ambar, transform: `scaleX(${underline})` }} />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
