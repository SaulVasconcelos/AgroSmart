// Cena 4 — A solução. Cartão `crane-rise-reveal` do video-shotcraft
// (demos/opening/crane-rise-reveal/CraneRiseReveal.tsx): começa colado em um indicador e sobe
// revelando a página inteira. Mantidos do cartão: 20 quadros parado, 100 de subida, escala 3,2→1,
// um só progresso com Easing.out(quad) para escala e ponto de mira, pulso escuro (0→0,22→0 em
// 22 quadros) quando cada bloco entra no quadro, e parada total depois. Adaptado: a página é a
// captura real da Visão Geral; o plano fechado usa o recorte em 4x dos indicadores.
import React from 'react';
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { COR } from '../tema';
import { Ambar, Legenda } from '../lib/ui';
import layout from '../layout.json';

const HOLD = 20;
const MOVE_END = 120;
const ease = Easing.out(Easing.quad);
const L = layout.visao_geral;
const K = L.kpi_leituras;
const F0 = { x: K.x + K.w * 0.42, y: K.y + K.h / 2 }; // mira inicial: o indicador "Leituras no período"
const F1 = { x: 960, y: 540 };
const S0 = 3.2;

const camAt = (frame: number) => {
  const p = Math.min(1, Math.max(0, (frame - HOLD) / (MOVE_END - HOLD)));
  const e = ease(p);
  const s = S0 + (1 - S0) * e;
  const fx = F0.x + (F1.x - F0.x) * e;
  const fy = F0.y + (F1.y - F0.y) * e;
  return { s, tx: 960 - fx * s, ty: 540 - fy * s, visBottom: fy + 540 / s };
};

const BLOCOS = [L.painel0, L.painel1, L.painel2, L.painel3];
// quadro em que a borda de baixo do quadro passa pelo topo de cada bloco (resolvido quadro a quadro)
const gatilhos = BLOCOS.map((b) => {
  for (let f = HOLD; f <= MOVE_END; f++) if (camAt(f).visBottom >= b.y + 24) return f;
  return MOVE_END;
});

export const S04VisaoGeral: React.FC<{ quadros: number }> = ({ quadros }) => {
  const frame = useCurrentFrame();
  const { s, tx, ty } = camAt(frame);
  const anel = interpolate(frame, [MOVE_END + 6, MOVE_END + 20], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    * interpolate(frame, [quadros - 10, quadros - 2], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: COR.tela, overflow: 'hidden' }}>
      <div style={{ position: 'absolute', width: 1920, height: 1080, transformOrigin: '0 0', transform: `translate(${tx}px, ${ty}px) scale(${s})` }}>
        <Img src={staticFile('tex/visao_geral.png')} style={{ position: 'absolute', width: 1920, height: 1080 }} />
        <Img src={staticFile('tex/kpis_4x.png')} style={{ position: 'absolute', left: L.kpis.x, top: L.kpis.y, width: L.kpis.w, height: L.kpis.h }} />
        {gatilhos.map((t, i) => {
          const op = interpolate(frame, [t, t + 4, t + 22], [0, 0.22, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          if (op <= 0.001) return null;
          const b = BLOCOS[i];
          return <div key={i} style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, borderRadius: 10, background: COR.tinta, opacity: op }} />;
        })}
        {/* depois de parar: contorno no painel de prioridades, que é o assunto da fala */}
        <div style={{ position: 'absolute', left: L.prioridades.x - 4, top: L.prioridades.y - 4, width: L.prioridades.w + 8, height: L.prioridades.h + 8, borderRadius: 14, border: `3px solid ${COR.ambarEscuro}`, opacity: anel * 0.9, boxShadow: `0 0 0 6px rgba(242,198,109,${0.22 * anel})` }} />
      </div>
      <Legenda de={MOVE_END - 14} ate={quadros - 4} texto={<>Sensores + observações de campo = <Ambar>prioridades por talhão</Ambar></>} />
    </AbsoluteFill>
  );
};
