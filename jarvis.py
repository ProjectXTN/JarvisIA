import sys
import atexit
import time
import re
from datetime import datetime, timedelta
from threading import Thread
from brain.audio import say, listen
from jarvis_commands import process_command
from comandos.comandos_sistema import comando_desligar
from core.inicializador import iniciar_llava, ja_esta_rodando, remover_lock, modo_passivo
from brain.learning import auto_aprendizado
from brain.learning.auto_aprendizado import auto_aprender

atexit.register(remover_lock)

if ja_esta_rodando():
    print("⚠️ Já existe uma instância do Jarvis rodando.")
    sys.exit()

iniciar_llava()

# Inicia aprendizado autônomo em segundo plano
# Thread(target=auto_aprender, daemon=True).start()

say("Olá Pedro, Jarvis está online e pronto para entrarmos no código da Matrix.")

while True:
    query = modo_passivo()
    if not query:
        continue
    
    # Ativar aprendizado autônomo por comando de voz
    if "comece a estudar" in query.lower():
        if not auto_aprendizado.aprendizado_ativado:
            auto_aprendizado.aprendizado_ativado = True
            Thread(target=auto_aprender, daemon=True).start()
            say("Modo de aprendizado ativado.")
        else:
            say("Já estou estudando, Pedro.")
        continue

    # Desativar aprendizado autônomo
    if re.search(r"\b(pare|parem|interrompa|pode parar|parar)\s+(de\s+)?(estudar|aprender)\b", query.lower()):
        if auto_aprendizado.aprendizado_ativado:
            auto_aprendizado.aprendizado_ativado = False
            say("Modo de aprendizado desativado.")
        else:
            say("Já estou com o modo de aprendizado desligado.")
        continue

    if "jarvis" in query.lower():
        say("Jarvis Ativado...")
        tempo_ultimo_comando = datetime.now()

        comando = query.lower().replace("jarvis", "").strip()
        if comando:
            if comando_desligar(comando) is False:
                sys.exit()
            if not process_command(comando):
                sys.exit()

        while True:
            query = listen()
            if not query:
                if datetime.now() - tempo_ultimo_comando > timedelta(minutes=2):
                    say("Nenhuma atividade detectada. Retornando ao modo passivo.")
                    break
                continue

            if comando_desligar(query.lower()) is False:
                sys.exit()

            resultado = process_command(query)
            if resultado is False:
                sys.exit()

            time.sleep(0.5)
            tempo_ultimo_comando = datetime.now()
