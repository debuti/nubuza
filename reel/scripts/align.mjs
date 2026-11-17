// Uso: node scripts/align.mjs voz.wav guion.txt salida.json
// Tiempos de cada palabra del guion: Whisper da los tiempos, el guion da las palabras.
import fs from 'node:fs';
import path from 'node:path';
import {execSync} from 'node:child_process';
import {transcribe} from '@remotion/install-whisper-cpp';

const [audio, script, out] = process.argv.slice(2);
const whisperPath = path.resolve('models/whisper.cpp');
const wav16 = out.replace(/\.json$/, '.16k.wav');
execSync(`ffmpeg -loglevel error -y -i ${audio} -ar 16000 -ac 1 ${wav16}`);
const res = await transcribe({
  inputPath: path.resolve(wav16), whisperPath, whisperCppVersion: '1.5.5', model: 'medium',
  tokenLevelTimestamps: true, language: 'es', splitOnWord: true,
});
fs.unlinkSync(wav16);
// palabras de Whisper con tiempos
const heard = [];
for (const seg of res.transcription) for (const t of seg.tokens) {
  const txt = t.text; if (/^\[_/.test(txt.trim()) || !txt.trim()) continue;
  const s = t.offsets.from / 1000, e = t.offsets.to / 1000;
  if (txt.startsWith(' ') || heard.length === 0) heard.push({w: txt.trim(), s, e});
  else {const h = heard[heard.length - 1]; h.w += txt; h.e = e;}
}
const norm = (w) => w.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-zñ0-9]/g, '');
const lines = fs.readFileSync(script, 'utf8').split('\n').map((l) => l.trim()).filter(Boolean);
const words = [];
lines.forEach((l, si) => l.split(/\s+/).forEach((w) => words.push({text: w, sentence: si})));
// alineado por programación dinámica (Levenshtein entre listas de palabras)
const A = words.map((w) => norm(w.text)), B = heard.map((h) => norm(h.w));
const n = A.length, m = B.length, D = [...Array(n + 1)].map(() => Array(m + 1).fill(0));
for (let i = 0; i <= n; i++) D[i][0] = i; for (let j = 0; j <= m; j++) D[0][j] = j;
for (let i = 1; i <= n; i++) for (let j = 1; j <= m; j++)
  D[i][j] = Math.min(D[i - 1][j] + 1, D[i][j - 1] + 1, D[i - 1][j - 1] + (A[i - 1] === B[j - 1] ? 0 : 1));
let i = n, j = m;
while (i > 0 && j > 0) {
  if (D[i][j] === D[i - 1][j - 1] + (A[i - 1] === B[j - 1] ? 0 : 1)) {words[i - 1].start = heard[j - 1].s; words[i - 1].end = heard[j - 1].e; words[i - 1].match = A[i - 1] === B[j - 1]; i--; j--;}
  else if (D[i][j] === D[i - 1][j] + 1) i--; else j--;
}
// rellena las que no casaron interpolando entre vecinas
for (let k = 0; k < n; k++) if (words[k].start == null) {
  const prev = words.slice(0, k).reverse().find((w) => w.start != null);
  const next = words.slice(k + 1).find((w) => w.start != null);
  words[k].start = prev ? prev.end : 0; words[k].end = next ? next.start : words[k].start + 0.3;
}
const matched = words.filter((w) => w.match).length;
fs.writeFileSync(out, JSON.stringify(words.map(({text, sentence, start, end}) => ({text, sentence, start: +start.toFixed(3), end: +end.toFixed(3)})), null, 1));
console.log(`palabras: ${n}, casadas exactas: ${matched}, oídas: ${m}`);
