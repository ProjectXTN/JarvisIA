import os
import subprocess
import requests
import time
import sys
from brain.audio import listen
from brain.utils.utils import normalize_text, sounds_like_jarvis

LOCK_FILE = "jarvis.lock"
VISION_MODELS = ["llama3.2-vision:90b", "llama3.2", "llama3.3"]
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
        subprocess.Popen(
            ["ollama", "run", model],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

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
            timeout=10,
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
