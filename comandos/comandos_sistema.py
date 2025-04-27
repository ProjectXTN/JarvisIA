import psutil
import shutil
import platform
import re
from brain.localizacao import get_location
from brain.audio import say
from brain.sistema import open_folder

# Função auxiliar de status
def uso_sistema():
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disco = shutil.disk_usage("/")
    return (
        f"🖥️ Sistema: {platform.system()}\n"
        f"🧠 CPU: {cpu}%\n"
        f"💾 RAM: {mem.percent}%\n"
        f"💽 Disco: {disco.used // (1024**3)}GB de {disco.total // (1024**3)}GB"
    )

# Handler principal de comandos do sistema
def comando_sistema(query):
    query = query.lower()

    if "uso da memória" in query or "uso da cpu" in query or "status do sistema" in query:
        say(uso_sistema())
        return True

    elif "abrir a pasta" in query:
        nome = query.split("abrir a pasta")[-1].strip()
        if open_folder(nome):
            say(f"Pasta \"{nome}\" aberta.")
        else:
            say(f"Pasta \"{nome}\" não encontrada.")
        return True

    elif "abrir pasta" in query:
        caminho = query.split("abrir pasta")[-1].strip()
        if caminho:
            resposta = open_folder(caminho)
            say(resposta)
        else:
            say("Informe o nome da pasta.")
        return True

    return False

def comando_desligar(query):
    query = query.lower()

    # Lista de padrões que indicam comandos de desligamento
    padroes = [
        r"\b(jarvis)?[ ,]*desliga[rs]?\b",
        r"\b(encerrar|desligar|sair|off|tchau|falou|vaza|vá embora|vai embora|até logo|adeus)\b",
        r"\b(jarvis)?[ ,]*(pode)?[ ]*(desligar|sair)\b"
    ]

    for padrao in padroes:
        if re.search(padrao, query):
            say("Jarvis desligando.")
            return False  # Retorna False para encerrar o loop principal

    return True

def comando_localizacao(query):
    if "onde estou" in query or "qual minha localização" in query:
        resposta = get_location()
        say(resposta)
        return True
    return False

# Dicionário de comandos do sistema
comandos_sistema = {
    "abrir a pasta": comando_sistema,
    "abrir pasta": comando_sistema,
    "uso da memória": comando_sistema,
    "uso da cpu": comando_sistema,
    "status do sistema": comando_sistema
}