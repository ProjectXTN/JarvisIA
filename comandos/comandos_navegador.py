from brain.audio import say
from brain.sistema import open_browser, open_vscode

def comando_navegador(query):
    if "abrir navegador" in query or "abrir chrome" in query:
        say("Abrindo o navegador agora.")
        open_browser()
        return True

    elif "abrir vs code" in query or "abrir visual studio code" in query:
        say("Abrindo o VS Code agora.")
        open_vscode()
        return True

    return False

# === Dicionário de comandos ===
comandos_navegador = {
    "abrir navegador": comando_navegador,
    "abrir chrome": comando_navegador,
    "abrir vs code": comando_navegador,
    "abrir visual studio code": comando_navegador
}
