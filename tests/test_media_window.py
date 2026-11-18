"""Janela de mídia (brain/media_window.py): um vídeo por vez, na mesma janela."""
import unittest
from unittest import mock

import tests.test_regressao  # noqa: F401  (dublês de bibliotecas)
from brain import media_window as mw


def reply(json_data=None, status=200, ok=True):
    response = mock.Mock(status_code=status, ok=ok)
    response.json.return_value = json_data
    return response


class MediaWindowTest(unittest.TestCase):
    def test_primeiro_pedido_abre_a_janela_propria(self):
        with mock.patch.object(mw, "_alive", return_value=False), \
             mock.patch.object(mw, "_find_browser", return_value="msedge.exe"), \
             mock.patch.object(mw.os, "makedirs"), \
             mock.patch.object(mw.subprocess, "Popen") as popen:
            self.assertEqual(mw.open_media("https://www.youtube.com/watch?v=A"), "nova janela")
        args = popen.call_args.args[0]
        self.assertEqual(args[0], "msedge.exe")
        self.assertIn(f"--remote-debugging-port={mw.MEDIA_BROWSER_PORT}", args)
        self.assertTrue(any(a.startswith("--user-data-dir=") for a in args))
        self.assertEqual(args[-1], "https://www.youtube.com/watch?v=A")

    def test_pedido_seguinte_substitui_o_video(self):
        calls = []

        def fake_get(url, timeout=0):
            calls.append(url)
            if url.endswith("/json/list"):
                return reply([{"id": "velha", "type": "page"}, {"id": "w", "type": "service_worker"}])
            return reply({})

        with mock.patch.object(mw, "_alive", return_value=True), \
             mock.patch.object(mw.requests, "get", side_effect=fake_get), \
             mock.patch.object(mw.requests, "put", return_value=reply({"id": "nova"})) as put:
            self.assertEqual(mw.open_media("https://www.youtube.com/watch?v=B"), "substituído")
        self.assertTrue(put.call_args.args[0].endswith("/json/new?https://www.youtube.com/watch?v=B"))
        self.assertTrue(any(c.endswith("/json/close/velha") for c in calls))
        self.assertFalse(any(c.endswith("/json/close/w") for c in calls))  # só páginas
        self.assertTrue(any(c.endswith("/json/activate/nova") for c in calls))

    def test_sem_navegador_compativel_usa_o_padrao(self):
        with mock.patch.object(mw, "_alive", return_value=False), \
             mock.patch.object(mw, "_find_browser", return_value=None), \
             mock.patch.object(mw.webbrowser, "open") as browser:
            self.assertEqual(mw.open_media("https://x.com"), "navegador padrão")
        browser.assert_called_once()

    def test_falha_no_controle_usa_o_padrao(self):
        with mock.patch.object(mw, "_alive", return_value=True), \
             mock.patch.object(mw.requests, "get", side_effect=OSError("porta fechada")), \
             mock.patch.object(mw.webbrowser, "open") as browser:
            self.assertEqual(mw.open_media("https://x.com"), "navegador padrão")
        browser.assert_called_once()


if __name__ == "__main__":
    unittest.main()
