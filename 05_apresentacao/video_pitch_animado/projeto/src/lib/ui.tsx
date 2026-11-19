// Peças de texto reutilizadas pelas cenas: legenda inferior, etiqueta e palco.
import React from 'react';
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from 'remotion';
import { COR, FONTE } from '../tema';

const SUAVE = Easing.bezier(0.2, 0.75, 0.3, 1);

/** Fundo de palco verde-escuro do AgroSmart, com um brilho discreto. */
export const Palco: React.FC<{ children?: React.ReactNode; brilho?: number }> = ({ children, brilho = 1 }) => (
  <AbsoluteFill style={{ background: `linear-gradient(170deg, #0f3a30 0%, ${COR.floresta} 45%, ${COR.florestaFunda} 100%)` }}>
    <div style={{ position: 'absolute', left: 360, top: 180, width: 1200, height: 640, opacity: 0.55 * brilho,
      background: 'radial-gradient(ellipse at center, rgba(47,143,95,0.38) 0%, rgba(47,143,95,0) 68%)', filter: 'blur(30px)' }} />
    <div style={{ position: 'absolute', right: 120, top: 120, width: 520, height: 300, opacity: 0.5 * brilho,
      background: 'radial-gradient(ellipse at center, rgba(242,198,109,0.16) 0%, rgba(242,198,109,0) 70%)', filter: 'blur(28px)' }} />
    {children}
  </AbsoluteFill>
);

/** Legenda inferior: entra subindo, sai apagando. `de`/`ate` em quadros da cena. */
export const Legenda: React.FC<{ texto: React.ReactNode; de: number; ate: number; y?: number; clara?: boolean; tamanho?: number }> = ({ texto, de, ate, y = 948, clara = false, tamanho = 36 }) => {
  const f = useCurrentFrame();
  const entra = interpolate(f, [de, de + 12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: SUAVE });
  const sai = interpolate(f, [ate - 10, ate], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  if (f < de || f > ate) return null;
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, top: y, display: 'flex', justifyContent: 'center', pointerEvents: 'none' }}>
      <div style={{
        padding: '16px 34px', borderRadius: 14, opacity: entra * sai, transform: `translateY(${(1 - entra) * 22}px)`,
        background: clara ? 'rgba(255,255,255,0.96)' : 'rgba(12,48,40,0.94)', color: clara ? COR.tinta : COR.branco,
        boxShadow: '0 14px 40px rgba(7,31,26,0.28)', border: clara ? `1px solid ${COR.linha}` : '1px solid rgba(193,217,203,0.22)',
        fontFamily: FONTE.ui, fontWeight: 600, fontSize: tamanho, letterSpacing: '-0.01em', whiteSpace: 'nowrap',
      }}>{texto}</div>
    </div>
  );
};

/** Destaque em âmbar dentro de uma legenda. */
export const Ambar: React.FC<{ children: React.ReactNode }> = ({ children }) => <span style={{ color: COR.ambar }}>{children}</span>;
