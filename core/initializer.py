import os
import subprocess
import requests
import time
import sys
import threading
import psutil
from brain.audio import listen
from brain.utils.utils import normalize_text, sounds_like_jarvis
from core.settings import LOCK_FILE, OLLAMA_HOST, DEFAULT_MODEL, OLLAMA_KEEP_ALIVE, OLLAMA_NUM_CTX
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


def start_ollama():
    try:
        requests.get(OLLAMA_HOST, timeout=3)
    except requests.exceptions.RequestException:
        print("Starting Ollama server...")
        subprocess.Popen(
            ["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(5)

    # Consulta o mesmo servidor HTTP usado na inferência, nunca outro CLI/host.
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        response.raise_for_status()
        names = {m["name"] for m in response.json()["models"]}
        if DEFAULT_MODEL not in names and DEFAULT_MODEL + ":latest" not in names:
            print(f"[OLLAMA] Modelo {DEFAULT_MODEL} não instalado em {OLLAMA_HOST}.")
            return
    except Exception as error:
        print(f"[OLLAMA] Não consegui consultar modelos: {error}")
        return
    threading.Thread(target=warmup_model, args=(DEFAULT_MODEL,), daemon=True).start()


# Compatibilidade para consumidores antigos.
start_llava = start_ollama


def warmup_model(model):
    """Carrega o modelo na GPU (prompt vazio) e o mantém carregado."""
    print(f"[OLLAMA] Carregando o modelo {model}...")
    start = time.time()
    try:
        requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={"model": model, "messages": [], "stream": False, "think": False,
                  "options": {"num_ctx": OLLAMA_NUM_CTX}, "keep_alive": OLLAMA_KEEP_ALIVE},
            timeout=(5, 600),
        ).raise_for_status()
        print(f"[OLLAMA] Modelo {model} pronto em {time.time() - start:.1f}s.")
    except Exception as e:
        print(f"[OLLAMA] Não consegui pré-carregar {model}: {e}")


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
