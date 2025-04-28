import re
from brain.learning.consultar_memoria import consultar_memoria, consultar_tudo
from brain.memoria import DEFAULT_MODEL, DEFAULT_MODEL_HIGH, llama_query

def is_code_request(question):
    """Detect if the question is requesting code."""
    keywords = ["código", "script", "função", "programa", "html", "css", "javascript", "python", "classe", "crie", "faça"]
    return any(word in question.lower() for word in keywords)

def find_best_topic(question):
    """Find the best matching topic from the knowledge base."""
    all_knowledge = consultar_tudo()
    question_lower = question.lower()
    
    for title, _ in all_knowledge:
        if title.lower() in question_lower:
            print(f"[🔍 MATCH] Topic match found: '{title}'")
            return title
    print("[🔎 MATCH] No specific topic found in knowledge base.")
    return None

def generate_dynamic_contextual_response(question, model=DEFAULT_MODEL_HIGH):
    """Generate a response dynamically using existing knowledge if possible."""
    # Detect code request
    if is_code_request(question):
        model = DEFAULT_MODEL_HIGH
        prompt = (
            f"Gere apenas o código-fonte para: {question}\n"
            f"Não adicione comentários, explicações, título, introdução ou conclusão.\n"
            f"Use quebras de linha, indentação e escopo correto. Escreva o código como se fosse colado diretamente num editor de código.\n"
            f"Não coloque a linguagem ('python', 'javascript', etc.) no início.\n"
            f"Retorne apenas um único bloco de código válido entre crases triplas (```), sem texto fora dele."
        )
        return llama_query(prompt, model)

    # Try to match a topic from knowledge base
    matched_topic = find_best_topic(question)

    if matched_topic:
        knowledge = consultar_memoria(matched_topic)
        if knowledge:
            print(f"[🧠 CONTEXT] Knowledge found for topic: '{matched_topic}'.")
            content = knowledge[0]
            prompt = (
                f"Você é Jarvis, um assistente que responde com base no que já aprendeu.\n\n"
                f"Conhecimento armazenado sobre '{matched_topic}':\n{content}\n\n"
                f"Pergunta: {question}\n"
                f"Responda de forma clara, objetiva e apenas com base no que você sabe."
            )
            return llama_query(prompt, model)
        else:
            print(f"[❌ CONTEXT] Topic matched but no content found for: '{matched_topic}'.")

    # Fallback if no contextual match found
    print("[🧠 CONTEXT] No contextual match found. Using fallback prompt.")
    prompt = (
        f"Você é Jarvis, um assistente que responde perguntas com base em conhecimento amplo.\n"
        f"Pergunta: {question}\n"
        f"Responda de forma objetiva e clara em português."
    )
    return llama_query(prompt, model)
