import os
import subprocess
import requests
import time
from brain.audio import listen

LOCK_FILE = "jarvis.lock"
VISION_MODELS = ["llama3.2-vision:90b", "llama3.2", "llama3.3"]


def ja_esta_rodando():
    if os.path.exists(LOCK_FILE):
        return True
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        return False
    except Exception as e:
        print(f"Erro ao criar lock: {e}")
        return True

def remover_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def iniciar_llava():
    try:
        requests.get("http://localhost:11434")
    except requests.exceptions.ConnectionError:
        print("Iniciando o servidor Ollama...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)

    for modelo in VISION_MODELS:
        modelos = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if modelo not in modelos.stdout:
            print(f"⬇️ Baixando o modelo {modelo}...")
            subprocess.run(["ollama", "pull", modelo])

        print(f"Iniciando o modelo {modelo}...")
        subprocess.Popen(["ollama", "run", modelo], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(5)
    aquecer_modelo_vision()

def aquecer_modelo_vision():
    print("🔥 Pré-aquecendo o modelo vision...")
    try:
        subprocess.run(
            ["ollama", "run", "llama3.2-vision:90b"],
            input="<image>nula</image>\nIgnore isso.",
            capture_output=True,
            encoding="utf-8",
            text=True,
            timeout=10
        )
    except:
        pass

def modo_passivo():
    print("Modo passivo ativado. Aguardando a hotword 'Jarvis'...")
    while True:
        texto = listen()
        if not texto:
            continue

        texto = texto.strip()
        if "jarvis" in texto.lower():
            return texto