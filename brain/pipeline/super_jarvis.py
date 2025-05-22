from brain.websearch.websearch import search_web
from brain.rag.query_rag import query_rag
from brain.memory.memory import llama_query, DEFAULT_MODEL

def super_jarvis_query(user_prompt):
    # 1. Busca contexto web
    web_context, web_sources = search_web(user_prompt)
    # 2. Busca contexto local
    local_context = query_rag(user_prompt)

    prompt = (
        f"Contexto recente extraído da internet:\n{web_context}\n\n"
        f"Fontes web:\n{web_sources}\n\n"
        f"Informações de documentos internos:\n{local_context}\n\n"
        f"Pergunta do usuário: {user_prompt}\n"
        "Responda de forma objetiva, usando as informações acima. "
        "Se não houver resposta suficiente, diga que não foi possível encontrar."
    )

    resposta = llama_query(prompt, model=DEFAULT_MODEL, direct_mode=True)
    return resposta
