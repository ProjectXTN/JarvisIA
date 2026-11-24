import re
import threading
import string
import time

from commands.commands_day_time import datetime_commands
from commands.commands_music import music_commands, music_control_commands
from commands.commands_browser import browser_commands
from commands.commands_image import image_commands
from commands.commands_folders import comandos_pastas
from commands.comandos_software import software_commands
from commands.commands_memorie import comandos_memoria
from commands.commands_emotions import emotional_commands
from commands.commands_reflection import comandos_reflexao
from commands.commands_traduction import translation_commands
from commands.commands_search import execute_search
from commands.commands_avatar import generate_avatar, avatar_view_commands
from commands.commands_systeme import system_command, shutdown_command
from brain.weatherAPI.weatherAPI import handle_weather_query
from brain.storage.file_saver import save_response_to_file, should_save_to_file
from core.settings import STREAMING_ENABLED, WEB_ROUTER_ENABLED, TOOL_ROUTER_ENABLED
from brain import tool_router
from core import config
from brain.pipeline.super_jarvis import today_line
from brain.memory.memory import llama_stream
from brain.memory.memory import llama_query, memory_context, remember_turn
from brain.pipeline.super_jarvis import super_jarvis_query
from brain.utils.querySensitive import is_query_time_sensitive
from brain.utils.utils import is_code_request
from brain.utils.inputs import markdown_instruction

from brain.audio import say, speak_stream
from brain.utils.utils import log_interaction

class ResponseCache:
    """Cache da API do site: respostas valem 10 minutos e no máximo 200 ficam
    guardadas. Antes não havia validade nem limite: uma resposta sobre
    notícias do dia ficava guardada para sempre."""

    def __init__(self, ttl=600, max_items=200):
        self.ttl, self.max_items = ttl, max_items
        self._items = {}

    def get(self, key):
        item = self._items.get(key)
        if item is None:
            return None
        saved_at, value = item
        if time.monotonic() - saved_at > self.ttl:
            del self._items[key]
            return None
        return value

    def __setitem__(self, key, value):
        self._items.pop(key, None)
        self._items[key] = (time.monotonic(), value)
        while len(self._items) > self.max_items:
            del self._items[next(iter(self._items))]  # o mais antigo sai primeiro

    def __len__(self):
        return len(self._items)


response_cache = ResponseCache()

# Join all command handlers with internal regex detection
COMMAND_HANDLERS = [
    avatar_view_commands,
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

# Atalhos que rodam antes do modelo (item 33): frases inequívocas e rápidas
def open_chat_window(query=None):
    from brain import chat_window

    chat_window.open_window()
    say("Abri a janela para você escrever.")
    return True


chat_commands = [
    (r"\b(abr[aei]r?|abre|mostr[ae]r?|quero|preciso)\b.*\b(chat|janela de (texto|conversa|escrever)|"
     r"caixa de texto|lugar (pra|para) escrever)\b", open_chat_window),
    (r"\b(quero|vou|deixa eu|prefiro|preciso)\s+(te\s+)?(escrever|digitar)\b", open_chat_window),
]


SHORTCUT_HANDLERS = [
    chat_commands,
    datetime_commands,
    music_control_commands,
    avatar_view_commands,
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


def _matching_handlers(query, blocked=(), handlers=None):
    """Gera as funções de comando cujo gatilho aparece na frase."""
    for group in COMMAND_HANDLERS if handlers is None else handlers:
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


def run_command_handlers(query, blocked=(), handlers=None):
    """Executa o primeiro comando que aceitar a frase.

    Devolve (True, resultado) se algum comando tratou a frase, ou
    (False, None) se nenhum tratou. Um comando que devolve False está dizendo
    "não era comigo": a busca continua e, no fim, a frase vai para o LLM.
    (Antes esse False era confundido com pedido de desligar.)
    """
    for func in _matching_handlers(query, blocked, handlers):
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


def needs_web(query, history=None):
    """Pergunta ao modelo se a resposta depende de informação atual.

    Usado quando as regras fixas acham a pergunta atemporal. Exemplo que elas
    perdiam: "o que é esse apagão que estão falando?". Em falha, não busca.
    """
    if not WEB_ROUTER_ENABLED:
        return False
    try:
        turns = "".join(
            f"Pedro: {q[:200]}\nJarvis: {a[:200]}\n" for q, a in list(history or [])[-2:]
        )
        prompt = (
            f"{today_line('pt')}\n"
            "Decida se a pergunta precisa de busca na internet para ser respondida corretamente. "
            "Responda BUSCAR se ela depende de fatos atuais ou recentes: notícias, boatos, "
            "eventos, lançamentos, versões de produtos, preços, resultados, quem ocupa um "
            "cargo hoje, coisas 'que estão falando', ou qualquer assunto que possa ter mudado "
            "depois do seu treinamento. Responda RESPONDER se é conhecimento estável "
            "(definições, explicações, história, ciência, matemática, conselhos), conversa, "
            "opinião ou assunto pessoal.\n"
            + (f"Conversa recente:\n{turns}" if turns else "")
            + f"Pergunta: {query}\nResponda só com uma palavra: BUSCAR ou RESPONDER."
        )
        answer = llama_query(prompt, direct_mode=True, mode="route", remember=False)
    except Exception as error:
        print(f"[ROTA] Falha ao decidir, respondendo sem buscar: {error}")
        return False
    decision = bool(answer and "BUSCAR" in answer.upper())
    print(f"[ROTA] Modelo decidiu: {'buscar na internet' if decision else 'responder direto'}.")
    return decision


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
        elif (is_explicit_search(query) or is_query_time_sensitive(query)
              or needs_web(query, [] if api else list(memory_context))):
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


# Voz e janela de texto não atendem ao mesmo tempo
_command_lock = threading.RLock()


def process_command(query, lang="pt"):
    """Trata uma frase (falada ou escrita). Devolve False apenas quando é para desligar."""
    try:
        from brain.chat_window import publish

        publish("pedro", query)
    except Exception:
        pass
    with _command_lock:
        config.NOT_BUSY.clear()  # lembretes da rotina esperam terminar
        try:
            return _process_command(query, lang)
        finally:
            config.NOT_BUSY.set()




def _process_command(query, lang="pt"):
    query = clean_query(query)

    print(f"[DEBUG] Phrase after cleaning: {query}")

    if shutdown_command(query) is False:
        return False

    from brain.persona.rotina import mark_activity

    mark_activity()  # a rotina de fundo (estudo, reflexão) espera o Pedro parar

    # Atalhos sem modelo: instantâneos e sem ambiguidade (hora, data, música, avatar)
    handled, result = run_command_handlers(query, handlers=SHORTCUT_HANDLERS)
    if handled:
        return True

    # Depois de reiniciar o PC o modelo ainda pode estar saindo do disco
    if not config.MODEL_READY.is_set():
        say("Ainda estou carregando, só um instante.")
        started = time.monotonic()
        config.MODEL_READY.wait(240)
        print(f"[OLLAMA] Esperei {time.monotonic() - started:.0f}s o modelo terminar de carregar.")

    # Fase 4: o modelo decide (responder, buscar, abrir, tocar...)
    if TOOL_ROUTER_ENABLED:
        try:
            answer = tool_router.handle(query, lang=lang)
        except tool_router.RouterUnavailable as error:
            print(f"[ROTEADOR] Indisponível ({error}); usando as regras antigas.")
        else:
            if answer:
                log_interaction(query, answer)
                if should_save_to_file(query):
                    save_response_to_file(query, answer)
            else:
                say("Desculpe, não consegui responder agora.")
            return True

    # Caminho antigo (regras de palavras), usado se o roteador estiver desligado ou falhar
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


def is_raw_prompt(text):
    """Instrução pronta de um app (o site manda prompts longos, como o do gráfico em JSON)."""
    low = text.lower()
    return len(text) > 300 or "return only the json" in low or "responda só o json" in low


def process_command_api(query, lang="pt"):
    # Prompt pronto do site: vai direto ao modelo, sem comandos, clima nem busca na
    # internet (antes o JSON do gráfico de conceitos virava uma busca no Brave)
    if is_raw_prompt(query):
        cached = response_cache.get(query)
        if cached:
            return cached
        print(f"[API] Prompt direto ({len(query)} caracteres).")
        response = llama_query(query.strip(), direct_mode=True, mode="prompt", lang=lang)
        if response:
            response_cache[query] = response
            return response
        return "Sorry, I couldn't generate a response."

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
