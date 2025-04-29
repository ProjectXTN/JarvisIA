import subprocess
import psutil
import shutil
import platform
import re
from brain.audio import say
from brain.sistema import open_folder
from core.inicializador import get_stable_diffusion_process
from core.inicializador import get_stable_diffusion_pid


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


def shutdown_stable_diffusion():
    pid = get_stable_diffusion_pid()

    if pid is not None:
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"])
            print(f"Stable Diffusion (PID {pid}) terminated cleanly.")
        except Exception as e:
            print(f"Failed to shutdown Stable Diffusion server: {e}")
    else:
        print("No Stable Diffusion process to terminate.")


def shutdown_command(query):
    query = query.lower()

    # List of patterns indicating shutdown commands
    patterns = [
        r"\b(jarvis)?[ ,]*desliga[rs]?\b",
        r"\b(encerrar|desligar|sair|off|tchau|falou|vaza|vá embora|vai embora|até logo|adeus)\b",
        r"\b(jarvis)?[ ,]*(pode)?[ ]*(desligar|sair)\b",
    ]

    for pattern in patterns:
        if re.search(pattern, query):
            say("Jarvis desligando.")

            shutdown_stable_diffusion()

            return False

    return True
