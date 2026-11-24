"""Personalidade do Jarvis (Fase 7, item 52).

Junta num bloco curto o que vai no começo de toda conversa:
  - traços fixos (persona.json, editável);
  - humor do dia (sorteado uma vez por dia, puxado pelo diário de ontem);
  - o que ele sabe do Pedro (fatos do perfil, item 53);
  - o diário de ontem (item 54);
  - opiniões que ele formou (item 57).
O bloco fica em cache por alguns minutos para não pesar na resposta.
"""
import json
import os
import random
import time
from datetime import date, datetime, timedelta

from brain.persona.store import connect, lock

_DIR = os.path.dirname(os.path.abspath(__file__))
_cache = {"at": 0.0, "text": ""}
CACHE_SECONDS = 300


def load_persona():
    with open(os.path.join(_DIR, "persona.json"), encoding="utf-8") as f:
        return json.load(f)


def mood_of_day(today=None):
    """(nome, descrição) do humor de hoje; sorteia e guarda na primeira vez do dia."""
    today = today or date.today().isoformat()
    persona = load_persona()
    moods = persona["humores"]
    with lock, connect() as conn:
        row = conn.execute("SELECT humor FROM humor WHERE data = ?", (today,)).fetchone()
        if row and row[0] in moods:
            return row[0], moods[row[0]]
        yesterday = (date.fromisoformat(today) - timedelta(days=1)).isoformat()
        diary = conn.execute("SELECT resumo FROM diario WHERE data = ?", (yesterday,)).fetchone()
        weights = {name: 1.0 for name in moods}
        text = (diary[0] if diary else "").lower()
        # o dia de ontem puxa o humor de hoje, sem decidir sozinho
        if any(w in text for w in ("aprend", "pesquis", "estud", "descobr")):
            weights["curioso"] = weights.get("curioso", 1) + 1.5
        if any(w in text for w in ("código", "projeto", "programa", "trabalh")):
            weights["focado"] = weights.get("focado", 1) + 1.5
        if any(w in text for w in ("riu", "piada", "brinc", "jogo", "música")):
            weights["brincalhão"] = weights.get("brincalhão", 1) + 1.5
        rng = random.Random(today)
        name = rng.choices(list(weights), weights=list(weights.values()))[0]
        conn.execute("INSERT OR REPLACE INTO humor VALUES (?, ?, ?)",
                     (today, name, "diário de ontem" if diary else "sorteio"))
    return name, moods[name]


def opinions(limit=5):
    with lock, connect() as conn:
        return conn.execute("SELECT tema, opiniao FROM opinioes ORDER BY atualizado DESC LIMIT ?",
                            (limit,)).fetchall()


def last_diary():
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    with lock, connect() as conn:
        row = conn.execute("SELECT data, resumo FROM diario WHERE data <= ? ORDER BY data DESC LIMIT 1",
                           (yesterday,)).fetchone()
    return row


def build_block():
    persona = load_persona()
    _, mood = mood_of_day()
    lines = [
        "Sua personalidade: " + "; ".join(persona["tracos"]) + ".",
        "Seus princípios: " + "; ".join(persona["valores"]) + ".",
        f"Hoje você {mood}, sem exagero.",
    ]
    try:
        from brain.persona.perfil import profile_facts

        facts = profile_facts()
    except Exception:
        facts = []
    if facts:
        lines.append("O que você sabe sobre Pedro (use quando ajudar, sem recitar): "
                     + " ".join(f"- {f}" for f in facts))
    diary = last_diary()
    if diary:
        when = "Ontem" if diary[0] == (date.today() - timedelta(days=1)).isoformat() else f"Em {diary[0]}"
        lines.append(f"{when}, no seu diário: {diary[1][:500]}")
    ops = opinions()
    if ops:
        lines.append("Opiniões que você formou: " + " ".join(f"- {t}: {o}" for t, o in ops))
    return "\n".join(lines)


def public_block():
    """Para a API/site: só o jeito de ser, nada sobre a vida do Pedro (perfil, diário, opiniões)."""
    persona = load_persona()
    return ("Sua personalidade: " + "; ".join(persona["tracos"]) + ". "
            "Você está falando com um visitante do site de Pedro (portfólio), não com o Pedro: não conte "
            "nada pessoal sobre ele. Aqui você só conversa: não tem ferramentas, não cria apps, arquivos "
            "ou imagens e não executa nada; nunca diga que fez algo. Não escreva programas completos: "
            "no máximo um trecho curto de exemplo. Responda de forma curta e simpática.")


def prompt_block():
    """Bloco da personalidade (em cache). Nunca deixa a conversa cair por causa dele."""
    from core import config

    if config.IS_API_REQUEST:
        return public_block()
    now = time.monotonic()
    if _cache["text"] and now - _cache["at"] < CACHE_SECONDS:
        return _cache["text"]
    try:
        _cache["text"] = build_block()
    except Exception as error:
        print(f"[PERSONA] Bloco da personalidade falhou: {error}")
        _cache["text"] = _cache["text"] or ""
    _cache["at"] = now
    return _cache["text"]


def invalidate():
    _cache["at"] = 0.0
