import re
from brain.audio import say
from brain.websearch.websearch import search_web


def execute_search(query, speak=True):
    try:
        cleaned = re.sub(
            r"^(jarvis,?\s*)?(pesquise|procure|busque)(\s+(na\s+(internet|web))|\s+sobre)?\s+",
            "",
            query,
            flags=re.IGNORECASE
        ).strip(" ,.")

        print(f"🔍 Cleaned search: '{cleaned}'")

        if not cleaned:
            if speak:
                say("O que você quer que eu pesquise?")
            return None, None

        response = search_web(cleaned)

        if isinstance(response, tuple):
            content, source = response
        else:
            content, source = str(response), "desconhecida"

        if speak and content:
            say(str(content[:3000]) + "..." if len(content) > 3000 else str(content))
        elif speak:
            say("Não encontrei nada relevante na internet.")

        return content, source

    except Exception as e:
        print(f"[ERROR] Web search failed: {e}")
        if speak:
            say("Algo deu errado ao tentar pesquisar.")
        return None, None