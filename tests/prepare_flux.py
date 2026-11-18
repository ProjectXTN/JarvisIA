"""Baixa os arquivos do FLUX.2 [klein] 4B para a pasta do ComfyUI.

Uso:  venv\\Scripts\\python.exe tests\\prepare_flux.py [pasta do ComfyUI]
Padrão: JARVIS_COMFYUI_DIR do .env ou C:\\ComfyUI (versão portátil).
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.settings import COMFYUI_DIR  # noqa: E402

FILES = [
    ("diffusion_models", "flux-2-klein-4b-fp8.safetensors",
     "https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8/resolve/main/flux-2-klein-4b-fp8.safetensors"),
    ("text_encoders", "qwen_3_4b.safetensors",
     "https://huggingface.co/Comfy-Org/flux2-klein-4B/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors"),
    ("vae", "flux2-vae.safetensors",
     "https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors"),
]


def models_dir(root):
    for candidate in (os.path.join(root, "ComfyUI", "models"), os.path.join(root, "models")):
        if os.path.isdir(candidate):
            return candidate
    raise SystemExit(f"Não achei a pasta models do ComfyUI em {root}.")


def download(url, path):
    tmp = path + ".part"
    headers = {}
    token = os.getenv("HF_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with requests.get(url, stream=True, timeout=60, headers=headers) as r:
        if r.status_code in (401, 403):
            raise SystemExit(f"Acesso negado a {url}. Aceite a licença no site do Hugging Face "
                             "e defina HF_TOKEN no .env.")
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(8 * 1024 * 1024):
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r  {done / total:6.1%} de {total / 1e9:.1f} GB", end="", flush=True)
    os.replace(tmp, path)
    print()


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else COMFYUI_DIR
    base = models_dir(root)
    for folder, name, url in FILES:
        target = os.path.join(base, folder, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if os.path.isfile(target):
            print(f"✔ {folder}/{name} já existe.")
            continue
        print(f"⬇ {folder}/{name}")
        download(url, target)
    print("Pronto. Abra o ComfyUI e peça uma imagem ao Jarvis.")


if __name__ == "__main__":
    main()
