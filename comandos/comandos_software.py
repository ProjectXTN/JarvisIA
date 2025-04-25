import subprocess
import re
from brain.audio import say

def abrir_software(nome_software):
    caminhos = {
        "steam": r"C:\Program Files (x86)\Steam\Steam.exe",
        "discord": r"C:\Users\pedro\AppData\Local\Discord\Update.exe --processStart Discord.exe"
    }

    if nome_software in caminhos:
        try:
            subprocess.Popen(caminhos[nome_software])
            say(f"Abrindo o {nome_software.capitalize()} agora.")
        except Exception as e:
            say(f"Não consegui abrir o {nome_software}: {e}")
    else:
        say(f"Não sei como abrir o {nome_software} ainda.")

def comando_software(query):
    if re.search(r"\b(steam)\b", query):
        abrir_software("steam")
        return True
    if re.search(r"\b(discord)\b", query):
        abrir_software("discord")
        return True
    return False

comandos_software = {
    "steam": comando_software,
    "discord": comando_software
}
