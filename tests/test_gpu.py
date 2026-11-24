"""Placa de vídeo livre para jogos: modo jogo, desligar e ComfyUI ocioso."""
import unittest
from unittest import mock

import tests.test_regressao  # noqa: F401
import jarvis_commands
from brain import image_gen
from core import config, gpu


class Resp:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class GpuTest(unittest.TestCase):
    def tearDown(self):
        config.GAME_MODE = False

    def test_descarrega_todos_os_modelos(self):
        posts = []
        with mock.patch.object(gpu.requests, "get", return_value=Resp({"models": [
                {"name": "gemma4:26b"}, {"name": "qwen3-embedding:0.6b"}]})), \
             mock.patch.object(gpu.requests, "post", side_effect=lambda url, json, **k: posts.append(json)):
            self.assertEqual(gpu.unload_ollama(), ["gemma4:26b", "qwen3-embedding:0.6b"])
        self.assertEqual(posts, [{"model": "gemma4:26b", "keep_alive": 0},
                                 {"model": "qwen3-embedding:0.6b", "keep_alive": 0}])

    def test_ollama_fora_nao_quebra(self):
        with mock.patch.object(gpu.requests, "get", side_effect=gpu.requests.RequestException("off")):
            self.assertEqual(gpu.unload_ollama(), [])

    def test_frases_do_modo_jogo(self):
        def first(phrase):
            funcs = list(jarvis_commands._matching_handlers(phrase, (), [jarvis_commands.game_commands]))
            return funcs[0].__name__ if funcs else None

        self.assertEqual(first("modo jogo"), "game_mode_on")
        self.assertEqual(first("vou jogar aion agora"), "game_mode_on")
        self.assertEqual(first("sair do modo jogo"), "game_mode_off")
        self.assertEqual(first("terminei de jogar"), "game_mode_off")
        self.assertIsNone(first("qual o melhor jogo de 2026"))

    def test_modo_jogo_libera_e_pausa(self):
        with mock.patch.object(gpu, "release") as release:
            gpu.game_mode(True)
        release.assert_called_once()
        self.assertTrue(config.GAME_MODE)

    def test_comfy_so_fecha_se_foi_o_jarvis_que_abriu(self):
        image_gen._comfy["process"] = None
        self.assertFalse(image_gen.stop_comfy())
        process = mock.Mock()
        process.poll.return_value = None
        image_gen._comfy["process"] = process
        self.assertTrue(image_gen.stop_comfy())
        process.terminate.assert_called_once()
        self.assertIsNone(image_gen._comfy["process"])


if __name__ == "__main__":
    unittest.main()
