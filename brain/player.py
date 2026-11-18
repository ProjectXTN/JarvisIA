"""Toca a fala direto pela placa de som, sem abrir o ffplay a cada frase.

SoundPlayer imita o pedaço do subprocess.Popen que o monitor de reprodução
usa (poll, terminate, kill, wait), então a interrupção por voz funciona igual.
WAV (Kokoro) toca pelo sounddevice; outros formatos (MP3 do Google, quando o
Kokoro falha) continuam pelo ffplay.
"""

import subprocess
import threading
import wave

import numpy as np

# Atraso típico entre mandar tocar e o som sair (ms), usado pelo avatar
SOUNDDEVICE_DELAY_MS = 40
FFPLAY_DELAY_MS = 180


def read_wav(path):
    """(amostras int16 [n, canais], taxa) de um WAV PCM de 16 bits."""
    with wave.open(path, "rb") as wav:
        if wav.getsampwidth() != 2:
            raise ValueError(f"WAV de {wav.getsampwidth() * 8} bits não suportado")
        channels, rate = wav.getnchannels(), wav.getframerate()
        data = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")
    return data.reshape(-1, channels), rate


class SoundPlayer:
    def __init__(self, samples, rate, sounddevice=None):
        if sounddevice is None:
            import sounddevice
        self._sd = sounddevice
        self._data = np.ascontiguousarray(samples, dtype=np.int16)
        if self._data.ndim == 1:
            self._data = self._data.reshape(-1, 1)
        self._pos = 0
        self._done = threading.Event()
        self._closed = False
        self._stream = self._sd.OutputStream(
            samplerate=rate,
            channels=self._data.shape[1],
            dtype="int16",
            callback=self._callback,
            finished_callback=self._done.set,
        )
        self._stream.start()

    def _callback(self, outdata, frames, time_info, status):
        chunk = self._data[self._pos:self._pos + frames]
        count = len(chunk)
        outdata[:count] = chunk
        self._pos += count
        if count < frames:
            outdata[count:] = 0
            raise self._sd.CallbackStop  # acabou: o stream termina e avisa

    def poll(self):
        return 0 if self._done.is_set() else None

    def terminate(self):
        if not self._done.is_set():
            try:
                self._stream.abort()  # para na hora (interrupção)
            finally:
                self._done.set()

    kill = terminate

    def wait(self, timeout=None):
        if not self._done.wait(timeout):
            raise subprocess.TimeoutExpired("sounddevice", timeout)
        if not self._closed:
            self._closed = True
            self._stream.close()
        return 0


def expected_delay_ms(path):
    return SOUNDDEVICE_DELAY_MS if path.lower().endswith(".wav") else FFPLAY_DELAY_MS


def open_player(path):
    """(player, atraso em ms). WAV pela placa de som; o resto, ou erro, pelo ffplay."""
    if path.lower().endswith(".wav"):
        try:
            samples, rate = read_wav(path)
            return SoundPlayer(samples, rate), SOUNDDEVICE_DELAY_MS
        except Exception as error:
            print(f"[AUDIO] Placa de som indisponível ({error}); usando o ffplay.")
    proc = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return proc, FFPLAY_DELAY_MS
