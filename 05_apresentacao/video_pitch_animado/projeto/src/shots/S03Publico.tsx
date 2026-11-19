// Cena 3 — Público-alvo. Cartão `pill-slot-cycle` do video-shotcraft
// (demos/typography/pill-slot-cycle/PillSlotCycle.tsx): a frase fica presa à esquerda e não se
// mexe; só a etiqueta troca. Mantidos do cartão: troca em 8 quadros, entrada +120 px com desfoque
// 14→4→0 (ease-out cúbico), saída −130 px com desfoque 0→10 (ease-in cúbico), espaço reservado
// invisível para a largura. Adaptado: cada etiqueta entra no quadro em que a fala a diz (em vez
// do metrônomo de 21 quadros) e a última fica parada; a frase vai em duas linhas porque não cabe
// em uma em 1920 px.
import React from 'react';
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from 'remotion';
import { COR, FONTE } from '../tema';

const cl = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
const INTRO = 12;
const SWAP = 8;

const Etiqueta: React.FC<{ texto: string; style?: React.CSSProperties }> = ({ texto, style }) => (
  <div style={{
    display: 'inline-flex', alignItems: 'center', gap: 22, padding: '18px 44px 18px 30px', borderRadius: 999,
    background: COR.branco, border: `3px solid ${COR.linha}`, boxShadow: '0 10px 30px rgba(18,41,35,0.10)',
    fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 84, letterSpacing: '-0.02em', color: COR.verde, whiteSpace: 'nowrap', ...style,
  }}>
    <span style={{ width: 26, height: 26, borderRadius: 13, background: COR.ambar, flexShrink: 0 }} />
    {texto}
  </div>
);

export const S03Publico: React.FC<{ quadros: number; entradas: number[] }> = ({ quadros, entradas }) => {
  const frame = useCurrentFrame();
  const ITENS = ['o produtor rural', 'o agrônomo', 'o gestor da operação'];
  const stemT = interpolate(frame, [0, INTRO], [0, 1], { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
  const sai = 1; // corte seco para a cena seguinte (as duas são claras)

  let idx = -1;
  for (let i = 0; i < entradas.length; i++) if (frame >= entradas[i]) idx = i;
  let slot: React.ReactNode = null;
  if (idx >= 0) {
    const beatFrame = frame - entradas[idx];
    const inT = interpolate(beatFrame, [0, SWAP], [0, 1], { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
    const inY = interpolate(inT, [0, 1], [120, 0]);
    const inBlur = interpolate(inT, [0, 0.7, 1], [14, 4, 0]);
    const outT = interpolate(beatFrame, [0, SWAP - 1], [0, 1], { extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic) });
    const outY = interpolate(outT, [0, 1], [0, -130]);
    slot = (
      <div style={{ position: 'relative', display: 'inline-block' }}>
        <Etiqueta texto={ITENS[idx]} style={{ visibility: 'hidden' }} />
        {idx > 0 && outT < 1 && (
          <div style={{ position: 'absolute', left: 0, top: 0, transform: `translateY(${outY}px)`, opacity: 1 - outT, filter: `blur(${outT * 10}px)` }}>
            <Etiqueta texto={ITENS[idx - 1]} />
          </div>
        )}
        <div style={{ position: 'absolute', left: 0, top: 0, transform: `translateY(${inY}px)`, opacity: idx === 0 ? inT : Math.min(1, inT * 1.6), filter: `blur(${inBlur}px)` }}>
          <Etiqueta texto={ITENS[idx]} />
        </div>
      </div>
    );
  }

  return (
    <AbsoluteFill style={{ background: COR.tela, opacity: sai }}>
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 20, background: COR.floresta }} />
      {/* frase presa à esquerda: não recentra quando a etiqueta muda de largura */}
      <div style={{ position: 'absolute', left: 190, top: 330, opacity: stemT, transform: `translateY(${(1 - stemT) * 50}px)` }}>
        <div style={{ fontFamily: FONTE.ui, fontWeight: 600, fontSize: 30, letterSpacing: '0.14em', textTransform: 'uppercase', color: COR.suave, marginBottom: 26 }}>Público-alvo</div>
        <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 108, lineHeight: 1.05, letterSpacing: '-0.03em', color: COR.tinta, whiteSpace: 'nowrap' }}>Para quem decide no campo:</div>
      </div>
      <div style={{ position: 'absolute', left: 190, top: 560 }}>{slot}</div>
    </AbsoluteFill>
  );
};
