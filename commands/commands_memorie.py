import re
import string
import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.learning.response_with_memory import generate_dynamic_contextual_response
from brain.learning.insert_memory import insert_memory
from brain.learning.consult_memory import consultar_memoria
from brain.learning.update_memory import atualizar_memoria
from brain.learning.clean_memory import apagar_memoria
from brain.learning.list_memory import listar_memoria
from brain.learning.verify_memory import memoria_ja_existe
from commands.commands_search import execute_search
from brain.learning.consult_learnings_of_the_day import aprendizados_de_hoje
from brain.audio import say,listen
from brain.memory.memory import llama_query, DEFAULT_MODEL_HIGH

def learn(content):
    match = re.search(r"aprenda que (.+)", content)
    if match:
        data = match.group(1).strip()

        parts = data.split(" é ", 1)
        if len(parts) == 2:
            topic = parts[0].strip().lower()
            information = "é " + parts[1].strip()

            if memoria_ja_existe(topic):
                say("Eu já sabia disso, mas obrigado por reforçar!")
                return True

            if insert_memory(topic, information):
                say("Aprendido com sucesso.")
            else:
                say("Algo deu errado ao tentar aprender isso.")
        else:
            say("Não consegui entender o que devo aprender.")
        return True
    return False



def remember(content):
    match = re.search(r"(o que você sabe sobre|lembra sobre) (.+)", content)
    if match:
        subject = match.group(2).strip().rstrip("?.,!").lower()
        result = consultar_memoria(subject)

        if result:
            info, source, date = result
            say(f"Sim, eu sei que {info} (Fonte: {source}, Aprendido em {date})")
        else:
            response = generate_dynamic_contextual_response(subject)
            if response:
                say(response)
            else:
                say("Não consegui encontrar informações relevantes sobre isso.")
        return True
    return False

def update_info(content):
    match = re.search(r"atualize (.+) para (.+)", content)
    if match:
        old_info = match.group(1).strip()
        new_info = match.group(2).strip()
        if atualizar_memoria(old_info, new_info):
            say("Informação atualizada.")
        else:
            say("Não consegui atualizar isso.")
        return True
    return False

def forget(content):
    match = re.search(r"esqueça (.+)", content)
    if match:
        data = match.group(1).strip()
        if apagar_memoria(data):
            say("Informação esquecida.")
        else:
            say("Não consegui encontrar isso para esquecer.")
        return True
    return False

def list_all(content):
    titles = listar_memoria()
    if titles:
        listing = ", ".join(titles)
        say(f"Eu sei sobre: {listing}.")
    else:
        say("Ainda não aprendi nada.")
    return True

def learn_from_web(content):
    match = re.search(r"(pesquise|procure|busque)\s+sobre\s+(.+?)(?:\s+e\s+(aprenda|aprenda isso))?$", content, re.IGNORECASE)
    if match:
        subject = match.group(2).strip()

        # Now returns (response, main_source)
        response, source = execute_search(f"O que é {subject}?")
        if not response or "Erro" in response:
            say("Não consegui encontrar nada relevante na internet.")
            return True

        say(f"Deseja que eu memorize isso como conhecimento sobre {subject}?")

        confirmation = listen().lower()
        if "sim" in confirmation or "pode" in confirmation:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Clean title
            clean_title = subject.strip().lower()
            clean_title = re.sub(r"\be\b$", "", clean_title).strip()
            clean_title = clean_title.strip(string.punctuation)

            success = insert_memory(clean_title, response, source, date)

            if success:
                say(f"Informação aprendida com sucesso a partir da fonte {source}.")
            else:
                say("Não consegui armazenar essa informação.")
        else:
            say("Tudo bem, não vou memorizar isso.")
        return True
    return False

def learnings_today(content):
    titles = aprendizados_de_hoje()
    if titles:
        listing = ", ".join(titles)
        say(f"Hoje eu aprendi sobre: {listing}.")
    else:
        say("Hoje ainda não aprendi nada novo.")
    return True



comandos_memoria = {
    "aprenda que": learn,
    "o que você sabe sobre": remember,
    "lembra sobre": remember,
    "atualize": update_info,
    "esqueça": forget,
    "liste tudo o que você sabe": list_all,
    "liste tudo que você sabe": list_all,
    "pesquise sobre": learn_from_web,
    "o que você aprendeu hoje": learnings_today,
    "o que você aprendeu": learnings_today,
    "e você aprendeu": learnings_today 
}
