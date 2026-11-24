"""Frases ouvidas depois de uma resposta: são para o Jarvis ou vêm de uma live/vídeo?"""
import re
from datetime import datetime

from brain.utils.utils import sounds_like_jarvis


def accept_followup(text, last_command_time, now=None):
    """Frase ouvida depois de uma resposta: é para o Jarvis? Devolve o comando ou None.

    Sem dizer "Jarvis", só vale dentro de FOLLOWUP_SECONDS depois da última
    resposta e se nenhum outro programa estiver tocando som (live, vídeo): antes,
    durante 2 minutos qualquer voz da live virava comando, e um "tchau" da live
    desligava o Jarvis.
    """
    from brain.system_audio import other_audio_playing
    from commands.commands_systeme import is_shutdown_request
    from core.settings import FOLLOWUP_SECONDS

    now = now or datetime.now()
    cleaned = re.sub(r"[^\w\s]", "", text.lower()).strip()
    addressed, word = sounds_like_jarvis(cleaned)
    if addressed:
        if word:
            cleaned = re.sub(rf"\b{re.escape(word)}\b[\s,]*", "", cleaned, count=1).strip()
        return cleaned or None
    from core import config

    spoke = getattr(config, "LAST_SPEECH_END", None)
    reference = max(last_command_time, spoke) if spoke else last_command_time
    if (now - reference).total_seconds() > FOLLOWUP_SECONDS:
        print(f"[DEBUG] Ignorado (sem 'Jarvis', fora da conversa): {text}")
        return None
    playing = other_audio_playing()
    if playing:
        print(f"[DEBUG] Ignorado (sem 'Jarvis' e {playing} tocando som): {text}")
        return None
    if is_shutdown_request(cleaned):
        print(f"[DEBUG] Despedida sem 'Jarvis' ignorada: {text}")
        return None
    return cleaned
