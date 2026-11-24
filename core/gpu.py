"""Devolver a placa de vídeo para o Pedro (jogos, vídeo).

  - release(): tira da placa todos os modelos que o Ollama tiver carregado e
    fecha o ComfyUI se foi o Jarvis que abriu;
  - modo jogo: release() + pausa a rotina de fundo (estudo, reflexão, leitura
    da conversa) até o Pedro sair do modo jogo.
Chamado ao desligar o Jarvis, no "modo jogo" e pelo ComfyUI ocioso.
"""
import requests

from core import config
from core.settings import OLLAMA_HOST


def unload_ollama():
    """Descarrega todos os modelos do Ollama (keep_alive 0). Devolve os nomes."""
    try:
        loaded = requests.get(f"{OLLAMA_HOST}/api/ps", timeout=3).json().get("models", [])
    except (requests.RequestException, ValueError):
        return []
    names = [m.get("name") or m.get("model") for m in loaded]
    for name in names:
        try:
            requests.post(f"{OLLAMA_HOST}/api/generate", json={"model": name, "keep_alive": 0}, timeout=30)
        except requests.RequestException:
            pass
    return names


def release(reason=""):
    names = unload_ollama()
    try:
        from brain.image_gen import stop_comfy

        comfy = stop_comfy()
    except Exception:
        comfy = False
    what = ", ".join(names) or "nenhum modelo"
    print(f"[GPU] Placa liberada{f' ({reason})' if reason else ''}: {what}"
          f"{'; ComfyUI fechado' if comfy else ''}.")
    return names, comfy


def game_mode(on=True):
    """Liga/desliga o modo jogo. Ligado: nada roda sozinho e a placa fica livre."""
    config.GAME_MODE = on
    if on:
        release("modo jogo")
