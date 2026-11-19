// Cena 1 — O problema. Abertura com imagens de lavoura geradas por IA (Gemini): plano aéreo,
// dois planos de sensor e uma foto de folha. Não usa cartão do video-shotcraft: é montagem
// simples, com as três etiquetas do roteiro entrando no ritmo da fala.
import React from 'react';
import { AbsoluteFill, Easing, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { COR, FONTE } from '../tema';
import { batidaF, seg } from '../timeline';

const SUAVE = Easing.bezier(0.2, 0.75, 0.3, 1);
const cl = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;

// Trechos, em batidas da trilha (cortes em tempos fortes).
const T = { sensor: batidaF(12), folha: batidaF(18), separados: batidaF(24), alerta: batidaF(36), fim: batidaF(56) };
// A fala desta cena começa em 1,45 s; as etiquetas entram junto das frases correspondentes.
const ETIQUETAS = [
  { texto: 'Dados separados', em: seg(11.75) },
  { texto: 'Alerta sem explicação', em: seg(18.1) },
  { texto: 'Falta de dado vira “normal”', em: seg(21.7) },
];
const ESCURECE = [seg(23.4), seg(25.3)];

const Foto: React.FC<{ de: number; dur: number; zoom?: [number, number]; origem?: string }> = ({ de, dur, zoom = [1.04, 1.12], origem = '42% 55%' }) => {
  const f = useCurrentFrame();
  const s = interpolate(f, [de, de + dur], zoom, cl);
  return <Img src={staticFile('clips/folha.jpg')} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${s})`, transformOrigin: origem }} />;
};

export const S01Abertura: React.FC = () => {
  const f = useCurrentFrame();
  const abre = interpolate(f, [0, 20], [1, 0], cl);
  const escuro = interpolate(f, ESCURECE, [0, 1], { ...cl, easing: Easing.bezier(0.4, 0, 0.3, 1) });
  const some = interpolate(f, [T.fim - 20, T.fim - 4], [1, 0], cl);
  // tela dividida: a fresta abre quando a fala diz "ficam separadas"
  const fresta = interpolate(f, [T.separados, T.separados + 16], [0, 34], { ...cl, easing: SUAVE });

  return (
    <AbsoluteFill style={{ backgroundColor: COR.floresta }}>
      <Sequence from={0} durationInFrames={T.sensor}>
        <OffthreadVideo src={staticFile('clips/aerea.mp4')} muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </Sequence>
      <Sequence from={T.sensor} durationInFrames={T.folha - T.sensor}>
        <OffthreadVideo src={staticFile('clips/sensor.mp4')} muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </Sequence>
      {f >= T.folha && f < T.separados ? <Foto de={T.folha} dur={T.separados - T.folha} /> : null}

      {f >= T.separados && f < T.alerta ? (
        <AbsoluteFill style={{ backgroundColor: COR.floresta }}>
          <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 960 - fresta / 2, overflow: 'hidden' }}>
            <Sequence from={T.separados} layout="none">
              <OffthreadVideo src={staticFile('clips/sensor.mp4')} muted startFrom={64}
                style={{ position: 'absolute', left: -480, top: 0, width: 1920, height: 1080, objectFit: 'cover' }} />
            </Sequence>
          </div>
          <div style={{ position: 'absolute', right: 0, top: 0, bottom: 0, width: 960 - fresta / 2, overflow: 'hidden' }}>
            <div style={{ position: 'absolute', right: -330, top: 0, width: 1920, height: 1080 }}>
              <Foto de={T.separados} dur={T.alerta - T.separados} zoom={[1.1, 1.16]} />
            </div>
          </div>
        </AbsoluteFill>
      ) : null}

      <Sequence from={T.alerta} durationInFrames={T.fim - T.alerta}>
        <OffthreadVideo src={staticFile('clips/sensor2.mp4')} muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </Sequence>

      {/* leitura: escurece embaixo e à esquerda, onde ficam as etiquetas */}
      <AbsoluteFill style={{ background: 'linear-gradient(90deg, rgba(7,31,26,0.62) 0%, rgba(7,31,26,0.18) 46%, rgba(7,31,26,0) 70%), linear-gradient(0deg, rgba(7,31,26,0.55) 0%, rgba(7,31,26,0) 34%)', opacity: interpolate(f, [T.separados - 6, T.separados + 10], [0.35, 1], cl) }} />
      {/* passagem para o palco da marca */}
      <AbsoluteFill style={{ background: `linear-gradient(170deg, #0f3a30 0%, ${COR.floresta} 45%, ${COR.florestaFunda} 100%)`, opacity: escuro }} />
      <AbsoluteFill style={{ backgroundColor: COR.floresta, opacity: abre }} />

      {/* etiquetas do roteiro, uma a uma */}
      <div style={{ position: 'absolute', left: 120, top: 380, display: 'flex', flexDirection: 'column', gap: 26, opacity: some }}>
        {ETIQUETAS.map((e, i) => {
          const t = interpolate(f, [e.em, e.em + 12], [0, 1], { ...cl, easing: SUAVE });
          if (f < e.em) return null;
          const atual = i === ETIQUETAS.length - 1 || f < ETIQUETAS[i + 1].em;
          const forca = atual ? 1 : interpolate(f, [ETIQUETAS[i + 1].em, ETIQUETAS[i + 1].em + 12], [1, 0.5], cl);
          return (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 22, opacity: t * forca, transform: `translateX(${(1 - t) * -36}px)`, filter: `blur(${(1 - t) * 6}px)` }}>
              <div style={{ width: 8, height: 62, borderRadius: 4, background: COR.ambar }} />
              <div style={{ fontFamily: FONTE.titulo, fontWeight: 700, fontSize: 68, lineHeight: 1.05, letterSpacing: '-0.02em', color: COR.branco, textShadow: '0 4px 28px rgba(7,31,26,0.55)' }}>{e.texto}</div>
            </div>
          );
        })}
      </div>

      {/* aviso obrigatório do roteiro */}
      <div style={{ position: 'absolute', right: 44, bottom: 36, padding: '8px 16px', borderRadius: 8, background: 'rgba(7,31,26,0.62)', color: 'rgba(255,255,255,0.86)', fontFamily: FONTE.ui, fontWeight: 500, fontSize: 22, letterSpacing: '0.01em', opacity: (1 - abre) * (1 - escuro) }}>
        Imagens ilustrativas geradas por IA
      </div>
    </AbsoluteFill>
  );
};
