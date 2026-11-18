"""Cliente de conversa Ollama; apenas a voz compartilha memória."""
import json
import re
import threading
import time
import requests
from brain.utils.utils import clean_output
from brain.learning.personal_responses import check_personal_answer
from core.settings import (OLLAMA_HOST, OLLAMA_TIMEOUT, OLLAMA_KEEP_ALIVE,
    OLLAMA_NUM_CTX, NEWS_LLM_TIMEOUT, WEB_LLM_TIMEOUT, DEFAULT_MODEL, DEFAULT_MODEL_HIGH, DEFAULT_MODEL_CODE)

memory_context = []
MAX_CONTEXT = 5
_history_lock = threading.RLock()
session = requests.Session()
system_prompt = (
    "Você é Jarvis, o assistente pessoal de Pedro. Responda para uma conversa por voz: "
    "frases naturais, claras e curtas, normalmente de duas a quatro frases. "
    "Seja direto e prestativo, com humor discreto quando couber. "
    "Não use títulos, listas ou Markdown na fala. Detalhe quando solicitado. "
    "Admita incertezas; não invente fatos, fontes, lembranças nem ações executadas. "
    "Só afirme que pesquisou ou executou algo quando houver resultados de ferramentas. "
    "Ao fornecer código, preserve a sintaxe e a formatação em blocos de código."
)
site_system_prompt = terminal_prompt = system_prompt


def remember_turn(prompt, response):
    if prompt and response:
        with _history_lock:
            memory_context.append((prompt[:6000], response[:6000]))
            del memory_context[:-MAX_CONTEXT]


def clear_history():
    with _history_lock:
        memory_context.clear()


def _is_refusal(text):
    if not text or "```" in text:
        return False
    return bool(re.match(
        r"^(?:desculpe[,.: ]*|sinto muito[,.: ]*|sorry[,.: ]*)?"
        r"(?:não posso (?:ajudar|fornecer|criar|gerar)|não consigo (?:criar|gerar)|"
        r"i (?:cannot|can't) (?:help|provide|create)|je ne peux pas)",
        text.strip(), re.IGNORECASE))


def _read_timeout(mode):
    """Limite de espera por modo: notícias e busca web não podem travar a voz."""
    if mode == "news":
        return (OLLAMA_TIMEOUT[0], min(OLLAMA_TIMEOUT[1], NEWS_LLM_TIMEOUT))
    if mode == "web":
        return (OLLAMA_TIMEOUT[0], min(OLLAMA_TIMEOUT[1], WEB_LLM_TIMEOUT))
    if mode == "rewrite":
        return (OLLAMA_TIMEOUT[0], 15)
    if mode == "route":
        return (OLLAMA_TIMEOUT[0], 8)
    return OLLAMA_TIMEOUT


def _build_messages(prompt, lang, history, use_voice_history, images=None):
    instruction = {"pt": "Responda em português brasileiro.",
                   "fr": "Répondez en français.", "en": "Reply in English."}.get(lang, "Responda no idioma do usuário.")
    messages = [{"role": "system", "content": system_prompt + " " + instruction}]
    if history is None:
        with _history_lock:
            turns = list(memory_context) if use_voice_history else []
    else:
        turns = list(history)
    for question, answer in turns[-MAX_CONTEXT:]:
        messages.extend([{"role": "user", "content": question},
                         {"role": "assistant", "content": answer}])
    user_message = {"role": "user", "content": prompt}
    if images:
        user_message["images"] = images
    messages.append(user_message)
    return messages


def open_chat(messages, model=None, tools=None, num_predict=512, timeout=None):
    """Abre uma conversa em stream com o Ollama e confere a resposta HTTP.

    É síncrono de propósito: um erro (Ollama fora do ar, modelo que não aceita
    ferramentas) aparece aqui, antes de a fala começar, para quem chamou poder
    usar outro caminho. Devolve a resposta HTTP aberta; leia com iter_chat().
    """
    payload = {
        "model": model or DEFAULT_MODEL, "messages": messages, "stream": True,
        "think": False, "keep_alive": OLLAMA_KEEP_ALIVE,
        "options": {"temperature": 0.2, "num_ctx": OLLAMA_NUM_CTX, "num_predict": num_predict},
    }
    if tools:
        payload["tools"] = tools
    started = time.monotonic()
    response = session.post(f"{OLLAMA_HOST}/api/chat", json=payload,
                            timeout=timeout or _read_timeout("web"), stream=True)
    response.jarvis_started = started  # para medir o tempo até as primeiras palavras
    if response.status_code >= 400:
        detail = response.text[:300]
        response.close()
        raise RuntimeError(f"Ollama respondeu {response.status_code}: {detail}")
    return response


def iter_chat(response, tool_calls=None, parts=None):
    """Lê o stream aberto por open_chat: devolve os pedaços de texto e guarda
    as chamadas de ferramenta em tool_calls e o texto inteiro em parts."""
    started = getattr(response, "jarvis_started", None) or time.monotonic()
    first = True
    try:
        for line in response.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            if data.get("error"):
                raise RuntimeError(data["error"])
            message = data.get("message", {})
            if tool_calls is not None and message.get("tool_calls"):
                tool_calls.extend(message["tool_calls"])
                print(f"[LLM] Ferramentas escolhidas em {time.monotonic()-started:.1f}s.")
            piece = message.get("content", "")
            if piece:
                if first:
                    print(f"[LLM] Primeiras palavras em {time.monotonic()-started:.1f}s.")
                    first = False
                if parts is not None:
                    parts.append(piece)
                yield piece
            if data.get("done"):
                break
    finally:
        response.close()


def llama_stream(prompt, model=None, direct_mode=False, mode=None, lang="pt",
                 history=None, remember=None, on_complete=None):
    """Como llama_query, mas devolve a resposta em pedaços, à medida que o
    modelo escreve (stream do Ollama). Serve para a fala começar antes do fim.

    Guarda o turno no histórico só quando a resposta termina. on_complete(texto)
    é chamado no fim com a resposta inteira. Em erro, para de gerar; o que já
    saiu continua valendo.
    """
    use_voice_history = not direct_mode and mode not in ("site", "code", "vision") and history is None
    if remember is None:
        remember = use_voice_history
    personal = check_personal_answer(prompt) if not direct_mode else None
    if personal:
        if remember:
            remember_turn(prompt, personal)
        if on_complete:
            on_complete(personal)
        yield personal
        return
    messages = _build_messages(prompt, lang, history, use_voice_history)
    candidate = model or DEFAULT_MODEL
    started = time.monotonic()
    parts = []
    response = None
    print(f"[LLM] Gerando resposta em stream com {candidate} ({sum(len(m['content']) for m in messages)} caracteres)...", flush=True)
    try:
        response = session.post(
            f"{OLLAMA_HOST}/api/chat",
            json={"model": candidate, "messages": messages, "stream": True,
                  "think": False, "keep_alive": OLLAMA_KEEP_ALIVE,
                  "options": {"temperature": 0.2, "num_ctx": OLLAMA_NUM_CTX,
                              "num_predict": {"news": 192}.get(mode, 512)}},
            timeout=_read_timeout(mode), stream=True)
        response.raise_for_status()
        first = True
        for line in response.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            if data.get("error"):
                raise RuntimeError(data["error"])
            piece = data.get("message", {}).get("content", "")
            if piece:
                if first:
                    print(f"[LLM] Primeiras palavras em {time.monotonic()-started:.1f}s.")
                    first = False
                parts.append(piece)
                yield piece
            if data.get("done"):
                break
        print(f"[LLM] Resposta completa em {time.monotonic()-started:.1f}s.")
    except GeneratorExit:
        print("[LLM] Stream encerrado (você interrompeu).")
        raise
    except Exception as error:
        print(f"[ERROR] Falha no Ollama ({candidate}): {error}")
    finally:
        if response is not None:
            response.close()
        output = clean_output("".join(parts)).strip()
        if output:
            if remember:
                remember_turn(prompt, output)
            if on_complete:
                on_complete(output)


def llama_query(prompt, model=None, direct_mode=False, mode=None, lang="pt",
                history=None, remember=None, images=None):
    """Texto ou None. Resumos/API não alteram a conversa; history isola sessões."""
    use_voice_history = not direct_mode and mode not in ("site", "code", "vision") and history is None
    if remember is None:
        remember = use_voice_history
    personal = check_personal_answer(prompt) if not direct_mode and mode != "code" else None
    if personal:
        if remember:
            remember_turn(prompt, personal)
        return personal
    messages = _build_messages(prompt, lang, history, use_voice_history, images)
    chosen = model or DEFAULT_MODEL
    candidates = [chosen]
    if mode == "code" and chosen != DEFAULT_MODEL_CODE:
        candidates.append(DEFAULT_MODEL_CODE)
    original_refusal = None
    for index, candidate in enumerate(candidates):
        started = time.monotonic()
        finished = threading.Event()
        def progress(model_name=candidate, stop=finished, since=started):
            while not stop.wait(10):
                print(f"[LLM] {model_name}: aguardando há {time.monotonic()-since:.0f}s...", flush=True)
        threading.Thread(target=progress, daemon=True).start()
        try:
            print(f"[LLM] Gerando resposta com {candidate} ({sum(len(m['content']) for m in messages)} caracteres)...", flush=True)
            response = session.post(
                f"{OLLAMA_HOST}/api/chat",
                json={"model": candidate, "messages": messages, "stream": False,
                      "think": False, "keep_alive": OLLAMA_KEEP_ALIVE,
                      "options": {"temperature": 0.2, "num_ctx": OLLAMA_NUM_CTX,
                                  "num_predict": {"code": 2048, "news": 192, "rewrite": 64, "route": 4}.get(mode, 512)}},
                timeout=_read_timeout(mode))
            response.raise_for_status()
            print(f"[LLM] Resposta recebida em {time.monotonic()-started:.1f}s.")
            raw = response.json()["message"]["content"].strip()
            if not raw:
                return original_refusal
            if mode == "code" and index == 0 and len(candidates) > 1 and _is_refusal(raw):
                original_refusal = raw
                print("[LLM] Recusa explícita; tentando o modelo reserva de código.")
                continue
            output = raw if mode == "code" else clean_output(raw)
            if not output:
                return None
            if remember:
                remember_turn(prompt, output)
            return output
        except Exception as error:
            print(f"[ERROR] Falha no Ollama ({candidate}): {error}")
            return original_refusal
        finally:
            finished.set()
    return None
