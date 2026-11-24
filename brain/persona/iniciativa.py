"""Iniciativa do Jarvis (Fase 7, item 58).

  - Compromissos: Pedro pede "me lembra amanhã às 15h de ligar para o banco";
    o modelo chama lembrar_compromisso e, na hora, o Jarvis avisa por voz
    (espera terminar de atender se estiver ocupado).
  - Ao abrir o Jarvis: lembra os compromissos do dia e puxa UM assunto do que
    aprendeu sozinho desde a última conversa ("Enquanto você estava fora...").
    A frase entra no histórico, então "sim, conta" funciona em seguida.
"""
import re
from datetime import datetime, timedelta

from brain.persona.store import connect, lock

_FORMATS = ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M", "%Y-%m-%d")


def _table():
    with lock, connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS compromissos (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                     "quando TEXT, texto TEXT, criado TEXT, avisado INTEGER DEFAULT 0)")
        conn.execute("CREATE TABLE IF NOT EXISTS mencionados (memoria INTEGER PRIMARY KEY)")


def parse_when(value):
    value = re.sub(r"\s+", " ", str(value or "").strip().replace("Z", ""))
    value = re.sub(r"([+-]\d{2}:\d{2})$", "", value)
    for fmt in _FORMATS:
        try:
            when = datetime.strptime(value, fmt)
            return when.replace(hour=9) if fmt == "%Y-%m-%d" else when
        except ValueError:
            continue
    return None


def add_reminder(when, text):
    _table()
    moment = parse_when(when)
    if not moment or not str(text or "").strip():
        return None
    with lock, connect() as conn:
        conn.execute("INSERT INTO compromissos (quando, texto, criado) VALUES (?, ?, ?)",
                     (moment.strftime("%Y-%m-%d %H:%M"), str(text).strip()[:300],
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    return moment


def upcoming(days=7, now=None):
    _table()
    now = now or datetime.now()
    with lock, connect() as conn:
        return conn.execute("SELECT id, quando, texto FROM compromissos WHERE avisado = 0 AND quando >= ? "
                            "AND quando <= ? ORDER BY quando",
                            (now.strftime("%Y-%m-%d 00:00"),
                             (now + timedelta(days=days)).strftime("%Y-%m-%d 23:59"))).fetchall()


def due(now=None):
    """Compromissos cuja hora chegou e que ainda não foram avisados (até 12 h de atraso)."""
    _table()
    now = now or datetime.now()
    with lock, connect() as conn:
        return conn.execute("SELECT id, quando, texto FROM compromissos WHERE avisado = 0 AND quando <= ? "
                            "AND quando >= ? ORDER BY quando",
                            (now.strftime("%Y-%m-%d %H:%M"),
                             (now - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M"))).fetchall()


def mark_told(reminder_id):
    with lock, connect() as conn:
        conn.execute("UPDATE compromissos SET avisado = 1 WHERE id = ?", (reminder_id,))


def cancel(text):
    _table()
    with lock, connect() as conn:
        rows = conn.execute("SELECT id, texto FROM compromissos WHERE avisado = 0").fetchall()
        words = set(re.findall(r"\w{3,}", text.lower()))
        best = max(rows, key=lambda r: len(words & set(re.findall(r"\w{3,}", r[1].lower()))), default=None)
        if best and words & set(re.findall(r"\w{3,}", best[1].lower())):
            conn.execute("DELETE FROM compromissos WHERE id = ?", (best[0],))
            return best[1]
    return None


def spoken_time(moment, now=None):
    now = now or datetime.now()
    hour = f"{moment.hour}h{moment.minute:02d}" if moment.minute else f"{moment.hour}h"
    if moment.date() == now.date():
        return f"hoje às {hour}"
    if moment.date() == (now + timedelta(days=1)).date():
        return f"amanhã às {hour}"
    return f"dia {moment:%d/%m} às {hour}"


def check_and_announce():
    """Chamado pela rotina a cada minuto: avisa os compromissos que chegaram."""
    from core import config

    for reminder_id, when, text in due():
        config.NOT_BUSY.wait(120)  # espera terminar de atender o Pedro
        from brain.audio import say

        say(f"Pedro, lembrete: {text}.")
        mark_told(reminder_id)
        print(f"[LEMBRETE] {when}: {text}")


def new_learning(limit=1):
    """Aprendizados do estudo autônomo ainda não mencionados ao Pedro."""
    _table()
    from brain import semantic_memory

    with semantic_memory._lock, semantic_memory._connect() as conn:
        return conn.execute(
            "SELECT id, assunto, texto FROM memorias WHERE tipo = 'aprendido' AND fonte LIKE '%estudado sozinho%' "
            "AND id NOT IN (SELECT memoria FROM mencionados) ORDER BY criado DESC LIMIT ?", (limit,)).fetchall()


def opening_lines(now=None):
    """Frases curtas para depois do bom-dia. Marca o que foi dito."""
    now = now or datetime.now()
    lines = []
    today = [r for r in upcoming(days=0, now=now) if r[1][:10] == now.strftime("%Y-%m-%d")]
    if today:
        items = "; ".join(f"{spoken_time(parse_when(q), now)}, {t}" for _, q, t in today[:3])
        lines.append(f"Seus compromissos de hoje: {items}.")
    learned = new_learning()
    if learned:
        memory_id, subject, _ = learned[0]
        lines.append(f"Enquanto você estava fora, estudei sobre {subject}. Quer que eu conte?")
        with lock, connect() as conn:
            conn.execute("INSERT OR IGNORE INTO mencionados VALUES (?)", (memory_id,))
    return lines
