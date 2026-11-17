"""Regras de texto para a fala do Jarvis (sem dependências de áudio).

- prepare_for_speech: tira do texto o que não deve ser pronunciado.
- is_interrupt / interrupt_remainder: decidem se o que o microfone ouviu
  enquanto o Jarvis falava é um pedido para ele parar.
"""

import re
import unicodedata

# Marcações do extrator de páginas: [TÍTULO], [PARÁGRAFO], [LISTA], [FONTE]...
_TAG = re.compile(r"\[[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ \-]{1,24}\]")
_URL = re.compile(r"(https?://|www\.)\S+")
_SYMBOLS = {
    "→": ", ", "←": ", ", "⇒": ", ", "->": ", ", "=>": ", ",
    "·": ", ", "•": ", ", "|": ", ", "—": ", ", "–": ", ",
    "…": ".", "...": ".",
}


def _normalize(text):
    text = unicodedata.normalize("NFD", text.lower())
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def prepare_for_speech(text, max_chars=1200):
    """Texto pronto para o TTS: sem marcações, links, símbolos ou repetições."""
    text = _TAG.sub(". ", text)                                # marcação = fim de frase
    text = _URL.sub(" ", text)
    for symbol, replacement in _SYMBOLS.items():
        text = text.replace(symbol, replacement)
    text = re.sub(r"#(\d+)", r"\1", text)                      # "#1 Accuracy" -> "1 Accuracy"
    text = re.sub(r"(^|\s)[-*]\s+", r"\1", text)               # marcadores de lista
    text = re.sub(r"\s*,\s*(,\s*)+", ", ", text)               # vírgulas repetidas
    text = re.sub(r"([.!?:;,])(\s*[.,])+", r"\1", text)          # pontuação duplicada
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip(" ,.")
    if text:
        text += "."
    text = re.sub(r"([.!?])\.$", r"\1", text)

    # Frases repetidas (o extrator de páginas costuma duplicar blocos)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    seen, kept = set(), []
    for sentence in sentences:
        key = _normalize(sentence)
        if not key or key in seen:
            continue
        seen.add(key)
        kept.append(sentence)
    text = " ".join(kept)

    if len(text) > max_chars:
        cut = text[:max_chars]
        end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
        text = cut[: end + 1] if end > max_chars * 0.4 else cut.rsplit(" ", 1)[0] + "."
    return text


# Pedidos para parar. Só estas frases interrompem o Jarvis enquanto ele fala;
# qualquer outra coisa dita nesse momento é ignorada. Texto já sem acentos.
_STOP = re.compile(
    r"\b("
    r"pode parar|parar de falar|para de falar|pare de falar|pode calar|"
    r"para jarvis|jarvis para|para ai|para por favor|"
    r"pare|parar|chega|ja entendi|entendi|ta bom|ta certo|"
    r"silencio|cala a boca|fica quieto|stop|interrompa|cancela|esquece"
    r")\b"
)


# Começos de pergunta. "para que" / "pra que" são sempre pergunta, nunca pedido de parar.
_QUESTION_START = re.compile(
    r"^(jarvis )?("
    r"para que|pra que|por que|porque|o que|que|qual|quais|quem|como|onde|aonde|"
    r"quando|quanto|quanta|quantos|quantas|sera que|me explica|explica|explique|"
    r"me diz|me diga|voce sabe|sabe|pode me|significa"
    r")\b"
)


def is_question(heard):
    """True se a frase é uma pergunta, e não uma ordem.

    Pergunta: termina com "?", começa com palavra de pergunta ("para que
    serve...", "o que é...") ou pergunta sobre a palavra ("o que significa pare").
    Uma ordem dita antes da pergunta ("Pare. Que horas são?") não conta como
    pergunta: quem decide é o começo da frase.
    """
    h = _normalize(heard)
    if not h:
        return False
    # Ordem seguida de pausa ("Para, que horas são?", "Pare. O que..."): é ordem.
    # Sem a pausa, "para que..." é pergunta.
    if re.match(
        r"^\s*(jarvis\W+)?(para|pare|parar|chega|pode parar|j[aá] entendi|entendi)\s*[,.!;]",
        heard.lower(),
    ):
        return False
    if _QUESTION_START.match(h):
        return True
    # Termina com "?" e não começa com ordem de parar ("Pare, que horas são?")
    starts_with_order = re.match(r"^(jarvis )?(pare|parar|para|chega|pode parar|ja entendi|entendi)\b", h)
    stripped = heard.strip()
    if stripped.endswith("?") and not starts_with_order:
        return True
    # "Para, que horas são?" tem pausa depois de "para": é ordem
    return False


def is_interrupt(heard, spoken=""):
    """True se a frase ouvida durante a fala é um pedido para o Jarvis parar.

    Só frases da lista _STOP contam ("pare", "pode parar", "já entendi"...).
    "para" conta quando vem sozinho ou seguido de pausa ("Para, ..."); no meio
    de uma frase é preposição.

    `spoken` é o que o Jarvis está falando: se a palavra de parar também está
    no texto dele, provavelmente o microfone captou a própria voz dele na caixa
    de som, e é ignorada (a menos que você diga "Jarvis", que ele não fala).
    """
    h = _normalize(heard)
    if not h:
        return False
    words = h.split()
    if len(words) > 10:
        return False  # frase longa: é conversa ou eco, não pedido de parar
    if is_question(heard):
        return False  # "para que serve isso?", "o que significa pare?"

    match = None
    if words[0] == "para" and len(words) <= 3:
        match = "para"
    elif re.match(r"^\s*(jarvis\W+)?para\s*[,.!]", heard.lower()):
        match = "para"
    else:
        found = _STOP.search(h)
        if found:
            match = found.group(0)
    if not match:
        return False

    # Eco: a voz do Jarvis captada pelo microfone vem em trechos longos, com a
    # palavra no meio. Frase curta ("chega", "pode parar") ou que começa com o
    # pedido ("Para, que horas são?") é você, mesmo que a palavra apareça no
    # que ele está falando.
    starts_with_stop = re.match(rf"^(jarvis )?{match}\b", h) is not None
    s = _normalize(spoken)
    if (len(words) > 3 and not starts_with_stop and "jarvis" not in words
            and s and f" {match} " in f" {s} "):
        return False
    return True


def interrupt_remainder(heard):
    """Comando que veio junto com o pedido de parar.

    "Para, que horas são?" -> "que horas são?"; "Entendi, pode parar" -> ""
    (só parar). Mantém a grafia original para seguir como comando.
    """
    original = heard.strip().split()
    h = _normalize(heard).split()
    skip, found_any = 0, False
    while skip < len(h):
        if h[skip] in ("jarvis", "por", "favor", "ai", "e", "ok"):
            skip += 1
            continue
        rest_norm = " ".join(h[skip:])
        found = re.match(r"^para\b", rest_norm) or _STOP.match(rest_norm)
        if not found:
            break
        skip += len(found.group(0).split())
        found_any = True
    if not found_any:
        return ""
    rest = " ".join(original[skip:]).strip(" ,.!")
    return rest if len(rest.split()) >= 2 else ""
