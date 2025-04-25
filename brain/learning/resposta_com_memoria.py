import re
from brain.learning.consultar_memoria import consultar_memoria, consultar_tudo
from brain.memoria import DEFAULT_MODEL,DEFAULT_MODEL_HIGH, generate_response


def generate_contextual_response(pergunta, modelo=DEFAULT_MODEL):
    # Detecta se a pergunta é sobre código de programação
    dev_codigo = any(p in pergunta.lower() for p in [
        "código", "script", "função", "programa",
        "html", "css", "javascript", "python",
        "classe",
    ])

    # Se for pedido de código, forçamos o modelo high (LLaMA 3.3)
    modelo = DEFAULT_MODEL_HIGH if dev_codigo else modelo

    match = re.search(r"sobre\s+(.+)", pergunta.lower())
    assunto = match.group(1).strip() if match else pergunta.strip().lower()

    conhecimento = consultar_memoria(assunto)

    if conhecimento:
        print(f"[🔍 CONTEXTO] Conhecimento pré-existente encontrado sobre '{assunto}'.")

    if dev_codigo:
        prompt = (
            f"Gere apenas o código-fonte para: {pergunta}\n"
            f"Não adicione comentários, explicações, título, introdução ou conclusão.\n"
            f"Use quebras de linha, indentação e escopo correto. Escreva o código como se fosse colado diretamente num editor de código.\n"
            f"Não coloque a linguagem ('python', 'javascript', etc.) no início.\n"
            f"Retorne apenas um único bloco de código válido entre crases triplas (```), sem texto fora dele."
        )
    else:
        prompt = (
            f"Você é Jarvis, um assistente que responde com base no que já aprendeu.\n\n"
            f"Conhecimento armazenado sobre '{assunto}':\n{conhecimento}\n\n"
            f"Pergunta: {pergunta}\n"
            f"Responda de forma clara, objetiva e apenas com base no que você sabe.\n"
        )

    return generate_response(prompt, modelo)


def responder_com_inferencia(pergunta, modelo=DEFAULT_MODEL):
    dev_codigo = any(p in pergunta.lower() for p in ["código", "script", "função", "programa", "html", "css", "javascript", "python", "classe", "crie", "faça"])

    if dev_codigo:
        prompt = (
            f"Gere apenas o código-fonte para: {pergunta}\n"
            f"Não adicione comentários, explicações, título, introdução ou conclusão.\n"
            f"Retorne apenas o bloco de código entre crases triplas no formato da linguagem."
        )
        return generate_response(prompt, modelo)

    topicos = re.findall(
        r"\b(?:inteligência artificial|robótica|blockchain|energia renovável|biotecnologia|computação quântica|aumento da população)\b",
        pergunta.lower()
    )
    topicos = list(set(topicos))

    if not topicos:
        print("[🧠 INFERÊNCIA] Nenhum tópico identificado na pergunta. Usando modelo direto como fallback final.")
        prompt = (
            f"Você é Jarvis, um assistente que responde perguntas com base em conhecimento amplo.\n"
            f"Pergunta: {pergunta}\n"
            f"Responda de forma objetiva e clara em português."
        )
        return generate_response(prompt, modelo)

    conhecimentos = []
    for topico in topicos:
        conteudo = consultar_memoria(topico)
        if conteudo:
            conhecimentos.append((topico, conteudo))
            print(f"[🧠 INFERÊNCIA] Conhecimento encontrado: '{topico}'")
        else:
            print(f"[❌ INFERÊNCIA] Nenhum dado salvo sobre: '{topico}'")

    if not conhecimentos:
        print("[🧠 INFERÊNCIA] Nenhuma base de conhecimento foi encontrada. Usando modelo direto como fallback final.")
        prompt = (
            f"Você é Jarvis, um assistente que responde perguntas com base em conhecimento amplo.\n"
            f"Pergunta: {pergunta}\n"
            f"Responda de forma objetiva e clara em português."
        )
        return generate_response(prompt, modelo)

    contexto = "\n\n".join(
        f"[{titulo.upper()}]\n{texto}" for titulo, texto in conhecimentos
    )

    prompt = (
        f"Você é Jarvis, um assistente que responde com base no que já aprendeu.\n\n"
        f"Abaixo estão informações que você já aprendeu:\n\n{contexto}\n\n"
        f"Pergunta: {pergunta}\n"
        f"Use o que aprendeu para responder de forma objetiva e em português."
    )

    print(f"[🧠 INFERÊNCIA] Gerando resposta com base em múltiplos conhecimentos...")
    return generate_response(prompt, modelo)
