"""Escolha do motor de voz (brain/tts.py): Kokoro local com o Google de reserva."""
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

import numpy as np

from brain import tts


class FakeKokoro:
    def __init__(self, model, voices):
        self.calls = []

    def create(self, text, voice, speed, lang):
        self.calls.append((text, voice, speed, lang))
        return np.zeros(2400, dtype=np.float32), 24000


class TtsEngineTest(unittest.TestCase):
    def setUp(self):
        self.engine = tts._Kokoro()
        self.files = tempfile.TemporaryDirectory()
        self.addCleanup(self.files.cleanup)
        self.model = os.path.join(self.files.name, "kokoro.onnx")
        self.voices = os.path.join(self.files.name, "voices.bin")
        patches = [
            mock.patch.object(tts, "kokoro", self.engine),
            mock.patch.object(tts, "KOKORO_MODEL", self.model),
            mock.patch.object(tts, "KOKORO_VOICES", self.voices),
            mock.patch.object(tts, "google_synthesize", return_value="google.mp3"),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def _install_model(self):
        for path in (self.model, self.voices):
            open(path, "wb").close()
        module = types.SimpleNamespace(Kokoro=FakeKokoro)
        patch = mock.patch.dict(sys.modules, {"kokoro_onnx": module})
        patch.start()
        self.addCleanup(patch.stop)

    def test_kokoro_gera_wav_com_a_voz_configurada(self):
        self._install_model()
        with mock.patch.object(tts, "TTS_ENGINE", "kokoro"):
            path = tts.synthesize("Olá Pedro.")
        self.addCleanup(os.remove, path)
        self.assertTrue(path.endswith(".wav"))
        text, voice, speed, lang = self.engine.model.calls[0]
        self.assertEqual((text, voice, lang), ("Olá Pedro.", tts.KOKORO_VOICE, "pt-br"))
        tts.google_synthesize.assert_not_called()

    def test_sem_modelo_baixado_usa_o_google(self):
        with mock.patch.object(tts, "TTS_ENGINE", "kokoro"):
            self.assertEqual(tts.synthesize("Olá."), "google.mp3")
        self.assertIn("prepare_kokoro", self.engine.failed)
        # não tenta carregar de novo a cada frase
        with mock.patch.object(tts, "TTS_ENGINE", "kokoro"):
            self.assertEqual(tts.synthesize("De novo."), "google.mp3")

    def test_falha_numa_frase_usa_o_google_so_nela(self):
        self._install_model()
        with mock.patch.object(tts, "TTS_ENGINE", "kokoro"):
            self.assertTrue(self.engine.load())
            with mock.patch.object(self.engine.model, "create", side_effect=RuntimeError("fonema")):
                self.assertEqual(tts.synthesize("Frase difícil."), "google.mp3")
            path = tts.synthesize("Frase normal.")
        self.addCleanup(os.remove, path)
        self.assertTrue(path.endswith(".wav"))

    def test_google_escolhido_no_env_nao_carrega_o_kokoro(self):
        with mock.patch.object(tts, "TTS_ENGINE", "google"), \
             mock.patch.object(self.engine, "load", side_effect=AssertionError("carregou o Kokoro")):
            self.assertEqual(tts.synthesize("Olá."), "google.mp3")


if __name__ == "__main__":
    unittest.main()
