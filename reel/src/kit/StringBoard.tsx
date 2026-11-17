import React, {useLayoutEffect, useRef} from 'react';
import {C} from './theme';

/** Tablero circular con clavos y un hilo que va de clavo a clavo (canvas: miles de líneas por frame). */
export const StringBoard: React.FC<{
  size: number; nails: number; sequence: number[];
  lines: number;                 // cuántas líneas se ven (puede tener decimales)
  threadAlpha?: number;          // opacidad del hilo
  highlight?: number | null;     // índice de una línea para pintar en acento
  candidates?: number[];         // clavos candidatos (líneas punteadas desde el clavo actual)
  nailsShown?: number;           // 0..1 para que los clavos aparezcan
  glowNail?: number | null;
}> = ({size, nails, sequence, lines, threadAlpha = 0.16, highlight = null, candidates = [], nailsShown = 1, glowNail = null}) => {
  const ref = useRef<HTMLCanvasElement>(null);
  useLayoutEffect(() => {
    const cv = ref.current!;
    const g = cv.getContext('2d')!;
    const S = size * 2; // retina
    g.clearRect(0, 0, S, S);
    const R = S / 2 - 10;
    const pt = (i: number) => {
      const a = (i / nails) * 2 * Math.PI - Math.PI / 2;
      return [S / 2 + R * Math.cos(a), S / 2 + R * Math.sin(a)];
    };
    // tablero
    g.fillStyle = C.board; g.beginPath(); g.arc(S / 2, S / 2, S / 2 - 2, 0, 2 * Math.PI); g.fill();
    // hilo
    const full = Math.floor(lines);
    g.strokeStyle = `rgba(29,24,56,${threadAlpha})`; g.lineWidth = 1.6;
    // una pasada por línea: así las que se cruzan se oscurecen, como el hilo de verdad
    for (let i = 0; i < Math.min(full, sequence.length - 1); i++) {
      const [x1, y1] = pt(sequence[i]); const [x2, y2] = pt(sequence[i + 1]);
      g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke();
    }
    // la línea que se está tendiendo (parcial), más marcada
    if (full < sequence.length - 1 && lines > 0) {
      const f = lines - full;
      const [x1, y1] = pt(sequence[full]); const [x2, y2] = pt(sequence[full + 1]);
      g.strokeStyle = C.bg; g.lineWidth = 3;
      g.beginPath(); g.moveTo(x1, y1); g.lineTo(x1 + (x2 - x1) * f, y1 + (y2 - y1) * f); g.stroke();
    }
    // candidatas (punteadas)
    if (candidates.length) {
      const [cx, cy] = pt(sequence[Math.min(full, sequence.length - 1)]);
      g.setLineDash([18, 12]); g.lineWidth = 8; g.strokeStyle = C.accent;
      candidates.forEach((c) => { const [x, y] = pt(c); g.beginPath(); g.moveTo(cx, cy); g.lineTo(x, y); g.stroke(); });
      g.setLineDash([]);
    }
    // línea resaltada
    if (highlight != null && highlight < sequence.length - 1) {
      const [x1, y1] = pt(sequence[highlight]); const [x2, y2] = pt(sequence[highlight + 1]);
      g.strokeStyle = C.accent; g.lineWidth = 7; g.lineCap = 'round';
      g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke();
    }
    // clavos
    const shown = Math.round(nails * nailsShown);
    g.fillStyle = C.bg;
    for (let i = 0; i < shown; i++) { const [x, y] = pt(i); g.beginPath(); g.arc(x, y, 3.2, 0, 2 * Math.PI); g.fill(); }
    if (glowNail != null) {
      const [x, y] = pt(glowNail); g.fillStyle = C.accent;
      g.beginPath(); g.arc(x, y, 14, 0, 2 * Math.PI); g.fill();
    }
  });
  return <canvas ref={ref} width={size * 2} height={size * 2} style={{width: size, height: size, display: 'block'}} />;
};
