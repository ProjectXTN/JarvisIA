"""Lista de temas que o Jarvis quer estudar (Fase 7, item 55).

Alimentada por:
  - conversas: a leitura do perfil (perfil.py) devolve até 3 temas por vez;
  - pedido do Pedro: "estude sobre X" entra com prioridade alta;
  - interesses do Pedro: quando a lista esvazia, o modelo sugere temas ligados
    aos fatos do perfil (projetos, jogos, gostos).
"""
import re
from datetime import datetime

from brain.persona import llm
from brain.persona.store import connect, lock

SUGGEST_SYSTEM = (
    "Você é Jarvis e quer aprender coisas úteis ou interessantes para conversar com Pedro. "
    "Com base no que sabe dele, sugira temas concretos para estudar na internet: novidades, "
    "aprofundamentos, dúvidas práticas ligadas aos interesses e projetos dele. "
    'Responda só JSON: {"temas": [{"tema": "até 6 palavras", "motivo": "frase curta"}]}, no máximo 5.'
)


def _clean(theme):
    theme = re.sub(r"\s+", " ", str(theme or "")).strip(" .,:;!?\"'").lower()
    return theme if 3 <= len(theme) <= 80 else ""


def add(theme, reason="", origin="conversa", priority=1):
    """Anota um tema (ignora repetido). Devolve True se entrou."""
    theme = _clean(theme)
    if not theme:
        return False
    with lock, connect() as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO curiosidades (tema, motivo, origem, prioridade, criado) "
            "VALUES (?, ?, ?, ?, ?)",
            (theme, str(reason or "")[:200], origin, priority, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        if not cursor.rowcount and priority > 1:  # pedido do Pedro: sobe a prioridade
            conn.execute("UPDATE curiosidades SET prioridade = MAX(prioridade, ?), status = "
                         "CASE WHEN status = 'descartado' THEN 'pendente' ELSE status END WHERE tema = ?",
                         (priority, theme))
        added = bool(cursor.rowcount)
    if added:
        print(f"[CURIOSIDADE] Novo tema: {theme} ({origin})")
    return added


def next_theme():
    with lock, connect() as conn:
        return conn.execute("SELECT id, tema, motivo FROM curiosidades WHERE status = 'pendente' "
                            "ORDER BY prioridade DESC, id LIMIT 1").fetchone()


def mark(theme_id, status, result=""):
    with lock, connect() as conn:
        conn.execute("UPDATE curiosidades SET status = ?, estudado = ?, resultado = ? WHERE id = ?",
                     (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), result[:300], theme_id))


def pending(limit=20):
    with lock, connect() as conn:
        return [r[0] for r in conn.execute("SELECT tema FROM curiosidades WHERE status = 'pendente' "
                                           "ORDER BY prioridade DESC, id LIMIT ?", (limit,))]


def studied(limit=20):
    with lock, connect() as conn:
        return conn.execute("SELECT tema, estudado FROM curiosidades WHERE status = 'estudado' "
                            "ORDER BY estudado DESC LIMIT ?", (limit,)).fetchall()


def refill():
    """Lista vazia: pede ao modelo temas ligados ao que sabe do Pedro."""
    from brain.persona.perfil import profile_facts

    facts = profile_facts()
    if not facts:
        return 0
    with lock, connect() as conn:
        done = [r[0] for r in conn.execute("SELECT tema FROM curiosidades ORDER BY id DESC LIMIT 40")]
    user = "Sobre Pedro:\n" + "\n".join(f"- {f}" for f in facts)
    if done:
        user += "\nJá estudados ou anotados (não repita): " + ", ".join(done)
    result = llm.ask(SUGGEST_SYSTEM, user, as_json=True, num_predict=300) or {}
    return sum(add(i.get("tema"), i.get("motivo"), "interesses")
               for i in (result.get("temas") or [])[:5] if isinstance(i, dict))
