import time, torch, torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
torch.set_num_threads(8)
T = "Hacer un retrato con hilo y clavos parece fácil, hasta que intentas calcularlo. A mano, nadie puede saber cuál es el siguiente clavo."
m = ChatterboxMultilingualTTS.from_local("models/cb-es", "cpu", t3_model="t3_es_es.safetensors")
for name, ref in [("default", None), ("ref-davefx", "out/samples/piper-es_ES-davefx-medium.wav"), ("ref-sharvard", "out/samples/piper-es_ES-sharvard-medium.wav")]:
    t = time.time()
    w = m.generate(T, language_id="es", audio_prompt_path=ref, cfg_weight=0.5, exaggeration=0.5)
    ta.save(f"out/samples/cb-{name}.wav", w, m.sr); print(name, round(time.time()-t), "s", flush=True)
