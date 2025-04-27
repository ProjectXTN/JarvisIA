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
from brain.weatherAPI import handle_weather_query
from brain.weatherAPI import get_weather, is_weather_request, extract_city
from comandos.comandos_avatar import generate_avatar
from comandos.comandos_pesquisa import execute_search
from comandos.comandos_sistema import system_command, shutdown_command
from brain.llama_connection import llama_query

from brain.audio import say, listen
from brain.utils import log_interaction, normalize_country
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
    generate_avatar
]

def process_command(query):
    query = query.lower().strip()

    # Remove "jarvis" from the beginning, with or without comma/space
    query = re.sub(r"^jarvis[\s,]*", "", query)
    query = query.lstrip(", ").strip()
    query = query.rstrip(string.punctuation)

    print(f"[DEBUG] Received phrase: {query}")

    if shutdown_command(query) is False:
        return False

    # Still expecting search-related phrases in Portuguese
    if re.search(r"\b(pesquise|procure|busque)\s+(na\s+)?(internet|web)\b", query):
        if execute_search(query):
            return True

    for group in COMMAND_HANDLERS:
        if isinstance(group, dict):
            for key, func in group.items():
                if key in query:
                    print(f"[DEBUG] Executing command: {key}")
                    return func(query)
        elif isinstance(group, list):
            for pattern, func in group:
                if re.search(pattern, query):
                    print(f"[DEBUG] Executing regex: {pattern}")
                    return func(query)
    
    # Intelligently detects weather forecast request
    if handle_weather_query(query):
        return True

    # 🔁 Fallback using LLaMA3 + Cache
    if query in response_cache:
        response = response_cache[query]
        print("[DEBUG] Response retrieved from cache.")
    else:
        start_time = time.time()
        response = llama_query(query)
        end_time = time.time()
        print(f"⏱️ Time to generate response (turbo memory): {end_time - start_time:.2f} seconds.")

        if response:
            response_cache[query] = response

    if response:
        log_interaction(query, response)

        if "```" in response:
            print("[🤖 SAVING] Code detected via memory.")
            extract_and_save_code(response, titulo=query)
        say(response)
        return True

    say("Desculpe, ainda não aprendi sobre isso.")
    return True
