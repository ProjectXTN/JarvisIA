"""Reproduz Whisper preso e player preso sem GPU/microfone."""
import queue
import subprocess
import threading
import time
import unittest
from unittest import mock
from brain.playback import InterruptRecognizer, monitor_playback, finish_player


class PlaybackTest(unittest.TestCase):
    def frames(self):
        frames = queue.Queue()
        for value in [True]*6 + [False]*10:
            frames.put(value)
        return frames

    def test_whisper_preso_nao_impede_fim_do_audio(self):
        started, release = threading.Event(), threading.Event()
        def slow(blocks):
            started.set()
            release.wait(2)
            return 'pare'
        recognizer = InterruptRecognizer(slow)
        proc = mock.Mock()
        count = 0
        def poll():
            nonlocal count
            count += 1
            return 0 if count > 20 else None
        proc.poll.side_effect = poll
        before = time.monotonic()
        try:
            result = monitor_playback(proc, self.frames(), bool, recognizer,
                                      lambda *_:True, 'Hoje é dia 17', 1)
            self.assertTrue(started.is_set())
            self.assertIsNone(result)
            self.assertLess(time.monotonic()-before, 0.7)
            self.assertIsNone(recognizer.submit([]))  # não acumula threads
        finally:
            release.set()

    def test_resultado_atrasado_fica_na_fila_da_fala_antiga(self):
        release = threading.Event()
        recognizer = InterruptRecognizer(lambda blocks: (release.wait(1), blocks[0])[1])
        first = recognizer.submit(['pare antigo'])
        self.assertIsNone(recognizer.submit(['novo']))
        release.set()
        self.assertEqual(first.get(timeout=1), ('pare antigo',None))
        # Sincronizar apenas no teste; a reprodução nunca espera por este lock.
        with recognizer._busy:
            pass
        second = recognizer.submit(['novo'])
        self.assertEqual(second.get(timeout=1), ('novo',None))

    def test_ordem_de_parar_e_devolvida_durante_audio(self):
        result = queue.Queue()
        result.put(('pare, que horas são', None))
        recognizer = mock.Mock()
        recognizer.submit.return_value = result
        proc = mock.Mock()
        proc.poll.return_value = None
        self.assertEqual(monitor_playback(proc,self.frames(),bool,recognizer,
            lambda *_:True,'fala',0.5), 'pare, que horas são')

    def test_sem_frames_nao_bloqueia_player_encerrado(self):
        proc = mock.Mock()
        proc.poll.side_effect = [None,0]
        before = time.monotonic()
        self.assertIsNone(monitor_playback(proc,queue.Queue(),bool,None,
            lambda *_:False,'fala',1))
        self.assertLess(time.monotonic()-before,0.5)

    def test_timeout_reproducao(self):
        proc = mock.Mock()
        proc.poll.return_value = None
        self.assertIsNone(monitor_playback(proc,queue.Queue(),bool,None,
            lambda *_:False,'fala',0))

    def test_player_preso_recebe_kill_com_wait_limitado(self):
        proc = mock.Mock()
        proc.poll.return_value = None
        proc.wait.side_effect = [subprocess.TimeoutExpired('ffplay',2),0]
        finish_player(proc)
        proc.terminate.assert_called_once()
        proc.kill.assert_called_once()
        self.assertEqual(proc.wait.call_args_list, [mock.call(timeout=2),mock.call(timeout=2)])

    def test_erro_de_transcricao_libera_worker(self):
        recognizer = InterruptRecognizer(mock.Mock(side_effect=ValueError('GPU')))
        result = recognizer.submit([]).get(timeout=1)
        self.assertIsNone(result[0])
        self.assertIsInstance(result[1],ValueError)
        with recognizer._busy:
            pass
        self.assertIsNotNone(recognizer.submit([]))

if __name__ == '__main__':
    unittest.main()
