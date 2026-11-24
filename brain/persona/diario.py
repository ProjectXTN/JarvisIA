"""Diário do Jarvis (Fase 7, item 54).

Na abertura (e ao voltar ao modo passivo), se um dia anterior teve conversa e
ainda não tem diário, o Jarvis escreve um resumo curto: do que falaram, o que
ele aprendeu e o que ficou pendente. O diário de ontem entra na personalidade.
"""
from datetime import date, datetime

from brain.persona import llm
from brain.persona.store import connect, lock

DIARY_SYSTEM = (
    "Você é Jarvis, assistente pessoal de Pedro, escrevendo seu diário em primeira pessoa. "
    "Com base nas conversas do dia, escreva de 3 a 5 frases: do que vocês falaram, o que "
    "você aprendeu, o que ficou pendente ou vale retomar. Sem listas, sem inventar."
)


def days_without_diary(today=None):
    today = today or date.today().isoformat()
    with lock, connect() as conn:
        return [r[0] for r in conn.execute(
            "SELECT DISTINCT substr(criado, 1, 10) AS dia FROM turnos WHERE dia < ? "
            "AND dia NOT IN (SELECT data FROM diario) ORDER BY dia", (today,))]


def write_day(day):
    with lock, connect() as conn:
        turns = conn.execute("SELECT pergunta, resposta FROM turnos WHERE substr(criado, 1, 10) = ? "
                             "ORDER BY id", (day,)).fetchall()
        learned = []
        try:
            learned = conn.execute("SELECT assunto FROM memorias WHERE tipo = 'aprendido' "
                                   "AND substr(criado, 1, 10) = ?", (day,)).fetchall()
        except Exception:
            pass
    if not turns:
        return None
    talk = "\n".join(f"Pedro: {q}\nJarvis: {a[:300]}" for q, a in turns[-60:])
    if learned:
        talk += "\nAssuntos que você estudou: " + ", ".join(r[0] for r in learned)
    summary = llm.ask(DIARY_SYSTEM, f"Dia {day}:\n{talk}", num_predict=300)
    if summary:
        with lock, connect() as conn:
            conn.execute("INSERT OR REPLACE INTO diario VALUES (?, ?, ?)",
                         (day, summary.strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        print(f"[DIÁRIO] {day}: {summary.strip()[:160]}")
    return summary


def catch_up(max_days=3):
    """Escreve os diários que faltam (os mais recentes, até max_days)."""
    written = 0
    for day in days_without_diary()[-max_days:]:
        try:
            if write_day(day):
                written += 1
        except Exception as error:
            print(f"[DIÁRIO] Não consegui escrever {day}: {error}")
            break
    if written:
        from brain.persona.core import invalidate

        invalidate()
    return written


def read(day):
    with lock, connect() as conn:
        row = conn.execute("SELECT resumo FROM diario WHERE data = ?", (day,)).fetchone()
    return row[0] if row else None
