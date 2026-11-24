import os
import subprocess
import requests
import time
import sys
import threading
import psutil
from brain.audio import listen
from brain.utils.utils import normalize_text, sounds_like_jarvis
from core import config
from core.settings import LOCK_FILE, OLLAMA_HOST, DEFAULT_MODEL, OLLAMA_KEEP_ALIVE, OLLAMA_NUM_CTX


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
            config.MODEL_READY.set()
            return
    except Exception as error:
        print(f"[OLLAMA] Não consegui consultar modelos: {error}")
        config.MODEL_READY.set()
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
    finally:
        config.MODEL_READY.set()


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


