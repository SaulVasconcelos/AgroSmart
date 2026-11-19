// Cena 5 — Talhão B. Cartão `spotlight-hero-card` do video-shotcraft
// (demos/opening/spotlight-hero-card/SpotlightHeroCard.tsx): um foco de luz passeia pela página,
// trava no elemento, a câmera se aproxima de lado, o elemento sobe, um feixe dá duas voltas no
// contorno e ele volta ao lugar. Mantidos do cartão: todos os tempos (foco 4→28, trava 32,
// aproximação 32→48, subida 48→58 com ultrapassagem, flutuação com balanço de 4 px e período 40,
// feixe 60→74 e 80→100, pouso 112→130 com pressão 0,997), z de 110 px, sombra dupla, remendo no
// lugar vago com contorno âmbar, câmera travada depois do pouso. Adaptado: o "cartão" é a linha
// real do Talhão B (larga e baixa), então o zoom e o giro são menores (1,2 e 10° em vez de 2,6 e
// 34°) para a linha caber no quadro; os 12 primeiros quadros recuam de 1x para 0,78x para emendar
// com o fim da cena 4; a anotação 3D do exemplo virou a legenda do roteiro.
import React from 'react';
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { PageCam2D, CamKey2D } from '../lib/PageCam2D';
import { COR } from '../tema';
import { Ambar, Legenda } from '../lib/ui';
import layout from '../layout.json';

const AMBER = COR.ambarEscuro;
const SLOT_AMBER = '#c98a2b';
const BEAM_CORE = 'rgba(255,248,232,0.98)';
const PATCH = '#ffffff';
const CARD = layout.visao_geral.linha_b;
const MCX = CARD.x + CARD.w / 2;
const MCY = CARD.y + CARD.h / 2;
const RADIUS = 8;
const Z0 = 0.78;
const ZOOM = 1.2;

const CAM_KEYS: CamKey2D[] = [
  { frame: 0, cx: 960, cy: 540, zoom: 1, rotX: 0, rotY: 0, rotZ: 0, persp: 1200 }, // mesmo quadro em que a cena 4 termina
  { frame: 12, cx: 960, cy: 540, zoom: Z0, rotX: 0, rotY: 0, rotZ: 0, persp: 1200 },
  { frame: 32, cx: 960, cy: 540, zoom: Z0, rotX: 0, rotY: 0, rotZ: 0, persp: 1200 },
  { frame: 48, cx: MCX + 6, cy: MCY + 14, zoom: ZOOM, rotX: 6, rotY: 10, rotZ: 0.8, persp: 1200 },
  { frame: 400, cx: MCX + 6, cy: MCY + 14, zoom: ZOOM, rotX: 6, rotY: 10, rotZ: 0.8, persp: 1200 },
];
const PUSH_EASE = Easing.bezier(0.35, 0, 0.2, 1);
const POP_EASE = Easing.bezier(0.2, 1.25, 0.3, 1);
const RESEAT_EASE = Easing.bezier(0.4, 0, 0.3, 1.05);
const cl = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
// posição da linha na tela, em %, na vista de frente (zoom 0,78)
const ALVO_X = ((960 + (MCX - 960) * Z0) / 1920) * 100;
const ALVO_Y = ((540 + (MCY - 540) * Z0) / 1080) * 100;

export const S05TalhaoB: React.FC<{ quadros: number }> = ({ quadros }) => {
  const frame = useCurrentFrame();
  const macroIn = 1; // sem clarão de entrada: a cena continua a imagem da anterior
  const spotEase = Easing.bezier(0.4, 0, 0.3, 1);
  const spotX = interpolate(frame, [4, 8, 16, 22, 28, 48], [25, 25, 70, 42, ALVO_X, 50], { ...cl, easing: spotEase });
  const spotY = interpolate(frame, [4, 8, 16, 22, 28, 48], [30, 30, 62, 78, ALVO_Y, 50], { ...cl, easing: spotEase });
  const spotOn = interpolate(frame, [2, 10], [0, 1], cl);
  const poolBase = interpolate(frame, [22, 32, 48], [620, 420, 520], { ...cl, easing: Easing.bezier(0.4, 0, 0.3, 1) });
  const poolPulse = interpolate(frame, [32, 36, 41], [0, 0.06, 0], cl);
  const alarga = interpolate(frame, [32, 48], [1, 1.9], cl); // a linha é larga: a poça de luz acompanha
  const poolRx = poolBase * (1 + poolPulse) * alarga;
  const poolRy = poolBase * 0.8 * (1 + poolPulse) * interpolate(frame, [32, 48], [1, 0.62], cl);
  const vignette = interpolate(frame, [22, 32, 48], [0.16, 0.34, 0.42], cl);

  const rise = interpolate(frame, [48, 58], [0, 1], { ...cl, easing: POP_EASE });
  const reseat = interpolate(frame, [112, 130], [0, 1], { ...cl, easing: RESEAT_EASE });
  const lift = rise * (1 - reseat);
  const bob = Math.sin(((frame - 58) / 40) * Math.PI * 2) * 4 * lift;
  const z = 110 * lift + bob;
  const landed = frame >= 130;
  const press = interpolate(frame, [126, 129, 130], [1, 0.997, 1], cl);
  const shadow = `0 ${8 * lift}px ${10 + 12 * lift}px rgba(18,41,35,${0.2 * lift}), 0 ${46 * lift}px ${90 * lift}px rgba(18,41,35,${0.24 * lift})`;
  const slotVis = Math.min(1, rise * 2) * (1 - reseat);
  const landPulse = interpolate(frame, [126, 130, 134], [0, 1, 0], cl);
  const slotEdge = Math.min(1, 0.4 * (1 - reseat)) + landPulse * 0.6;

  const beam1Prog = interpolate(frame, [60, 74], [0, 1], { ...cl, easing: Easing.linear });
  const beam1On = frame >= 59 && frame <= 75;
  const beam2Prog = interpolate(frame, [80, 100], [0, 1], { ...cl, easing: Easing.bezier(0.4, 0, 0.4, 1) });
  const beam2On = frame >= 79 && frame <= 101;
  const beamTrail = interpolate(frame, [100, 112], [0.35, 0], cl);
  const bw = CARD.w + 6;
  const bh = CARD.h + 6;
  const sai = 1; // corte seco para o cartão de texto

  return (
    <AbsoluteFill style={{ backgroundColor: COR.tela }}>
      <AbsoluteFill style={{ opacity: macroIn * sai }}>
        <PageCam2D src="tex/visao_geral.png" pageH={1080} keys={CAM_KEYS} ease={PUSH_EASE} bg={COR.tela}>
          <div style={{ transformStyle: 'preserve-3d' }}>
            {slotVis > 0.02 ? (
              <div style={{ position: 'absolute', left: CARD.x - 2, top: CARD.y - 2, width: CARD.w + 4, height: CARD.h + 4, background: PATCH, borderRadius: RADIUS, boxShadow: `inset 0 0 26px rgba(169,107,20,${0.14 * slotEdge})`, opacity: slotVis }}>
                <div style={{ position: 'absolute', inset: 0, borderRadius: RADIUS, border: `1.5px solid ${SLOT_AMBER}`, opacity: slotEdge, pointerEvents: 'none' }} />
              </div>
            ) : null}
            <div style={{ position: 'absolute', left: CARD.x, top: CARD.y, width: CARD.w, height: CARD.h, transform: `translateZ(${z}px) scale(${press})`, transformOrigin: 'center center', transformStyle: 'preserve-3d' }}>
              <div style={{ position: 'absolute', inset: 0, borderRadius: RADIUS, overflow: 'hidden', boxShadow: landed ? 'none' : shadow, background: '#fff' }}>
                <Img src={staticFile('tex/linha_talhao_b_4x.png')} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', display: 'block' }} />
                <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(160deg, rgba(255,255,255,0.5), transparent 40%)', opacity: lift, pointerEvents: 'none' }} />
              </div>
              <div style={{ position: 'absolute', inset: 0, borderRadius: RADIUS, boxShadow: `inset 0 0 0 1px rgba(255,255,255,${0.7 * lift})`, pointerEvents: 'none' }} />
              {(beam1On || beam2On) && lift > 0.4 ? (
                <svg width={bw} height={bh} viewBox={`0 0 ${bw} ${bh}`} style={{ position: 'absolute', left: -3, top: -3, overflow: 'visible', pointerEvents: 'none', opacity: beam1On ? 1 : 0.62, filter: `drop-shadow(0 0 6px ${AMBER}) drop-shadow(0 0 18px rgba(255,240,210,0.55))` }}>
                  <rect x={2} y={2} width={bw - 4} height={bh - 4} rx={RADIUS} fill="none" stroke={AMBER} strokeWidth={beam1On ? 5 : 3.5} strokeLinecap="round" pathLength={1} strokeDasharray="0.14 1" strokeDashoffset={-(beam1On ? beam1Prog : beam2Prog)} />
                  <rect x={2} y={2} width={bw - 4} height={bh - 4} rx={RADIUS} fill="none" stroke={BEAM_CORE} strokeWidth={beam1On ? 2.5 : 1.75} strokeLinecap="round" pathLength={1} strokeDasharray="0.14 1" strokeDashoffset={-(beam1On ? beam1Prog : beam2Prog)} />
                </svg>
              ) : null}
              {beamTrail > 0.01 ? <div style={{ position: 'absolute', inset: -3, borderRadius: RADIUS + 3, border: `1.5px solid ${AMBER}`, opacity: beamTrail, pointerEvents: 'none' }} /> : null}
            </div>
          </div>
        </PageCam2D>
        <AbsoluteFill style={{ background: `radial-gradient(${poolRx}px ${poolRy}px at ${spotX}% ${spotY}%, rgba(255,246,224,0.14), rgba(255,246,224,0.03) 45%, rgba(18,41,35,${(vignette + 0.14) * spotOn}) 100%)`, pointerEvents: 'none', opacity: spotOn }} />
      </AbsoluteFill>
      <Legenda de={58} ate={quadros - 4} y={900} texto={<>Talhão B · prioridade <Ambar>alta</Ambar> · regra <Ambar>R2</Ambar></>} />
    </AbsoluteFill>
  );
};
