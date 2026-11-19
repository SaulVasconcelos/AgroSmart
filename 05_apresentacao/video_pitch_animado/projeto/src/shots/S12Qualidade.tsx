// Cena 12 — Qualidade e segurança. Cartão `odometer-digit-roll` do video-shotcraft
// (demos/data/odometer-digit-roll/OdometerDigitRoll.tsx): cada dígito é um rolo de 0 a 9 que gira
// a 0,85 linha por quadro, desacelera em 16 quadros a partir de 20 + i·7, passa meia linha do
// ponto e volta em 6, com duas cópias fantasma enquanto gira; quando todos travam, o número
// escurece e cresce 3,5% por 8 quadros. Mantidos esses valores. Adaptado: o número é o total
// real de testes da entrega (45 em Python + 18 de interface); as outras duas medidas e a nota
// entram depois, no ritmo da fala. Fonte: 03_evidencias/devsecops_ci/LEIA_ME.md.
import React from 'react';
import { Easing, interpolate, interpolateColors, useCurrentFrame } from 'remotion';
import { COR, FONTE } from '../tema';

const ROW = 300, DW = 190, FS = 290, SPIN = 0.85;
const DIGITS = [6, 3];
const cl = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
const TRAVA = 20 + (DIGITS.length - 1) * 7 + 22; // quadro em que o último dígito trava

const posAt = (f: number, i: number): number => {
  const d = DIGITS[i];
  const s = 20 + i * 7;
  const p0 = SPIN * s;
  const T = Math.ceil((p0 + 6 - d) / 10) * 10 + d;
  if (f < s) return SPIN * Math.max(f, 0);
  if (f < s + 16) return interpolate(f, [s, s + 16], [p0, T + 0.5], { ...cl, easing: Easing.out(Easing.cubic) });
  if (f < s + 22) return interpolate(f, [s + 16, s + 22], [T + 0.5, T], { ...cl, easing: Easing.out(Easing.cubic) });
  return T;
};

const Strip: React.FC<{ pos: number; color: string; opacity?: number; dy?: number }> = ({ pos, color, opacity = 1, dy = 0 }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: DW, transform: `translateY(${-(pos % 10) * ROW + dy}px)`, opacity }}>
    {Array.from({ length: 20 }).map((_, k) => (
      <div key={k} style={{ width: DW, height: ROW, lineHeight: `${ROW}px`, textAlign: 'center', fontSize: FS, fontWeight: 700, fontVariantNumeric: 'tabular-nums', color }}>{k % 10}</div>
    ))}
  </div>
);

const DigitReel: React.FC<{ frame: number; i: number; color: string }> = ({ frame, i, color }) => {
  const pos = posAt(frame, i);
  const speed = Math.abs(pos - posAt(frame - 1, i));
  const gate = interpolate(speed, [0.06, 0.5], [0, 1], cl);
  return (
    <div style={{ position: 'relative', width: DW, height: ROW, overflow: 'hidden' }}>
      {gate > 0.001 && (<><Strip pos={pos} color={color} opacity={0.25 * gate} dy={ROW * 0.5} /><Strip pos={pos} color={color} opacity={0.12 * gate} dy={-ROW * 0.5} /></>)}
      <Strip pos={pos} color={color} />
    </div>
  );
};

const Linha: React.FC<{ numero: string; texto: string; em: number; frame: number }> = ({ numero, texto, em, frame }) => {
  const t = interpolate(frame, [em, em + 14], [0, 1], { ...cl, easing: Easing.bezier(0.2, 0.75, 0.3, 1) });
  return (
    <div style={{ flex: 1, opacity: t, transform: `translateY(${(1 - t) * 26}px)`, background: COR.branco, border: `2px solid ${COR.linha}`, borderRadius: 14, padding: '26px 34px', boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 28, boxShadow: '0 10px 30px rgba(18,41,35,0.07)' }}>
      <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 84, lineHeight: 1, letterSpacing: '-0.03em', color: COR.verde, whiteSpace: 'nowrap' }}>{numero}</div>
      <div style={{ fontFamily: FONTE.ui, fontWeight: 600, fontSize: 31, lineHeight: 1.22, color: COR.tinta }}>{texto}</div>
    </div>
  );
};

export const S12Qualidade: React.FC<{ quadros: number; linhas: [number, number]; nota: number }> = ({ quadros, linhas, nota }) => {
  const frame = useCurrentFrame();
  const inkNow = interpolateColors(frame, [TRAVA, TRAVA + 4, TRAVA + 8], [COR.verde, COR.florestaFunda, COR.verde]);
  const pulseScale = interpolate(frame, [TRAVA, TRAVA + 4, TRAVA + 8], [1, 1.035, 1], { ...cl, easing: Easing.inOut(Easing.quad) });
  const labelOp = interpolate(frame, [TRAVA + 3, TRAVA + 21], [0, 1], { ...cl, easing: Easing.out(Easing.quad) });
  const notaOp = interpolate(frame, [nota, nota + 16], [0, 1], cl);
  const entra = 1, sai = 1; // cortes secos
  return (
    <div style={{ width: 1920, height: 1080, background: COR.tela, position: 'relative', overflow: 'hidden', opacity: entra * sai }}>
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 20, background: COR.floresta }} />
      <div style={{ position: 'absolute', left: 150, top: 120, fontFamily: FONTE.ui, fontWeight: 600, fontSize: 30, letterSpacing: '0.14em', textTransform: 'uppercase', color: COR.suave }}>Qualidade e segurança · pipeline DevSecOps</div>
      <div style={{ position: 'absolute', left: 150, top: 200, display: 'flex', alignItems: 'center', gap: 56 }}>
        <div style={{ display: 'flex', fontFamily: FONTE.titulo, transform: `scale(${pulseScale})`, transformOrigin: '190px 150px' }}>
          <DigitReel frame={frame} i={0} color={inkNow} />
          <DigitReel frame={frame} i={1} color={inkNow} />
        </div>
        <div style={{ opacity: labelOp, transform: `translateX(${(1 - labelOp) * 24}px)` }}>
          <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 84, lineHeight: 1.04, letterSpacing: '-0.03em', color: COR.tinta }}>testes automatizados<br />aprovados</div>
          <div style={{ fontFamily: FONTE.ui, fontWeight: 500, fontSize: 30, color: COR.suave, marginTop: 18 }}>45 em Python + 18 de interface</div>
        </div>
      </div>
      <div style={{ position: 'absolute', left: 150, right: 130, top: 590, display: 'flex', gap: 36 }}>
        <Linha numero="22 de 22" texto="verificações no container" em={linhas[0]} frame={frame} />
        <Linha numero="0" texto="vulnerabilidades críticas ou altas com correção disponível" em={linhas[1]} frame={frame} />
      </div>
      <div style={{ position: 'absolute', left: 150, right: 130, top: 840, opacity: notaOp, display: 'flex', alignItems: 'center', gap: 18 }}>
        <div style={{ width: 6, height: 44, borderRadius: 3, background: COR.ambar }} />
        <div style={{ fontFamily: FONTE.ui, fontWeight: 500, fontSize: 30, color: COR.suave }}>47 altas sem correção publicada seguem no relatório</div>
      </div>
    </div>
  );
};
