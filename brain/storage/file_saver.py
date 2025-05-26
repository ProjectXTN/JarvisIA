import os
import re
from datetime import datetime, timedelta
import unidecode

from brain.audio import say

def should_save_to_file(query):
    triggers = [
        "receita",
        "escreva",
        "passo a passo",
        "relatorio",
        "documento",
    ]
    normalized_query = unidecode.unidecode(query.lower())
    return any(trigger in normalized_query for trigger in triggers)


def save_response_to_file(question, response):
    try:
        # Pega o caminho da pasta Documentos do usuário
        documents_folder = os.path.join(os.path.expanduser("~"), "Documents")

        if not os.path.exists(documents_folder):
            print("Pasta 'Documentos' não encontrada.")
            return

        # Limpa o título do arquivo
        file_title = re.sub(r'[^\w\s-]', '', question).strip()
        file_title = re.sub(r'\s+', '_', file_title)

        file_path = os.path.join(documents_folder, f"{file_title}.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Pergunta: {question}\n\n")
            f.write(f"Resposta do Jarvis:\n{response}")
        
        print(f"Resposta salva com sucesso em: {file_path}")
        say(f"Resposta salva na pasta Documentos como {file_title}.txt")

    except Exception as e:
        print(f"Erro ao salvar a resposta: {e}")


##SERVICE NOT ACTIVATE
def list_recent_files(limit=5, last_24h_only=False):
    documents_folder = os.path.join(os.path.expanduser("~"), "Documents")

    if not os.path.exists(documents_folder):
        print("Nenhuma pasta 'Documentos' encontrada.")
        return

    files = [
        os.path.join(documents_folder, f)
        for f in os.listdir(documents_folder)
        if f.endswith(".txt") and os.path.isfile(os.path.join(documents_folder, f))
    ]

    if not files:
        print("Nenhum arquivo .txt encontrado na pasta Documentos.")
        return

    filtered_files = []

    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                if "Resposta do Jarvis" in content:
                    if last_24h_only:
                        file_time = datetime.fromtimestamp(os.path.getmtime(file))
                        if datetime.now() - file_time <= timedelta(days=1):
                            filtered_files.append(file)
                    else:
                        filtered_files.append(file)
        except Exception as e:
            print(f"Erro ao ler o arquivo {file}: {e}")

    if not filtered_files:
        print("Nenhum arquivo relevante encontrado.")
        return

    # Sort by modified time (newest first)
    filtered_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    print(f"📄 Últimos {min(limit, len(filtered_files))} arquivos relevantes:\n")

    for idx, file in enumerate(filtered_files[:limit], start=1):
        modified_time = datetime.fromtimestamp(os.path.getmtime(file)).strftime("%d/%m/%Y %H:%M:%S")
        file_name = os.path.basename(file)
        print(f"{idx}. {file_name} (Modificado em: {modified_time})")