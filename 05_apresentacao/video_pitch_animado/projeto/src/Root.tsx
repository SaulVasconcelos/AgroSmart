import React from 'react';
import { AbsoluteFill, Composition } from 'remotion';
import { CENAS, FPS, H, TOTAL, W } from './timeline';
import { Filme, conteudo } from './Filme';
import { Fontes } from './fontes';

export const Root: React.FC = () => (
  <>
    <Composition id="Pitch" component={Filme} durationInFrames={TOTAL} fps={FPS} width={W} height={H} />
    {/* uma composição por cena, para conferir quadros isolados */}
    {CENAS.map((c) => (
      <Composition key={c.id} id={c.id} component={() => <AbsoluteFill><Fontes>{conteudo(c.id)}</Fontes></AbsoluteFill>} durationInFrames={c.quadros} fps={FPS} width={W} height={H} />
    ))}
  </>
);
