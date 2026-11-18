"""Microfone aberto o tempo todo, compartilhado pela escuta e pela interrupção.

Antes, cada escuta e cada fala do Jarvis abriam e fechavam o microfone. No
intervalo o começo da sua fala podia se perder (o "Jar-" de "Jarvis" logo
depois de ele terminar de falar), e abrir o dispositivo custava tempo.

Agora um único stream fica aberto e entrega blocos de 30 ms a quem estiver
inscrito: listen() durante a escuta e o monitor de interrupção durante a fala.
Se o dispositivo parar de mandar áudio (desconectado, por exemplo), o stream é
reaberto na próxima leitura.
"""

import queue
import threading
import time

RATE = 16000
BLOCK = 480  # 30 ms a 16 kHz, o tamanho que o webrtcvad aceita


class Microphone:
    def __init__(self, rate=RATE, block=BLOCK, sounddevice=None):
        if sounddevice is None:
            import sounddevice
        self._sd = sounddevice
        self.rate, self.block = rate, block
        self._lock = threading.Lock()
        self._subscribers = set()
        self._stream = None
        self._last_block = 0.0

    def _callback(self, indata, frames, time_info, status):
        block = indata.copy()
        self._last_block = time.monotonic()
        with self._lock:
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            try:
                subscriber.put_nowait(block)
            except queue.Full:
                pass  # quem não está lendo perde blocos; o microfone não para

    def _open(self):
        stream = self._sd.InputStream(
            samplerate=self.rate, channels=1, dtype="int16",
            blocksize=self.block, callback=self._callback,
        )
        stream.start()
        self._stream = stream
        self._last_block = time.monotonic()

    def start(self):
        with self._lock:
            if self._stream is None:
                self._open()

    def restart(self):
        """Reabre o dispositivo (usado quando ele para de mandar áudio)."""
        with self._lock:
            old, self._stream = self._stream, None
        if old is not None:
            for action in (old.abort, old.close):
                try:
                    action()
                except Exception:
                    pass
        print("[MIC] Reabrindo o microfone.")
        self.start()

    def subscribe(self, maxsize=400):
        """Fila que passa a receber os blocos de agora em diante."""
        self.start()
        subscriber = queue.Queue(maxsize=maxsize)
        with self._lock:
            self._subscribers.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber):
        with self._lock:
            self._subscribers.discard(subscriber)

    def read(self, subscriber, stall_after=2.0):
        """Próximo bloco da fila. Reabre o microfone se ele parar de mandar áudio."""
        while True:
            try:
                return subscriber.get(timeout=0.5)
            except queue.Empty:
                if time.monotonic() - self._last_block > stall_after:
                    self.restart()

    def close(self):
        with self._lock:
            stream, self._stream = self._stream, None
            self._subscribers.clear()
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass


_shared = None
_shared_lock = threading.Lock()


def get_microphone():
    """O microfone do Jarvis (um só para o processo inteiro)."""
    global _shared
    with _shared_lock:
        if _shared is None:
            _shared = Microphone()
        return _shared
