"""Baixa o modelo da voz local Kokoro e grava uma fala de teste.

    venv\\Scripts\\python.exe -m pip install kokoro-onnx
    venv\\Scripts\\python.exe -X utf8 -m tests.prepare_kokoro

Arquivos (cerca de 340 MB) vão para models/kokoro/. O teste grava
logs/kokoro_teste.wav com as três vozes em português, para você comparar.
"""
import os
import time

import requests

from core.settings import KOKORO_DIR, KOKORO_LANG, KOKORO_SPEED

BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/"
FILES = ["kokoro-v1.0.onnx", "voices-v1.0.bin"]


def download(name):
    path = os.path.join(KOKORO_DIR, name)
    if os.path.isfile(path) and os.path.getsize(path) > 1_000_000:
        print(f"[KOKORO] {name} já existe.")
        return path
    partial = path + ".part"
    with requests.get(BASE + name, stream=True, timeout=(10, 60)) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        done, last = 0, -1
        with open(partial, "wb") as f:
            for chunk in response.iter_content(1 << 20):
                f.write(chunk)
                done += len(chunk)
                percent = int(100 * done / total) if total else 0
                if percent // 10 != last:
                    last = percent // 10
                    print(f"[KOKORO] {name}: {percent}%", flush=True)
    os.replace(partial, path)
    return path


if __name__ == "__main__":
    os.makedirs(KOKORO_DIR, exist_ok=True)
    model, voices = [download(name) for name in FILES]

    import numpy as np
    import scipy.io.wavfile
    from kokoro_onnx import Kokoro

    started = time.monotonic()
    kokoro = Kokoro(model, voices)
    print(f"[KOKORO] Modelo carregado em {time.monotonic() - started:.1f}s.")

    os.makedirs("logs", exist_ok=True)
    parts, rate = [], 24000
    for voice in ["pm_alex", "pm_santa", "pf_dora"]:
        text = f"Olá Pedro, esta é a voz {voice.split('_')[1]}. Jarvis online e pronto para entrar no código da Matrix."
        started = time.monotonic()
        samples, rate = kokoro.create(text, voice=voice, speed=KOKORO_SPEED, lang=KOKORO_LANG)
        took = time.monotonic() - started
        print(f"[KOKORO] {voice}: {len(samples) / rate:.1f}s de áudio gerados em {took:.2f}s.")
        parts += [np.asarray(samples, dtype=np.float32), np.zeros(int(rate * 0.6), dtype=np.float32)]
    audio = np.clip(np.concatenate(parts), -1, 1)
    scipy.io.wavfile.write("logs/kokoro_teste.wav", rate, (audio * 32767).astype(np.int16))
    print("[KOKORO] Ouça logs/kokoro_teste.wav (alex, santa e dora, nessa ordem).")
