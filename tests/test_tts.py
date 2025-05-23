import os
import json
import base64
import tempfile
import subprocess
import re
from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY_GOOGLE_SPEECH = os.getenv("API_KEY_GOOGLE_SPEECH")

# === Função limpa o texto ===
def clean_output(text):
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text

# === Função TTS com Google ===
def say(text, lang="pt-BR", gender="MALE"):
    text = clean_output(text)

    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={API_KEY}"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
    }
    body = {
        "input": {"text": text},
        "voice": {
            "languageCode": lang,
            "name": "pt-BR-Wavenet-B",
            "ssmlGender": gender
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": 1.10,
            "pitch": -2.0
        }
    }

    print(f"🔊 Enviando texto para TTS: {text}")
    response = requests.post(url, headers=headers, data=json.dumps(body))

    if response.status_code == 200:
        print("✅ Áudio recebido! Reproduzindo...")
        audio_content = base64.b64decode(response.json()["audioContent"])
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as out:
            out.write(audio_content)
            out.flush()
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", out.name])
        os.remove(out.name)
    else:
        print(f"❌ Erro {response.status_code}")
        print(response.text)

# === Teste simples ===
say("Olá Pedro, esse é um teste do Google TTS!")
