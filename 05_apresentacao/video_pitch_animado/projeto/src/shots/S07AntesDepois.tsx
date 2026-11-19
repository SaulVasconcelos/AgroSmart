// Cena 7 — Honesto com a incerteza. Cartão `before-after-slider-scrub` do video-shotcraft
// (demos/data/before-after-slider-scrub/BeforeAfterSliderScrub.tsx): duas versões sobrepostas e
// uma barra que primeiro é arremessada e depois volta devagar. Mantidos do cartão: arremesso em
// 12 quadros até 76% com volta a 70% em 12, parada de 18, varredura lenta de 48 quadros até 40%
// (razão de velocidade ~5:1), recorte que acompanha a barra e puxador que estica com a velocidade.
// Adaptado: as duas versões são capturas reais da mesma leitura do Talhão B (sem filtro para
// "piorar" o antes), enquadradas na parte esquerda do cartão para o texto ficar legível; a barra fica parada enquanto a fala trata do "antes" e é arremessada quando
// a fala diz "Registrada a observação".
import React from 'react';
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { COR, FONTE } from '../tema';
import { Palco } from '../lib/ui';
import layout from '../layout.json';

const CL = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
const C = layout.cartao_depois_r2.cartao;
const ESC = 1.6;
const VISIVEL = 930; // px de CSS do cartão que entram no quadro (título, medidas, evidências e orientação)
const CW = VISIVEL * ESC;
const CH = C.h * ESC;
const CX = (1920 - CW) / 2;
const CY = 200;
const SELO = { x: 260.5, y: 23, w: 103, h: 24.5 }; // selo "Indeterminada", medido na captura

export const S07AntesDepois: React.FC<{ quadros: number; arremesso: number }> = ({ quadros, arremesso }) => {
  const frame = useCurrentFrame();
  // linha do tempo do cartão, deslocada para o quadro em que a fala muda de assunto
  const T0 = arremesso;
  const FLING = T0 + 12;
  const BOUNCE = T0 + 24;
  const HOLD = T0 + 42;
  const SCRUB = T0 + 90;
  const posAt = (f: number): number => {
    if (f < FLING) return interpolate(f, [T0, FLING], [0, 76], { easing: Easing.out(Easing.cubic), ...CL });
    if (f < BOUNCE) return interpolate(f, [FLING, BOUNCE], [76, 70], { easing: Easing.inOut(Easing.cubic), ...CL });
    if (f < HOLD) return 70;
    return interpolate(f, [HOLD, SCRUB], [70, 40], { easing: Easing.inOut(Easing.quad), ...CL });
  };
  const p = posAt(frame);
  const x = (p / 100) * CW; // posição da barra dentro do cartão
  const v = Math.abs(posAt(frame) - posAt(frame - 1));
  const squish = 1 + Math.min(v / 8, 1) * 0.18;
  const entra = interpolate(frame, [0, 12], [0, 1], { ...CL, easing: Easing.bezier(0.2, 0.75, 0.3, 1) });
  const sai = 1; // corte seco: a cena 8 começa com o mesmo cartão no mesmo lugar
  const barra = interpolate(frame, [T0 - 6, T0], [0, 1], CL);
  const depois = interpolate(frame, [FLING - 2, FLING + 10], [0, 1], { ...CL, easing: Easing.bezier(0.2, 0.75, 0.3, 1) });
  // enquanto a fala diz "a resposta é indeterminada", um contorno marca o selo real do cartão
  const marca = interpolate(frame, [58, 70], [0, 1], CL) * interpolate(frame, [T0 - 14, T0 - 4], [1, 0], CL);

  const Rotulo: React.FC<{ titulo: string; texto: string; op: number; lado: 'esq' | 'dir'; cor: string }> = ({ titulo, texto, op, lado, cor }) => (
    <div style={{ position: 'absolute', top: CY - 96, ...(lado === 'esq' ? { left: CX } : { right: CX }), opacity: op, transform: `translateY(${(1 - op) * 16}px)`, display: 'flex', alignItems: 'center', gap: 14 }}>
      <span style={{ padding: '7px 13px', borderRadius: 8, background: cor, color: COR.floresta, fontFamily: FONTE.ui, fontWeight: 800, fontSize: 21, letterSpacing: '0.12em' }}>{titulo}</span>
      <span style={{ fontFamily: FONTE.titulo, fontWeight: 600, fontSize: 31, letterSpacing: '-0.01em', color: COR.branco }}>{texto}</span>
    </div>
  );

  return (
    <Palco brilho={0.7}>
      <AbsoluteFill style={{ opacity: entra * sai }}>
        <Rotulo titulo="DEPOIS" texto="Com a observação: prioridade alta" op={depois} lado="esq" cor={COR.ambar} />
        <Rotulo titulo="ANTES" texto="Sem observação de campo: indeterminada" op={1 - depois * 0.0} lado="dir" cor={COR.menta} />
        <div style={{ position: 'absolute', left: CX, top: CY + (1 - entra) * 30, width: CW, height: CH, borderRadius: 14, overflow: 'hidden', boxShadow: '0 30px 90px rgba(0,0,0,0.38)', background: '#fff' }}>
          <Img src={staticFile('tex/cartao_antes_nd.png')} style={{ position: 'absolute', left: 0, top: 0, width: C.w * ESC, height: CH }} />
          <div style={{ position: 'absolute', inset: 0, clipPath: `inset(0 ${CW - x}px 0 0)` }}>
            <Img src={staticFile('tex/cartao_depois_r2.png')} style={{ position: 'absolute', left: 0, top: 0, width: C.w * ESC, height: CH }} />
          </div>
          <div style={{ position: 'absolute', left: SELO.x * ESC - 12, top: SELO.y * ESC - 10, width: SELO.w * ESC + 24, height: SELO.h * ESC + 20, borderRadius: 14, border: `4px solid ${COR.ambarEscuro}`, boxShadow: '0 0 0 6px rgba(242,198,109,0.25)', opacity: marca }} />
          <div style={{ position: 'absolute', left: x - 3, top: 0, width: 6, height: CH, background: '#ffffff', boxShadow: '0 0 14px rgba(0,0,0,0.35)', opacity: barra }} />
        </div>
        <div style={{ position: 'absolute', left: CX + x - 44, top: CY + CH / 2 - 44, width: 88, height: 88, borderRadius: 44, background: '#ffffff', border: `3px solid ${COR.linha}`, boxShadow: '0 6px 24px rgba(0,0,0,0.3)', transform: `scaleX(${squish})`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, boxSizing: 'border-box', opacity: barra }}>
          <div style={{ width: 0, height: 0, borderTop: '10px solid transparent', borderBottom: '10px solid transparent', borderRight: `14px solid ${COR.suave}` }} />
          <div style={{ width: 0, height: 0, borderTop: '10px solid transparent', borderBottom: '10px solid transparent', borderLeft: `14px solid ${COR.suave}` }} />
        </div>
        <div style={{ position: 'absolute', left: 0, right: 0, top: CY + CH + 36, textAlign: 'center', fontFamily: FONTE.ui, fontWeight: 500, fontSize: 27, color: COR.menta }}>
          A mesma leitura do Talhão B, antes e depois de registrar a observação de campo · dados simulados
        </div>
      </AbsoluteFill>
    </Palco>
  );
};
