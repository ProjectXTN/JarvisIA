"""Monitor de recursos: placa de vídeo, processador, memória e o que o Jarvis
tem carregado. Mostrado na janela "Jarvis, abre o monitor" (interface/monitor.html).
"""
import os
import shutil
import subprocess
import threading
import time

import psutil
import requests

from core.settings import COMFYUI_URL, OLLAMA_HOST

_cache = {"at": 0.0, "data": None}
_lock = threading.Lock()
_me = psutil.Process(os.getpid())
_me.cpu_percent(None)
psutil.cpu_percent(None)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_GPU_FIELDS = ("utilization.gpu", "memory.used", "memory.total", "temperature.gpu",
               "power.draw", "power.limit", "name")


def _nvidia_smi():
    exe = shutil.which("nvidia-smi")
    if not exe:
        for path in (r"C:\Windows\System32\nvidia-smi.exe",
                     r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe"):
            if os.path.isfile(path):
                exe = path
                break
    return exe


def gpu():
    exe = _nvidia_smi()
    if not exe:
        return None
    try:
        out = subprocess.run([exe, f"--query-gpu={','.join(_GPU_FIELDS)}", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=3, creationflags=NO_WINDOW).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    line = out.strip().splitlines()[0] if out.strip() else ""
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < len(_GPU_FIELDS):
        return None

    def num(value):
        try:
            return float(value)
        except ValueError:
            return None

    util, used, total, temp, power, limit = (num(p) for p in parts[:6])
    return {"nome": parts[6], "uso": util, "vram_usada": used, "vram_total": total,
            "temperatura": temp, "potencia": power, "potencia_max": limit}


def ollama_models():
    try:
        models = requests.get(f"{OLLAMA_HOST}/api/ps", timeout=1.5).json().get("models", [])
    except (requests.RequestException, ValueError):
        return None  # Ollama fora do ar
    return [{"nome": m.get("name") or m.get("model"),
             "vram_mb": round((m.get("size_vram") or 0) / 2**20),
             "total_mb": round((m.get("size") or 0) / 2**20)} for m in models]


def comfy_running():
    try:
        return requests.get(f"{COMFYUI_URL}/system_stats", timeout=0.8).ok
    except requests.RequestException:
        return False


def snapshot():
    """Leitura atual (no máximo uma por 0,8 s, mesmo com várias janelas abertas)."""
    with _lock:
        if _cache["data"] and time.monotonic() - _cache["at"] < 0.8:
            return _cache["data"]
        memory = psutil.virtual_memory()
        try:
            from core import config

            game = bool(getattr(config, "GAME_MODE", False))
        except Exception:
            game = False
        data = {
            "hora": time.strftime("%H:%M:%S"),
            "gpu": gpu(),
            "cpu": psutil.cpu_percent(None),
            "nucleos": psutil.cpu_count(),
            "ram_usada": round(memory.used / 2**30, 1),
            "ram_total": round(memory.total / 2**30, 1),
            "jarvis_cpu": round(_me.cpu_percent(None) / max(1, psutil.cpu_count()), 1),
            "jarvis_ram": round(_me.memory_info().rss / 2**20),
            "modelos": ollama_models(),
            "comfyui": comfy_running(),
            "modo_jogo": game,
        }
        _cache.update(at=time.monotonic(), data=data)
        return data
