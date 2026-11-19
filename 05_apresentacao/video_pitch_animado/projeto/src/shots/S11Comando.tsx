// Cena 11 — Leve e local. Cartão `typewriter-moves`, variante `terminal-typewriter`, do
// video-shotcraft (demos/typography/typewriter-moves/TerminalTypewriter.tsx): o comando é
// digitado a 2 quadros por caractere, o cursor pisca em onda quadrada de 12 quadros, há uma
// pausa de 12 quadros, e no Enter a cena avança de 1x a 3,2x em 6 quadros (Easing.in cúbico, com
// desfoque nos 2 últimos) e corta seco para a tela real, que assenta de 1,06x para 1x em 4.
// Mantidos todos esses tempos. Adaptado: o comando é o do projeto, as cores são as do AgroSmart
// e a tela que entra é a captura real do painel de execução contínua, parada depois do corte.
import React from 'react';
import { Easing, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { COR, FONTE } from '../tema';
import { Legenda } from '../lib/ui';
import layout from '../layout.json';

const CMD = 'docker compose up -d';
const T = { typeStart: 10, typeEnd: 10 + CMD.length * 2, enter: 10 + CMD.length * 2 + 12, pushEnd: 10 + CMD.length * 2 + 18, settleEnd: 10 + CMD.length * 2 + 22 };
const TW = 1180, TH = 600, TL = (1920 - TW) / 2, TT = (1080 - TH) / 2, TITLEBAR = 52, PAD = 34;
const FOCUS_X = 960, FOCUS_Y = TT + TITLEBAR + PAD + 92;
const cl = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
const P = layout.painel_operacao.painel;
const PESC = 1.3;
const ATIVA = { x: 546, y: 191, w: 49, h: 23 }; // selo "Ativa", medido na captura

const Terminal: React.FC<{ chars: number; cursorOn: boolean }> = ({ chars, cursorOn }) => (
  <div style={{ width: TW, height: TH, background: '#0a1f1a', borderRadius: 14, boxShadow: '0 24px 64px rgba(7,31,26,0.45)', overflow: 'hidden', boxSizing: 'border-box', border: '1px solid rgba(193,217,203,0.16)' }}>
    <div style={{ height: TITLEBAR, background: '#12302a', borderBottom: '1px solid rgba(193,217,203,0.14)', display: 'flex', alignItems: 'center', gap: 12, padding: '0 22px', boxSizing: 'border-box' }}>
      {['#3f6a5a', '#5f8a78', '#8fb3a2'].map((c, i) => <div key={i} style={{ width: 16, height: 16, borderRadius: 8, background: c }} />)}
      <div style={{ margin: '0 auto', fontFamily: FONTE.mono, fontSize: 20, color: '#8fb3a2', letterSpacing: '0.04em' }}>terminal</div>
      <div style={{ width: 72 }} />
    </div>
    <div style={{ padding: PAD, fontFamily: FONTE.mono, fontSize: 44, color: '#e8f1ec', lineHeight: 1.5 }}>
      <div style={{ color: '#7fa392', fontSize: 30, marginBottom: 18 }}>~/AgroSmart/02_plataforma</div>
      <div style={{ display: 'flex', alignItems: 'center', whiteSpace: 'pre' }}>
        <span style={{ color: COR.ambar }}>{'$ '}</span>
        <span>{CMD.substring(0, chars)}</span>
        <span style={{ display: 'inline-block', width: 26, height: 52, marginLeft: 4, background: '#e8f1ec', opacity: cursorOn ? 1 : 0 }} />
      </div>
    </div>
  </div>
);

export const S11Comando: React.FC<{ quadros: number }> = ({ quadros }) => {
  const frame = useCurrentFrame();
  const chars = Math.min(CMD.length, Math.max(0, Math.floor((frame - T.typeStart) / 2)));
  const cursorOn = frame % 12 < 6;
  const pushScale = interpolate(frame, [T.enter, T.pushEnd], [1, 3.2], { ...cl, easing: Easing.in(Easing.cubic) });
  const pushBlur = interpolate(frame, [T.pushEnd - 2, T.pushEnd], [0, 10], cl);
  const cut = frame >= T.pushEnd;
  const dashScale = interpolate(frame, [T.pushEnd, T.settleEnd], [1.06, 1], { ...cl, easing: Easing.out(Easing.cubic) });
  const entra = 1, sai = 1; // cortes secos
  const anel = interpolate(frame, [T.settleEnd + 14, T.settleEnd + 26], [0, 1], cl);
  const PW = P.w * PESC, PH = P.h * PESC, PX = (1920 - PW) / 2, PY = 86;

  return (
    <div style={{ width: 1920, height: 1080, background: cut ? COR.tela : COR.floresta, position: 'relative', overflow: 'hidden', opacity: entra * sai }}>
      {!cut ? (
        <div style={{ width: 1920, height: 1080, transform: `scale(${pushScale})`, transformOrigin: `${FOCUS_X}px ${FOCUS_Y}px`, ...(pushBlur > 0 ? { filter: `blur(${pushBlur}px)` } : {}) }}>
          <div style={{ position: 'absolute', left: TL, top: TT }}><Terminal chars={chars} cursorOn={cursorOn} /></div>
        </div>
      ) : (
        <div style={{ width: 1920, height: 1080, transform: `scale(${dashScale})`, transformOrigin: '960px 540px' }}>
          <div style={{ position: 'absolute', left: PX, top: PY, width: PW, height: PH, borderRadius: 14, overflow: 'hidden', boxShadow: '0 18px 60px rgba(18,41,35,0.16)', background: '#fff' }}>
            <Img src={staticFile('tex/painel_operacao.png')} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} />
            <div style={{ position: 'absolute', left: ATIVA.x * PESC - 10, top: ATIVA.y * PESC - 9, width: ATIVA.w * PESC + 20, height: ATIVA.h * PESC + 18, borderRadius: 12, border: `4px solid ${COR.ambarEscuro}`, boxShadow: '0 0 0 6px rgba(242,198,109,0.25)', opacity: anel }} />
          </div>
        </div>
      )}
      {cut ? <Legenda de={T.settleEnd + 6} ate={quadros - 4} y={958} texto="Um container. Um comando." /> : null}
    </div>
  );
};
