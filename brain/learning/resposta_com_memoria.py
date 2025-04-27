import re
from brain.learning.consultar_memoria import consultar_memoria, consultar_tudo
from brain.memoria import DEFAULT_MODEL,DEFAULT_MODEL_HIGH, generate_response


def generate_contextual_response(question, model=DEFAULT_MODEL):
    # Detect if the question is about programming code
    is_code_request = any(p in question.lower() for p in [
        "código", "script", "função", "programa",
        "html", "css", "javascript", "python",
        "classe",
    ])

    # If it's a code request, force the high model (LLaMA 3.3)
    model = DEFAULT_MODEL_HIGH if is_code_request else model

    match = re.search(r"sobre\s+(.+)", question.lower())
    subject = match.group(1).strip() if match else question.strip().lower()

    knowledge = consultar_memoria(subject)

    if knowledge:
        print(f"[🔍 CONTEXT] Pre-existing knowledge found about '{subject}'.")

    if is_code_request:
        prompt = (
            f"Gere apenas o código-fonte para: {question}\n"
            f"Não adicione comentários, explicações, título, introdução ou conclusão.\n"
            f"Use quebras de linha, indentação e escopo correto. Escreva o código como se fosse colado diretamente num editor de código.\n"
            f"Não coloque a linguagem ('python', 'javascript', etc.) no início.\n"
            f"Retorne apenas um único bloco de código válido entre crases triplas (```), sem texto fora dele."
        )
    else:
        prompt = (
            f"Você é Jarvis, um assistente que responde com base no que já aprendeu.\n\n"
            f"Conhecimento armazenado sobre '{subject}':\n{knowledge}\n\n"
            f"Pergunta: {question}\n"
            f"Responda de forma clara, objetiva e apenas com base no que você sabe.\n"
        )

    return generate_response(prompt, model)

def respond_with_inference(question, model=DEFAULT_MODEL):
    is_code_request = any(p in question.lower() for p in ["código", "script", "função", "programa", "html", "css", "javascript", "python", "classe", "crie", "faça"])

    if is_code_request:
        prompt = (
            f"Gere apenas o código-fonte para: {question}\n"
            f"Não adicione comentários, explicações, título, introdução ou conclusão.\n"
            f"Retorne apenas o bloco de código entre crases triplas no formato da linguagem."
        )
        return generate_response(prompt, model)

    topics = re.findall(
        r"\b(?:inteligência artificial|robótica|blockchain|energia renovável|biotecnologia|computação quântica|aumento da população)\b",
        question.lower()
    )
    topics = list(set(topics))

    if not topics:
        print("[🧠 INFERENCE] No topic identified in the question. Using direct model as final fallback.")
        prompt = (
            f"Você é Jarvis, um assistente que responde perguntas com base em conhecimento amplo.\n"
            f"Pergunta: {question}\n"
            f"Responda de forma objetiva e clara em português."
        )
        return generate_response(prompt, model)

    knowledge_base = []
    for topic in topics:
        content = consultar_memoria(topic)
        if content:
            knowledge_base.append((topic, content))
            print(f"[🧠 INFERENCE] Knowledge found: '{topic}'")
        else:
            print(f"[❌ INFERENCE] No saved data about: '{topic}'")

    if not knowledge_base:
        print("[🧠 INFERENCE] No knowledge base found. Using direct model as final fallback.")
        prompt = (
            f"Você é Jarvis, um assistente que responde perguntas com base em conhecimento amplo.\n"
            f"Pergunta: {question}\n"
            f"Responda de forma objetiva e clara em português."
        )
        return generate_response(prompt, model)

    context = "\n\n".join(
        f"[{title.upper()}]\n{text}" for title, text in knowledge_base
    )

    prompt = (
        f"Você é Jarvis, um assistente que responde com base no que já aprendeu.\n\n"
        f"Abaixo estão informações que você já aprendeu:\n\n{context}\n\n"
        f"Pergunta: {question}\n"
        f"Use o que aprendeu para responder de forma objetiva e em português."
    )

    print(f"[🧠 INFERENCE] Generating response based on multiple knowledge entries...")
    return generate_response(prompt, model)