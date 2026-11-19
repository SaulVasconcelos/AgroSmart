// Cena 8 — Explicável. Cartão `scanline-annotate-focus` do video-shotcraft
// (demos/effects/scanline-annotate-focus/ScanlineAnnotateFocus.tsx): uma linha de luz desce em
// velocidade constante; cada região só é marcada depois que a linha passa por ela; a moldura
// fecha de 1,75x para 1x com ultrapassagem; o rótulo vem logo depois; o contador acompanha.
// Mantidos do cartão: linha sem aceleração, moldura 1,75→1 (outBack), cantos em colchete,
// clarão de foco de 0,07, rótulo atrasado em relação à moldura, contador calculado em tempo real.
// Adaptado: a "página" é a captura real do cartão da ocorrência R2; as três regiões são as do
// roteiro; a velocidade da linha foi calculada para as molduras caírem junto das palavras da
// fala ("a regra", "a evidência", "a orientação").
import React from 'react';
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { COR, FONTE } from '../tema';
import { Palco } from '../lib/ui';
import { E, lerp } from '../lib/Motion';
import layout from '../layout.json';
import registro from '../../public/tex/registro.json';

const cl = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
const L = layout.cartao_depois_r2;
const C = L.cartao;
const ESC = 1.6;
const VISIVEL = 930; // mesmo enquadramento da cena anterior
const CW = VISIVEL * ESC;
const CH = C.h * ESC;
const CX = (1920 - CW) / 2;
const CY = 200;
const rel = (b: { x: number; y: number; w: number; h: number }, m = 8) => ({ x: (b.x - C.x) * ESC - m, y: (b.y - C.y) * ESC - m, w: b.w * ESC + 2 * m, h: b.h * ESC + 2 * m });
const d = registro.depois;
const praga = String(d.praga_detectada).toLowerCase();
const pct = String(d.percentual_folhas_doentes).replace('.0', '');

export const S08Porque: React.FC<{ quadros: number; gatilhos: [number, number, number] }> = ({ quadros, gatilhos }) => {
  const f = useCurrentFrame();
  const ALVOS = [
    { ...rel(L.linha_regra), titulo: 'A regra', texto: d.regra, ft: gatilhos[0] },
    { ...rel(L.evidencias), titulo: 'A evidência', texto: `${pct}% de folhas afetadas, ${praga}, ${d.dias_mesma_praga} dias`, ft: gatilhos[1] },
    { ...rel({ ...L.orientacao, h: L.orientacao.h + 28 }), titulo: 'A orientação', texto: String(d.acao).toLowerCase(), ft: gatilhos[2] },
  ];
  // linha em velocidade constante: passa pela base da linha da regra em gatilhos[0] e pelo topo
  // das evidências em gatilhos[1]; daí sai a velocidade e o início
  const yA = ALVOS[0].y + ALVOS[0].h;
  const yB = ALVOS[1].y + 40;
  const vel = (yB - yA) / (gatilhos[1] - gatilhos[0]);
  const ini = gatilhos[0] - (yA + 30) / vel;
  const fim = ini + (CH + 60) / vel;
  const ly = -30 + (f - ini) * vel;
  const lineOpacity = interpolate(f, [ini - 3, ini + 3], [0, 1], cl) * interpolate(f, [fim - 4, fim + 4], [1, 0], cl);
  const fired = ALVOS.filter((a) => f >= a.ft).length;
  const entra = 1; // o cartão já está no lugar: é o mesmo da cena 7
  const sai = 1;
  const titulo = interpolate(f, [0, 10], [0, 1], { ...cl, easing: Easing.bezier(0.2, 0.75, 0.3, 1) });
  const DUR = 138; // os tempos relativos do cartão foram medidos em 138 quadros
  const B = `3px solid ${COR.verde}`;
  const CANTOS: React.CSSProperties[] = [
    { left: 0, top: 0, borderTop: B, borderLeft: B }, { right: 0, top: 0, borderTop: B, borderRight: B },
    { left: 0, bottom: 0, borderBottom: B, borderLeft: B }, { right: 0, bottom: 0, borderBottom: B, borderRight: B },
  ];
  return (
    <Palco brilho={0.7}>
      <AbsoluteFill style={{ opacity: entra * sai }}>
        <div style={{ position: 'absolute', left: CX, top: 78, right: CX, display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', opacity: titulo, transform: `translateY(${(1 - titulo) * 14}px)` }}>
          <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 54, letterSpacing: '-0.02em', color: COR.branco }}>Toda prioridade mostra o <span style={{ color: COR.ambar }}>porquê</span></div>
          <div style={{ fontFamily: FONTE.mono, fontWeight: 500, fontSize: 24, letterSpacing: '0.12em', color: fired === 3 ? COR.ambar : COR.menta }}>
            {fired === 3 ? 'EXPLICAÇÃO · COMPLETA' : `EXPLICAÇÃO · ${fired}/3`}
          </div>
        </div>
        <div style={{ position: 'absolute', left: CX, top: CY + (1 - entra) * 30, width: CW, height: CH, borderRadius: 14, boxShadow: '0 30px 90px rgba(0,0,0,0.38)', background: '#fff' }}>
          <div style={{ position: 'absolute', inset: 0, borderRadius: 14, overflow: 'hidden' }}>
            <Img src={staticFile('tex/cartao_depois_r2.png')} style={{ position: 'absolute', left: 0, top: 0, width: C.w * ESC, height: CH }} />
          </div>
          {ALVOS.map((a, i) => {
            const t = (f - a.ft) / DUR;
            const ap = E.outCubic(Math.min(1, Math.max(0, t / 0.11)));
            const s = lerp(E.outBack(Math.min(1, Math.max(0, t / 0.13))), 1.75, 1);
            const fillO = 0.07 * Math.min(1, Math.max(0, (t - 0.04) / 0.05)) * (1 - Math.min(1, Math.max(0, (t - 0.09) / 0.13)));
            if (f < a.ft) return null;
            return (
              <div key={i} style={{ position: 'absolute', left: a.x, top: a.y, width: a.w, height: a.h, opacity: Math.min(1, ap * 1.6), transform: `scale(${s})` }}>
                {CANTOS.map((c, k) => <div key={k} style={{ position: 'absolute', width: 22, height: 22, boxSizing: 'content-box', ...c }} />)}
                <div style={{ position: 'absolute', inset: 2, background: COR.verde, opacity: fillO }} />
              </div>
            );
          })}
          {/* linha de leitura: rastro + núcleo */}
          <div style={{ position: 'absolute', left: -24, right: -24, top: 0, height: 90, transform: `translateY(${ly - 90}px)`, opacity: lineOpacity, background: 'linear-gradient(180deg, transparent, rgba(242,198,109,0.20) 60%, rgba(242,198,109,0.06) 96%, transparent)' }}>
            <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: 4, background: '#e0a030', boxShadow: '0 0 12px #f2c66d, 0 0 30px rgba(242,198,109,0.6)' }} />
          </div>
        </div>
        {/* rótulos fora do cartão, na mesma coluna de cada região */}
        <div style={{ position: 'absolute', left: CX, top: CY + CH + 26, width: CW, display: 'grid', gridTemplateColumns: '0.5fr 1.5fr 1.2fr', gap: 26 }}>
          {ALVOS.map((a, i) => {
            const la = E.outCubic(Math.min(1, Math.max(0, ((f - a.ft) / DUR - 0.05) / 0.11)));
            return (
              <div key={i} style={{ opacity: la, transform: `translateY(${lerp(la, 14, 0)}px)`, borderLeft: `4px solid ${COR.ambar}`, paddingLeft: 20 }}>
                <div style={{ fontFamily: FONTE.mono, fontWeight: 500, fontSize: 20, letterSpacing: '0.14em', textTransform: 'uppercase', color: COR.menta }}>{a.titulo}</div>
                <div style={{ fontFamily: FONTE.titulo, fontWeight: 600, fontSize: 31, lineHeight: 1.18, letterSpacing: '-0.01em', color: COR.branco, marginTop: 6 }}>{a.texto}</div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </Palco>
  );
};
