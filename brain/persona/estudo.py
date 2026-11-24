"""Estudo autônomo (Fase 7, item 56).

Pega o próximo tema da lista de curiosidades, busca na internet (só leitura,
limites.py), lê as páginas, pede ao modelo um resumo que use só o que as fontes
dizem e confira se mais de uma fonte concorda. Guarda na memória por semelhança
como "aprendido", com as fontes e o nível de confiança.
"""
import os
from datetime import datetime

from brain import semantic_memory
from brain.persona import curiosidade, limites, llm

STUDY_SYSTEM = (
    "Você é Jarvis estudando um tema para conversar com Pedro depois. Use SÓ o texto das "
    "fontes abaixo, nunca o que você acha que sabe. Responda só JSON: "
    '{"resumo": "5 a 8 frases em português, com os fatos principais e datas quando houver", '
    '"fontes_que_concordam": ["site1", "site2"], '
    '"conflitos": "onde as fontes discordam, ou vazio", '
    '"confianca": "alta|media|baixa"}. '
    "Confiança alta só se duas ou mais fontes diferentes dizem a mesma coisa. "
    'Se as fontes não tratam do tema: {"resumo": "", "confianca": "baixa"}.'
)


def _search(theme):
    from brain.websearch.websearch import search_web

    def ok(url):
        try:
            limites.check_url(url)
            return True
        except limites.NotAllowed:
            return False

    return search_web(theme, total_limit=9000, max_links=5, remember=False, url_filter=ok)


def _log(theme, summary, sources, confidence):
    folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, f"aprendizados_{datetime.now():%Y-%m-%d}.txt"), "a", encoding="utf-8") as f:
        f.write(f"\n=== {theme.upper()} ({confidence}) ===\n{datetime.now():%H:%M} | Fontes: {sources}\n{summary}\n")


def study_one():
    """Estuda o próximo tema. Devolve o tema estudado, ou None."""
    item = curiosidade.next_theme()
    if not item:
        if not curiosidade.refill():
            return None
        item = curiosidade.next_theme()
        if not item:
            return None
    theme_id, theme, _ = item
    print(f"[ESTUDO] Estudando: {theme}")
    text, sources = _search(theme)
    if not text or sources == "internet":
        curiosidade.mark(theme_id, "descartado", f"busca sem resultado: {text[:120]}")
        return None
    result = llm.ask(STUDY_SYSTEM, f"Tema: {theme}\n\nFontes ({sources.replace(chr(10), ', ')}):\n{text}",
                     as_json=True, num_predict=700, timeout=180) or {}
    summary = str(result.get("resumo") or "").strip()
    confidence = str(result.get("confianca") or "baixa").lower()
    agreeing = [s for s in (result.get("fontes_que_concordam") or []) if isinstance(s, str)]
    if len(summary) < 60:
        curiosidade.mark(theme_id, "descartado", "fontes não tratavam do tema")
        return None
    if confidence == "alta" and len(set(agreeing)) < 2:
        confidence = "media"  # não confirmado em duas fontes
    conflicts = str(result.get("conflitos") or "").strip()
    if conflicts:
        summary += f" Atenção, as fontes divergem: {conflicts}"
    source_text = ", ".join(agreeing) or sources.replace("\n", ", ")
    note = f"{source_text} (confiança {confidence}, estudado sozinho)"
    similar = semantic_memory.search(theme, k=1, tipos=("aprendido",), min_score=0.9)
    if similar:
        semantic_memory.update_text(similar[0]["id"], summary, theme)
    else:
        semantic_memory.add(theme, summary, note, "aprendido")
    curiosidade.mark(theme_id, "estudado", f"confiança {confidence}")
    _log(theme, summary, note, confidence)
    print(f"[ESTUDO] Aprendi sobre {theme} (confiança {confidence}).")
    return theme
