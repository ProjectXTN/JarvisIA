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

# Só aprende quando você pede: "pesquise sobre X e aprenda", "aprenda sobre X",
# "estude sobre X". Um "pesquise sobre X" simples vai para a busca normal (com
# contexto da conversa e fala em fluxo). Antes este comando pegava qualquer
# "pesquise sobre" e ainda perguntava se devia memorizar.
LEARN_FROM_WEB = re.compile(
    r"(?:(?:pesquise|procure|busque)\s+sobre\s+(?P<a>.+?)\s+e\s+(?:aprenda|memorize|guarde)(?:\s+isso)?"
    r"|(?:aprenda|estude|memorize)\s+(?:sobre|a respeito de)\s+(?P<b>.+?))[\s.!?]*$",
    re.IGNORECASE,
)


def learn_from_web(content):
    match = LEARN_FROM_WEB.search(content)
    if not match:
        return False
    subject = (match.group("a") or match.group("b")).strip()

    # Fala o resumo e devolve (resumo, fonte principal)
    response, source = execute_search(f"O que é {subject}?")
    if not response or "Erro" in response:
        return True  # execute_search já avisou que não encontrou

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_title = subject.strip().lower().strip(string.punctuation)
    if insert_memory(clean_title, response, source, date):
        say(f"Guardei isso sobre {clean_title}.")
    else:
        say("Não consegui guardar essa informação.")
    return True

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
    "aprenda sobre": learn_from_web,
    "estude sobre": learn_from_web,
    "memorize sobre": learn_from_web,
    "e aprenda": learn_from_web,
    "e memorize": learn_from_web,
    "e guarde": learn_from_web,
    "o que você aprendeu hoje": learnings_today,
    "o que você aprendeu": learnings_today,
    "e você aprendeu": learnings_today 
}
