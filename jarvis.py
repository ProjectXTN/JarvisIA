import sys
import atexit
import time
import re
from datetime import datetime, timedelta
from threading import Thread
from brain.audio import say, listen
from jarvis_commands import process_command
from comandos.comandos_sistema import comando_desligar
from core.inicializador import is_already_running, start_llava, remove_lock, passive_mode
from brain.learning import auto_aprendizado
from brain.learning.auto_aprendizado import auto_aprender
from brain.utils import sounds_like_jarvis

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
    
    # Activate autonomous learning by voice command
    if ("start studying" in query.lower()) or ("begin studying" in query.lower()):
        if not auto_aprendizado.aprendizado_ativado:
            auto_aprendizado.aprendizado_ativado = True
            Thread(target=auto_aprender, daemon=True).start()
            say("Learning mode activated.")
        else:
            say("I'm already studying, Pedro.")
        continue

    if sounds_like_jarvis(query):
        print(f"[DEBUG] Activator recognized: {query}")
        say("Jarvis Activated...")
        last_command_time = datetime.now()

        command = query.lower().replace("jarvis", "").strip()
        if command:
            if comando_desligar(command) is False:
                sys.exit()
            if not process_command(command):
                sys.exit()

        while True:
            query = listen()
            if not query:
                if datetime.now() - last_command_time > timedelta(minutes=2):
                    say("No activity detected. Returning to passive mode.")
                    break
                continue

            if comando_desligar(query.lower()) is False:
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
