"""Som de live/vídeo no PC não pode virar comando nem desligar o Jarvis."""
import unittest
from datetime import datetime, timedelta
from unittest import mock

import tests.test_regressao  # noqa: F401

from brain import followup  # noqa: E402
from brain import system_audio  # noqa: E402

NOW = datetime(2026, 11, 24, 9, 37, 0)


class FollowupTest(unittest.TestCase):
    def setUp(self):
        from core import config

        config.LAST_SPEECH_END = None

    def accept(self, text, seconds_ago, playing=False):
        with mock.patch.object(system_audio, "other_audio_playing", return_value=playing):
            return followup.accept_followup(text, NOW - timedelta(seconds=seconds_ago), now=NOW)

    def test_logo_depois_da_resposta_aceita_sem_jarvis(self):
        self.assertEqual(self.accept("E amanhã, vai chover?", 5), "e amanhã vai chover")

    def test_fora_da_janela_ignora(self):
        self.assertIsNone(self.accept("Obrigado, Lexy, Adriano.", 40))

    def test_com_som_tocando_exige_jarvis(self):
        self.assertIsNone(self.accept("E você, como eu faço, eu sei.", 3, playing="chrome.exe"))
        self.assertEqual(self.accept("Jarvis, que horas são?", 3, playing="chrome.exe"), "que horas são")

    def test_tchau_da_live_nao_desliga(self):
        self.assertIsNone(self.accept("Tchau.", 3))
        self.assertIsNone(self.accept("Tchau.", 60, playing="chrome.exe"))
        self.assertEqual(self.accept("Tchau, Jarvis.", 60, playing="chrome.exe"), "tchau")  # com Jarvis vale

    def test_depois_de_um_aviso_em_segundo_plano_responde_sem_jarvis(self):
        from core import config

        with mock.patch.object(config, "LAST_SPEECH_END", NOW - timedelta(seconds=5)):
            self.assertEqual(self.accept("Abre o aplicativo que você criou.", 300), "abre o aplicativo que você criou")

    def test_jarvis_no_meio_da_frase(self):
        self.assertEqual(self.accept("Ok Jarvis, abre o chat", 90), "ok abre o chat")


if __name__ == "__main__":
    unittest.main()
