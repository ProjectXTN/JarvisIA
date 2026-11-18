"""Visão pelo mesmo servidor HTTP de conversa."""
import base64
import re
from pathlib import Path
from brain.memory.memory import llama_query
from core.settings import VISION_MODEL_LOW, VISION_MODEL_HIGH


def is_detailed_prompt(user_text):
    return bool(re.search(r"detalh|precisão|com riqueza|alta definição", user_text.lower()))


def describe_image(image_path, user_text=""):
    detailed = is_detailed_prompt(user_text)
    try:
        path = Path(image_path)
        if path.stat().st_size > 20 * 1024 * 1024:
            raise ValueError("Imagem excede o limite de 20 MB")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    except (OSError, ValueError) as error:
        print(f"[VISION] Não consegui ler a imagem: {error}")
        return None
    return llama_query(
        user_text or "Descreva o conteúdo desta imagem em português.",
        model=VISION_MODEL_HIGH if detailed else VISION_MODEL_LOW,
        mode="vision", direct_mode=True, images=[encoded])
