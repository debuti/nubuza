"""Efectos cortos generados en código (sin descargas). Uso: sfx.py carpeta"""
import sys, numpy as np, soundfile as sf
SR = 44100; d = sys.argv[1]
def env(n, a=0.002, r=0.08):
    t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / r)
def save(name, x): sf.write(f"{d}/{name}.wav", (x / np.abs(x).max() * 0.8).astype(np.float32), SR)
n = int(0.12 * SR); t = np.arange(n) / SR
save("pop", np.sin(2 * np.pi * (900 - 2500 * t) * t) * env(n, 0.001, 0.03))
n = int(0.05 * SR); t = np.arange(n) / SR
save("tick", np.sin(2 * np.pi * 2400 * t) * env(n, 0.0005, 0.008) + 0.3 * np.random.randn(n) * env(n, 0.0005, 0.004))
n = int(0.45 * SR); t = np.arange(n) / SR; noise = np.random.randn(n)
k = np.ones(40) / 40; noise = np.convolve(noise, k, "same")
save("whoosh", noise * np.sin(np.pi * t / t[-1]) ** 2)
n = int(0.7 * SR); t = np.arange(n) / SR
save("ding", (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 1976 * t)) * env(n, 0.002, 0.25))
n = int(0.25 * SR); t = np.arange(n) / SR
save("pluck", np.sin(2 * np.pi * 220 * t) * np.sign(np.sin(2 * np.pi * 110 * t)) * 0.4 * env(n, 0.001, 0.06) + np.sin(2*np.pi*440*t)*env(n,0.001,0.08))
