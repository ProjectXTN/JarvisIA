import sys
import atexit

# Registro em logs/jarvis.log (com nível e hora) antes de qualquer print
from core import log
log.setup()
import time
import re
from brain.initiate.personalized_greeting import personalized_greeting
from datetime import datetime, timedelta
from threading import Thread
from brain.audio import say, listen, activation_sound
from jarvis_commands import process_command
from commands.commands_systeme import shutdown_command
from core.initializer import (
    is_already_running,
    start_ollama,
    remove_lock,
    passive_mode,
    start_stable_diffusion,
)
from brain.utils.utils import sounds_like_jarvis
from brain import avatar
from core.settings import AVATAR_AUTO_OPEN, SD_AUTOSTART

START_STUDY_PATTERN = (
    r"\b(comece|começar|comeca|comecar)\s+a\s+(estudar|aprender)\b"
)
STOP_STUDY_PATTERN = (
    r"\b(para|parar|interromper|interrompa|cancelar|cancele|pausar|pause)\b"
    r"(?:\s+\w+){0,3}\s+\b(estudo|estudar|aprendizado)\b"
)


def handle_study_mode(query):
    """Liga ou desliga o estudo autônomo por voz. True se a frase era sobre isso."""
    query = query.lower()

    from brain.persona import rotina

    # Fase 7: liga/desliga a rotina de fundo (estudo, reflexão), que só roda com o PC parado
    if re.search(START_STUDY_PATTERN, query):
        if not rotina.state["enabled"]:
            rotina.enable(True)
            say("Modo de estudo ativado. Vou estudar quando o computador estiver parado.")
        else:
            say("Já estou estudando quando o computador fica parado, Pedro.")
        return True

    if re.search(STOP_STUDY_PATTERN, query):
        if rotina.state["enabled"]:
            rotina.enable(False)
            say("Modo de estudo desativado.")
        else:
            say("O modo de estudo já estava desligado.")
        return True

    return False


def persona_background():
    """Fase 7: tira fatos da conversa e escreve os diários que faltam."""
    from core import config
    from brain.persona import diario, perfil

    config.MODEL_READY.wait(300)
    perfil.process_pending()
    diario.catch_up()


def main():
    if is_already_running():
        print("⚠️ There is already an instance of Jarvis running.")
        sys.exit()

    atexit.register(remove_lock)

    if AVATAR_AUTO_OPEN:
        avatar.show()

    start_ollama()

    # Memória por semelhança: importa as memórias antigas (uma vez) e
    # atualiza o índice da pasta de documentos, sem atrasar a abertura
    from brain import semantic_memory
    Thread(target=semantic_memory.prepare, daemon=True).start()
    Thread(target=persona_background, daemon=True).start()
    from brain.persona import rotina
    rotina.start()
    if SD_AUTOSTART:
        start_stable_diffusion()

    # Hello Pedro! =)
    personalized_greeting()

    while True:
        query = passive_mode()
        if not query:
            continue

        query = query.lower().strip()
        query = re.sub(r"[^\w\s]", "", query)

        # Activate or deactivate autonomous learning by voice command
        if handle_study_mode(query):
            continue

        matched, activator_word = sounds_like_jarvis(query)
        if matched:
            print("[DEBUG] Activator recognized:", query)
            activation_sound()
            last_command_time = datetime.now()

            # Remove trigger word and comma/space if present
            if activator_word:
                query = re.sub(
                    rf"^{re.escape(activator_word)}[\s,]*",
                    "",
                    query,
                    flags=re.IGNORECASE,
                ).strip()

            print(f"[DEBUG] Phrase after removing activator: {query}")

            if query:
                if shutdown_command(query) is False:
                    sys.exit()
                with log.etapa("pedido", query):
                    result = process_command(query)
                if result is False:
                    sys.exit()

            while True:
                query = listen()
                if not query:
                    if datetime.now() - last_command_time > timedelta(minutes=2):
                        say(
                            "Nenhuma atividade detectada. Retornando para o modo passivo."
                        )
                        # Parado: hora de ler a conversa (perfil do Pedro) e do diário
                        Thread(target=persona_background, daemon=True).start()
                        break
                    continue

                if shutdown_command(query.lower()) is False:
                    sys.exit()

                if handle_study_mode(query):
                    continue

                with log.etapa("pedido", query):
                    result = process_command(query)
                if result is False:
                    sys.exit()

                last_command_time = datetime.now()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.logger.exception("Erro inesperado")
        print(f"🔥 Jarvis encountered an unexpected error: {e}")
        say("Houve um erro inesperado. Encerrando o sistema.")
        sys.exit(1)
