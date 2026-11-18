"""Fase 6: segurança da API (sem precisar do Flask)."""
import threading
import unittest

import tests.test_regressao  # noqa: F401 (bibliotecas falsas quando faltam)
import server
from core import config


class TokenTest(unittest.TestCase):
    def test_token(self):
        token = "a" * 32
        self.assertTrue(server.token_ok(f"Bearer {token}", token))
        self.assertFalse(server.token_ok("Bearer errado", token))
        self.assertFalse(server.token_ok(token, token))
        self.assertFalse(server.token_ok(None, token))

    def test_sem_token_configurado_nunca_aceita(self):
        # antes: sem token no .env, "Bearer None" passava
        self.assertFalse(server.token_ok("Bearer None", None))
        self.assertFalse(server.token_ok("Bearer ", ""))


class QuestionTest(unittest.TestCase):
    def test_valida(self):
        self.assertEqual(server.parse_question({"question": " Oi "}), ("Oi", "pt"))
        self.assertEqual(server.parse_question({"question": "Hi", "lang": "en"}), ("Hi", "en"))
        for bad in (None, [], {}, {"question": 3}, {"question": "  "},
                    {"question": "x" * 2001}, {"question": "oi", "lang": "xx"}):
            with self.assertRaises(server.BadRequest):
                server.parse_question(bad)

    def test_origens(self):
        self.assertEqual(server.allowed_origins(None), [])
        self.assertEqual(server.allowed_origins("http://a, http://b"), ["http://a", "http://b"])


class ApiStateTest(unittest.TestCase):
    def test_modo_api_vale_so_na_thread_do_pedido(self):
        seen = {}
        inside = threading.Event()
        release = threading.Event()

        def api():
            with config.api_request():
                seen["api"] = config.IS_API_REQUEST
                inside.set()
                release.wait(2)

        t = threading.Thread(target=api)
        t.start()
        inside.wait(2)
        seen["voz"] = config.IS_API_REQUEST  # voz continua falando
        release.set()
        t.join()
        self.assertEqual(seen, {"api": True, "voz": False})
        self.assertFalse(config.IS_API_REQUEST)


if __name__ == "__main__":
    unittest.main()
