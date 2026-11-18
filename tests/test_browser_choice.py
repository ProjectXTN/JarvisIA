"""Escolha do navegador das janelas do Jarvis: Chrome primeiro, Edge se não houver Chrome."""
import os
import unittest
from unittest import mock

import tests.test_regressao  # noqa: F401
from brain import avatar


class BrowserChoiceTest(unittest.TestCase):
    def _choose(self, installed):
        env = {"ProgramFiles": "C:/PF", "ProgramFiles(x86)": "C:/PF86", "LocalAppData": "C:/LAD"}
        with mock.patch.dict(os.environ, env), \
             mock.patch.object(avatar.shutil, "which", return_value=None), \
             mock.patch.object(avatar.os.path, "isfile", side_effect=lambda p: p.replace("\\", "/") in installed):
            return avatar._browser_for_app_window()

    def test_chrome_tem_preferencia(self):
        chosen = self._choose({"C:/PF86/Microsoft/Edge/Application/msedge.exe",
                               "C:/PF/Google/Chrome/Application/chrome.exe"})
        self.assertIn("chrome.exe", chosen)

    def test_edge_so_sem_chrome(self):
        self.assertIn("msedge.exe", self._choose({"C:/PF86/Microsoft/Edge/Application/msedge.exe"}))

    def test_nenhum(self):
        self.assertIsNone(self._choose(set()))


if __name__ == "__main__":
    unittest.main()
