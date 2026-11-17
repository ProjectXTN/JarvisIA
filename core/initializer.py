import os
import subprocess
import requests
import time
import sys
import psutil
from brain.audio import listen
from brain.utils.utils import normalize_text, sounds_like_jarvis
from core.settings import LOCK_FILE, OLLAMA_HOST, STARTUP_MODELS, VISION_MODEL_HIGH

VISION_MODELS = STARTUP_MODELS
stable_diffusion_process = None
stable_diffusion_pid = None


def set_stable_diffusion_pid(pid):
    global stable_diffusion_pid
    stable_diffusion_pid = pid


def get_stable_diffusion_pid():
    global stable_diffusion_pid
    return stable_diffusion_pid


def set_stable_diffusion_process(process):
    global stable_diffusion_process
    stable_diffusion_process = process


def get_stable_diffusion_process():
    global stable_diffusion_process
    return stable_diffusion_process


def _read_lock_pid():
    """PID gravado no lock, ou None se o arquivo não existe ou está ilegível."""
    try:
        with open(LOCK_FILE, "r") as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def _is_jarvis_process(pid):
    """True se o PID pertence a um processo Python/Jarvis ainda vivo."""
    try:
        name = psutil.Process(pid).name().lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
    return "python" in name or "jarvis" in name


def is_already_running():
    pid = _read_lock_pid()
    if pid is not None and pid != os.getpid() and _is_jarvis_process(pid):
        return True

    if os.path.exists(LOCK_FILE):
        print("Lock antigo encontrado (processo já encerrado). Ignorando.")

    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        return False
    except Exception as e:
        print(f"Error creating lock: {e}")
        return True


def remove_lock():
    # Só apaga o lock que esta instância criou; uma segunda instância que
    # desiste de iniciar não pode apagar o lock da primeira.
    if _read_lock_pid() == os.getpid():
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass


def start_llava():
    try:
        requests.get(OLLAMA_HOST, timeout=3)
    except requests.exceptions.RequestException:
        print("Starting Ollama server...")
        subprocess.Popen(
            ["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(5)

    for model in VISION_MODELS:
        models = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if model not in models.stdout:
            print(f"⬇️ Downloading model {model}...")
            subprocess.run(["ollama", "pull", model])

        print(f"Starting model {model}...")
        # Prompt vazio: só carrega o modelo e sai. stdin fechado para o
        # processo não ficar disputando o teclado do console.
        subprocess.Popen(
            ["ollama", "run", model, ""],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    time.sleep(5)
    warmup_vision_model()


def warmup_vision_model():
    print("🔥 Warming up the vision model...")
    try:
        subprocess.run(
            ["ollama", "run", VISION_MODEL_HIGH],
            input="<image>null</image>\nIgnore this.",
            capture_output=True,
            encoding="utf-8",
            text=True,
            timeout=10,
        )
    except Exception:
        pass


def passive_mode():
    print("Passive mode activated. Waiting for the 'Jarvis' hotword...")
    while True:
        text = listen()
        if not text:
            continue

        text_raw = text.strip()
        text_normalized = normalize_text(text_raw)

        # sounds_like_jarvis devolve (bool, palavra); testar a tupla direto
        # era sempre verdadeiro e qualquer fala ativava o Jarvis.
        matched, _ = sounds_like_jarvis(text_normalized)
        if matched:
            return text_raw
        else:
            print(f"[DEBUG] Nenhuma ativação detectada em: {text_raw}")


def start_stable_diffusion():
    global stable_diffusion_pid

    try:
        response = requests.get("http://127.0.0.1:7860/sdapi/v1/options", timeout=3)
        if response.status_code == 200:
            print("✅ Stable Diffusion server is already running.")
            return
    except requests.exceptions.RequestException:
        print("⚙️ Stable Diffusion server not detected. Starting now...")

    try:
        webui_bat = os.path.abspath("stable-diffusion-webui/webui-user.bat")

        process = subprocess.Popen(
            ["cmd.exe", "/c", webui_bat],
            cwd="stable-diffusion-webui",
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )

        set_stable_diffusion_process(process)
        set_stable_diffusion_pid(process.pid)

        print(
            f"⏳ Waiting for Stable Diffusion server to start (PID {stable_diffusion_pid})..."
        )
        start_time = time.time()
        timeout = 120
        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    "http://127.0.0.1:7860/sdapi/v1/options", timeout=3
                )
                if response.status_code == 200:
                    print("✅ Stable Diffusion API is online!")
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(3)

        print("❌ Timeout: Stable Diffusion server did not start in time.")
    except Exception as e:
        print(f"❌ Failed to start Stable Diffusion: {e}")
