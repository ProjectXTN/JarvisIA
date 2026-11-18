"""Memória por semelhança (Fase 5): lembranças e documentos.

Antes a memória só achava um assunto pelo nome exato ("minha impressora" e
"impressora" eram coisas diferentes) e os documentos usavam o llama-index,
que pesava na abertura. Aqui cada texto é guardado com um vetor de
significado (embedding, gerado no Ollama) e a busca é por semelhança.

Tudo fica no mesmo banco SQLite (tabela "memorias"):
  - tipo "fato": o que Pedro pediu para lembrar;
  - tipo "aprendido": o que Jarvis pesquisou e guardou;
  - tipo "documento": trechos dos arquivos da pasta de documentos.

Sem o modelo de embeddings, a busca cai para comparação de palavras.
"""

import hashlib
import os
import re
import sqlite3
import threading
import time
from datetime import datetime

import numpy as np
import requests

from core.settings import (
    DOCS_DIR,
    EMBEDDING_MODEL,
    EMBEDDING_ON_GPU,
    MEMORY_DB,
    OLLAMA_HOST,
    OLLAMA_KEEP_ALIVE,
)

_lock = threading.RLock()
# Instrução de consulta recomendada para modelos qwen3-embedding
_QUERY_PREFIX = "Instruct: Dada uma pergunta, encontre lembranças e trechos relevantes\nQuery: "
# Textos que o estudo automático antigo guardou como se fossem conhecimento
_JUNK = re.compile(r"^(não consegui|nenhum resultado|erro|api key|desculpe)", re.I)


# ----------------------------------------------------------------- vetores
def embed(texts, query=False):
    """Vetores normalizados (np.float32) dos textos, ou None se o modelo faltar."""
    if not texts:
        return []
    inputs = [(_QUERY_PREFIX + t) if query else t for t in texts]
    options = {"num_ctx": 2048}
    if not EMBEDDING_ON_GPU:
        options["num_gpu"] = 0  # fica na CPU e não disputa a VRAM com o gemma4
    started = time.monotonic()
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/embed",
            json={"model": EMBEDDING_MODEL, "input": inputs, "truncate": True,
                  "options": options, "keep_alive": OLLAMA_KEEP_ALIVE},
            timeout=(3, 30),
        )
        response.raise_for_status()
        vectors = np.asarray(response.json()["embeddings"], dtype=np.float32)
    except Exception as error:
        print(f"[MEMÓRIA] Embeddings indisponíveis ({EMBEDDING_MODEL}): {error}")
        return None
    elapsed = time.monotonic() - started
    if elapsed > 1:
        print(f"[MEMÓRIA] Embeddings de {len(texts)} texto(s) em {elapsed:.1f}s.")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.where(norms == 0, 1, norms)


def _words(text):
    return set(re.findall(r"\w{3,}", text.lower()))


# ------------------------------------------------------------------- banco
def _connect():
    conn = sqlite3.connect(MEMORY_DB)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS memorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            assunto TEXT,
            texto TEXT NOT NULL,
            fonte TEXT,
            criado TEXT,
            vetor BLOB,
            modelo TEXT,
            hash TEXT
        )"""
    )
    return conn


def add(assunto, texto, fonte="Pedro", tipo="fato", file_hash=None):
    """Guarda uma lembrança. Devolve o id, ou None se não deu para guardar."""
    texto = (texto or "").strip()
    if not texto:
        return None
    vector = embed([f"{assunto}: {texto}" if assunto else texto])
    blob = vector[0].tobytes() if vector is not None and len(vector) else None
    with _lock, _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO memorias (tipo, assunto, texto, fonte, criado, vetor, modelo, hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (tipo, (assunto or "").lower(), texto, fonte,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"), blob,
             EMBEDDING_MODEL if blob else None, file_hash),
        )
        return cursor.lastrowid


def search(consulta, k=3, tipos=("fato", "aprendido"), min_score=0.45):
    """As k lembranças mais parecidas com a consulta: lista de dicts com score."""
    with _lock, _connect() as conn:
        marks = ",".join("?" * len(tipos))
        rows = conn.execute(
            f"SELECT id, tipo, assunto, texto, fonte, criado, vetor, modelo FROM memorias "
            f"WHERE tipo IN ({marks})", tipos).fetchall()
    if not rows:
        return []
    query_vector = embed([consulta], query=True)
    scored = []
    if query_vector is not None:
        dim = query_vector.shape[1]
        for row in rows:
            blob, model = row[6], row[7]
            if blob and model == EMBEDDING_MODEL and len(blob) == dim * 4:
                score = float(np.frombuffer(blob, dtype=np.float32) @ query_vector[0])
                scored.append((score, row))
    if not scored:  # sem embeddings: palavras em comum
        wanted = _words(consulta)
        for row in rows:
            have = _words(f"{row[2]} {row[3]}")
            if wanted and have:
                scored.append((len(wanted & have) / len(wanted), row))
        min_score = 0.34
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {"id": r[0], "tipo": r[1], "assunto": r[2], "texto": r[3], "fonte": r[4],
         "criado": r[5], "score": round(s, 3)}
        for s, r in scored[:k] if s >= min_score
    ]


def forget(consulta, min_score=0.6):
    """Apaga a lembrança mais parecida (se for parecida o bastante). Devolve o texto apagado."""
    found = search(consulta, k=1, min_score=min_score)
    if not found:
        return None
    with _lock, _connect() as conn:
        conn.execute("DELETE FROM memorias WHERE id = ?", (found[0]["id"],))
    return found[0]


def list_subjects(limit=30):
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT assunto, texto FROM memorias WHERE tipo IN ('fato', 'aprendido') "
            "ORDER BY criado DESC LIMIT ?", (limit,)).fetchall()
    return [assunto or texto[:40] for assunto, texto in rows]


# --------------------------------------------------------------- migração
def migrate_old_memories():
    """Copia a tabela antiga "conhecimento" para a memória nova, uma vez.

    Pula o lixo do estudo automático antigo (mensagens de erro, textos curtos).
    """
    with _lock, _connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS memorias_info (chave TEXT PRIMARY KEY, valor TEXT)")
        done = conn.execute("SELECT 1 FROM memorias_info WHERE chave = 'migrado'").fetchone()
        try:
            old = conn.execute("SELECT titulo, conteudo, fonte, data FROM conhecimento").fetchall()
        except sqlite3.OperationalError:
            old = []
    if done:
        return 0
    imported = 0
    for title, content, source, date in old:
        content = (content or "").strip()
        if len(content) < 40 or _JUNK.match(content):
            continue
        tipo = "fato" if (source or "").lower() in ("pedro", "usuário", "usuario") else "aprendido"
        if add(title, content[:2000], (source or "").split("\n")[0], tipo):
            imported += 1
    with _lock, _connect() as conn:
        conn.execute("INSERT OR REPLACE INTO memorias_info VALUES ('migrado', ?)",
                     (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    if old:
        print(f"[MEMÓRIA] {imported} memórias antigas importadas ({len(old) - imported} puladas).")
    return imported


# ------------------------------------------------------------- documentos
def _read_document(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md"):
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    if ext == ".pdf":
        from pypdf import PdfReader

        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return None


def _chunks(text, size=900, overlap=150):
    text = re.sub(r"\s+", " ", text).strip()
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        cut = text.rfind(". ", start + size // 2, end)
        end = cut + 1 if cut != -1 and end < len(text) else end
        yield text[start:end].strip()
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)


def index_documents(folder=DOCS_DIR):
    """Indexa .txt, .md e .pdf da pasta. Só reprocessa arquivos que mudaram."""
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
        return 0
    added = 0
    with _lock, _connect() as conn:
        known = dict(conn.execute(
            "SELECT fonte, hash FROM memorias WHERE tipo = 'documento' GROUP BY fonte").fetchall())
    present = set()
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        present.add(name)
        with open(path, "rb") as f:
            digest = hashlib.sha1(f.read()).hexdigest()
        if known.get(name) == digest:
            continue
        try:
            text = _read_document(path)
        except Exception as error:
            print(f"[DOCUMENTOS] Não consegui ler {name}: {error}")
            continue
        if not text:
            continue
        with _lock, _connect() as conn:
            conn.execute("DELETE FROM memorias WHERE tipo = 'documento' AND fonte = ?", (name,))
        for chunk in _chunks(text):
            add(os.path.splitext(name)[0], chunk, name, "documento", digest)
            added += 1
        print(f"[DOCUMENTOS] {name} indexado.")
    with _lock, _connect() as conn:  # arquivos apagados saem do índice
        for name in set(known) - present:
            conn.execute("DELETE FROM memorias WHERE tipo = 'documento' AND fonte = ?", (name,))
    return added


def search_documents(pergunta, k=4):
    return search(pergunta, k=k, tipos=("documento",), min_score=0.4)


def prepare():
    """Na abertura: importa as memórias antigas e atualiza o índice de documentos."""
    started = time.monotonic()
    try:
        migrate_old_memories()
        added = index_documents()
        if added:
            print(f"[DOCUMENTOS] {added} trechos novos em {time.monotonic() - started:.1f}s.")
    except Exception as error:
        print(f"[MEMÓRIA] Preparação falhou: {error}")
