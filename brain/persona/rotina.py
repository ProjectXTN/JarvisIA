"""Rotina de fundo do Jarvis (Fase 7): o que ele faz sozinho quando o PC está parado.

A cada minuto confere se:
  - a autonomia está ligada (JARVIS_AUTONOMY, ou por voz: "modo de estudo");
  - o Jarvis não atende ninguém há JARVIS_IDLE_MINUTES minutos;
  - no Windows, ninguém mexe no teclado e no mouse há esse tempo (jogo,
    filme, trabalho: a placa de vídeo fica livre para o Pedro).
Então, nesta ordem, faz uma coisa por vez:
  1. lê a conversa (perfil do Pedro, temas novos);
  2. escreve os diários que faltam;
  3. reflexão, uma vez por dia, a partir de JARVIS_REFLECT_HOUR;
  4. estuda um tema da lista (até JARVIS_STUDY_PER_DAY por dia).
Se o Pedro chamar o Jarvis no meio, o passo atual termina e o próximo espera.
"""
import ctypes
import threading
import time
from datetime import date, datetime

from core import config
from core.settings import AUTONOMY_ENABLED, IDLE_MINUTES, REFLECT_HOUR, STUDY_PER_DAY
from brain.persona.store import connect, lock

state = {"enabled": AUTONOMY_ENABLED, "thread": None}
_stop = threading.Event()


def mark_activity():
    """Chamado a cada pedido do Pedro."""
    config.LAST_ACTIVITY = time.monotonic()


def pc_idle_seconds():
    """Segundos sem teclado/mouse no Windows; em outro sistema, infinito."""
    try:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(info)
        if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            return float("inf")
        return (ctypes.windll.kernel32.GetTickCount() - info.dwTime) / 1000.0
    except (AttributeError, OSError):
        return float("inf")


def is_idle():
    limit = IDLE_MINUTES * 60
    jarvis_quiet = time.monotonic() - getattr(config, "LAST_ACTIVITY", 0.0) >= limit
    return jarvis_quiet and pc_idle_seconds() >= limit


def _get(key, default=""):
    with lock, connect() as conn:
        row = conn.execute("SELECT valor FROM rotina WHERE chave = ?", (key,)).fetchone()
    return row[0] if row else default


def _set(key, value):
    with lock, connect() as conn:
        conn.execute("INSERT OR REPLACE INTO rotina VALUES (?, ?)", (key, str(value)))


def studies_today():
    today = date.today().isoformat()
    if _get("estudo_dia") != today:
        return 0
    return int(_get("estudo_qtd", "0") or 0)


def _count_study():
    today = date.today().isoformat()
    count = studies_today() + 1
    _set("estudo_dia", today)
    _set("estudo_qtd", count)


def reflection_due(now=None):
    now = now or datetime.now()
    return _get("reflexao_dia") != now.date().isoformat() and now.hour >= REFLECT_HOUR


def step():
    """Um passo da rotina. Devolve o nome do que fez, ou None."""
    from brain.persona import diario, estudo, perfil, reflexao

    if perfil.pending_turns(limit=1):
        perfil.process_pending()
        return "perfil"
    if diario.days_without_diary():
        if diario.catch_up():
            return "diario"
    if reflection_due():
        reflexao.reflect()
        _set("reflexao_dia", date.today().isoformat())
        return "reflexao"
    if studies_today() < STUDY_PER_DAY:
        _count_study()  # conta antes: um tema que falha não vira repetição sem fim
        if estudo.study_one():
            return "estudo"
        return "estudo_sem_tema"
    return None


def _loop():
    config.MODEL_READY.wait(600)
    while not _stop.wait(60):
        try:  # lembretes valem mesmo com a autonomia desligada ou o PC em uso
            from brain.persona.iniciativa import check_and_announce

            check_and_announce()
        except Exception as error:
            print(f"[LEMBRETE] Falhou: {error}")
        if not state["enabled"] or not is_idle():
            continue
        try:
            done = step()
            if done:
                print(f"[ROTINA] {done} concluído.")
        except Exception as error:
            print(f"[ROTINA] Passo falhou: {error}")
            _stop.wait(600)  # Ollama ou internet fora: espera mais antes de tentar de novo


def start():
    if state["thread"] and state["thread"].is_alive():
        return
    _stop.clear()
    state["thread"] = threading.Thread(target=_loop, name="rotina-jarvis", daemon=True)
    state["thread"].start()


def enable(on=True):
    state["enabled"] = on
    if on:
        start()
