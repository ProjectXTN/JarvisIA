"""Roteador por ferramentas (Fase 4): o modelo decide o que fazer.

Fluxo de uma fala:
  1. Uma chamada ao modelo com a conversa e a lista de ferramentas (stream).
     Se ele responder em texto, a resposta já vai sendo falada.
  2. Se ele chamar ferramentas, elas rodam na ordem pedida ("abra o Steam e
     toque música" vira duas chamadas).
  3. Se alguma ferramenta trouxe informação (busca, clima, memória...), uma
     segunda chamada, sem ferramentas, transforma o resultado na resposta falada.

Se o Ollama recusar ferramentas ou der erro antes de começar, levanta
RouterUnavailable e o Jarvis usa o caminho antigo (regras de palavras).
"""

from datetime import datetime

from brain import audio
from brain import tools as toolbox
from brain.audio import speak_stream
from brain.memory.memory import (
    MAX_CONTEXT,
    iter_chat,
    memory_context,
    open_chat,
    remember_turn,
    system_prompt,
    persona_block,
)
from brain.pipeline.super_jarvis import today_line

ROUTER_GUIDE = (
    "Você tem ferramentas. Use-as para ações no computador de Pedro e para informações "
    "atuais ou que podem ter mudado depois do seu treinamento (notícias, boatos, versões, "
    "preços, eventos, clima, guias de jogos). Para conhecimento estável, explicações e "
    "conversa, responda direto, sem ferramentas. Se o pedido tiver várias ações, chame "
    "várias ferramentas, na ordem. Ao buscar, escreva a consulta completa, incluindo o "
    "assunto da conversa quando a fala depender dele. Nunca diga que fez, abriu ou "
    "pesquisou algo sem ter chamado a ferramenta. Pedido para criar um app, programa, jogo ou "
    "site de verdade vai para criar_app; dúvida de programação ou trecho curto, responda direto."
)

ANSWER_GUIDE = (
    "Responda à fala de Pedro usando os resultados das ferramentas acima. Seja natural e "
    "curto, para ser falado. Cite a data exata das fontes quando importar. Se os "
    "resultados não responderem, diga isso."
)


BROWSER_TOOLS = {"pesquisar_no_google", "abrir_site", "tocar_no_youtube"}


def _opens_bare_browser(call):
    function = call.get("function", {})
    arguments = function.get("arguments") or {}
    if isinstance(arguments, str):
        return function.get("name") == "abrir_programa" and "navegador" in arguments
    return function.get("name") == "abrir_programa" and arguments.get("programa") == "navegador"


class RouterUnavailable(Exception):
    """O modelo não pôde decidir (Ollama fora, modelo sem ferramentas...)."""


def _base_messages(query, lang):
    instruction = {"pt": "Responda em português brasileiro.", "en": "Reply in English.",
                   "fr": "Répondez en français."}.get(lang, "Responda no idioma do usuário.")
    now = f"Agora são {datetime.now():%H:%M}."
    try:  # o programador está esperando o Pedro responder algo?
        from brain.dev import conversa

        waiting = conversa.pending()
    except Exception:
        waiting = None
    if waiting:
        now += (f"\nO PROGRAMADOR está esperando a resposta de Pedro sobre o app {waiting['app']}: "
                f"\"{waiting['texto'][:400]}\". Se a fala de Pedro responde isso (sim, pode começar, "
                "uma escolha, mudanças no plano), chame responder_programador com a fala completa; "
                "se for outro assunto, atenda normalmente.")
    messages = [{"role": "system",
                 "content": f"{system_prompt} {instruction}{persona_block()}\n{today_line(lang)} {now}\n{ROUTER_GUIDE}"}]
    for question, answer in list(memory_context)[-MAX_CONTEXT:]:
        messages += [{"role": "user", "content": question},
                     {"role": "assistant", "content": answer}]
    messages.append({"role": "user", "content": query})
    return messages


def _interrupted():
    return bool(getattr(audio, "silenced", False))


def handle(query, lang="pt", speak=speak_stream, run_tool=toolbox.run_tool,
           interrupted=_interrupted):
    """Atende uma fala pelo modelo com ferramentas. Devolve o texto da resposta."""
    messages = _base_messages(query, lang)
    try:
        first = open_chat(messages, tools=toolbox.schemas())
    except Exception as error:
        raise RouterUnavailable(str(error)) from error

    tool_calls, parts = [], []
    spoken = speak(iter_chat(first, tool_calls, parts)) or ""
    direct = "".join(parts).strip()

    if not tool_calls or interrupted():
        # Sem ferramentas, ou você disse "pare" enquanto ele falava: não executa nada
        if direct:
            remember_turn(query, direct)
        return direct

    # Pesquisa, site ou vídeo já abrem o navegador: um "abrir o navegador" na
    # mesma frase só criaria uma janela vazia a mais
    names = {c.get("function", {}).get("name") for c in tool_calls}
    if names & BROWSER_TOOLS:
        tool_calls = [c for c in tool_calls if not _opens_bare_browser(c)]

    # Ferramentas, na ordem em que o modelo pediu
    results, actions = [], []
    for call in tool_calls:
        function = call.get("function", {})
        name = function.get("name", "")
        text, for_model = run_tool(name, function.get("arguments") or {})
        if for_model:
            results.append((name, text))
        else:
            actions.append(text or name)

    if not results:
        summary = direct or "Feito: " + "; ".join(actions)
        remember_turn(query, summary)
        return summary

    # Segunda chamada: o resultado das ferramentas vira a resposta falada
    followup = messages + [{"role": "assistant", "content": direct, "tool_calls": tool_calls}]
    followup += [{"role": "tool", "tool_name": name, "content": text[:8000]} for name, text in results]
    followup.append({"role": "system", "content": ANSWER_GUIDE})
    try:
        second = open_chat(followup)
    except Exception as error:
        print(f"[ROTEADOR] Falha ao responder com o resultado das ferramentas: {error}")
        speak(["Consegui os dados, mas não consegui montar a resposta agora."])
        return direct
    answer_parts = []
    speak(iter_chat(second, None, answer_parts))
    answer = (direct + " " + "".join(answer_parts)).strip()
    if answer:
        remember_turn(query, answer)
    return answer
