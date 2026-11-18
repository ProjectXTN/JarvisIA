"""Microfone compartilhado (brain/microphone.py), com um dispositivo simulado."""
import queue
import threading
import time
import types
import unittest

import numpy as np

from brain.microphone import Microphone


class FakeInputStream:
    opened = 0

    def __init__(self, samplerate, channels, dtype, blocksize, callback):
        self.callback, self.blocksize = callback, blocksize
        self.running = False
        self.counter = 0
        FakeInputStream.opened += 1

    def start(self):
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while self.running:
            block = np.full((self.blocksize, 1), self.counter % 1000, dtype=np.int16)
            self.counter += 1
            self.callback(block, self.blocksize, None, None)
            time.sleep(0.003)

    def abort(self):
        self.running = False

    def close(self):
        self.running = False


class StalledStream(FakeInputStream):
    def _run(self):
        pass  # dispositivo que nunca manda áudio


def fake_sd(stream_class=FakeInputStream):
    return types.SimpleNamespace(InputStream=stream_class)


class MicrophoneTest(unittest.TestCase):
    def test_abre_uma_vez_para_varias_escutas(self):
        FakeInputStream.opened = 0
        mic = Microphone(sounddevice=fake_sd())
        self.addCleanup(mic.close)
        for _ in range(3):
            q = mic.subscribe()
            mic.read(q)
            mic.unsubscribe(q)
        self.assertEqual(FakeInputStream.opened, 1)

    def test_escuta_e_interrupcao_recebem_os_mesmos_blocos(self):
        mic = Microphone(sounddevice=fake_sd())
        self.addCleanup(mic.close)
        a, b = mic.subscribe(), mic.subscribe()
        time.sleep(0.05)
        mic.unsubscribe(a)
        mic.unsubscribe(b)
        first_a = [a.get_nowait()[0, 0] for _ in range(3)]
        first_b = [b.get_nowait()[0, 0] for _ in range(3)]
        self.assertEqual(first_a, first_b)

    def test_quem_saiu_nao_recebe_mais(self):
        mic = Microphone(sounddevice=fake_sd())
        self.addCleanup(mic.close)
        q = mic.subscribe()
        mic.unsubscribe(q)
        while not q.empty():
            q.get_nowait()
        time.sleep(0.03)
        self.assertTrue(q.empty())

    def test_fila_cheia_nao_trava_o_microfone(self):
        mic = Microphone(sounddevice=fake_sd())
        self.addCleanup(mic.close)
        slow = mic.subscribe(maxsize=2)
        fast = mic.subscribe()
        time.sleep(0.05)
        self.assertEqual(slow.qsize(), 2)
        self.assertGreater(fast.qsize(), 5)

    def test_dispositivo_parado_e_reaberto(self):
        FakeInputStream.opened = 0
        sd = fake_sd(StalledStream)
        mic = Microphone(sounddevice=sd)
        self.addCleanup(mic.close)
        q = mic.subscribe()
        sd.InputStream = FakeInputStream  # o "novo" dispositivo funciona
        block = mic.read(q, stall_after=0.2)
        self.assertEqual(block.shape, (480, 1))
        self.assertGreaterEqual(FakeInputStream.opened, 2)


if __name__ == "__main__":
    unittest.main()
