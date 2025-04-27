import re
import time
import pyautogui
import pyperclip
import webbrowser
import keyboard
from brain.audio import say

def play_music(_):
    say("Abrindo sua biblioteca de músicas no navegador.")
    webbrowser.open("https://music.apple.com/us/library/recently-added", new=2)
    return True

def search_and_play_apple_music(query):
    music = query
    for word in ["tocar", "toque", "coloque", "quero ouvir", "na música", "no apple music", "apple music"]:
        music = music.replace(word, "")
    music = music.strip()

    say(f"Procurando por {music} no Apple Music.")

    webbrowser.open("https://music.apple.com/us/search", new=2)
    time.sleep(5)

    pyperclip.copy(music)
    pyautogui.press("tab", presses=2, interval=0.2)
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")

    say("Buscando a música...")

    return True

def pause_music(_):
    say("Pausando a música.")
    keyboard.send("play/pause media")
    return True

def next_music(_):
    say("Avançando para a próxima música.")
    keyboard.send("next track")
    return True

def previous_music(_):
    say("Voltando para a música anterior.")
    keyboard.send("previous track")
    return True

music_commands = [
    (r"\b(tocar|toque|coloque|quero ouvir)\b", search_and_play_apple_music),
    (r"\b(abrir|iniciar)\s+(minha\s+)?(biblioteca|playlist|apple music|música)$", play_music),
    (r"\b(pausar|parar|interromper)\s+(a\s+)?música\b", pause_music),
    (r"\b(stop|pausa)\b", pause_music),
    (r"\b(próxima|avançar|pular|trocar)\s+(faixa|música)\b", next_music),
    (r"\b(troca|passa)\s+(a\s+)?música\b", next_music),
    (r"\b(voltar|anterior|volte)\s+(faixa|música)\b", previous_music),
    (r"\b(retornar|volte)\s+.*música\b", previous_music)
]
