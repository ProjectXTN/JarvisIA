"""Síntese de voz: Kokoro local (padrão) com o Google TTS como reserva.

O Kokoro roda no próprio PC, na CPU (ONNX Runtime): não depende de internet
nem de chave de API, e não disputa a memória da placa com o modelo principal.
Se ele não estiver instalado, faltar o modelo ou falhar numa frase, a frase
sai pelo Google, como antes.

Para instalar o Kokoro (uma vez):
    venv\\Scripts\\python.exe -m pip install kokoro-onnx
    venv\\Scripts\\python.exe -X utf8 -m tests.prepare_kokoro
"""

import base64
import json
import os
import tempfile
import threading
import time
import wave

import numpy as np
import requests

from core.settings import (
    TTS_ENGINE,
    KOKORO_DIR,
    KOKORO_VOICE,
    KOKORO_SPEED,
    KOKORO_LANG,
    GOOGLE_TTS_VOICE,
)

API_KEY_GOOGLE_SPEECH = os.getenv("API_KEY_GOOGLE_SPEECH")
KOKORO_MODEL = os.path.join(KOKORO_DIR, "kokoro-v1.0.onnx")
KOKORO_VOICES = os.path.join(KOKORO_DIR, "voices-v1.0.bin")


# ------------------------------------------------------------------ Google
def google_synthesize(text, gender="MALE"):
    """Google TTS: caminho de um MP3 temporário, ou None em erro."""
    if not API_KEY_GOOGLE_SPEECH:
        print("❌ Google TTS sem chave (API_KEY_GOOGLE_SPEECH no .env).")
        return None
    body = {
        "input": {"text": text},
        "voice": {"languageCode": "pt-BR", "name": GOOGLE_TTS_VOICE, "ssmlGender": gender},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.10, "pitch": -2.0},
    }
    try:
        response = requests.post(
            f"https://texttospeech.googleapis.com/v1/text:synthesize?key={API_KEY_GOOGLE_SPEECH}",
            headers={"Content-Type": "application/json; charset=utf-8"},
            data=json.dumps(body),
            timeout=30,
        )
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de rede no Google TTS: {e}")
        return None
    if response.status_code != 200:
        print(f"❌ Erro no Google TTS: {response.status_code} {response.text[:200]}")
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as out:
        out.write(base64.b64decode(response.json()["audioContent"]))
        return out.name


# ------------------------------------------------------------------ Kokoro
class _Kokoro:
    def __init__(self):
        self.model = None
        self.failed = None  # motivo de não poder usar o Kokoro nesta sessão
        self.lock = threading.Lock()
        self.ready = threading.Event()

    def load(self):
        """Carrega o modelo uma vez. Devolve True se o Kokoro pode ser usado."""
        with self.lock:
            if self.model is not None or self.failed:
                return self.model is not None
            try:
                if not (os.path.isfile(KOKORO_MODEL) and os.path.isfile(KOKORO_VOICES)):
                    raise FileNotFoundError(
                        "modelo não baixado; rode: venv\\Scripts\\python.exe -X utf8 -m tests.prepare_kokoro"
                    )
                from kokoro_onnx import Kokoro

                started = time.monotonic()
                self.model = Kokoro(KOKORO_MODEL, KOKORO_VOICES)
                print(f"🗣️ Voz local Kokoro pronta ({KOKORO_VOICE}) em {time.monotonic() - started:.1f}s.")
                return True
            except ImportError:
                self.failed = "pacote kokoro-onnx não instalado (pip install kokoro-onnx)"
            except Exception as e:
                self.failed = str(e)
            print(f"⚠️ Voz local Kokoro indisponível: {self.failed}. Usando o Google TTS.")
            return False

    def synthesize(self, text):
        """WAV temporário com a frase, ou None."""
        if not self.load():
            return None
        try:
            with self.lock:  # o ONNX Runtime é usado por uma frase de cada vez
                samples, rate = self.model.create(
                    text, voice=KOKORO_VOICE, speed=KOKORO_SPEED, lang=KOKORO_LANG
                )
        except Exception as e:
            print(f"⚠️ Kokoro falhou nesta frase ({e}); usando o Google.")
            return None
        audio = np.clip(np.asarray(samples, dtype=np.float32).reshape(-1), -1.0, 1.0)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as out:
            path = out.name
        with wave.open(path, "wb") as wav:  # WAV mono de 16 bits
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(int(rate))
            wav.writeframes((audio * 32767).astype("<i2").tobytes())
        return path


kokoro = _Kokoro()


def preload():
    """Carrega o Kokoro em segundo plano na abertura, para a primeira fala não esperar."""
    if TTS_ENGINE == "kokoro":
        threading.Thread(target=kokoro.load, daemon=True).start()


def synthesize(text, gender="MALE"):
    """Áudio da frase (caminho do arquivo) pelo motor escolhido, ou None."""
    started = time.monotonic()
    path, engine = None, "Google"
    if TTS_ENGINE == "kokoro":
        path, engine = kokoro.synthesize(text), "Kokoro"
    if path is None:
        path, engine = google_synthesize(text, gender), "Google"
    if path:
        print(f"⏱️ Áudio gerado em {time.monotonic() - started:.2f}s ({len(text)} caracteres, {engine}).")
    return path
