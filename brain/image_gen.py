"""Gerador de imagens: ComfyUI com FLUX.2 [klein] 4B (Fase 6, itens 42 e 51).

Substitui o Stable Diffusion 1.5 (AUTOMATIC1111). O ComfyUI roda à parte
(http://127.0.0.1:8188); se não estiver aberto e COMFYUI_DIR estiver
configurado, o Jarvis abre.

VRAM (24 GB): o gemma4:26b e o FLUX não cabem juntos. Antes de gerar, o
Jarvis tira o modelo de conversa da placa (keep_alive 0 no Ollama); depois,
pede ao ComfyUI para liberar a memória e recarrega o gemma4 em segundo plano.

Arquivos (pasta models do ComfyUI):
  diffusion_models/flux-2-klein-4b-fp8.safetensors (ou flux-2-klein-4b)
  text_encoders/qwen_3_4b.safetensors
  vae/flux2-vae.safetensors
"""

import json
import os
import random
import shutil
import subprocess
import threading
import time
import uuid
from datetime import datetime

import requests

from core.settings import (
    COMFYUI_DIR,
    COMFYUI_URL,
    DEFAULT_MODEL,
    FLUX_CLIP,
    FLUX_UNET,
    FLUX_VAE,
    IMAGE_OUTPUT_DIR,
    OLLAMA_HOST,
)


_comfy = {"process": None, "timer": None}
IDLE_CLOSE_SECONDS = 600  # ComfyUI aberto pelo Jarvis fecha depois de 10 min sem imagem


class ImageError(Exception):
    """Mensagem curta, pronta para o Jarvis falar."""


# ------------------------------------------------------------------ grafo
def build_workflow(prompt, width=1024, height=1024, seed=None, unet=FLUX_UNET,
                   steps=4, cfg=1.0, prefix="Jarvis"):
    """Grafo no formato da API do ComfyUI (modelo destilado: 4 passos, cfg 1)."""
    seed = random.randint(0, 2**48) if seed is None else seed
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": unet, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": FLUX_CLIP, "type": "flux2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": FLUX_VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "CFGGuider",
              "inputs": {"model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "cfg": cfg}},
        "7": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "8": {"class_type": "Flux2Scheduler", "inputs": {"steps": steps, "width": width, "height": height}},
        "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "10": {"class_type": "EmptyFlux2LatentImage",
               "inputs": {"width": width, "height": height, "batch_size": 1}},
        "11": {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["9", 0], "guider": ["6", 0], "sampler": ["7", 0],
                          "sigmas": ["8", 0], "latent_image": ["10", 0]}},
        "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["3", 0]}},
        "13": {"class_type": "SaveImage", "inputs": {"images": ["12", 0], "filename_prefix": prefix}},
    }


_SIZES = {"quadrada": (1024, 1024), "retrato": (832, 1216), "paisagem": (1216, 832)}


# ---------------------------------------------------------------- ComfyUI
def comfy_running():
    try:
        return requests.get(f"{COMFYUI_URL}/system_stats", timeout=2).ok
    except requests.RequestException:
        return False


def start_comfy(wait=120):
    """Abre o ComfyUI de COMFYUI_DIR (portátil ou instalação com git) e espera responder."""
    if comfy_running():
        return True
    if not COMFYUI_DIR or not os.path.isdir(COMFYUI_DIR):
        raise ImageError("O ComfyUI não está aberto e a pasta dele não foi configurada.")
    port = COMFYUI_URL.rsplit(":", 1)[-1].strip("/")
    portable_python = os.path.join(COMFYUI_DIR, "python_embeded", "python.exe")
    if os.path.isfile(portable_python):
        cmd = [portable_python, "-s", os.path.join("ComfyUI", "main.py")]
    else:
        venv_python = os.path.join(COMFYUI_DIR, "venv", "Scripts", "python.exe")
        cmd = [venv_python if os.path.isfile(venv_python) else "python", "main.py"]
    cmd += ["--listen", "127.0.0.1", "--port", port, "--disable-auto-launch"]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    log = open(os.path.join(COMFYUI_DIR, "jarvis_comfyui.log"), "a", encoding="utf-8")
    _comfy["process"] = subprocess.Popen(cmd, cwd=COMFYUI_DIR, stdout=log, stderr=subprocess.STDOUT,
                                         creationflags=flags)
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        if comfy_running():
            return True
        time.sleep(2)
    raise ImageError("O ComfyUI não abriu a tempo.")


def available_unet():
    """Usa o arquivo configurado; se faltar, qualquer FLUX.2 klein 4B presente."""
    try:
        info = requests.get(f"{COMFYUI_URL}/object_info/UNETLoader", timeout=10).json()
        names = info["UNETLoader"]["input"]["required"]["unet_name"][0]
    except Exception:
        return FLUX_UNET
    if FLUX_UNET in names:
        return FLUX_UNET
    for name in names:
        low = name.lower()
        if "klein" in low and "4b" in low and "base" not in low:
            return name
    raise ImageError("Não achei o modelo FLUX.2 klein na pasta do ComfyUI.")


# -------------------------------------------------------------------- VRAM
def unload_llm():
    """Tira o modelo de conversa da placa para o FLUX caber."""
    try:
        requests.post(f"{OLLAMA_HOST}/api/generate",
                      json={"model": DEFAULT_MODEL, "keep_alive": 0}, timeout=30)
    except requests.RequestException as error:
        print(f"[IMAGEM] Não consegui descarregar o {DEFAULT_MODEL}: {error}")


def stop_comfy():
    """Fecha o ComfyUI, só se foi o Jarvis que abriu. Devolve True se fechou."""
    process = _comfy.get("process")
    timer = _comfy.get("timer")
    if timer:
        timer.cancel()
        _comfy["timer"] = None
    if not process or process.poll() is not None:
        _comfy["process"] = None
        return False
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
    _comfy["process"] = None
    print("[IMAGEM] ComfyUI fechado (ficou parado ou o Jarvis desligou).")
    return True


def _close_when_idle():
    if _comfy.get("timer"):
        _comfy["timer"].cancel()
    _comfy["timer"] = threading.Timer(IDLE_CLOSE_SECONDS, stop_comfy)
    _comfy["timer"].daemon = True
    _comfy["timer"].start()


def free_comfy_and_reload_llm():
    def work():
        try:
            requests.post(f"{COMFYUI_URL}/free",
                          json={"unload_models": True, "free_memory": True}, timeout=30)
        except requests.RequestException:
            pass
        _close_when_idle()
        from core import config

        if getattr(config, "GAME_MODE", False):
            return  # modo jogo: não recarrega o modelo de conversa
        from core.initializer import start_ollama

        try:
            start_ollama()
        except Exception as error:
            print(f"[IMAGEM] Recarregar o {DEFAULT_MODEL} falhou: {error}")

    threading.Thread(target=work, daemon=True).start()


# ------------------------------------------------------------------ gerar
def _wait_result(prompt_id, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        history = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10).json()
        entry = history.get(prompt_id)
        if entry:
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                print(f"[IMAGEM] Erro no ComfyUI: {json.dumps(status)[:500]}")
                raise ImageError("O ComfyUI deu erro ao gerar a imagem.")
            for output in entry.get("outputs", {}).values():
                for image in output.get("images", []):
                    return image
        time.sleep(1)
    raise ImageError("A imagem demorou demais.")


def generate(prompt, formato="quadrada", timeout=240, open_after=True):
    """Gera a imagem e devolve o caminho do PNG salvo em Imagens/Jarvis."""
    started = time.monotonic()
    width, height = _SIZES.get(formato, _SIZES["quadrada"])
    start_comfy()
    unet = available_unet()
    unload_llm()
    try:
        workflow = build_workflow(prompt, width, height, unet=unet)
        response = requests.post(f"{COMFYUI_URL}/prompt",
                                 json={"prompt": workflow, "client_id": str(uuid.uuid4())}, timeout=30)
        if not response.ok:
            print(f"[IMAGEM] ComfyUI recusou o pedido: {response.text[:500]}")
            raise ImageError("O ComfyUI recusou o pedido. Veja se os arquivos do FLUX estão no lugar.")
        image = _wait_result(response.json()["prompt_id"], timeout)
        data = requests.get(f"{COMFYUI_URL}/view", params={
            "filename": image["filename"], "subfolder": image.get("subfolder", ""),
            "type": image.get("type", "output")}, timeout=30)
        data.raise_for_status()
    finally:
        free_comfy_and_reload_llm()

    os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)
    path = os.path.join(IMAGE_OUTPUT_DIR, datetime.now().strftime("jarvis_%Y-%m-%d_%H-%M-%S.png"))
    with open(path, "wb") as f:
        f.write(data.content)
    print(f"[IMAGEM] Pronta em {time.monotonic() - started:.1f}s: {path}")
    try:
        from core.log import record_time

        record_time("imagem", time.monotonic() - started, prompt)
    except OSError:
        pass
    if open_after and hasattr(os, "startfile"):
        os.startfile(path)
    return path
