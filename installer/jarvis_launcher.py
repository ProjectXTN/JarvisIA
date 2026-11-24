"""Jarvis.exe: abre o Jarvis como um programa comum.

Compilado com PyInstaller (só biblioteca padrão, ~8 MB). Fica na pasta do
Jarvis, ao lado do jarvis.py:
  Jarvis.exe            abre o Jarvis (janela de console com o log)
  Jarvis.exe --api      abre a API do site e o túnel (start_api.bat)
  Jarvis.exe --painel   abre a API e o painel no navegador
  Jarvis.exe --instalar roda o install.bat de novo (atualiza bibliotecas/modelos)
Se o venv ainda não existe (primeira vez), roda o install.bat antes.
"""
import ctypes
import os
import subprocess
import sys
import time
import webbrowser

NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)


def root_dir():
    base = sys.executable if getattr(sys, "frozen", False) else __file__
    here = os.path.dirname(os.path.abspath(base))
    # Rodando de installer/ durante o desenvolvimento: sobe para a pasta do projeto
    return here if os.path.isfile(os.path.join(here, "jarvis.py")) else os.path.dirname(here)


def message(text, title="Jarvis", error=False):
    try:
        ctypes.windll.user32.MessageBoxW(None, text, title, 0x10 if error else 0x40)
    except (AttributeError, OSError):
        print(f"{title}: {text}")


def run_installer(root):
    bat = os.path.join(root, "install.bat")
    if not os.path.isfile(bat):
        message(f"Não achei o install.bat em {root}.", error=True)
        return False
    subprocess.run(["cmd.exe", "/c", bat], cwd=root, creationflags=NEW_CONSOLE)
    return True


def main():
    root = root_dir()
    python = os.path.join(root, "venv", "Scripts", "python.exe")
    args = set(a.lower() for a in sys.argv[1:])

    if "--instalar" in args or not os.path.isfile(python):
        if not os.path.isfile(python):
            message("Primeira vez: vou instalar o que o Jarvis precisa (Python, bibliotecas e modelos). "
                    "Pode levar um tempo, principalmente o download dos modelos.")
        if not run_installer(root) or not os.path.isfile(python):
            message("A instalação não terminou. Abra o install.bat na pasta do Jarvis para ver o erro.",
                    error=True)
            return 1
        if "--instalar" in args:
            return 0

    if "--api" in args or "--painel" in args:
        subprocess.Popen(["cmd.exe", "/c", os.path.join(root, "start_api.bat")], cwd=root,
                         creationflags=NEW_CONSOLE)
        if "--painel" in args:
            time.sleep(4)
            webbrowser.open("http://127.0.0.1:11600/painel")
        return 0

    subprocess.Popen([python, "jarvis.py"], cwd=root, creationflags=NEW_CONSOLE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
