// Carrega as fontes do pacote (public/fonts) antes do primeiro quadro, para o texto nunca sair na fonte reserva.
import React, { useEffect, useState } from 'react';
import { continueRender, delayRender, staticFile } from 'remotion';

const ARQUIVOS: [string, number, string][] = [
  ['Inter', 400, 'inter-latin-400-normal.woff2'],
  ['Inter', 500, 'inter-latin-500-normal.woff2'],
  ['Inter', 600, 'inter-latin-600-normal.woff2'],
  ['Inter', 700, 'inter-latin-700-normal.woff2'],
  ['Inter', 800, 'inter-latin-800-normal.woff2'],
  ['Space Grotesk', 500, 'space-grotesk-latin-500-normal.woff2'],
  ['Space Grotesk', 600, 'space-grotesk-latin-600-normal.woff2'],
  ['Space Grotesk', 700, 'space-grotesk-latin-700-normal.woff2'],
  ['JetBrains Mono', 400, 'jetbrains-mono-latin-400-normal.woff2'],
  ['JetBrains Mono', 500, 'jetbrains-mono-latin-500-normal.woff2'],
  ['JetBrains Mono', 700, 'jetbrains-mono-latin-700-normal.woff2'],
];

let pronto: Promise<unknown> | null = null;
/** Promessa resolvida quando todas as fontes estão registradas (usada também por quem mede texto). */
export const carregarFontes = (): Promise<unknown> => {
  if (pronto) return pronto;
  if (typeof document === 'undefined') return (pronto = Promise.resolve());
  pronto = Promise.all(
    ARQUIVOS.map(([familia, peso, arquivo]) => {
      const f = new FontFace(familia, `url(${staticFile('fonts/' + arquivo)}) format('woff2')`, { weight: String(peso), style: 'normal' });
      return f.load().then((ok) => document.fonts.add(ok));
    }),
  ).catch((e) => console.error('fontes: falha ao carregar', String(e)));
  return pronto;
};

/**
 * Segura a renderização até as fontes carregarem. O pedido de espera é feito dentro do componente
 * (e não no carregamento do módulo): feito no módulo, o Remotion perde o controle dele e a
 * renderização longa cai por tempo esgotado.
 */
export const Fontes: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [espera] = useState(() => delayRender('fontes'));
  const [ok, setOk] = useState(false);
  useEffect(() => {
    carregarFontes().then(() => { setOk(true); continueRender(espera); });
  }, [espera]);
  return ok ? <>{children}</> : null;
};
