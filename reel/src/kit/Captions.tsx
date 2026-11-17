import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {C, fontFamily} from './theme';
import {pop} from './motion';

export type Word = {text: string; sentence: number; start: number; end: number};
// Palabras tras las que no se corta la línea en español
const GLUE = new Set(['el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'a', 'al', 'en', 'con', 'por', 'para', 'y', 'o', 'que', 'se', 'te', 'tu', 'mi', 'su', 'lo', 'sin', 'es', 'nunca', 'cada']);

/** Agrupa en líneas de 2 a 5 palabras: corta en puntuación y nunca tras un artículo o preposición. */
export const toLines = (words: Word[], max = 4): Word[][] => {
  const lines: Word[][] = [];
  let cur: Word[] = [];
  const flush = () => { if (cur.length) lines.push(cur); cur = []; };
  words.forEach((w, i) => {
    const next = words[i + 1];
    cur.push(w);
    const bare = w.text.toLowerCase().replace(/[^a-záéíóúñü]/g, '');
    const sentenceEnd = !next || next.sentence !== w.sentence;
    const punct = /[,:;]$/.test(w.text);
    if (sentenceEnd) {
      // no dejar una palabra sola al final de la frase
      const prev = lines[lines.length - 1];
      if (cur.length === 1 && prev && prev[0].sentence === w.sentence && prev.length < 5) prev.push(w), (cur = []);
      flush();
    } else if ((punct && cur.length >= 2) || (cur.length >= max && !GLUE.has(bare))) flush();
  });
  flush();
  return lines;
};

export const Captions: React.FC<{words: Word[]; y: number; size?: number}> = ({words, y, size = 62}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const lines = toLines(words);
  const idx = lines.findIndex((l, i) => t >= l[0].start - 0.05 && (i === lines.length - 1 || t < lines[i + 1][0].start - 0.05));
  if (idx < 0) return null;
  const line = lines[idx];
  const last = line[line.length - 1];
  if (t > last.end + 1.2) return null;
  const k = pop(frame, fps, line[0].start - 0.05, 16);
  return (
    <div style={{position: 'absolute', left: 150, right: 150, top: y, textAlign: 'center', fontFamily, fontWeight: 600,
      fontSize: size, lineHeight: 1.15, color: C.text, scale: `${0.92 + 0.08 * k}`, opacity: k}}>
      {line.map((w, i) => {
        const on = t >= w.start - 0.03;
        const now = on && (t < w.end + 0.05 || i === line.length - 1);
        return (
          <span key={i} style={{color: now ? C.accent : on ? C.text : C.soft, marginRight: '0.28em'}}>{w.text}</span>
        );
      })}
    </div>
  );
};
