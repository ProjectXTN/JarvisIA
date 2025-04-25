from utils_datetime import responder_data, responder_hora
from brain.audio import say

def comando_data(query):
    say(responder_data())
    return True

def comando_hora(query):
    say(responder_hora())
    return True

# === DICIONÁRIO DE COMANDOS ===
comandos_datahora = {
    "que dia é hoje": comando_data,
    "qual é a data de hoje": comando_data,
    "que horas são": comando_hora,
    "me diga as horas": comando_hora,
    "horas": comando_hora
}
