import os
import subprocess
import webbrowser
from datetime import datetime

def open_folder(folder_name):
    folder_name = folder_name.strip().lower().replace(".", "").replace("á", "a").replace("ã", "a").replace("ç", "c")

    mapped_folders = {
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

    converted_folder = mapped_folders.get(folder_name, folder_name.capitalize())
    path = os.path.expanduser(f"~\\{converted_folder}")

    if os.path.isdir(path):
        subprocess.Popen(["explorer", path])
        return f"Abrindo a pasta \"{folder_name}\"."
    else:
        return f"Não encontrei a pasta \"{folder_name}\" na sua máquina."

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
