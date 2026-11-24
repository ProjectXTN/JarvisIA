"""Reflexão noturna (Fase 7, item 57).

Uma vez por dia, com o PC parado (de preferência à noite), o Jarvis:
  1. junta notas aprendidas repetidas (mesmo assunto, semelhança alta);
  2. procura contradições entre notas parecidas e anota na tabela contradicoes;
  3. forma ou atualiza até 2 opiniões a partir do que aprendeu e do diário.
"""
from datetime import date, datetime, timedelta

import numpy as np

from brain import semantic_memory
from brain.persona import llm
from brain.persona.store import connect, lock

MERGE_SYSTEM = (
    "Junte as duas anotações abaixo sobre o mesmo assunto em uma só, de 4 a 8 frases, sem "
    "perder fatos nem datas e sem inventar. Responda só com o texto final."
)
CONTRADICTION_SYSTEM = (
    "Compare as duas anotações. Elas se contradizem (afirmam fatos incompatíveis)? Responda "
    'só JSON: {"contradiz": true|false, "explicacao": "frase curta"}.'
)
OPINION_SYSTEM = (
    "Você é Jarvis, assistente de Pedro, com personalidade própria: curioso, franco, humor seco. "
    "Com base no que aprendeu e no diário, forme ou atualize até 2 opiniões suas, honestas e "
    "fundamentadas no que leu (não sobre política nem sobre pessoas). Responda só JSON: "
    '{"opinioes": [{"tema": "até 5 palavras", "opiniao": "1 frase", "motivo": "1 frase"}]}.'
)


def _vectors(tipo="aprendido", days=None):
    with semantic_memory._lock, semantic_memory._connect() as conn:
        sql = "SELECT id, assunto, texto, vetor, modelo, criado FROM memorias WHERE tipo = ? AND vetor IS NOT NULL"
        rows = conn.execute(sql, (tipo,)).fetchall()
    rows = [r for r in rows if r[4] == semantic_memory.EMBEDDING_MODEL]
    if not rows:
        return [], None
    matrix = np.stack([np.frombuffer(r[3], dtype=np.float32) for r in rows])
    return rows, matrix


def similar_pairs(low, high, recent_days=7, limit=10):
    """Pares (a, b, score) com semelhança em [low, high), um deles recente."""
    rows, matrix = _vectors()
    if matrix is None or len(rows) < 2:
        return []
    since = (datetime.now() - timedelta(days=recent_days)).strftime("%Y-%m-%d")
    scores = matrix @ matrix.T
    pairs = []
    for i in range(len(rows)):
        if rows[i][5] < since:
            continue
        for j in range(len(rows)):
            if i != j and low <= scores[i, j] < high and (rows[j][5] < since or j > i):
                pairs.append((rows[i], rows[j], float(scores[i, j])))
    pairs.sort(key=lambda p: -p[2])
    return pairs[:limit]


def merge_duplicates():
    merged = 0
    gone = set()
    for a, b, _ in similar_pairs(0.93, 1.01):
        if a[0] in gone or b[0] in gone:
            continue
        text = llm.ask(MERGE_SYSTEM, f"Assunto: {a[1]}\nAnotação 1: {a[2]}\nAnotação 2: {b[2]}", num_predict=500)
        if text and len(text) > 60:
            semantic_memory.update_text(a[0], text.strip(), a[1])
            with semantic_memory._lock, semantic_memory._connect() as conn:
                conn.execute("DELETE FROM memorias WHERE id = ?", (b[0],))
            gone.add(b[0])
            merged += 1
    return merged


def find_contradictions():
    found = 0
    for a, b, _ in similar_pairs(0.75, 0.93, limit=6):
        result = llm.ask(CONTRADICTION_SYSTEM, f"Anotação 1 ({a[1]}): {a[2]}\nAnotação 2 ({b[1]}): {b[2]}",
                         as_json=True, num_predict=120) or {}
        if result.get("contradiz") is True:
            with lock, connect() as conn:
                exists = conn.execute("SELECT 1 FROM contradicoes WHERE memoria_a = ? AND memoria_b = ?",
                                      (a[0], b[0])).fetchone()
                if not exists:
                    conn.execute("INSERT INTO contradicoes (memoria_a, memoria_b, explicacao, criado) "
                                 "VALUES (?, ?, ?, ?)", (a[0], b[0], str(result.get("explicacao", ""))[:300],
                                                         datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    found += 1
    return found


def update_opinions():
    since = (date.today() - timedelta(days=7)).isoformat()
    with semantic_memory._lock, semantic_memory._connect() as conn:
        learned = conn.execute("SELECT assunto, substr(texto, 1, 400) FROM memorias WHERE tipo = 'aprendido' "
                               "AND criado >= ? ORDER BY criado DESC LIMIT 8", (since,)).fetchall()
    with lock, connect() as conn:
        diaries = conn.execute("SELECT data, resumo FROM diario WHERE data >= ? ORDER BY data", (since,)).fetchall()
        current = conn.execute("SELECT tema, opiniao FROM opinioes ORDER BY atualizado DESC LIMIT 10").fetchall()
    if not learned and not diaries:
        return 0
    user = "Aprendido:\n" + "\n".join(f"- {a}: {t}" for a, t in learned)
    user += "\nDiário:\n" + "\n".join(f"- {d}: {r}" for d, r in diaries)
    if current:
        user += "\nSuas opiniões atuais (pode manter, ajustar ou mudar):\n" + "\n".join(f"- {t}: {o}" for t, o in current)
    result = llm.ask(OPINION_SYSTEM, user, as_json=True, num_predict=300) or {}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    saved = 0
    for item in (result.get("opinioes") or [])[:2]:
        if not isinstance(item, dict):
            continue
        theme = str(item.get("tema", "")).strip().lower()[:60]
        opinion = str(item.get("opiniao", "")).strip()[:300]
        if len(theme) < 3 or len(opinion) < 10:
            continue
        with lock, connect() as conn:
            conn.execute("INSERT INTO opinioes (tema, opiniao, motivo, criado, atualizado) VALUES (?, ?, ?, ?, ?) "
                         "ON CONFLICT(tema) DO UPDATE SET opiniao = excluded.opiniao, motivo = excluded.motivo, "
                         "atualizado = excluded.atualizado",
                         (theme, opinion, str(item.get("motivo", ""))[:300], now, now))
        saved += 1
    return saved


def reflect():
    merged = merge_duplicates()
    contradictions = find_contradictions()
    opinions = update_opinions()
    print(f"[REFLEXÃO] {merged} nota(s) juntadas, {contradictions} contradição(ões), {opinions} opinião(ões).")
    from brain.persona.core import invalidate

    invalidate()
    return merged, contradictions, opinions
