import os
import subprocess
import webbrowser
from datetime import datetime

def abrir_pasta(nome_pasta):
    nome_pasta = nome_pasta.strip().lower().replace(".", "").replace("á", "a").replace("ã", "a").replace("ç", "c")

    pastas_mapeadas = {
        "documentos": "Documents",
        "downloads": "Downloads",
        "imagens": "Pictures",
        "musicas": "Music",
        "músicas": "Music",
        "videos": "Videos",
        "vídeos": "Videos",
        "area de trabalho": "Desktop",
        "desktop": "Desktop"
    }

    pasta_convertida = pastas_mapeadas.get(nome_pasta, nome_pasta.capitalize())
    caminho = os.path.expanduser(f"~\\{pasta_convertida}")

    if os.path.isdir(caminho):
        subprocess.Popen(["explorer", caminho])
        return f"Abrindo a pasta \"{nome_pasta}\"."
    else:
        return f"Não encontrei a pasta \"{nome_pasta}\" na sua máquina."

def open_browser():
    webbrowser.open("https://www.google.com", new=2)

def search_google(query):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url, new=2)

def open_vscode():
    try:
        subprocess.Popen("code", shell=True)
    except FileNotFoundError:
        print("VS Code não encontrado. Verifique se o comando 'code' está no PATH.")