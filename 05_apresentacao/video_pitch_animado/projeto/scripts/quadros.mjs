// Renderiza vários quadros de conferência com um único empacotamento.
// Uso: node scripts/quadros.mjs s02:40 s02:120 Pitch:900 ...   (saída em out/qa/<comp>_<quadro>.jpg)
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import path from 'node:path';
import fs from 'node:fs';

const raiz = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const navegador = process.env.REMOTION_CHROME || undefined;
const escala = Number(process.env.ESCALA || 0.5);
const serveUrl = await bundle({ entryPoint: path.join(raiz, 'src/index.ts'), publicDir: path.join(raiz, 'public') });
fs.mkdirSync(path.join(raiz, 'out/qa'), { recursive: true });
const cache = {};
for (const item of process.argv.slice(2)) {
  const [id, q] = item.split(':');
  cache[id] ??= await selectComposition({ serveUrl, id, browserExecutable: navegador, chromiumOptions: { gl: 'angle' } });
  const saida = path.join(raiz, 'out/qa', `${id}_${String(q).padStart(4, '0')}.jpg`);
  await renderStill({ composition: cache[id], serveUrl, output: saida, frame: Number(q), imageFormat: 'jpeg', jpegQuality: 86, scale: escala, browserExecutable: navegador, chromiumOptions: { gl: 'angle' } });
  console.log('ok', saida);
}
