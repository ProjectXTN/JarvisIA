from brain.websearch.websearch import search_web
from brain.semantic_memory import search_documents


def query_rag(user_prompt):
    """Trechos dos documentos de Pedro (memória por semelhança; antes llama-index)."""
    return "\n\n".join(f"[{m['fonte']}] {m['texto']}" for m in search_documents(user_prompt))
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from brain.memory.memory import llama_query, llama_stream, DEFAULT_MODEL, memory_context, remember_turn
from core.settings import RAG_TIMEOUT, RAG_ENABLED
from brain.websearch.news import is_news_request, news_response

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


_WEEKDAYS = {
    "pt": ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
}


def today_line(lang="pt", now=None):
    """Data de hoje para o modelo, que não sabe o dia e confundia a data das notícias."""
    now = now or datetime.now()
    day = _WEEKDAYS.get(lang, _WEEKDAYS["pt"])[now.weekday()]
    date = now.strftime("%d/%m/%Y")
    return {
        "pt": f"Hoje é {day}, {date}. Ao falar de datas das fontes, diga a data exata e só use \"hoje\" se for {date}.",
        "en": f"Today is {day}, {now.strftime('%Y-%m-%d')}. When mentioning source dates, say the exact date and only say \"today\" if it matches.",
        "fr": f"Nous sommes le {day} {date}. Pour les dates des sources, donnez la date exacte et ne dites « aujourd'hui » que si elle correspond.",
    }.get(lang, f"Hoje é {date}.")


def contextualize_search(user_prompt, history):
    """Transforma uma continuação ("procure as mais recentes") numa busca completa.

    Usa as últimas trocas da conversa para trazer o assunto ("...da OpenAI").
    Se a fala já é completa ou o modelo falhar, devolve a fala original.
    """
    if not history:
        return user_prompt
    turns = "\n".join(f"Pedro: {q[:300]}\nJarvis: {a[:400]}" for q, a in history[-3:])
    prompt = (
        f"Conversa recente:\n{turns}\n\n"
        f"Nova fala do Pedro: \"{user_prompt}\"\n\n"
        "Escreva a consulta de busca na internet que atende a nova fala. Se ela "
        "depende da conversa (\"isso\", \"as mais recentes\", \"sim, quero\", "
        "\"e sobre ele\"), inclua o assunto da conversa. Se for um assunto novo e "
        "completo, devolva a fala sem mudanças. Responda só com a consulta, "
        "em uma linha, sem aspas e sem explicações."
    )
    rewritten = llama_query(prompt, direct_mode=True, mode="rewrite", lang="pt", remember=False)
    if not rewritten:
        return user_prompt
    rewritten = rewritten.strip().splitlines()[0].strip(" \"'.")
    if not rewritten or len(rewritten) > 200:
        return user_prompt
    if rewritten.lower() != user_prompt.lower():
        print(f"[BUSCA] Pergunta com o contexto da conversa: {rewritten}")
    return rewritten


def super_jarvis_query(user_prompt, lang="pt", conversation=False, stream=False):
    history = list(memory_context) if conversation else []
    search_query = contextualize_search(user_prompt, history)
    if is_news_request(search_query):
        return news_response(search_query, lang=lang, conversation=conversation)
    web_context, web_sources = search_web(search_query)
    local_context = ""
    if RAG_ENABLED:
        print("[RAG] Consultando documentos internos...")
        try:
            local_context = _rag_pool.submit(query_rag, user_prompt).result(
                timeout=RAG_TIMEOUT
            )
        except Exception as e:
            # Sem índice, sem modelo de embeddings ou demorou demais: segue só com a web
            print(f"[RAG] Indisponível, seguindo sem documentos internos: {e!r}")
    pt = PROMPT_TEMPLATES.get(lang, PROMPT_TEMPLATES["en"])

    prompt = (
        f"{pt['lang_instruction']}\n"
        f"{today_line(lang)}\n"
        f"{pt['context']}\n{web_context}\n\n"
        f"{pt['sources']}\n{web_sources}\n\n"
        f"{pt['internal']}\n{local_context}\n\n"
        f"{pt['user_question']} {user_prompt}"
        + (f" (busca feita: {search_query})" if search_query != user_prompt else "")
        + "\n"
        f"{pt['answer_instruction']}"
    )

    if stream:
        # Fala em fluxo: devolve os pedaços; o turno é guardado quando terminar
        return llama_stream(
            prompt, model=DEFAULT_MODEL, direct_mode=True, lang=lang, mode="web",
            history=history, remember=False,
            on_complete=(lambda text: remember_turn(user_prompt, text)) if conversation else None,
        )

    resposta = llama_query(prompt, model=DEFAULT_MODEL, direct_mode=True, lang=lang, mode="web",
                           history=list(memory_context) if conversation else [], remember=False)
    if conversation and resposta:
        remember_turn(user_prompt, resposta)
    return resposta
