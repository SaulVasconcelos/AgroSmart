// Cena 13 — Estágio do produto. Cartão `card-flip-reveal` do video-shotcraft
// (demos/transition/card-flip-reveal/CardFlipReveal.tsx): cada cartão vira 180° no eixo Y em
// 18 quadros, passa 12° do ponto e assenta em 8 (perspectiva 1200), com uma faixa escura que
// cruza a face perto dos 90°. Mantidos esses valores e as curvas. Adaptado: cada cartão vira no
// quadro em que a fala entra no assunto dele (em vez de 10 quadros de defasagem fixa); a frente
// é o nome do estágio e o verso, o que está nele.
import React from 'react';
import { Easing, interpolate, useCurrentFrame } from 'remotion';
import { COR, FONTE } from '../tema';

const CW = 520, CH = 440, GAP = 50;
const X0 = (1920 - (CW * 3 + GAP * 2)) / 2;
const Y = 370;
const FLIP_DUR = 18, SETTLE = 8, OVERSHOOT = 12;
const cl = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;

const CARTOES = [
  { nome: 'Entregue', cor: COR.verdeClaro, itens: ['motor de regras', 'painel', 'execução contínua', 'container', 'pipeline'] },
  { nome: 'Simulado', cor: COR.ambar, itens: ['dados de sensores', 'dados de campo'] },
  { nome: 'Roadmap', cor: COR.menta, itens: ['sensores físicos', 'login', 'notificações'] },
];

const angleAt = (f: number, s: number): number => {
  if (f < s + FLIP_DUR) return interpolate(f, [s, s + FLIP_DUR], [0, 180 + OVERSHOOT], { ...cl, easing: Easing.bezier(0.55, 0, 0.3, 1) });
  return interpolate(f, [s + FLIP_DUR, s + FLIP_DUR + SETTLE], [180 + OVERSHOOT, 180], { ...cl, easing: Easing.out(Easing.poly(5)) });
};

const Sheen: React.FC<{ angle: number }> = ({ angle }) => {
  const pos = interpolate(angle, [35, 145], [-25, 115], cl);
  const op = Math.max(0, 1 - Math.abs(angle - 90) / 55);
  if (op <= 0.004) return null;
  return <div style={{ position: 'absolute', inset: 0, borderRadius: 16, pointerEvents: 'none', opacity: op, background: `linear-gradient(105deg, rgba(0,0,0,0) ${pos - 14}%, rgba(0,0,0,0.32) ${pos}%, rgba(0,0,0,0) ${pos + 14}%)` }} />;
};

export const S13Estagio: React.FC<{ quadros: number; viradas: [number, number, number] }> = ({ quadros, viradas }) => {
  const frame = useCurrentFrame();
  const entra = 1, sai = 1; // cortes secos
  return (
    <div style={{ width: 1920, height: 1080, background: COR.tela, position: 'relative', overflow: 'hidden', opacity: entra * sai }}>
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 20, background: COR.floresta }} />
      <div style={{ position: 'absolute', left: X0, top: 140 }}>
        <div style={{ fontFamily: FONTE.ui, fontWeight: 600, fontSize: 30, letterSpacing: '0.14em', textTransform: 'uppercase', color: COR.suave }}>Estágio do produto</div>
        <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 76, letterSpacing: '-0.03em', color: COR.tinta, marginTop: 12 }}>O que existe hoje, e o que não</div>
      </div>
      {CARTOES.map((c, i) => {
        const angle = angleAt(frame, viradas[i]);
        return (
          <div key={i} style={{ position: 'absolute', left: X0 + i * (CW + GAP), top: Y, width: CW, height: CH, perspective: 1200 }}>
            <div style={{ width: '100%', height: '100%', position: 'relative', transformStyle: 'preserve-3d', transform: `rotateY(${angle}deg)` }}>
              <div style={{ position: 'absolute', inset: 0, backfaceVisibility: 'hidden', background: COR.floresta, borderRadius: 16, boxShadow: '0 16px 44px rgba(18,41,35,0.18)', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 44px', boxSizing: 'border-box' }}>
                <div style={{ width: 64, height: 8, borderRadius: 4, background: c.cor, marginBottom: 30 }} />
                <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 92, letterSpacing: '-0.03em', color: COR.branco }}>{c.nome}</div>
                <Sheen angle={angle} />
              </div>
              <div style={{ position: 'absolute', inset: 0, backfaceVisibility: 'hidden', transform: 'rotateY(180deg)', background: COR.branco, border: `2px solid ${COR.linha}`, borderRadius: 16, boxSizing: 'border-box', boxShadow: '0 16px 44px rgba(18,41,35,0.10)', padding: '38px 44px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 26 }}>
                  <div style={{ width: 22, height: 22, borderRadius: 11, background: c.cor, border: `2px solid ${COR.floresta}`, boxSizing: 'border-box' }} />
                  <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 52, letterSpacing: '-0.02em', color: COR.tinta }}>{c.nome}</div>
                </div>
                {c.itens.map((it, k) => (
                  <div key={k} style={{ fontFamily: FONTE.ui, fontWeight: 500, fontSize: 36, lineHeight: 1.5, color: COR.tinta, display: 'flex', gap: 16 }}>
                    <span style={{ color: COR.suave }}>·</span>{it}
                  </div>
                ))}
                <Sheen angle={angle} />
              </div>
            </div>
          </div>
        );
      })}
      <div style={{ position: 'absolute', left: X0, top: Y + CH + 46, fontFamily: FONTE.ui, fontWeight: 500, fontSize: 28, color: COR.suave }}>O roadmap é proposta: nada dele existe no produto hoje.</div>
    </div>
  );
};
