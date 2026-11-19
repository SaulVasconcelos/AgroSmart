// Cena 14 — Proposta de valor. Cartão `lead-word-zoom-assemble` do video-shotcraft
// (demos/typography/lead-word-zoom-assemble/LeadWordZoomAssemble.tsx): a primeira palavra entra
// a 2,3x no centro, avança mais 6% enquanto fica parada 12 quadros, e uma única curva faz ao
// mesmo tempo o recuo ao tamanho final (12 quadros) e o deslize da linha para o lugar (24); as
// outras palavras são empurradas de 0,5 em à direita, com 4 quadros de defasagem; a linha sobe
// 56 px no mesmo intervalo em que a linha de apoio aparece. O pivô fica preso no centro da
// primeira palavra e na linha de base, medidos na montagem — é o que impede a linha de tremer.
// Mantidos esses valores e as três curvas. Adaptado: letra e cores do AgroSmart, corpo menor
// para a frase caber em 1920 px, "e por quê." empurrado quando a fala chega nele, e o final é
// parada e saída suave (a ampliação brusca do cartão é meia transição, não fecho).
import React, { Fragment, useEffect, useRef, useState } from 'react';
import { AbsoluteFill, continueRender, delayRender, Easing, interpolate, useCurrentFrame } from 'remotion';
import { COR, FONTE } from '../tema';
import { Palco } from '../lib/ui';
import { carregarFontes } from '../fontes';

const PALAVRAS = ['Saber', 'onde', 'olhar', 'primeiro', 'na', 'lavoura,', 'e por quê.'];
const DESTAQUE = 'e por quê.';
const FONT_SIZE = 78;
const INITIAL_SCALE = 2.3, INTRO_DURATION = 6, HOLD_DURATION = 12, PUSH_SCALE = 1.06;
const RECEDE_DURATION = 12, ASSEMBLE_DURATION = 24, WORD_DELAY = 6, WORD_STAGGER = 4, WORD_DURATION = 12, WORD_PUSH = 0.5, WORD_FADE = 2;
const LIFT: [number, number] = [34, 50];
const LIFT_DISTANCE = -56;
const PUSH_EASE = Easing.bezier(0.25, 1, 0.5, 1);
const ZOOM_EASE = Easing.bezier(0.5, 0, 0.05, 1);
const WORD_EASE = Easing.bezier(0.22, 0.8, 0.36, 1);
const cl = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;

const Frase: React.FC<{ frame: number; ultimaEm: number }> = ({ frame, ultimaEm }) => {
  const lineRef = useRef<HTMLSpanElement>(null);
  const leadRef = useRef<HTMLSpanElement>(null);
  const baselineRef = useRef<HTMLSpanElement>(null);
  const [handle] = useState(() => delayRender('S14: medir a linha'));
  const [m, setM] = useState<{ lineWidth: number; leadRatio: number; baseline: number } | null>(null);
  useEffect(() => {
    // mede só depois de as fontes estarem carregadas: com a fonte reserva o pivô sairia errado
    carregarFontes().then(() => document.fonts.ready).then(() => {
      const line = lineRef.current, lead = leadRef.current;
      if (!line || !lead) { continueRender(handle); return; }
      setM({ lineWidth: line.offsetWidth, leadRatio: (lead.offsetLeft + lead.offsetWidth / 2) / line.offsetWidth, baseline: baselineRef.current?.offsetTop ?? line.offsetHeight * 0.8 });
    });
  }, [handle]);
  useEffect(() => { if (m) continueRender(handle); }, [m, handle]);

  const leadRatio = m?.leadRatio ?? 0.08;
  const lineWidth = m?.lineWidth ?? 1700;
  const baseline = m?.baseline ?? FONT_SIZE * 0.88;
  const zoomStart = HOLD_DURATION;
  const slideDistance = lineWidth * (0.5 - leadRatio);
  return (
    <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
      <span ref={lineRef} style={{
        position: 'relative', display: 'inline-block', fontSize: FONT_SIZE, fontWeight: 600, color: COR.branco, letterSpacing: '-0.03em', lineHeight: 1.1, whiteSpace: 'nowrap', fontFamily: FONTE.titulo,
        transformOrigin: `${leadRatio * 100}% ${baseline}px`,
        scale: String(interpolate(frame, [0, HOLD_DURATION], [INITIAL_SCALE, INITIAL_SCALE * PUSH_SCALE], { ...cl, easing: PUSH_EASE })
          + interpolate(frame, [zoomStart, zoomStart + RECEDE_DURATION], [0, 1 - INITIAL_SCALE * PUSH_SCALE], { ...cl, easing: ZOOM_EASE })),
        translate: `${interpolate(frame, [zoomStart, zoomStart + ASSEMBLE_DURATION], [slideDistance, 0], { ...cl, easing: ZOOM_EASE })}px`,
        opacity: m && frame >= 0 ? 1 : 0, textRendering: 'geometricPrecision',
      }}>
        {PALAVRAS.map((word, i) => {
          const isLead = i === 0;
          const ultima = i === PALAVRAS.length - 1;
          const pushStart = ultima ? ultimaEm : zoomStart + WORD_DELAY + (i - 1) * WORD_STAGGER;
          const opacity = isLead ? interpolate(frame, [0, INTRO_DURATION], [0, 1], cl) : interpolate(frame, [pushStart, pushStart + WORD_FADE], [0, 1], cl);
          return (
            <Fragment key={i}>
              <span ref={isLead ? leadRef : undefined} style={{ display: 'inline-block', opacity, color: word === DESTAQUE ? COR.ambar : undefined,
                translate: isLead ? undefined : `${interpolate(frame, [pushStart, pushStart + WORD_DURATION], [WORD_PUSH * FONT_SIZE, 0], { ...cl, easing: WORD_EASE })}px` }}>{word}</span>
              {i < PALAVRAS.length - 1 ? ' ' : null}
            </Fragment>
          );
        })}
        <span ref={baselineRef} style={{ display: 'inline-block', width: 0, height: 0 }} />
      </span>
    </AbsoluteFill>
  );
};

export const S14Valor: React.FC<{ quadros: number; inicio: number; porque: number }> = ({ quadros, inicio, porque }) => {
  const frame = useCurrentFrame();
  const f = frame - inicio; // o cartão começa quando a fala diz "saber"
  const lift = interpolate(f, LIFT, [0, 1], { ...cl, easing: Easing.out(Easing.cubic) });
  const rotulo = interpolate(frame, [4, 16], [0, 1], { ...cl, easing: Easing.bezier(0.2, 0.75, 0.3, 1) });
  const rotuloSobe = interpolate(f, [0, 10], [0, 1], { ...cl, easing: Easing.out(Easing.cubic) });
  const sai = interpolate(frame, [quadros - 12, quadros], [1, 0], cl);
  const entra = 1; // corte seco; só o texto sai suave no fim
  return (
    <Palco>
      <AbsoluteFill style={{ opacity: sai * entra }}>
        {/* antes da frase: o nome do item do pitch, que a fala anuncia */}
        <div style={{ position: 'absolute', left: 0, right: 0, top: 540 - 30 - rotuloSobe * 250, textAlign: 'center', fontFamily: FONTE.ui, fontWeight: 600, fontSize: 34, letterSpacing: '0.18em', textTransform: 'uppercase', color: COR.ambar, opacity: rotulo, transform: `translateY(${(1 - rotulo) * 16}px)` }}>
          A nossa proposta de valor
        </div>
        <AbsoluteFill style={{ transform: `translateY(${lift * LIFT_DISTANCE}px)` }}>
          <Frase frame={f} ultimaEm={porque - inicio} />
        </AbsoluteFill>
        <div style={{ position: 'absolute', left: 0, right: 0, top: '50%', marginTop: 62, textAlign: 'center', fontFamily: FONTE.ui, fontWeight: 500, fontSize: 34, color: COR.menta, opacity: lift, transform: `translateY(${(1 - lift) * 16}px)` }}>
          AgroMonitor · módulo do AgroSmart
        </div>
      </AbsoluteFill>
    </Palco>
  );
};
