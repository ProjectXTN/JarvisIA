"""Configuração central do Jarvis.

Tudo que antes estava espalhado pelos módulos (porta do Ollama, nomes de
modelos, limites) fica aqui. Valores podem ser trocados pelo arquivo .env.
"""

import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _normalize_host(value):
    """Aceita 'host:porta' ou URL completa e devolve sempre 'http://host:porta'."""
    value = (value or "").strip().rstrip("/")
    if not value:
        return "http://localhost:11434"
    if not value.startswith(("http://", "https://")):
        value = "http://" + value
    return value.replace("//0.0.0.0", "//127.0.0.1")


# === Ollama ===
OLLAMA_HOST = _normalize_host(os.getenv("OLLAMA_HOST"))
# (conexão, leitura) em segundos
OLLAMA_TIMEOUT = (5, 180)

# === Modelos (serão trocados na Fase 2 do PLANO.md) ===
DEFAULT_MODEL = os.getenv("JARVIS_MODEL", "llama3.2")
DEFAULT_MODEL_HIGH = os.getenv("JARVIS_MODEL_HIGH", "llama3.3")
DEFAULT_MODEL_CODE = os.getenv("JARVIS_MODEL_CODE", "codestral")
VISION_MODEL_LOW = os.getenv("JARVIS_VISION_MODEL_LOW", "llava:13b")
VISION_MODEL_HIGH = os.getenv("JARVIS_VISION_MODEL_HIGH", "llama3.2-vision:90b")
EMBEDDING_MODEL = os.getenv("JARVIS_EMBEDDING_MODEL", "nomic-embed-text")

# Modelos carregados na inicialização
STARTUP_MODELS = [VISION_MODEL_HIGH, DEFAULT_MODEL, DEFAULT_MODEL_HIGH]

# === Voz ===
WHISPER_MODEL = os.getenv("JARVIS_WHISPER_MODEL", "medium")
WHISPER_BEAM_SIZE = 5

# === Hotword ===
HOTWORDS = ["jarvis"]
# Similaridade mínima (0 a 1) entre a palavra ouvida e a hotword
HOTWORD_SIMILARITY = 0.8

# === Arquivos ===
LOCK_FILE = os.path.join(BASE_DIR, "jarvis.lock")
