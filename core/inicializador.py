import os
import subprocess
import requests
import time
from brain.audio import listen
from brain.utils import normalize_text, sounds_like_jarvis

LOCK_FILE = "jarvis.lock"
VISION_MODELS = ["llama3.2-vision:90b", "llama3.2", "llama3.3"]

def is_already_running():
    if os.path.exists(LOCK_FILE):
        return True
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        return False
    except Exception as e:
        print(f"Error creating lock: {e}")
        return True

def remove_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def start_llava():
    try:
        requests.get("http://localhost:11434")
    except requests.exceptions.ConnectionError:
        print("Starting Ollama server...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)

    for model in VISION_MODELS:
        models = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if model not in models.stdout:
            print(f"⬇️ Downloading model {model}...")
            subprocess.run(["ollama", "pull", model])

        print(f"Starting model {model}...")
        subprocess.Popen(["ollama", "run", model], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(5)
    warmup_vision_model()

def warmup_vision_model():
    print("🔥 Warming up the vision model...")
    try:
        subprocess.run(
            ["ollama", "run", "llama3.2-vision:90b"],
            input="<image>null</image>\nIgnore this.",
            capture_output=True,
            encoding="utf-8",
            text=True,
            timeout=10
        )
    except:
        pass

def passive_mode():
    print("Passive mode activated. Waiting for the 'Jarvis' hotword...")
    while True:
        text = listen()
        if not text:
            continue

        text_raw = text.strip()
        text_normalized = normalize_text(text_raw)

        if sounds_like_jarvis(text_normalized):
            return text_raw
        else:
            print(f"[DEBUG] Nenhuma ativação detectada em: {text_raw}")
