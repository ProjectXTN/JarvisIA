import os
import subprocess
import webbrowser


def open_folder(folder_name):
    folder_name = (
        folder_name.strip()
        .lower()
        .replace(".", "")
        .replace("á", "a")
        .replace("ã", "a")
        .replace("ç", "c")
    )

    mapped_folders = {
        "documentos": "Documents",
        "downloads": "Downloads",
        "imagens": "Pictures",
        "musicas": "Music",
        "músicas": "Music",
        "videos": "Videos",
        "vídeos": "Videos",
        "area de trabalho": "Desktop",
        "desktop": "Desktop",
    }

    converted_folder = mapped_folders.get(folder_name, folder_name.capitalize())
    path = os.path.expanduser(f"~\\{converted_folder}")

    if os.path.isdir(path):
        subprocess.Popen(["explorer", path])
        return f'Abrindo a pasta "{folder_name}".'
    else:
        return f'Não encontrei a pasta "{folder_name}" na sua máquina.'


def open_in_chrome(url):
    """Abre a URL no Chrome de Pedro (perfil normal, nova aba).

    Preferência do Pedro: Chrome; o Edge só se não houver Chrome; se nenhum
    for encontrado, o navegador padrão do Windows.
    """
    from brain.avatar import _browser_for_app_window

    browser = _browser_for_app_window()
    if browser:
        try:
            subprocess.Popen([browser, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except OSError as error:
            print(f"[NAVEGADOR] Não consegui abrir {browser}: {error}")
    webbrowser.open(url, new=2)


def open_browser():
    open_in_chrome("https://www.google.com")


def search_google(query):
    from urllib.parse import quote_plus

    open_in_chrome("https://www.google.com/search?q=" + quote_plus(query))


def open_vscode():
    try:
        subprocess.Popen("code", shell=True)
    except FileNotFoundError:
        print("VS Code não encontrado. Verifique se o comando 'code' está no PATH.")
