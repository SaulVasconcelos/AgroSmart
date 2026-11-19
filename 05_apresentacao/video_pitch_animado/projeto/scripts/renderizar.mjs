// Renderiza o filme cena a cena (sem som) em out/cenas/sNN.mp4, com um único empacotamento.
// Uso: node scripts/renderizar.mjs            -> todas as cenas
//      node scripts/renderizar.mjs s05 s12    -> só as cenas pedidas
// O som é montado à parte por scripts/montar_som.py; scripts/juntar.sh junta tudo.
import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';
import path from 'node:path';
import fs from 'node:fs';

const raiz = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const dados = JSON.parse(fs.readFileSync(path.join(raiz, 'src/timeline.json'), 'utf8'));
const quadro = (b) => Math.round(b * dados.batida_s * dados.fps);
const navegador = process.env.REMOTION_CHROME || undefined;
const pedidas = process.argv.slice(2);
const serveUrl = await bundle({ entryPoint: path.join(raiz, 'src/index.ts'), publicDir: path.join(raiz, 'public') });
const composition = await selectComposition({ serveUrl, id: 'Pitch', browserExecutable: navegador, chromiumOptions: { gl: 'angle' } });
fs.mkdirSync(path.join(raiz, 'out/cenas'), { recursive: true });
for (const c of dados.cenas) {
  if (pedidas.length && !pedidas.includes(c.id)) continue;
  const de = quadro(c.b0), ate = quadro(c.b1) - 1;
  const t0 = Date.now();
  await renderMedia({
    composition, serveUrl, codec: 'h264', crf: Number(process.env.CRF || 16), pixelFormat: 'yuv420p', imageFormat: 'jpeg', jpegQuality: 95,
    outputLocation: path.join(raiz, 'out/cenas', `${c.id}.mp4`), frameRange: [de, ate], muted: true,
    concurrency: Number(process.env.NUCLEOS || 2),
    // limite do cache de quadros de vídeo da abertura: sem ele o processo passou de 3 GB e foi encerrado
    offthreadVideoCacheSizeInBytes: Number(process.env.CACHE_VIDEO_MB || 400) * 1024 * 1024, browserExecutable: navegador, chromiumOptions: { gl: 'angle' },
  });
  console.log(`${c.id} quadros ${de}-${ate} (${ate - de + 1}) em ${((Date.now() - t0) / 1000).toFixed(0)} s`);
}
