"""Texto -> wav con la voz de style.md. Uso: tts.py guion.txt salida.wav
Genera frase a frase (una por línea) y deja una pausa natural entre ellas.
Escribe también salida.sentences.json con el inicio y fin de cada frase."""
import sys, json, torch, torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
torch.set_num_threads(8)
src, dst = sys.argv[1], sys.argv[2]
lines = [l.strip() for l in open(src, encoding="utf-8") if l.strip()]
m = ChatterboxMultilingualTTS.from_local("models/cb-es", "cpu", t3_model="t3_es_es.safetensors")
gap = torch.zeros(1, int(m.sr * 0.35))
parts, meta, t = [], [], 0.0
for i, l in enumerate(lines):
    w = m.generate(l, language_id="es", exaggeration=0.5, cfg_weight=0.5)
    # recorta silencio del principio y del final
    a = w[0]; idx = (a.abs() > 0.01).nonzero()
    if len(idx): a = a[max(0, idx[0].item() - 600): idx[-1].item() + 2400]
    d = a.shape[0] / m.sr
    meta.append({"text": l, "start": round(t, 3), "end": round(t + d, 3)})
    parts += [a[None], gap]; t += d + gap.shape[1] / m.sr
    print(f"{i+1}/{len(lines)}", flush=True)
ta.save(dst, torch.cat(parts[:-1], dim=1), m.sr)
json.dump(meta, open(dst.rsplit(".", 1)[0] + ".sentences.json", "w"), ensure_ascii=False, indent=1)
