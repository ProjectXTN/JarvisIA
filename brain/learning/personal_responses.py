import re
from brain.utils.utils import normalize_text

def detect_language(text: str):
    """Detecta o idioma com base em palavras-chave simples."""
    text = text.lower()

    if re.search(r"\b(who|what|tell|about)\b", text):
        return "en"
    elif re.search(r"\b(qui|qu\u2019est|parle|sais)\b", text):
        return "fr"
    else:
        return "pt"

def check_personal_answer(prompt: str):
    """Intercepta perguntas sobre Pedro Meireles e responde diretamente no idioma adequado."""
    prompt_lower = normalize_text(prompt)

    triggers = [
        r"pedro meireles",
        r"quem.*pedro",
        r"who.*pedro",
        r"tell.*pedro",
        r"what.*pedro",
        r"qui.*pedro",
        r"dono.*jarvis",
        r"quem.*manda.*em.*voce",
        r"quem.*e.*seu criador",
        r"quem.*te.*criou",
        r"who.*is.*your creator",
        r"who.*owns.*you",
        r"who.*created.*you",
        r"qui.*ta.*cree",
        r"qui.*t.*a.*cree"
    ]

    if any(re.search(trigger, prompt_lower) for trigger in triggers):
        lang = detect_language(prompt)

        if lang == "en":
            return str(
                "Pedro Meireles is a fullstack web developer with a futuristic mindset, specialized in intelligent interfaces, "
                "generative AI, and human-machine integration. He's the creator of this very Jarvis, blending technology, elegance, "
                "and code with coffee."
            )
        elif lang == "fr":
            return str(
                "Pedro Meireles est un d\u00e9veloppeur web fullstack, visionnaire dans les interfaces intelligentes, l'IA g\u00e9n\u00e9rative "
                "et l'int\u00e9gration homme-machine. C'est le cr\u00e9ateur de ce Jarvis, alliant technologie, style et caf\u00e9."
            )
        else:
            return str(
                "Pedro Meireles \u00e9 um desenvolvedor web fullstack, vision\u00e1rio em interfaces inteligentes, IA generativa e integra\u00e7\u00e3o "
                "homem-m\u00e1quina. Criador deste Jarvis e respons\u00e1vel por tornar a web mais esperta, bonita e funcional."
            )

    return None
