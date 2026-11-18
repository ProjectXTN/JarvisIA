"""Janela de mídia do Jarvis: um vídeo por vez, sempre na mesma janela.

O navegador comum só aceita "abrir este endereço", e cada pedido virava uma
aba nova. Aqui o Jarvis abre o próprio Edge/Chrome, com um perfil separado e
controle remoto ligado só no próprio PC (127.0.0.1). No primeiro pedido a
janela abre com o vídeo; nos seguintes, o vídeo novo entra e o anterior é
fechado, sem acumular abas.

Perfil separado: na primeira vez o YouTube estará deslogado. Entrando na conta
uma vez nessa janela, ela fica lembrada (pasta data/browser-media).
"""

import os
import subprocess
import time
import webbrowser

import requests

from core.settings import BASE_DIR, MEDIA_BROWSER_PORT

PROFILE_DIR = os.path.join(BASE_DIR, "data", "browser-media")


def _url(path):
    return f"http://127.0.0.1:{MEDIA_BROWSER_PORT}{path}"


def _alive():
    try:
        return requests.get(_url("/json/version"), timeout=0.8).ok
    except requests.RequestException:
        return False


def _find_browser():
    from brain.avatar import _browser_for_app_window

    return _browser_for_app_window()


def _launch(url):
    browser = _find_browser()
    if not browser:
        return False
    os.makedirs(PROFILE_DIR, exist_ok=True)
    subprocess.Popen(
        [
            browser,
            f"--remote-debugging-port={MEDIA_BROWSER_PORT}",
            "--remote-allow-origins=http://127.0.0.1",
            f"--user-data-dir={PROFILE_DIR}",
            "--autoplay-policy=no-user-gesture-required",  # o vídeo começa sozinho
            "--no-first-run",
            "--new-window",
            url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def _pages():
    targets = requests.get(_url("/json/list"), timeout=2).json()
    return [t for t in targets if t.get("type") == "page"]


def _new_page(url):
    # Chrome/Edge recentes exigem PUT; versões antigas aceitam GET
    response = requests.put(_url("/json/new?" + url), timeout=3)
    if response.status_code == 405:
        response = requests.get(_url("/json/new?" + url), timeout=3)
    response.raise_for_status()
    return response.json()


def open_media(url):
    """Abre a URL na janela de mídia, substituindo o que estava tocando.

    Devolve "nova janela", "substituído" ou "navegador padrão".
    """
    if not _alive():
        if _launch(url):
            print("[MÍDIA] Janela de mídia aberta.")
            return "nova janela"
        webbrowser.open(url, new=2)
        return "navegador padrão"
    try:
        old = _pages()
        new = _new_page(url)
        for page in old:  # o que estava tocando sai
            requests.get(_url(f"/json/close/{page['id']}"), timeout=2)
        requests.get(_url(f"/json/activate/{new['id']}"), timeout=2)
        print(f"[MÍDIA] Substituído ({len(old)} aba(s) anterior(es) fechada(s)).")
        return "substituído"
    except Exception as error:
        print(f"[MÍDIA] Controle da janela falhou ({error}); usando o navegador padrão.")
        webbrowser.open(url, new=2)
        return "navegador padrão"
