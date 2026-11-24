import subprocess
import psutil
import shutil
import platform
import re
from brain.audio import say
from brain.system import open_folder


# Auxiliary system status function
def system_usage():
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = shutil.disk_usage("/")
    return (
        f"🖥️ Sistema: {platform.system()}\n"
        f"🧠 CPU: {cpu}%\n"
        f"💾 RAM: {mem.percent}%\n"
        f"💽 Disco: {disk.used // (1024**3)}GB de {disk.total // (1024**3)}GB"
    )


# Main handler for system commands
def system_command(query):
    query = query.lower()

    if (
        "uso da memória" in query
        or "uso da cpu" in query
        or "status do sistema" in query
    ):
        say(system_usage())
        return True

    elif "abrir a pasta" in query:
        name = query.split("abrir a pasta")[-1].strip()
        if open_folder(name):
            say(f'Pasta "{name}" aberta.')
        else:
            say(f'Pasta "{name}" não encontrada.')
        return True

    elif "abrir pasta" in query:
        path = query.split("abrir pasta")[-1].strip()
        if path:
            response = open_folder(path)
            say(response)
        else:
            say("Informe o nome da pasta.")
        return True

    return False


# Só desliga quando a frase inteira é um pedido de desligamento.
# Palavras soltas no meio de outra frase ("o que ele falou", "quando vai sair")
# não contam mais.
_SHUTDOWN_VERB = r"(desligar|desliga|desligue|encerrar|encerra|encerre)"
SHUTDOWN_PATTERNS = [
    # "desligar", "jarvis pode desligar", "sair", "encerrar o sistema agora"
    rf"^(jarvis )?(pode )?(se )?({_SHUTDOWN_VERB}|sair)( (o )?(jarvis|sistema))?( agora)?( jarvis)?$",
    # despedidas ditas sozinhas
    r"^(jarvis )?(tchau|adeus|até logo|ate logo|até mais|ate mais|vai embora|vá embora|pode ir embora)( jarvis)?$",
    # "... desligar o jarvis" / "... encerre o sistema" no fim da frase
    rf"\b{_SHUTDOWN_VERB}( o)? (jarvis|sistema)( agora)?$",
]


def is_shutdown_request(query):
    """True se a frase é um pedido explícito para desligar o Jarvis."""
    normalized = re.sub(r"[^\w\s]", " ", query.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return any(re.search(pattern, normalized) for pattern in SHUTDOWN_PATTERNS)


def shutdown_command(query):
    """Devolve False quando o Jarvis deve desligar, True caso contrário."""
    if is_shutdown_request(query):
        say("Jarvis desligando.")

        return False

    return True
