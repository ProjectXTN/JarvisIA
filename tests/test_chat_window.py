"""Janela de texto: escrever para o Jarvis em vez de falar."""
import json
import time
import unittest
import urllib.error
import urllib.request
from unittest import mock

import tests.test_regressao  # noqa: F401
import jarvis_commands
from brain import chat_window


def _request(url, data=None, key=None):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["X-Jarvis-Key"] = key
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers=headers, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, r.read().decode("utf-8")


class ComandoTest(unittest.TestCase):
    def test_frases_que_abrem(self):
        for phrase in ("abre o chat", "abra a janela de texto", "quero te escrever", "prefiro digitar",
                       "abre um lugar pra escrever"):
            handlers = jarvis_commands._matching_handlers(phrase, (), [jarvis_commands.chat_commands])
            self.assertTrue(list(handlers), phrase)

    def test_frases_que_nao_abrem(self):
        for phrase in ("abra o youtube", "escreva um poema", "quero comprar um teclado novo", "qual o melhor teclado mecânico",
                       "que horas são", "pare"):
            handlers = jarvis_commands._matching_handlers(phrase, (), [jarvis_commands.chat_commands])
            self.assertFalse(list(handlers), phrase)


class ServidorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = chat_window.start()
        cls.base = url.split("/?")[0]

    def test_sem_chave_recusa(self):
        for call in (lambda: _request(self.base + "/"),
                     lambda: _request(self.base + "/mensagens?desde=0"),
                     lambda: _request(self.base + "/enviar", {"texto": "abra o cmd"}),
                     lambda: _request(self.base + "/enviar", {"texto": "x"}, key="errada")):
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                call()
            self.assertEqual(ctx.exception.code, 403)

    def test_pagina_e_envio(self):
        status, html = _request(f"{self.base}/?k={chat_window.KEY}")
        self.assertEqual(status, 200)
        self.assertIn("Escrever para o", html)
        with mock.patch("jarvis_commands.process_command", return_value=True) as process:
            status, _ = _request(self.base + "/enviar", {"texto": "que horas são", "so_texto": True},
                                 key=chat_window.KEY)
            for _ in range(50):
                if process.called:
                    break
                time.sleep(0.02)
        self.assertEqual(status, 200)
        process.assert_called_once_with("que horas são")

    def test_texto_vazio(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            _request(self.base + "/enviar", {"texto": "  "}, key=chat_window.KEY)
        self.assertEqual(ctx.exception.code, 400)

    def test_conversa_aparece_na_janela(self):
        before = len(chat_window.messages_since(0))
        chat_window.publish("pedro", "oi")
        chat_window.publish("jarvis", "Olá, Pedro.")
        _, body = _request(f"{self.base}/mensagens?desde={before}", key=chat_window.KEY)
        msgs = json.loads(body)["mensagens"]
        self.assertEqual([(m["quem"], m["texto"]) for m in msgs[-2:]], [("pedro", "oi"), ("jarvis", "Olá, Pedro.")])


if __name__ == "__main__":
    unittest.main()
