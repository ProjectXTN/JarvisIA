import re
import string
from brain.audio import say
from brain.sistema import abrir_pasta

def comando_abrir_pasta(query):
    texto = query.lower()
    texto = texto.translate(str.maketrans("", "", string.punctuation))  # remove pontuação

    # Regex mais flexível
    padrao = r"(abr(a|ir|e)?( a)? pasta(?: de)? )([\w\sçáéíóúãõâêîôû]+)"
    match = re.search(padrao, texto)

    if match:
        nome_pasta = match.group(4).strip()
        resposta = abrir_pasta(nome_pasta)
        say(resposta)
    else:
        say("Você precisa me dizer o nome da pasta.")

    return True

comandos_pastas = {
    "abrir pasta": comando_abrir_pasta,
    "abrir a pasta": comando_abrir_pasta,
    "abra a pasta": comando_abrir_pasta,
    "abra pasta": comando_abrir_pasta,
    "abre a pasta": comando_abrir_pasta,
    "abre pasta": comando_abrir_pasta,
}
