// O filme inteiro: cada cena ocupa o intervalo de batidas definido em timeline.json.
import React from 'react';
import { AbsoluteFill, Sequence } from 'remotion';
import { CENAS, cena, seg, CenaId } from './timeline';
import { Fontes } from './fontes';
import { COR } from './tema';
import { S01Abertura } from './shots/S01Abertura';
import { S02Marca } from './shots/S02Marca';
import { S03Publico } from './shots/S03Publico';
import { S04VisaoGeral } from './shots/S04VisaoGeral';
import { S05TalhaoB } from './shots/S05TalhaoB';
import { CartaoTexto } from './shots/CartaoTexto';
import { S07AntesDepois } from './shots/S07AntesDepois';
import { S08Porque } from './shots/S08Porque';
import { S09EventLog } from './shots/S09EventLog';
import { S11Comando } from './shots/S11Comando';
import { S12Qualidade } from './shots/S12Qualidade';
import { S13Estagio } from './shots/S13Estagio';
import { S14Valor } from './shots/S14Valor';
import { S15Encerramento } from './shots/S15Encerramento';

// Quadro, dentro da cena, em que um ponto da fala acontece (segundos contados do início da fala da cena).
const naFala = (id: CenaId, s: number) => cena(id).falaEm + seg(s);

export const conteudo = (id: CenaId): React.ReactNode => {
  const q = cena(id).quadros;
  switch (id) {
    case 's01': return <S01Abertura />;
    case 's02': return <S02Marca quadros={q} />;
    // "o produtor rural" 2,43 s · "o agrônomo" 3,49 s · "e o gestor da operação" 4,20 s depois do início da fala
    case 's03': return <S03Publico quadros={q} entradas={[naFala('s03', 2.33), naFala('s03', 3.45), naFala('s03', 4.2)]} />;
    case 's04': return <S04VisaoGeral quadros={q} />;
    case 's05': return <S05TalhaoB quadros={q} />;
    case 's06': return <CartaoTexto quadros={q} palavras={[{ texto: 'E' }, { texto: 'quando' }, { texto: 'falta', destaque: true }, { texto: 'dado?' }]} />;
    // a segunda frase ("Registrada a observação...") começa 4,95 s depois do início da fala
    case 's07': return <S07AntesDepois quadros={q} arremesso={naFala('s07', 4.95)} />;
    // "a regra aplicada" 2,27 s · "a evidência usada" 3,36 s · "e a orientação sugerida" 4,63 s
    case 's08': return <S08Porque quadros={q} gatilhos={[naFala('s08', 2.27), naFala('s08', 3.36), naFala('s08', 4.63)]} />;
    // "da entrada recebida" começa 2,81 s depois do início da fala; a fala termina em 5,87 s
    case 's09': return <S09EventLog quadros={q} partida={naFala('s09', 1.6)} chegada={naFala('s09', 5.5)} />;
    case 's10': return <CartaoTexto quadros={q} palavras={[{ texto: 'E' }, { texto: 'roda' }, { texto: 'sozinho.', destaque: true }]} />;
    case 's11': return <S11Comando quadros={q} />;
    // "22 de 22 verificações" 3,39 s · "e nenhuma vulnerabilidade" 6,4 s depois do início da fala
    case 's12': return <S12Qualidade quadros={q} linhas={[naFala('s12', 3.39), naFala('s12', 6.4)]} nota={naFala('s12', 8.6)} />;
    // as três frases da fala começam em 0 s, 2,25 s e 4,01 s
    case 's13': return <S13Estagio quadros={q} viradas={[naFala('s13', 0.1), naFala('s13', 2.3), naFala('s13', 4.05)]} />;
    // "saber" 1,81 s · "e por quê" 4,38 s depois do início da fala
    case 's14': return <S14Valor quadros={q} inicio={naFala('s14', 1.78)} porque={naFala('s14', 4.3)} />;
    // "no nosso repositório" ~3,9 s depois do início da fala
    case 's15': return <S15Encerramento quadros={q} endereco={naFala('s15', 3.6)} />;
    default: return <AbsoluteFill style={{ backgroundColor: COR.floresta }} />;
  }
};

export const Filme: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: COR.floresta }}>
    <Fontes>
      {CENAS.map((c) => (
        <Sequence key={c.id} from={c.de} durationInFrames={c.quadros} name={`${c.id} · ${c.nome}`}>
          {conteudo(c.id)}
        </Sequence>
      ))}
    </Fontes>
  </AbsoluteFill>
);
