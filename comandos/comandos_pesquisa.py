import re
from brain.audio import say
from brain.websearch import buscar_na_web

def executar_pesquisa(query, falar=True):
    try:
        from brain.audio import say
        from brain.websearch import buscar_na_web

        cleaned = re.sub(
            r"^(jarvis,?\s*)?(pesquise|procure|busque)(\s+(na\s+(internet|web))|\s+sobre)?\s+",
            "",
            query,
            flags=re.IGNORECASE
        ).strip(" ,.")


        print(f"🔍 Pesquisa limpa: '{cleaned}'")

        if not cleaned:
            if falar:
                say("O que você quer que eu pesquise?")
            return None, None

        resposta = buscar_na_web(cleaned)

        if isinstance(resposta, tuple):
            conteudo, fonte = resposta
        else:
            conteudo, fonte = str(resposta), "desconhecida"

        if falar and conteudo:
            say(str(conteudo[:3000]) + "..." if len(conteudo) > 3000 else str(conteudo))
        elif falar:
            say("Não encontrei nada relevante na internet.")

        return conteudo, fonte

    except Exception as e:
        print(f"[ERRO] Falha na pesquisa web: {e}")
        if falar:
            say("Algo deu errado ao tentar pesquisar.")
        return None, None
