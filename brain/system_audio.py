"""Descobre se OUTRO programa está tocando som no PC (live, vídeo, música, jogo).

Com som tocando, o microfone pega a voz da live e o Whisper transcreve como se
fosse o Pedro. Nesse caso o Jarvis só aceita frases que comecem com "Jarvis".

Usa o medidor de pico das sessões de áudio do Windows (biblioteca pycaw).
Sem pycaw (pip install pycaw) ou fora do Windows, responde False e o Jarvis
fica só com a janela curta de conversa.
"""
import os
import time

_warned = {"done": False}


def other_audio_playing(threshold=0.01, samples=3, interval=0.05):
    try:
        import comtypes
        from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
    except ImportError:
        if not _warned["done"]:
            _warned["done"] = True
            print("[ÁUDIO DO PC] pycaw não instalado (pip install pycaw): não sei se há som tocando.")
        return False
    try:
        comtypes.CoInitialize()
    except OSError:
        pass
    me = os.getpid()
    try:
        meters = []
        for session in AudioUtilities.GetAllSessions():
            process = session.Process
            if process is None or process.pid == me:
                continue  # sons do sistema e a própria voz do Jarvis não contam
            meters.append((process.name(), session._ctl.QueryInterface(IAudioMeterInformation)))
        for _ in range(samples):
            for name, meter in meters:
                if meter.GetPeakValue() > threshold:
                    return name
            time.sleep(interval)
    except Exception as error:
        print(f"[ÁUDIO DO PC] Não consegui medir: {error}")
    return False
