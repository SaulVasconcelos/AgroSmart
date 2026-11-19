// Cena 9 — Rastreável. Cartão `timeline-travel` do video-shotcraft
// (demos/data/timeline-travel/TimelineTravel.tsx): a câmera corre por uma régua, cada marca
// levanta um cartão quando a câmera chega, e ela freia de uma vez na última. Mantidos do cartão:
// a curva de velocidade [0, 0,15, 0,88, 1] → [0, 0,055, 0,9, 1], o cartão que levanta 6 quadros
// antes de a câmera chegar (mola com amortecimento 11 e rigidez 160), as marcas menores na
// régua, a freada com aproximação de 1x para 1,28x em 10 quadros e a parada total depois.
// Adaptado: sete marcas em vez de quatro — as etapas principais de uma execução no event log
// (04_processos/ANALISE_PROCESSO.md, seção 3) — e o percurso dura o tempo da fala.
import React from 'react';
import { Easing, interpolate, spring, useCurrentFrame } from 'remotion';
import { COR, FONTE } from '../tema';

const W = 1920;
const AXIS_Y = 730;
const GAP = 980;
const ETAPAS = ['Entrada recebida', 'Validar dados', 'Persistir Raw', 'Publicar Trusted', 'Aplicar regras', 'Publicar Refined', 'Execução concluída'];
// rótulo de cada cartão: descreve a etapa, sem numerar (o log completo tem mais atividades entre elas)
const ROTULOS = ['INÍCIO DO CASO', 'VALIDAÇÃO', 'CAMADA RAW', 'CAMADA TRUSTED', 'REGRAS R1–R7', 'CAMADA REFINED', 'FIM DO CASO'];
const TICKS = ETAPAS.map((label, i) => ({ label, x: 960 + GAP * i }));
const WORLD_W = 960 + GAP * (ETAPAS.length - 1) + 960;
const CARD_W = 600;
const CARD_H = 250;

export const S09EventLog: React.FC<{ quadros: number; partida: number; chegada: number }> = ({ quadros, partida, chegada }) => {
  const frame = useCurrentFrame();
  const ZOOM_END = chegada + 10;
  const camXAt = (f: number): number => {
    const total = TICKS[TICKS.length - 1].x - 960;
    const t = interpolate(f, [partida, chegada], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const eased = interpolate(t, [0, 0.15, 0.88, 1], [0, 0.055, 0.9, 1], { easing: Easing.inOut(Easing.quad) });
    return eased * total;
  };
  const popFrameOf = (tickX: number): number => {
    for (let f = partida; f <= chegada; f++) if (camXAt(f) >= tickX - 960) return f;
    return chegada;
  };
  const camX = camXAt(frame);
  const zoom = interpolate(frame, [chegada, ZOOM_END], [1, 1.28], { easing: Easing.out(Easing.cubic), extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const entra = 1, sai = 1; // cortes secos

  return (
    <div style={{ width: W, height: 1080, background: COR.tela, overflow: 'hidden', position: 'relative', opacity: entra * sai }}>
      <div style={{ width: W, height: 1080, transform: `scale(${zoom})`, transformOrigin: '50% 62%' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, width: WORLD_W, height: 1080, transform: `translateX(${-camX}px)` }}>
          <div style={{ position: 'absolute', left: 200, top: AXIS_Y - 3, width: WORLD_W - 400, height: 6, background: COR.linha, borderRadius: 3 }} />
          {Array.from({ length: (ETAPAS.length - 1) * 5 + 1 }).map((_, i) => (
            <div key={i} style={{ position: 'absolute', left: 960 + i * (GAP / 5) - 2, top: AXIS_Y - 12, width: 4, height: 24, background: '#b9c8bf', borderRadius: 2 }} />
          ))}
          {TICKS.map((tick, i) => {
            const pop = i === 0 ? 4 : popFrameOf(tick.x) - 6;
            const s = spring({ frame: frame - pop, fps: 30, config: { damping: 11, stiffness: 160, mass: 0.9 }, durationInFrames: 26 });
            const ultimo = i === TICKS.length - 1;
            return (
              <div key={i} style={{ position: 'absolute', left: tick.x, top: 0 }}>
                <div style={{ position: 'absolute', left: -3, top: AXIS_Y - 28, width: 6, height: 56, background: COR.verde, borderRadius: 3 }} />
                {frame >= pop && (
                  <div style={{ position: 'absolute', left: -CARD_W / 2, top: AXIS_Y - 40 - CARD_H, width: CARD_W, height: CARD_H, transform: `scaleY(${s}) scaleX(${0.6 + 0.4 * s})`, transformOrigin: '50% 100%', opacity: Math.min(1, s * 2),
                    background: ultimo ? COR.floresta : COR.branco, border: `2px solid ${ultimo ? COR.floresta : COR.linha}`, borderRadius: 14, boxShadow: '0 12px 34px rgba(18,41,35,0.12)', boxSizing: 'border-box', padding: '30px 38px', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 14 }}>
                    <div style={{ fontFamily: FONTE.mono, fontWeight: 500, fontSize: 24, letterSpacing: '0.14em', color: ultimo ? COR.ambar : COR.suave }}>{ROTULOS[i]}</div>
                    <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 58, lineHeight: 1.05, letterSpacing: '-0.02em', color: ultimo ? COR.branco : COR.tinta, whiteSpace: 'nowrap' }}>{tick.label}</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
      <div style={{ position: 'absolute', top: 96, left: 0, width: '100%', textAlign: 'center' }}>
        <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 60, letterSpacing: '-0.02em', color: COR.tinta }}>Cada execução deixa rastro no <span style={{ color: COR.verde }}>event log</span></div>
        <div style={{ fontFamily: FONTE.ui, fontWeight: 500, fontSize: 28, color: COR.suave, marginTop: 14 }}>Etapas principais de uma execução, da entrada ao resultado publicado</div>
      </div>
    </div>
  );
};
