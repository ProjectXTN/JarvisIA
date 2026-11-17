import re
from brain.audio import say
from brain.websearch.websearch import search_web
from brain.memory.memory import llama_query


def summarize_search(question, content, sources=""):
    """Resumo falado do que foi encontrado. None se o modelo falhar."""
    prompt = (
        "Você é o Jarvis, assistente de voz. Responda em português do Brasil, "
        "em no máximo 5 frases curtas, próprias para serem faladas em voz alta: "
        "sem listas, sem títulos, sem links e sem símbolos. Use só as informações "
        "do material abaixo; se ele não responder à pergunta, diga isso.\n\n"
        f"Pergunta: {question}\n\n"
        f"Material encontrado na internet:\n{content[:6000]}\n\n"
        f"Fontes: {sources}"
    )
    return llama_query(prompt, direct_mode=True)


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

        # search_web devolve mensagens de erro no lugar do conteúdo
        failed = not content or content.startswith(
            ("API KEY", "Nenhum resultado", "Não consegui acessar", "Erro ao buscar")
        )
        if failed:
            if speak:
                say("Não encontrei nada relevante na internet.")
            return None, None

        # O texto das páginas é cru (títulos, listas, repetições): resume antes
        summary = summarize_search(cleaned, content, source)
        if speak:
            if summary:
                say(summary)
            else:
                say("Encontrei resultados, mas não consegui resumir agora.")

        return summary or content, source

    except Exception as e:
        print(f"[ERROR] Web search failed: {e}")
        if speak:
            say("Algo deu errado ao tentar pesquisar.")
        return None, None