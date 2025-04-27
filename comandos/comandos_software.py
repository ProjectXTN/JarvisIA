import subprocess
import re
from brain.audio import say

def open_software(software_name):
    paths = {
        "steam": r"C:\Program Files (x86)\Steam\Steam.exe",
        "discord": r"C:\Users\pedro\AppData\Local\Discord\Update.exe --processStart Discord.exe"
    }

    if software_name in paths:
        try:
            subprocess.Popen(paths[software_name])
            say(f"Abrindo o {software_name.capitalize()} agora.")
        except Exception as e:
            say(f"Não consegui abrir o {software_name}: {e}")
    else:
        say(f"Não sei como abrir o {software_name} ainda.")

def software_command(query):
    if re.search(r"\b(steam)\b", query):
        open_software("steam")
        return True
    if re.search(r"\b(discord)\b", query):
        open_software("discord")
        return True
    return False

software_commands = {
    "steam": software_command,
    "discord": software_command
}
