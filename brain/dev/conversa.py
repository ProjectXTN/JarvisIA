"""Conversa entre o programador (em segundo plano) e o Pedro (Fase 8+).

O programador trabalha numa thread própria; quando precisa de algo (uma dúvida,
a aprovação do plano), chama ask(): a pergunta aparece na janela de texto,
o Jarvis fala um resumo e a thread espera. O Pedro responde por voz ou escrevendo
no chat: o roteador vê que há uma pergunta pendente e chama a ferramenta
responder_programador, que entrega a resposta aqui.
"""
import threading
import time

_lock = threading.Lock()
_state = {"pergunta": None}
cancel_flag = threading.Event()


def pending():
    """A pergunta que está esperando resposta (dict) ou None."""
    with _lock:
        return dict(_state["pergunta"]) if _state["pergunta"] else None


def answer(text):
    """Entrega a resposta do Pedro. False se não havia pergunta esperando."""
    with _lock:
        current = _state["pergunta"]
        if not current:
            return False
        current["resposta"] = str(text or "").strip()
        current["evento"].set()
        return True


def ask(question, app_name, say=None, timeout=900, kind="pergunta", detail=""):
    """Pergunta ao Pedro e espera (até `timeout` s). Devolve a resposta ou None.

    question: frase curta, que o Jarvis fala. detail: texto longo (plano,
    opções), que só aparece na janela de texto.
    """
    event = threading.Event()
    with _lock:
        _state["pergunta"] = {"texto": question, "app": app_name, "tipo": kind,
                              "evento": event, "resposta": None, "desde": time.time()}
    try:
        try:
            from brain import chat_window

            chat_window.publish("jarvis", f"[{app_name}] {detail}\n\n{question}".strip() if detail else
                                f"[{app_name}] {question}")
        except Exception:
            pass
        if say:
            say(question if len(question) <= 220 else
                f"Tenho uma pergunta sobre o app {app_name}. Está na janela de texto.")
        print(f"[DEV] Esperando o Pedro ({kind}): {question}")
        deadline = time.monotonic() + timeout
        while not event.wait(1):
            if cancel_flag.is_set() or time.monotonic() > deadline:
                return None
        return _state["pergunta"]["resposta"]
    finally:
        with _lock:
            _state["pergunta"] = None
