import re
import string
import time

from commands.commands_day_time import datetime_commands
from commands.commands_music import music_commands
from commands.commands_browser import browser_commands
from commands.commands_image import image_commands
from commands.commands_folders import comandos_pastas
from commands.comandos_software import software_commands
from commands.commands_multiples import multiple_commands
from commands.commands_memorie import comandos_memoria
from commands.commands_emotions import emotional_commands
from commands.commands_reflection import comandos_reflexao
from commands.commands_traduction import translation_commands
from commands.commands_search import execute_search
from commands.commands_avatar import generate_avatar, avatar_view_commands
from commands.commands_systeme import system_command, shutdown_command
from brain.weatherAPI.weatherAPI import handle_weather_query
from brain.storage.file_saver import save_response_to_file, should_save_to_file
from core.settings import STREAMING_ENABLED
from brain.memory.memory import llama_stream
from brain.memory.memory import llama_query, memory_context, remember_turn
from brain.pipeline.super_jarvis import super_jarvis_query
from brain.utils.querySensitive import is_query_time_sensitive
from brain.utils.utils import is_code_request
from brain.utils.inputs import markdown_instruction

from brain.audio import say, speak_stream
from brain.utils.utils import log_interaction

# Cache for responses to accelerate
response_cache = {}

# Join all command handlers with internal regex detection
COMMAND_HANDLERS = [
    avatar_view_commands,
    multiple_commands,
    software_commands,
    datetime_commands,
    music_commands,
    browser_commands,
    translation_commands,
    system_command,
    comandos_pastas,
    image_commands,
    comandos_memoria,
    comandos_reflexao,
    emotional_commands,
    generate_avatar,
]

BLOCKED_COMMANDS_API = [
    avatar_view_commands,
    music_commands,
    browser_commands,
    translation_commands,
    system_command,
    comandos_pastas,
    image_commands,
    comandos_memoria,
    comandos_reflexao,
    emotional_commands,
    generate_avatar,
]


def clean_query(query):
    query = query.lower().strip()
    query = re.sub(r"^jarvis[\s,]*", "", query)
    query = query.lstrip(", ").strip()
    return query.rstrip(string.punctuation)


def _matching_handlers(query, blocked=()):
    """Gera as funções de comando cujo gatilho aparece na frase."""
    for group in COMMAND_HANDLERS:
        if any(group is b for b in blocked):
            continue
        if isinstance(group, dict):
            for key, func in group.items():
                if key in query:
                    yield func
        elif isinstance(group, list):
            for pattern, func in group:
                if re.search(pattern, query):
                    yield func


def run_command_handlers(query, blocked=()):
    """Executa o primeiro comando que aceitar a frase.

    Devolve (True, resultado) se algum comando tratou a frase, ou
    (False, None) se nenhum tratou. Um comando que devolve False está dizendo
    "não era comigo": a busca continua e, no fim, a frase vai para o LLM.
    (Antes esse False era confundido com pedido de desligar.)
    """
    for func in _matching_handlers(query, blocked):
        try:
            result = func(query)
        except Exception as e:
            print(f"Error COMMAND_HANDLERS {e}")
            return True, e
        if result is not False:
            return True, result
    return False, None


# Pedidos explícitos de busca: sempre vão à internet, mesmo sem "na internet".
# Antes "procure sobre a nova versão do ChatGPT" era respondida só da memória
# do modelo, que ainda dizia ter pesquisado.
EXPLICIT_SEARCH = re.compile(
    r"\b(pesquise|pesquisa|pesquisar|procure|procura|procurar|busque|busca|buscar|"
    r"consulte|veja na internet|olhe na internet|search|look up)\b"
)


def is_explicit_search(query):
    return bool(EXPLICIT_SEARCH.search(query.lower()))


def generate_response(query, lang="pt", api=False, stream=False):
    """Resposta do LLM (com busca web quando o assunto é atual), ou None.

    stream=True (só na voz) devolve um gerador de pedaços de texto, para a
    fala começar antes de o modelo terminar. Pedidos de código e notícias
    continuam devolvendo o texto pronto.
    """
    stream = stream and not api
    start_time = time.time()
    response = None

    try:
        if is_code_request(query):
            response = llama_query(query, mode="code", lang=lang,
                                   history=[] if api else list(memory_context), remember=False)
            if response and not api:
                remember_turn(query, response)
        elif is_explicit_search(query) or is_query_time_sensitive(query):
            print("[DEBUG] Busca na internet (pedido explícito ou assunto atual).")
            response = super_jarvis_query(query, lang=lang, conversation=not api, stream=stream)
        else:
            print("[DEBUG] Timeless query. Using only LLaMA memory.")
            if stream:
                response = llama_stream(query, lang=lang)
            else:
                response = llama_query(query, lang=lang, mode="site" if api else None)
    except Exception as e:
        # Falha de rede, busca ou RAG não pode derrubar o Jarvis
        print(f"[ERROR] Falha ao gerar resposta: {e}")
        response = None

    generation_time = time.time() - start_time

    if response is not None and not isinstance(response, str):
        print(f"[DEBUG] Preparado em {generation_time:.2f}s; falando enquanto o modelo escreve.")
        return response

    if response:
        print(f"\nJarvis generated (in {generation_time:.2f} seconds)")
    else:
        print(
            f"LLaMA failed to generate a response after {generation_time:.2f} seconds."
        )

    return response or None


def process_command(query, lang="pt"):
    """Trata uma frase por voz. Devolve False apenas quando é para desligar."""
    query = clean_query(query)

    print(f"[DEBUG] Phrase after cleaning: {query}")

    if shutdown_command(query) is False:
        return False

    try:
        if handle_weather_query(query):
            return True
    except Exception as e:
        print(f"[ERROR] Clima falhou: {e}")


    handled, result = run_command_handlers(query)
    if handled:
        if isinstance(result, Exception):
            say("Houve um problema ao executar o comando. Tente novamente.")
        return True

    # 🔁 Fallback pipeline RAG+Web (super_jarvis_query)
    # Respostas de conversa dependem do histórico; cache só por texto é incorreto.
    response = generate_response(query, lang=lang, stream=STREAMING_ENABLED)

    if response is not None and not isinstance(response, str):
        # Fala em fluxo: guarda o texto inteiro enquanto fala as frases
        parts = []

        def collect():
            try:
                for piece in response:
                    parts.append(piece)
                    yield piece
            finally:
                closer = getattr(response, "close", None)
                if callable(closer):
                    closer()  # interrompido: encerra a conexão com o modelo

        speak_stream(collect())
        response = "".join(parts).strip() or None
        if response:
            log_interaction(query, response)
            if should_save_to_file(query):
                save_response_to_file(query, response)
            return True
        say("Desculpe, não consegui responder agora.")
        return True

    if response:
        log_interaction(query, response)

        say(response)

        if should_save_to_file(query):
            save_response_to_file(query, response)
        else:
            print("[DEBUG] Detecção: NÃO deve salvar a resposta.")

        return True

    say("Desculpe, não consegui responder agora.")
    return True


def process_command_api(query, lang="pt"):
    query = clean_query(query)

    if shutdown_command(query) is False:
        return "Shutting down Jarvis..."

    try:
        weather_response = handle_weather_query(query, lang=lang)
    except Exception as e:
        print(f"[API Error weather] {e}")
        weather_response = None

    handled, result = run_command_handlers(query, blocked=BLOCKED_COMMANDS_API)
    if handled:
        if isinstance(result, Exception):
            return "There was an error executing the command."
        if isinstance(result, str):
            return result
        return "Command executed."

    if weather_response and isinstance(weather_response, str):
        return weather_response

    # 🔁 Fallback pipeline RAG+Web (super_jarvis_query)
    response = response_cache.get(query)
    if not response:
        print(f"[DEBUG] Query API, {query}")
        response = generate_response(query, lang=lang, api=True)
        if response:
            response_cache[query] = response

    if response:
        log_interaction(query, response)
        return response

    return "Sorry, I couldn't generate a response."
