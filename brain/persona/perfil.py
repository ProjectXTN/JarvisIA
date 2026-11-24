"""Memória de longo prazo sobre o Pedro (Fase 7, item 53).

Cada troca da conversa por voz fica na tabela "turnos". Quando o Jarvis volta
ao modo passivo (ou na abertura), um passo de fundo lê os turnos novos e pede
ao modelo os fatos duradouros sobre o Pedro: preferências, projetos, pessoas,
rotina. Cada fato vira uma lembrança tipo "perfil" na memória por semelhança;
um fato quase igual a outro já guardado substitui o antigo em vez de repetir.
"""
import threading
from datetime import datetime

from brain import semantic_memory
from brain.persona import llm
from brain.persona.store import connect, lock

CATEGORIES = ("preferência", "projeto", "pessoa", "rotina", "fato")
_running = threading.Lock()

EXTRACT_SYSTEM = (
    "Você extrai fatos DURADOUROS sobre Pedro a partir de uma conversa entre Pedro e o "
    "assistente Jarvis. Só o que Pedro disse ou confirmou sobre si: gostos, projetos, "
    "pessoas próximas, rotina, equipamentos, objetivos. Ignore perguntas de curiosidade, "
    "pedidos pontuais (abrir site, tocar música), conteúdo de buscas e o que o Jarvis "
    "disse. Não invente. Responda só JSON: "
    '{"fatos": [{"categoria": "preferência|projeto|pessoa|rotina|fato", '
    '"fato": "frase curta em terceira pessoa, começando com Pedro"}]}. '
    'Sem fatos novos: {"fatos": []}. No máximo 5.'
)


def record_turn(question, answer):
    if not question or not answer:
        return
    with lock, connect() as conn:
        conn.execute("INSERT INTO turnos (criado, pergunta, resposta) VALUES (?, ?, ?)",
                     (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), question[:2000], answer[:2000]))


def pending_turns(limit=40):
    with lock, connect() as conn:
        return conn.execute("SELECT id, pergunta, resposta FROM turnos WHERE processado = 0 "
                            "ORDER BY id LIMIT ?", (limit,)).fetchall()


def _valid(item):
    if not isinstance(item, dict):
        return None
    fact = str(item.get("fato", "")).strip()
    category = str(item.get("categoria", "fato")).strip().lower()
    if len(fact) < 8 or len(fact) > 300:
        return None
    return (category if category in CATEGORIES else "fato"), fact


def save_fact(category, fact):
    """Guarda ou atualiza (se já houver um quase igual). Devolve 'novo', 'atualizado' ou None."""
    similar = semantic_memory.search(fact, k=1, tipos=("perfil",), min_score=0.88)
    if similar:
        semantic_memory.update_text(similar[0]["id"], fact, category)
        return "atualizado"
    return "novo" if semantic_memory.add(category, fact, "conversa", "perfil") else None


def process_pending():
    """Extrai fatos dos turnos ainda não lidos. Seguro chamar de qualquer thread."""
    if not _running.acquire(blocking=False):
        return 0
    try:
        turns = pending_turns()
        if not turns:
            return 0
        talk = "\n".join(f"Pedro: {q}\nJarvis: {a[:400]}" for _, q, a in turns)
        result = llm.ask(EXTRACT_SYSTEM, talk, as_json=True, num_predict=400)
        facts = [f for f in (_valid(i) for i in (result or {}).get("fatos", [])) if f][:5]
        saved = [save_fact(c, f) for c, f in facts]
        with lock, connect() as conn:
            conn.executemany("UPDATE turnos SET processado = 1 WHERE id = ?", [(t[0],) for t in turns])
        if facts:
            print(f"[PERFIL] {len(facts)} fato(s) sobre Pedro: " + "; ".join(f for _, f in facts))
            from brain.persona.core import invalidate

            invalidate()
        return sum(1 for s in saved if s)
    except Exception as error:
        print(f"[PERFIL] Não consegui ler a conversa: {error}")
        return 0
    finally:
        _running.release()


def profile_facts(limit=15):
    """Os fatos mais recentes do perfil, para o bloco da personalidade (sem embedding)."""
    with semantic_memory._lock, semantic_memory._connect() as conn:
        rows = conn.execute("SELECT texto FROM memorias WHERE tipo = 'perfil' "
                            "ORDER BY criado DESC LIMIT ?", (limit,)).fetchall()
    return [r[0] for r in rows]
