"""Carrega o Whisper (faster-whisper) na GPU quando possível.

O faster-whisper roda pelo CTranslate2, que tem suporte próprio a CUDA e não
depende do PyTorch. Antes o Jarvis perguntava ao PyTorch se havia GPU; como o
venv tem o PyTorch só de CPU, a resposta era sempre "não" e o Whisper rodava na
CPU (5 a 6 segundos por frase).

Na GPU o CTranslate2 precisa do cuBLAS 12 e do cuDNN 9. No Windows eles vêm dos
pacotes pip nvidia-cublas-cu12 e nvidia-cudnn-cu12; este módulo acrescenta as
pastas deles à busca de DLLs. Se algo faltar, volta para a CPU e avisa.
"""

import glob
import os
import sys


def _add_nvidia_dll_dirs():
    if os.name != "nt":
        return
    for base in sys.path:
        for folder in glob.glob(os.path.join(base, "nvidia", "*", "bin")):
            try:
                os.add_dll_directory(folder)
            except (OSError, AttributeError):
                pass
            os.environ["PATH"] = folder + os.pathsep + os.environ.get("PATH", "")


# Antes de importar o CTranslate2, para ele achar o cuBLAS e o cuDNN
_add_nvidia_dll_dirs()

import numpy as np  # noqa: E402
import ctranslate2  # noqa: E402
import faster_whisper  # noqa: E402
from core.settings import WHISPER_ALLOW_DOWNLOAD

GPU_HINT = (
    "Para usar a GPU, rode no terminal: "
    'venv\\Scripts\\python.exe -m pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"'
)


def cuda_available():
    try:
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def load_whisper(gpu_model, cpu_model, label="Whisper"):
    """Devolve (modelo, descrição). Tenta a GPU e confere com uma transcrição de teste."""
    if cuda_available():
        try:
            model = faster_whisper.WhisperModel(gpu_model, device="cuda", compute_type="float16", local_files_only=not WHISPER_ALLOW_DOWNLOAD)
            # Erros de DLL ausente só aparecem na primeira transcrição
            segments, _ = model.transcribe(np.zeros(16000, dtype=np.float32), language="pt", beam_size=1)
            list(segments)
            return model, f"{label} {gpu_model} na GPU"
        except Exception as e:
            print(f"[WHISPER] {label}: modelo GPU indisponível ({e}).")
            reason = str(e).lower()
            if any(word in reason for word in ("cublas", "cudnn", "dll", "cudart")):
                print(f"   {GPU_HINT}")
            elif any(word in reason for word in ("download", "cache", "model.bin", "huggingface", "cas service", "incompletebody", "connection", "localentrynotfound")):
                print("[WHISPER] Modelo ausente/incompleto ou falha de download; não indica falta de CUDA.")
                print("   Prepare o modelo separadamente: venv\\Scripts\\python.exe -X utf8 -m tests.prepare_whisper")
            else:
                print("[WHISPER] Voltando à CPU; verifique o erro acima antes de reinstalar dependências.")
    else:
        print(f"⚠️ {label}: nenhuma GPU CUDA encontrada pelo CTranslate2.")

    model = faster_whisper.WhisperModel(cpu_model, device="cpu", compute_type="int8", local_files_only=not WHISPER_ALLOW_DOWNLOAD)
    return model, f"{label} {cpu_model} na CPU, mais lento"
