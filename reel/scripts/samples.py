import wave, numpy as np, soundfile as sf, io
from kokoro_onnx import Kokoro
from piper import PiperVoice
T = "¿Alguna vez has intentado hacer un retrato con hilo? Calcular por dónde pasa cada vuelta es imposible a mano."
N = ["uno","dos","tres","cuatro","cinco","seis","siete"]
SR = 24000
out = []
def rs(a, sr):
    if sr == SR: return a
    x = np.linspace(0, len(a)-1, int(len(a)*SR/sr)); return np.interp(x, np.arange(len(a)), a)
k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
i = 0
for v in ["ef_dora", "em_alex", "em_santa"]:
    a, sr = k.create(f"Voz {N[i]}. {T}", voice=v, speed=1.05, lang="es"); out += [rs(a, sr), np.zeros(SR)]; i += 1
for v in ["es_ES-davefx-medium", "es_ES-sharvard-medium", "es_MX-claude-high", "es_MX-ald-medium"]:
    pv = PiperVoice.load(f"models/{v}.onnx"); b = io.BytesIO()
    with wave.open(b, "wb") as w: pv.synthesize_wav(f"Voz {N[i]}. {T}", w)
    b.seek(0); a, sr = sf.read(b); out += [rs(a, sr), np.zeros(SR)]; i += 1
sf.write("out/samples/todas.wav", np.concatenate(out), SR)
