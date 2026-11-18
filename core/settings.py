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
OLLAMA_TIMEOUT = (5, int(os.getenv("JARVIS_OLLAMA_TIMEOUT", "180")))
# Quanto tempo o modelo fica carregado na GPU depois de usado
OLLAMA_KEEP_ALIVE = "30m"
OLLAMA_NUM_CTX = int(os.getenv("JARVIS_NUM_CTX", "4096"))
# Tempo máximo de espera pela consulta aos documentos internos (RAG)
RAG_TIMEOUT = 15
NEWS_LLM_TIMEOUT = int(os.getenv("JARVIS_NEWS_LLM_TIMEOUT", "45"))
# Limite para respostas com busca na web; depois disso o Jarvis desiste e avisa
WEB_LLM_TIMEOUT = int(os.getenv("JARVIS_WEB_LLM_TIMEOUT", "60"))
# Consulta aos documentos internos (RAG). Desligada até a Fase 5: o índice só
# tem um arquivo de teste e a consulta carrega o modelo de embeddings na GPU,
# o que empurrava parte do modelo principal para a CPU.
RAG_ENABLED = os.getenv("JARVIS_RAG", "0") == "1"
# Abrir o Stable Diffusion junto com o Jarvis. Desligado: ele ocupa a GPU que o
# modelo principal precisa; agora abre só quando você pede uma imagem.
SD_AUTOSTART = os.getenv("JARVIS_SD_AUTOSTART", "0") == "1"

# === Modelos da Fase 2 (podem ser trocados no .env) ===
# Escolha de 18/11/2026 (logs/fase2_modelos.json, GPU inteira):
# gemma4:26b foi 2 a 3 vezes mais rápido (173-334 tokens/s contra 58-131) e
# acertou o cálculo que o qwen3.8:27b errou. O Qwen fica como reserva de
# código, usada só quando o principal recusa um pedido.
DEFAULT_MODEL = os.getenv("JARVIS_MODEL", "gemma4:26b")
DEFAULT_MODEL_HIGH = os.getenv("JARVIS_MODEL_HIGH", DEFAULT_MODEL)
DEFAULT_MODEL_CODE = os.getenv("JARVIS_MODEL_CODE", "qwen3.8:27b")
VISION_MODEL_LOW = os.getenv("JARVIS_VISION_MODEL_LOW", DEFAULT_MODEL)
VISION_MODEL_HIGH = os.getenv("JARVIS_VISION_MODEL_HIGH", VISION_MODEL_LOW)
EMBEDDING_MODEL = os.getenv("JARVIS_EMBEDDING_MODEL", "nomic-embed-text")

# === Voz ===
# Na GPU: large-v3-turbo (preciso e rápido). Se a GPU não puder ser usada,
# o Jarvis volta para o modelo de CPU.
WHISPER_MODEL = os.getenv("JARVIS_WHISPER_MODEL", "large-v3-turbo")
WHISPER_MODEL_CPU = os.getenv("JARVIS_WHISPER_MODEL_CPU", "medium")
# int8_float16 usa cerca de metade da memória de vídeo do float16, com perda
# de precisão desprezível. Com o Gemma (~19 GB) na mesma placa, a memória
# sobrando é pouca: quando acaba, o driver usa a RAM do PC e tudo fica lento.
WHISPER_COMPUTE_TYPE = os.getenv("JARVIS_WHISPER_COMPUTE", "int8_float16")
WHISPER_BEAM_SIZE = 5
# Downloads grandes são preparados separadamente para não travar a abertura.
WHISPER_ALLOW_DOWNLOAD = os.getenv("JARVIS_WHISPER_ALLOW_DOWNLOAD", "0") == "1"

# Fala em fluxo: a primeira frase toca enquanto o modelo ainda escreve o resto
STREAMING_ENABLED = os.getenv("JARVIS_STREAMING", "1") == "1"

# Som ao ouvir "Jarvis": "bip" (instantâneo) ou "voz" (fala "Jarvis Ativado", ~1 s)
ACTIVATION_SOUND = os.getenv("JARVIS_ACTIVATION_SOUND", "bip")

# Interromper o Jarvis por voz enquanto ele fala ("pare", "pode parar", "chega")
INTERRUPT_ENABLED = os.getenv("JARVIS_INTERRUPT", "1") == "1"
# Modelo pequeno e rápido, só para reconhecer o pedido de parar
INTERRUPT_WHISPER_MODEL = os.getenv("JARVIS_INTERRUPT_MODEL", "base")
INTERRUPT_WHISPER_MODEL_CPU = os.getenv("JARVIS_INTERRUPT_MODEL_CPU", "base")
# O Whisper de interrupção ouve trechos curtos ("pare"): na CPU ele é rápido
# o bastante e deixa a memória da GPU para o modelo principal.
INTERRUPT_ON_GPU = os.getenv("JARVIS_INTERRUPT_GPU", "0") == "1"
# Limite de caracteres de cada fala (o resto aparece só no console)
MAX_SPOKEN_CHARS = 1200

# Nomes próprios que o Whisper costuma errar; servem de dica na transcrição.
# Para acrescentar palavras, edite vocabulario.txt na raiz do projeto
# (uma por linha) e reinicie o Jarvis.
VOCABULARY_FILE = os.path.join(BASE_DIR, "vocabulario.txt")


def _load_vocabulary():
    words = ["Jarvis", "Pedro", "Lexy"]
    try:
        with open(VOCABULARY_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and line not in words:
                    words.append(line)
    except FileNotFoundError:
        pass
    return words


WHISPER_VOCABULARY = _load_vocabulary()

# === Clima ===
# Cidade usada quando nenhuma é dita, e também quando o que foi ouvido
# soa parecido com ela ("Alexi", "Lexi")
HOME_CITY = os.getenv("JARVIS_HOME_CITY", "Lexy")
HOME_COUNTRY = os.getenv("JARVIS_HOME_COUNTRY", "FR")

# === Avatar ===
AVATAR_PORT = int(os.getenv("JARVIS_AVATAR_PORT", "8765"))
# Abre o avatar junto com o Jarvis. Para desligar: JARVIS_AVATAR_AUTO_OPEN=0 no .env
AVATAR_AUTO_OPEN = os.getenv("JARVIS_AVATAR_AUTO_OPEN", "1") == "1"
# Atraso entre mandar tocar o áudio e o som sair (ms). Se a boca mexer antes
# da voz, aumente; se mexer depois, diminua.
AVATAR_AUDIO_DELAY_MS = int(os.getenv("JARVIS_AVATAR_AUDIO_DELAY_MS", "180"))

# === Hotword ===
HOTWORDS = ["jarvis"]
# Similaridade mínima (0 a 1) entre a palavra ouvida e a hotword
HOTWORD_SIMILARITY = 0.8

# === Arquivos ===
LOCK_FILE = os.path.join(BASE_DIR, "jarvis.lock")
