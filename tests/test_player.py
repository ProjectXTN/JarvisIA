"""Player pela placa de som (brain/player.py), com uma placa de som simulada."""
import os
import subprocess
import tempfile
import threading
import time
import types
import unittest
import wave
from unittest import mock

import numpy as np

from brain import player
from brain.playback import finish_player, monitor_playback


class CallbackStop(Exception):
    pass


class FakeStream:
    """Chama o callback em blocos de 256 amostras, como a placa de som faria."""

    played = None

    def __init__(self, samplerate, channels, dtype, callback, finished_callback):
        self.callback, self.finished = callback, finished_callback
        self.channels, self.rate = channels, samplerate
        self.aborted = self.closed = False
        FakeStream.played = []

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while not self.aborted:
            out = np.zeros((256, self.channels), dtype=np.int16)
            try:
                self.callback(out, 256, None, None)
            except CallbackStop:
                FakeStream.played.append(out.copy())
                break
            FakeStream.played.append(out.copy())
            time.sleep(256 / self.rate)
        self.finished()

    def abort(self):
        self.aborted = True

    def close(self):
        self.closed = True


FAKE_SD = types.SimpleNamespace(OutputStream=FakeStream, CallbackStop=CallbackStop)


class SoundPlayerTest(unittest.TestCase):
    def test_toca_todas_as_amostras_na_ordem(self):
        samples = np.arange(1000, dtype=np.int16)
        proc = player.SoundPlayer(samples, 8000, sounddevice=FAKE_SD)
        self.assertEqual(proc.wait(timeout=3), 0)
        self.assertEqual(proc.poll(), 0)
        played = np.concatenate(FakeStream.played)[:, 0]
        np.testing.assert_array_equal(played[:1000], samples)
        self.assertTrue((played[1000:] == 0).all())

    def test_terminate_para_na_hora(self):
        proc = player.SoundPlayer(np.ones(80000, dtype=np.int16), 8000, sounddevice=FAKE_SD)
        time.sleep(0.05)
        started = time.monotonic()
        finish_player(proc)
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertEqual(proc.poll(), 0)
        self.assertLess(sum(len(b) for b in FakeStream.played), 80000)

    def test_wait_respeita_o_prazo(self):
        proc = player.SoundPlayer(np.ones(80000, dtype=np.int16), 8000, sounddevice=FAKE_SD)
        with self.assertRaises(subprocess.TimeoutExpired):
            proc.wait(timeout=0.05)
        finish_player(proc)

    def test_monitor_de_reproducao_funciona_com_o_player(self):
        import queue

        proc = player.SoundPlayer(np.ones(2000, dtype=np.int16), 8000, sounddevice=FAKE_SD)
        heard = monitor_playback(proc, queue.Queue(), lambda b: False, None, lambda h, s: True, "", 5)
        self.assertIsNone(heard)
        self.assertEqual(proc.poll(), 0)


class OpenPlayerTest(unittest.TestCase):
    def _wav(self):
        handle = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        handle.close()
        with wave.open(handle.name, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(24000)
            wav.writeframes(np.arange(500, dtype="<i2").tobytes())
        self.addCleanup(os.remove, handle.name)
        return handle.name

    def test_wav_le_as_amostras(self):
        samples, rate = player.read_wav(self._wav())
        self.assertEqual((samples.shape, rate), ((500, 1), 24000))

    def test_wav_vai_para_a_placa_de_som_e_mp3_para_o_ffplay(self):
        with mock.patch.object(player, "SoundPlayer") as sound, \
             mock.patch.object(player.subprocess, "Popen") as popen:
            self.assertIs(player.open_player(self._wav())[0], sound.return_value)
            popen.assert_not_called()
            player.open_player("fala.mp3")
            self.assertEqual(popen.call_args.args[0][0], "ffplay")

    def test_placa_de_som_com_erro_volta_para_o_ffplay(self):
        with mock.patch.object(player, "SoundPlayer", side_effect=OSError("sem dispositivo")), \
             mock.patch.object(player.subprocess, "Popen") as popen:
            proc, delay = player.open_player(self._wav())
        self.assertIs(proc, popen.return_value)
        self.assertEqual(delay, player.FFPLAY_DELAY_MS)


if __name__ == "__main__":
    unittest.main()
