import sys
import atexit
import time
import re
from brain.initiate.personalized_greeting import personalized_greeting
from datetime import datetime, timedelta
from threading import Thread
from brain.audio import say, listen
from jarvis_commands import process_command
from commands.commands_systeme import shutdown_command
from core.initializer import (
    is_already_running,
    start_llava,
    remove_lock,
    passive_mode,
    start_stable_diffusion,
)
from brain.learning import auto_learning
from brain.learning.auto_learning import auto_learn
from brain.utils import sounds_like_jarvis


def main():
    atexit.register(remove_lock)

    if is_already_running():
        print("⚠️ There is already an instance of Jarvis running.")
        sys.exit()

    start_llava()
    start_stable_diffusion()

    # Start autonomous learning in background
    # Thread(target=auto_learn, daemon=True).start()

    # Hello Pedro! =)
    personalized_greeting()

    while True:
        query = passive_mode()
        if not query:
            continue

        query = query.lower().strip()
        query = re.sub(r"[^\w\s]", "", query)

        # Activate or deactivate autonomous learning by voice command
        if (
            ("comece a estudar" in query.lower())
            or ("começar a estudar" in query.lower())
            or ("comece a aprender" in query.lower())
            or ("começar a aprender" in query.lower())
        ):
            if not auto_learning.auto_learning_enabled:
                auto_learning.auto_learning_enabled = True
                Thread(target=auto_learn, daemon=True).start()
                say("Modo de estudo autônomo ativado.")
            else:
                say("Já estou estudando, Pedro.")
            continue

        # Deactivate autonomous learning by voice command
        if re.search(
            r"\b(para|parar|interromper|interrompa|cancelar|cancele|pausar|pause)\b(?:\s+\w+){0,3}\s+\b(estudo|estudar|aprendizado)\b",
            query.lower(),
        ):
            if auto_learning.auto_learning_enabled:
                auto_learning.auto_learning_enabled = False
                say("Modo de estudo autônomo desativado.")
            else:
                say("O modo de estudo já estava desligado.")
            continue

        matched, activator_word = sounds_like_jarvis(query)
        if matched:
            print("[DEBUG] Activator recognized:", query)
            say("Jarvis Ativado...")
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
                if shutdown_command(query) is False or not process_command(query):
                    sys.exit()

            while True:
                query = listen()
                if not query:
                    if datetime.now() - last_command_time > timedelta(minutes=2):
                        say(
                            "Nenhuma atividade detectada. Retornando para o modo passivo."
                        )
                        break
                    continue

                if shutdown_command(query.lower()) is False:
                    sys.exit()

                if ("comece a estudar" in query.lower()) or (
                    "começar a estudar" in query.lower()
                ):
                    if not auto_learning.aprendizado_ativado:
                        auto_learning.aprendizado_ativado = True
                        Thread(target=auto_learn, daemon=True).start()
                        say("Modo de estudo autônomo ativado.")
                    else:
                        say("Já estou estudando, Pedro.")
                    continue

                if re.search(
                    r"\b(parar|interromper|cancelar|pausar)\s+(estudo|aprendizado)\b",
                    query.lower(),
                ):
                    if auto_learning.aprendizado_ativado:
                        auto_learning.aprendizado_ativado = False
                        say("Modo de estudo desativado.")
                    else:
                        say("O modo de estudo já está desligado.")
                    continue

                result = process_command(query)
                if result is False:
                    sys.exit()

                time.sleep(0.5)
                last_command_time = datetime.now()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"🔥 Jarvis encountered an unexpected error: {e}")
        say("Houve um erro inesperado. Encerrando o sistema.")
        sys.exit(1)
