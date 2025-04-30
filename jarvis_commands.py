import re
import string
import time

from comandos.comandos_datahora import datetime_commands
from comandos.comandos_musica import music_commands
from comandos.comandos_navegador import browser_commands
from comandos.comandos_imagem import image_commands
from comandos.comandos_pastas import comandos_pastas
from comandos.comandos_software import software_commands
from comandos.comandos_multiplos import multiple_commands
from comandos.comandos_memoria import comandos_memoria
from comandos.comandos_emocionais import emotional_commands
from comandos.comandos_reflexao import comandos_reflexao
from comandos.comandos_pesquisa import execute_search
from comandos.comandos_avatar import generate_avatar
from comandos.comandos_sistema import system_command, shutdown_command
from brain.weatherAPI import handle_weather_query
from brain.storage.file_saver import save_response_to_file, should_save_to_file
from brain.memoria import llama_query
from core import config

from brain.audio import say
from brain.utils import log_interaction
from brain.dev import extract_and_save_code

# New: Persistent connection with LLaMA3
import requests

session = requests.Session()

# Cache for responses to accelerate
response_cache = {}

# Join all command handlers with internal regex detection
COMMAND_HANDLERS = [
    multiple_commands,
    software_commands,
    datetime_commands,
    music_commands,
    browser_commands,
    system_command,
    comandos_pastas,
    image_commands,
    comandos_memoria,
    comandos_reflexao,
    emotional_commands,
    generate_avatar,
]

BLOCKED_COMMANDS_API = [
    music_commands,
    browser_commands,
    system_command,
    comandos_pastas,
    image_commands,
    comandos_memoria,
    comandos_reflexao,
    emotional_commands,
    generate_avatar,
]


def process_command(query):
    query = query.lower().strip()

    # Remove "jarvis" do começo
    query = re.sub(r"^jarvis[\s,]*", "", query)
    query = query.lstrip(", ").strip()
    query = query.rstrip(string.punctuation)

    print(f"[DEBUG] Phrase after cleaning: {query}")

    if shutdown_command(query) is False:
        return False

    if re.search(r"\b(pesquise|procure|busque)\s+(na\s+)?(internet|web)\b", query):
        if execute_search(query):
            return True

    for group in COMMAND_HANDLERS:
        if isinstance(group, dict):
            for key, func in group.items():
                if key in query:
                    try:
                        return func(query)
                    except Exception as e:
                        say("Houve um problema ao executar o comando. Tente novamente.")
                        print(f"Error COMMAND_HANDLERS {e}")
                        return True
        elif isinstance(group, list):
            for pattern, func in group:
                if re.search(pattern, query):
                    try:
                        return func(query)
                    except Exception as e:
                        say("Houve um problema ao executar o comando. Tente novamente.")
                        print(f"Error COMMAND_HANDLERS {e}")
                        return True

    if handle_weather_query(query):
        return True

    # 🔁 Fallback usando LLaMA3 + Cache
    if query in response_cache:
        response = response_cache[query]
    else:
        start_time = time.time()
        response = llama_query(query)
        end_time = time.time()

        generation_time = end_time - start_time

        if response:
            print(f"\nJarvis generated (in {generation_time:.2f} seconds)")
        else:
            print(
                f"LLaMA failed to generate a response after {generation_time:.2f} seconds."
            )

        if response:
            response_cache[query] = response

    if response:
        log_interaction(query, response)

        if "```" in response:
            print(
                "[SAVING] Código detectado na resposta, chamando extract_and_save_code()..."
            )
            extract_and_save_code(response, title=query)

        say(response)

        if should_save_to_file(query):
            save_response_to_file(query, response)
        else:
            print("[DEBUG] Detecção: NÃO deve salvar a resposta.")

        return True

    say("Desculpe, ainda não aprendi sobre isso.")
    return True


def process_command_api(query):
    query = query.lower().strip()
    query = re.sub(r"^jarvis[\s,]*", "", query)
    query = query.lstrip(", ").strip()
    query = query.rstrip(string.punctuation)

    print(f"[API] Phrase after cleaning: {query}")

    if shutdown_command(query) is False:
        return "Shutting down Jarvis..."

    # DESACTIVATE FOR WEBSITE
    # if re.search(r"\b(pesquise|procure|busque)\s+(na\s+)?(internet|web)\b", query):
    #     if execute_search(query):
    #         return "Searching the internet..."

    for group in COMMAND_HANDLERS:
        if group in BLOCKED_COMMANDS_API:
            continue

        if isinstance(group, dict):
            for key, func in group.items():
                if key in query:
                    try:
                        result = func(query)
                        if isinstance(result, str):
                            return result
                        else:
                            return "Command executed."
                    except Exception as e:
                        print(f"[API Error COMMAND_HANDLERS] {e}")
                        return "There was an error executing the command."
        elif isinstance(group, list):
            for pattern, func in group:
                if re.search(pattern, query):
                    try:
                        result = func(query)
                        if isinstance(result, str):
                            return result
                        else:
                            return "Command executed."
                    except Exception as e:
                        print(f"[API Error COMMAND_HANDLERS] {e}")
                        return "There was an error executing the command."

    weather_response = handle_weather_query(query)

    if weather_response and isinstance(weather_response, str):
        return weather_response

    # Fallback para LLaMA3
    if query in response_cache:
        response = response_cache[query]
    else:
        start_time = time.time()
        response = llama_query(query, direct_mode=True, mode="site")
        end_time = time.time()

        generation_time = end_time - start_time

        if response:
            print(f"\n[API] LLaMA generated (in {generation_time:.2f} seconds)")
            response_cache[query] = response
        else:
            print(f"[API] LLaMA failed after {generation_time:.2f} seconds.")
            response = "Sorry, I couldn't generate a response."

    if response:
        log_interaction(query, response)

        return response

    return "Sorry, I didn't understand."
