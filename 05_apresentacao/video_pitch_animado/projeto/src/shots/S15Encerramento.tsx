// Cena 15 — Encerramento. Cartão `outro-group-photo-launch` do video-shotcraft
// (demos/outro/outro-group-photo-launch/OutroGroupPhotoLaunch.tsx): elementos das cenas
// anteriores voam dos quatro lados e cercam o nome; a câmera desce como uma grua; faixa de luz,
// luz de palco atrás do nome e poeira dourada. Mantidos do cartão: um elemento a cada 3 quadros
// a partir do 4, voo de 12 quadros com bezier(0.34, 1.4, 0.44, 1) (ultrapassa de verdade),
// rotação 2x→1x e escala 1,12→1 no voo, rastro desfocado, brilho de pouso de 6 quadros, recuo
// de todos (−12% de opacidade) quando o nome entra, letras com atraso 42 + i·1,8, traço 58→70
// com prolongamentos de 190 px, grua rotateX 4°→0 e escala 1,06→1 em 40 quadros e depois
// aproximação lenta, 20 partículas com parâmetros derivados do índice, página de fundo
// desfocada 0→14. Adaptado: a página é a Visão Geral real; os elementos são um por cena do
// filme; o nome é AgroSmart; o endereço do repositório entra quando a fala o cita; a cena dura
// mais que os 145 quadros do exemplo, parada no fim.
import React from 'react';
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { PageCam2D } from '../lib/PageCam2D';
import { COR, FONTE } from '../tema';
import layout from '../layout.json';

const LETTERS = 'AgroSmart'.split('');
const FLY_EASE = Easing.bezier(0.34, 1.4, 0.44, 1);
const CRANE_EASE = Easing.bezier(0.3, 0, 0.2, 1);
const cl = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
const L = layout.visao_geral;
const C = layout.cartao_depois_r2.cartao;

type FlyEl = { key: string; w: number; h: number; cx: number; cy: number; scale: number; rot: number; dx: number; dy: number; radius: number; cue: number; node: React.ReactNode };
const caixa: React.CSSProperties = { position: 'absolute', inset: 0, boxSizing: 'border-box' };
const ELS: FlyEl[] = [
  { key: 'indicadores', w: L.kpis.w, h: L.kpis.h, cx: 960, cy: 118, scale: 0.78, rot: 0, dx: 0, dy: -160, radius: 10, cue: 4,
    node: <Img src={staticFile('tex/kpis_4x.png')} style={{ ...caixa, width: '100%', height: '100%' }} /> },
  { key: 'ocorrencia', w: 620, h: C.h, cx: 290, cy: 420, scale: 0.7, rot: -5, dx: -520, dy: 0, radius: 12, cue: 7,
    node: <Img src={staticFile('tex/cartao_depois_r2.png')} style={{ position: 'absolute', left: 0, top: 0, width: C.w, height: C.h }} /> },
  { key: 'testes', w: 380, h: 270, cx: 1640, cy: 400, scale: 0.86, rot: 4, dx: 520, dy: 0, radius: 16, cue: 10,
    node: <div style={{ ...caixa, background: COR.branco, border: `2px solid ${COR.linha}`, padding: '26px 32px' }}>
      <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 132, lineHeight: 1, letterSpacing: '-0.03em', color: COR.verde }}>63</div>
      <div style={{ fontFamily: FONTE.ui, fontWeight: 600, fontSize: 28, lineHeight: 1.2, color: COR.tinta, marginTop: 12 }}>testes automatizados aprovados</div>
    </div> },
  { key: 'terminal', w: 640, h: 190, cx: 1560, cy: 800, scale: 0.76, rot: -3, dx: 470, dy: 260, radius: 14, cue: 13,
    node: <div style={{ ...caixa, background: '#0a1f1a', border: '1px solid rgba(193,217,203,0.16)' }}>
      <div style={{ height: 44, background: '#12302a', display: 'flex', alignItems: 'center', gap: 10, padding: '0 18px' }}>{['#3f6a5a', '#5f8a78', '#8fb3a2'].map((c, i) => <div key={i} style={{ width: 13, height: 13, borderRadius: 7, background: c }} />)}</div>
      <div style={{ padding: '34px 30px', fontFamily: FONTE.mono, fontSize: 38, color: '#e8f1ec', whiteSpace: 'pre' }}><span style={{ color: COR.ambar }}>$ </span>docker compose up -d</div>
    </div> },
  { key: 'etapa', w: 520, h: 210, cx: 300, cy: 800, scale: 0.78, rot: 3, dx: -420, dy: 300, radius: 14, cue: 16,
    node: <div style={{ ...caixa, background: COR.floresta, padding: '30px 34px', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 12 }}>
      <div style={{ fontFamily: FONTE.mono, fontWeight: 500, fontSize: 22, letterSpacing: '0.14em', color: COR.ambar }}>EVENT LOG · FIM DO CASO</div>
      <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 50, letterSpacing: '-0.02em', color: COR.branco, whiteSpace: 'nowrap' }}>Execução concluída</div>
    </div> },
  { key: 'linha', w: L.linha_b.w, h: L.linha_b.h, cx: 700, cy: 952, scale: 0.72, rot: 2, dx: 0, dy: 320, radius: 8, cue: 19,
    node: <Img src={staticFile('tex/linha_talhao_b_4x.png')} style={{ ...caixa, width: '100%', height: '100%', background: '#fff' }} /> },
  { key: 'publico', w: 700, h: 96, cx: 620, cy: 236, scale: 0.7, rot: -1.5, dx: 0, dy: -260, radius: 48, cue: 22,
    node: <div style={{ ...caixa, background: COR.branco, border: `3px solid ${COR.linha}`, borderRadius: 48, display: 'flex', alignItems: 'center', gap: 18, padding: '0 34px', fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 52, letterSpacing: '-0.02em', color: COR.verde, whiteSpace: 'nowrap' }}>
      <span style={{ width: 20, height: 20, borderRadius: 10, background: COR.ambar }} />quem decide no campo
    </div> },
  { key: 'alta', w: 300, h: 96, cx: 1240, cy: 968, scale: 0.86, rot: -2, dx: 400, dy: 0, radius: 12, cue: 25,
    node: <div style={{ ...caixa, background: COR.branco, border: `2px solid ${COR.linha}`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20 }}>
      <span style={{ padding: '6px 16px', borderRadius: 8, background: COR.altaFundo, color: COR.altaTexto, fontFamily: FONTE.ui, fontWeight: 700, fontSize: 30 }}>Alta</span>
      <span style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 44, color: COR.tinta }}>regra R2</span>
    </div> },
  { key: 'estagio', w: 420, h: 150, cx: 1580, cy: 178, scale: 0.8, rot: 2.5, dx: 380, dy: -220, radius: 14, cue: 28,
    node: <div style={{ ...caixa, background: COR.floresta, padding: '0 34px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
      <div style={{ width: 52, height: 7, borderRadius: 4, background: COR.verdeClaro, marginBottom: 16 }} />
      <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 60, letterSpacing: '-0.03em', color: COR.branco }}>Entregue</div>
    </div> },
];

// 20 partículas; todos os parâmetros saem do índice (renderização reprodutível)
const DUST = Array.from({ length: 20 }, (_, i) => ({ x: (i * 439 + 137) % 1920, y0: (i * 613 + 271) % 1080, rise: 0.3 + (i % 5) * 0.11, swayAmp: 9 + (i % 4) * 5, swayFreq: 0.022 + (i % 3) * 0.008, phase: (i * 0.83) % (Math.PI * 2), size: 2 + (i % 3) * 0.5, opacity: 0.15 + ((i * 7) % 5) * 0.05 }));

export const S15Encerramento: React.FC<{ quadros: number; endereco: number }> = ({ quadros, endereco }) => {
  const frame = useCurrentFrame();
  const blur = interpolate(frame, [0, 24], [0, 14], { ...cl, easing: Easing.bezier(0.4, 0, 0.4, 1) });
  const rule = interpolate(frame, [58, 70], [0, 1], { ...cl, easing: Easing.bezier(0.3, 0, 0.2, 1) });
  const tag = interpolate(frame, [68, 80], [0, 1], cl);
  const url = interpolate(frame, [endereco, endereco + 14], [0, 1], { ...cl, easing: Easing.bezier(0.2, 0.75, 0.3, 1) });
  const fadeOut = 1;
  const escurece = interpolate(frame, [quadros - 24, quadros - 3], [0, 1], { ...cl, easing: Easing.bezier(0.4, 0, 0.3, 1) }); // o filme termina no verde do palco
  const fadeIn = 1; // corte seco
  const recede = interpolate(frame, [42, 50], [0, 1], cl);
  const craneT = interpolate(frame, [0, 40], [0, 1], { ...cl, easing: CRANE_EASE });
  const pushT = interpolate(frame, [40, quadros], [0, 1], cl);
  const camScale = 1.06 - 0.06 * craneT + 0.035 * pushT;
  const camTilt = 4 * (1 - craneT);
  const sweepX = interpolate(frame, [2, 14], [-700, 2020], { ...cl, easing: Easing.bezier(0.4, 0, 0.6, 1) });
  const sweepOpacity = interpolate(frame, [2, 5, 11, 14], [0, 0.12, 0.12, 0], cl);
  const stageLight = interpolate(frame, [42, 50, 58], [0, 0.5, 0.25], cl);
  const vignette = interpolate(frame, [42, 54], [0, 0.1], cl);
  const ruleExt = interpolate(frame, [58, 66], [0, 1], { ...cl, easing: Easing.bezier(0.3, 0, 0.2, 1) });
  const ruleExtFade = interpolate(frame, [66, 72], [1, 0], cl);
  const wordSpacing = interpolate(frame, [62, 66], [-0.03, -0.015], { ...cl, easing: Easing.bezier(0.3, 0, 0.2, 1) });

  return (
    <AbsoluteFill style={{ backgroundColor: COR.tela }}>
      <AbsoluteFill style={{ opacity: fadeOut * fadeIn }}>
        <AbsoluteFill style={{ transform: `perspective(1400px) rotateX(${camTilt}deg) scale(${camScale})`, transformOrigin: '50% 45%' }}>
          <PageCam2D src="tex/visao_geral.png" pageH={1080} keys={[{ frame: 0, cx: 960, cy: 540, zoom: 0.9 }]} blur={blur} bg={COR.tela} />
          <AbsoluteFill style={{ background: 'radial-gradient(1200px 800px at 50% 48%, rgba(246,248,246,0.86), rgba(246,248,246,0.6) 60%, rgba(246,248,246,0.4))', pointerEvents: 'none' }} />
          <AbsoluteFill style={{ pointerEvents: 'none' }}>
            {ELS.map((el) => {
              if (frame < el.cue) return null;
              const t = interpolate(frame, [el.cue, el.cue + 12], [0, 1], { ...cl, easing: FLY_EASE });
              const opacity = interpolate(frame, [el.cue, el.cue + 3], [0, 1], cl);
              const x = el.dx * (1 - t), y = el.dy * (1 - t);
              const rot = el.rot * (2 - t);
              const scale = el.scale * (1.12 - 0.12 * t);
              const air = Math.max(0, 1 - t);
              const shadow = air > 0.01 ? `0 ${10 + 26 * air}px ${24 + 46 * air}px rgba(18,41,35,${0.16 + 0.1 * air}), 0 2px 6px rgba(18,41,35,.08)` : '0 10px 24px rgba(18,41,35,.16), 0 2px 6px rgba(18,41,35,.08)';
              const linT = interpolate(frame, [el.cue, el.cue + 12], [0, 1], cl);
              const showGhost = linT > 0.05 && linT < 0.95;
              const glow = interpolate(frame, [el.cue + 12, el.cue + 18], [0.35, 0], cl);
              const showGlow = frame >= el.cue + 12 && frame < el.cue + 18;
              const glowR = el.w * el.scale * 0.5;
              const base: React.CSSProperties = { position: 'absolute', left: el.cx - el.w / 2, top: el.cy - el.h / 2, width: el.w, height: el.h, transformOrigin: 'center center', borderRadius: el.radius, overflow: 'hidden' };
              return (
                <div key={el.key}>
                  {showGhost ? <div style={{ ...base, transform: `translate(${x + el.dx * 0.08}px, ${y + el.dy * 0.08}px) rotate(${rot}deg) scale(${scale})`, opacity: 0.2 * Math.max(0, 1 - linT), filter: 'blur(8px)' }}>{el.node}</div> : null}
                  <div style={{ ...base, transform: `translate(${x}px, ${y}px) rotate(${rot}deg) scale(${scale})`, boxShadow: shadow, opacity: opacity * (1 - 0.12 * recede), filter: `saturate(${1 - 0.08 * recede})`, background: '#fff' }}>{el.node}</div>
                  {showGlow ? <div style={{ position: 'absolute', left: el.cx - glowR, top: el.cy - glowR, width: glowR * 2, height: glowR * 2, borderRadius: '50%', background: 'radial-gradient(circle, rgba(242,198,109,0.9), rgba(242,198,109,0) 70%)', opacity: glow, mixBlendMode: 'multiply' }} /> : null}
                </div>
              );
            })}
          </AbsoluteFill>
        </AbsoluteFill>

        <AbsoluteFill style={{ pointerEvents: 'none' }}>
          {DUST.map((d, i) => {
            const y = (((d.y0 - frame * d.rise) % 1080) + 1080) % 1080;
            const x = d.x + Math.sin(frame * d.swayFreq + d.phase) * d.swayAmp;
            return <div key={i} style={{ position: 'absolute', left: x, top: y, width: d.size, height: d.size, borderRadius: '50%', background: '#d9a441', opacity: d.opacity }} />;
          })}
        </AbsoluteFill>
        {sweepOpacity > 0 ? (
          <AbsoluteFill style={{ pointerEvents: 'none', mixBlendMode: 'overlay' }}>
            <div style={{ position: 'absolute', top: 0, bottom: 0, left: sweepX - 300, width: 600, background: 'linear-gradient(90deg, rgba(255,244,224,0), rgba(255,244,224,1) 50%, rgba(255,244,224,0))', opacity: sweepOpacity }} />
          </AbsoluteFill>
        ) : null}
        {stageLight > 0 ? <AbsoluteFill style={{ pointerEvents: 'none', background: 'radial-gradient(760px 400px at 960px 520px, rgba(255,255,255,0.98), rgba(255,255,255,0.45) 55%, rgba(255,255,255,0) 75%)', opacity: stageLight + 0.35 * recede }} /> : null}
        {vignette > 0 ? <AbsoluteFill style={{ pointerEvents: 'none', background: 'radial-gradient(1400px 900px at 50% 50%, rgba(12,48,40,0) 55%, rgba(12,48,40,0.7) 100%)', opacity: vignette }} /> : null}

        <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', pointerEvents: 'none' }}>
          <div style={{ textAlign: 'center', transform: 'translateY(-24px)' }}>
            <div style={{ fontFamily: FONTE.titulo, fontSize: 168, fontWeight: 700, color: COR.floresta, letterSpacing: `${wordSpacing}em`, display: 'flex', justifyContent: 'center' }}>
              {LETTERS.map((ch, i) => {
                const delay = Math.round(42 + i * 1.8);
                const t = interpolate(frame, [delay, delay + 8], [0, 1], { ...cl, easing: Easing.bezier(0.2, 0.75, 0.3, 1) });
                return <span key={i} style={{ opacity: t, transform: `translateY(${(1 - t) * 28}px) scale(${1.35 - 0.35 * t})`, filter: `blur(${(1 - t) * 8}px)`, display: 'inline-block', whiteSpace: 'pre' }}>{ch}</span>;
              })}
            </div>
            <div style={{ position: 'relative', height: 6, width: 260, margin: '20px auto 0' }}>
              <div style={{ position: 'absolute', inset: 0, borderRadius: 3, background: COR.ambarEscuro, transform: `scaleX(${rule})` }} />
              {ruleExt > 0 && ruleExtFade > 0 ? (<>
                <div style={{ position: 'absolute', top: 2.5, height: 1, right: '100%', width: 190 * ruleExt, background: COR.ambarEscuro, opacity: ruleExtFade }} />
                <div style={{ position: 'absolute', top: 2.5, height: 1, left: '100%', width: 190 * ruleExt, background: COR.ambarEscuro, opacity: ruleExtFade }} />
              </>) : null}
            </div>
            <div style={{ fontFamily: FONTE.mono, fontWeight: 500, fontSize: 27, letterSpacing: '0.14em', color: COR.suave, marginTop: 28, opacity: tag, textTransform: 'uppercase' }}>AgroMonitor · Fase 7</div>
            <div style={{ fontFamily: FONTE.ui, fontWeight: 600, fontSize: 36, color: COR.verde, marginTop: 26, opacity: url, transform: `translateY(${(1 - url) * 14}px)` }}>github.com/SaulVasconcelos/AgroSmart</div>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      <AbsoluteFill style={{ backgroundColor: COR.floresta, opacity: escurece, pointerEvents: 'none' }} />
    </AbsoluteFill>
  );
};
