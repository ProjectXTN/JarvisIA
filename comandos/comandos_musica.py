import re
import time
import pyautogui
import pyperclip
import webbrowser
import keyboard
from brain.audio import say

def tocar_musica(_):
    say("Abrindo sua biblioteca de músicas no navegador.")
    webbrowser.open("https://music.apple.com/us/library/recently-added", new=2)
    return True

def buscar_e_tocar_apple_music(query):
    musica = query
    for palavra in ["tocar", "toque", "coloque", "quero ouvir", "na música", "no apple music", "apple music"]:
        musica = musica.replace(palavra, "")
    musica = musica.strip()

    say(f"Procurando por {musica} no Apple Music.")

    webbrowser.open("https://music.apple.com/us/search", new=2)
    time.sleep(5)

    pyperclip.copy(musica)
    pyautogui.press("tab", presses=2, interval=0.2)
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")

    say("Buscando a música...")

    return True


def pausar_musica(_):
    say("Pausando a música.")
    keyboard.send("play/pause media")
    return True

def avancar_musica(_):
    say("Avançando para a próxima música.")
    keyboard.send("next track")
    return True

def voltar_musica(_):
    say("Voltando para a música anterior.")
    keyboard.send("previous track")
    return True


comandos_musica = [
    (r"\b(tocar|toque|coloque|quero ouvir)\b", buscar_e_tocar_apple_music),
    (r"\b(abrir|iniciar)\s+(minha\s+)?(biblioteca|playlist|apple music|música)$", tocar_musica),
    (r"\b(pausar|parar|interromper)\s+(a\s+)?música\b", pausar_musica),
    (r"\b(stop|pausa)\b", pausar_musica),
    (r"\b(próxima|avançar|pular|trocar)\s+(faixa|música)\b", avancar_musica),
    (r"\b(troca|passa)\s+(a\s+)?música\b", avancar_musica),
    (r"\b(voltar|anterior|volte)\s+(faixa|música)\b", voltar_musica),
    (r"\b(retornar|volte)\s+.*música\b", voltar_musica)
]
