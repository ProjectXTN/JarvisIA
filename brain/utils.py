import os
import re
from datetime import datetime

def contem_data_antiga(resposta: str, tolerancia=1) -> bool:
    """Retorna True se encontrar datas muito antigas na resposta."""
    anos = re.findall(r"\b(19\d{2}|20\d{2})\b", resposta)
    if not anos:
        return False

    ano_atual = datetime.now().year
    for ano in anos:
        if int(ano) < (ano_atual - tolerancia):  # permite 2023 se estamos em 2024
            return True
    return False

def resposta_desatualizada(resposta: str, query: str) -> bool:
    palavras_chave = ["hoje", "atual", "agora", "neste momento", "previsão", "cotação", "valor"]
    ignorar_se_query_historica = ["história", "presidentes", "biografia", "quando", "passado", "fundação", "inauguração"]

    query_lower = query.lower()

    # Se for uma pergunta histórica, não considerar desatualizada
    if any(p in query_lower for p in ignorar_se_query_historica):
        return False

    # Se a pergunta fala de algo atual, verificar datas antigas
    if any(p in query_lower for p in palavras_chave):
        anos = re.findall(r"\b(19\d{2}|20\d{2})\b", resposta)
        for ano in anos:
            if int(ano) < datetime.now().year - 1:
                return True

    return False

def log_interaction(user_input, response):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y-%m-%d')}.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Você: {user_input}\n")
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Jarvis: {response}\n\n")

def clean_output(text):
    # Remove negrito/itálico em Markdown (**, *, __, _)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)  # negrito
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)      # itálico
    lines = text.splitlines()
    lines = [line for line in lines if line.strip() and not line.strip().startswith(">")]
    return " ".join(lines)
