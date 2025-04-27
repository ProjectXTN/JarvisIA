import sys
import atexit
import time
import re
from datetime import datetime, timedelta
from threading import Thread
from brain.audio import say, listen
from jarvis_commands import process_command
from comandos.comandos_sistema import shutdown_command
from core.inicializador import is_already_running, start_llava, remove_lock, passive_mode
from brain.learning import auto_aprendizado
from brain.learning.auto_aprendizado import auto_aprender
from brain.utils import normalize_text, sounds_like_jarvis

atexit.register(remove_lock)

if is_already_running():
    print("⚠️ There is already an instance of Jarvis running.")
    sys.exit()

start_llava()

# Start autonomous learning in background
# Thread(target=auto_aprender, daemon=True).start()

say("Ola Pedro, Jarvis esta online.")

while True:
    query = passive_mode()
    if not query:
        continue
    
    query = query.lower().strip()
    query = re.sub(r"[^\w\s]", "", query)
    
    # Activate autonomous learning by voice command
    if ("comece a estudar" in query.lower()) or ("começar a estudar" in query.lower()):
        if not auto_aprendizado.aprendizado_ativado:
            auto_aprendizado.aprendizado_ativado = True
            Thread(target=auto_aprender, daemon=True).start()
            say("Modo de estudos autonomo ativado.")
        else:
            say("Ja estou estudando, Pedro.")
        continue

    matched, activator_word = sounds_like_jarvis(query)
    if matched:
        print("[DEBUG] Activator recognized:", query)
        say("Jarvis Ativado...")
        last_command_time = datetime.now()

        # Remove trigger word and comma/space if present
        if activator_word:
            query = re.sub(rf"^{re.escape(activator_word)}[\s,]*", "", query, flags=re.IGNORECASE).strip()

        print(f"[DEBUG] Phrase after removing activator: {query}")

        if query:
            if shutdown_command(query) is False or not process_command(query):
                sys.exit()
                
        while True:
            query = listen()
            if not query:
                if datetime.now() - last_command_time > timedelta(minutes=2):
                    say("Nem ma atividade detectada. Retornando para o modo passivo.")
                    break
                continue

            if shutdown_command(query.lower()) is False:
                sys.exit()

            if ("start studying" in query.lower()) or ("begin studying" in query.lower()):
                if not auto_aprendizado.aprendizado_ativado:
                    auto_aprendizado.aprendizado_ativado = True
                    Thread(target=auto_aprender, daemon=True).start()
                    say("Learning mode activated.")
                else:
                    say("I'm already studying, Pedro.")
                continue

            if re.search(r"\b(stop|interrupt|can stop|halt)\s+(studying|learning)\b", query.lower()):
                if auto_aprendizado.aprendizado_ativado:
                    auto_aprendizado.aprendizado_ativado = False
                    say("Learning mode deactivated.")
                else:
                    say("Learning mode is already off.")
                continue

            result = process_command(query)
            if result is False:
                sys.exit()

            time.sleep(0.5)
            last_command_time = datetime.now()
