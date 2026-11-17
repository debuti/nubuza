"""Calcula un retrato de hilo (greedy) a partir de una imagen.
Uso: stringart.py imagen.jpg cx cy r clavos lineas salida.json [preview.png]"""
import sys, json, numpy as np
from PIL import Image, ImageOps, ImageDraw
img, cx, cy, r, N, L, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
S = 400
im = Image.open(img).convert("L").crop((cx - r, cy - r, cx + r, cy + r)).resize((S, S))
im = ImageOps.autocontrast(im, cutoff=1)
dark = (np.asarray(im, dtype=np.float32) / 255)  # hilo claro sobre fondo oscuro: 1 = claro (necesita hilo)
if len(sys.argv) > 9 and sys.argv[9] == "dark": dark = 1 - dark
yy, xx = np.mgrid[:S, :S]; mask = (xx - S / 2) ** 2 + (yy - S / 2) ** 2 <= (S / 2 - 1) ** 2
dark *= mask
ang = np.arange(N) * 2 * np.pi / N - np.pi / 2
px = (S / 2 + (S / 2 - 1) * np.cos(ang)); py = (S / 2 + (S / 2 - 1) * np.sin(ang))
cache = {}
def line(a, b):
    k = (min(a, b), max(a, b))
    if k not in cache:
        n = int(np.hypot(px[a] - px[b], py[a] - py[b])) + 1
        x = np.linspace(px[a], px[b], n).round().astype(int).clip(0, S - 1)
        y = np.linspace(py[a], py[b], n).round().astype(int).clip(0, S - 1)
        cache[k] = np.unique(y * S + x)
    return cache[k]
flat = dark.ravel().copy(); seq = [0]; cur = 0; W = float(__import__("os").environ.get("SA_W", "0.3")); recent = []
for _ in range(L):
    best, bs = None, -1
    for c in range(N):
        d = min(abs(c - cur), N - abs(c - cur))
        if d < 15 or c in recent: continue
        idx = line(cur, c); s = flat[idx].mean()
        if s > bs: bs, best = s, c
    idx = line(cur, best); flat[idx] = np.maximum(flat[idx] - W, 0)
    seq.append(best); recent = (recent + [cur])[-20:]; cur = best
json.dump({"nails": N, "sequence": seq}, open(out, "w"))
if len(sys.argv) > 8:
    P = 800; f = P / S; acc = np.zeros((P, P), np.float32)
    for a, b in zip(seq, seq[1:]):
        n = int(np.hypot(px[a] - px[b], py[a] - py[b]) * f) + 1
        x = np.linspace(px[a] * f, px[b] * f, n).astype(int).clip(0, P - 1); y = np.linspace(py[a] * f, py[b] * f, n).astype(int).clip(0, P - 1)
        acc[y, x] += 0.13
    Image.fromarray(((1 - np.clip(acc, 0, 1)) * 255).astype(np.uint8)).save(sys.argv[8])
print("ok", len(seq))
