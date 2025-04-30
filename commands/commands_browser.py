from brain.audio import say
from brain.system import open_browser, open_vscode

def browser_command(query):
    if "abrir navegador" in query or "abrir chrome" in query:
        say("Abrindo o navegador agora.")
        open_browser()
        return True

    elif "abrir vs code" in query or "abrir visual studio code" in query:
        say("Abrindo o VS Code agora.")
        open_vscode()
        return True

    return False

# === Commands dictionary ===
browser_commands = {
    "abrir navegador": browser_command,
    "abrir chrome": browser_command,
    "abrir vs code": browser_command,
    "abrir visual studio code": browser_command
}