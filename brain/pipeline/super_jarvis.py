from brain.websearch.websearch import search_web
from brain.rag.query_rag import query_rag
from concurrent.futures import ThreadPoolExecutor
from brain.memory.memory import llama_query, DEFAULT_MODEL
from core.settings import RAG_TIMEOUT

_rag_pool = ThreadPoolExecutor(max_workers=1)

PROMPT_TEMPLATES = {
    "pt": {
        "lang_instruction": "Sempre responda em português brasileiro.",
        "context": "Contexto recente extraído da internet:",
        "sources": "Fontes web:",
        "internal": "Informações de documentos internos:",
        "user_question": "Pergunta do usuário:",
        "answer_instruction": "Responda com base nas informações mais recentes do dia de hoje. Priorize notícias datadas ou com menção explícita ao dia atual. Evite respostas genéricas. Seja específico e direto.",
    },
    "en": {
        "lang_instruction": "Always reply in English.",
        "context": "Recent context extracted from the internet:",
        "sources": "Web sources:",
        "internal": "Internal document information:",
        "user_question": "User question:",
        "answer_instruction": "Respond based on the most recent information available today. Prioritize news dated or explicitly mentioning the current day. Avoid generic answers. Be specific and direct.",
    },
    "fr": {
        "lang_instruction": "Répondez toujours en français.",
        "context": "Contexte récent extrait d'internet :",
        "sources": "Sources web :",
        "internal": "Informations des documents internes :",
        "user_question": "Question de l'utilisateur :",
        "answer_instruction": "Répondez en vous basant sur les informations les plus récentes du jour. Priorisez les actualités datées ou mentionnant explicitement le jour en cours. Évitez les réponses génériques. Soyez spécifique et direct.",
    },
}


def super_jarvis_query(user_prompt, lang="pt"):
    web_context, web_sources = search_web(user_prompt)
    print("[RAG] Consultando documentos internos...")
    try:
        local_context = _rag_pool.submit(query_rag, user_prompt).result(
            timeout=RAG_TIMEOUT
        )
    except Exception as e:
        # Sem índice, sem modelo de embeddings ou demorou demais: segue só com a web
        print(f"[RAG] Indisponível, seguindo sem documentos internos: {e!r}")
        local_context = ""
    pt = PROMPT_TEMPLATES.get(lang, PROMPT_TEMPLATES["en"])

    prompt = (
        f"{pt['lang_instruction']}\n"
        f"{pt['context']}\n{web_context}\n\n"
        f"{pt['sources']}\n{web_sources}\n\n"
        f"{pt['internal']}\n{local_context}\n\n"
        f"{pt['user_question']} {user_prompt}\n"
        f"{pt['answer_instruction']}"
    )

    resposta = llama_query(prompt, model=DEFAULT_MODEL, direct_mode=True, lang=lang)
    return resposta
