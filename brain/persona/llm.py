"""Chamadas curtas ao modelo para tarefas de fundo (extrair fatos, diário, reflexão).

Usa o mesmo Ollama da conversa, sem stream e sem histórico. Só roda quando o
Jarvis está parado (modo passivo, abertura), para não atrasar a voz.
"""
import json

import requests

from core.settings import DEFAULT_MODEL, OLLAMA_HOST, OLLAMA_KEEP_ALIVE, OLLAMA_NUM_CTX


def ask(system, user, as_json=False, num_predict=600, timeout=120):
    payload = {
        "model": DEFAULT_MODEL, "stream": False, "think": False,
        "keep_alive": OLLAMA_KEEP_ALIVE,
        "options": {"num_ctx": OLLAMA_NUM_CTX, "num_predict": num_predict, "temperature": 0.3},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    if as_json:
        payload["format"] = "json"
    response = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=(5, timeout))
    response.raise_for_status()
    text = response.json()["message"]["content"].strip()
    if not as_json:
        return text
    try:
        return json.loads(text)
    except ValueError:
        return None
