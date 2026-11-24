"""Dados do painel "o que o Jarvis sabe" (Fase 7, item 59).

Funções puras (sem Flask) usadas pelas rotas /painel do server.py: listar,
corrigir e apagar lembranças, fatos do perfil, aprendizados, opiniões, temas
de estudo, diário, compromissos e contradições.
"""
from brain import semantic_memory
from brain.persona.store import connect, lock

MEMORY_KINDS = ("perfil", "fato", "aprendido", "documento")
# tabela -> (colunas mostradas, coluna de ordem, colunas editáveis)
TABLES = {
    "opinioes": ("id, tema, opiniao, motivo, atualizado", "atualizado DESC", ("opiniao", "motivo")),
    "curiosidades": ("id, tema, motivo, origem, status, estudado", "id DESC", ("tema", "status")),
    "diario": ("data AS id, resumo, criado", "data DESC", ("resumo",)),
    "compromissos": ("id, quando, texto, avisado", "quando DESC", ("quando", "texto")),
    "contradicoes": ("id, memoria_a, memoria_b, explicacao, resolvida", "id DESC", ("resolvida",)),
}
_KEYS = {"diario": "data"}


def _rows(cursor):
    names = [d[0] for d in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def overview(limit=300):
    from brain.persona.iniciativa import _table

    _table()  # garante a tabela compromissos
    data = {}
    with semantic_memory._lock, semantic_memory._connect() as conn:
        for kind in MEMORY_KINDS:
            data[kind] = _rows(conn.execute(
                "SELECT id, assunto, texto, fonte, criado FROM memorias WHERE tipo = ? "
                "ORDER BY criado DESC LIMIT ?", (kind, limit)))
    with lock, connect() as conn:
        for table, (columns, order, _) in TABLES.items():
            data[table] = _rows(conn.execute(f"SELECT {columns} FROM {table} ORDER BY {order} LIMIT ?", (limit,)))
    return data


def edit_memory(memory_id, text, subject=None):
    text = (text or "").strip()
    if not text:
        raise ValueError("Texto vazio.")
    semantic_memory.update_text(int(memory_id), text[:4000], (subject or None))


def delete_memory(memory_id):
    with semantic_memory._lock, semantic_memory._connect() as conn:
        return conn.execute("DELETE FROM memorias WHERE id = ?", (int(memory_id),)).rowcount


def edit_row(table, row_id, field, value):
    if table not in TABLES or field not in TABLES[table][2]:
        raise ValueError("Campo não editável.")
    key = _KEYS.get(table, "id")
    with lock, connect() as conn:
        return conn.execute(f"UPDATE {table} SET {field} = ? WHERE {key} = ?", (value, row_id)).rowcount


def delete_row(table, row_id):
    if table not in TABLES:
        raise ValueError("Tabela desconhecida.")
    key = _KEYS.get(table, "id")
    with lock, connect() as conn:
        return conn.execute(f"DELETE FROM {table} WHERE {key} = ?", (row_id,)).rowcount
