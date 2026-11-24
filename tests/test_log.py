"""Fase 6, item 45: registro com níveis e medição de tempo."""
import io
import logging
import os
import tempfile
import unittest
import unittest.mock

import tests.test_regressao  # noqa: F401
from core import log


class LevelTest(unittest.TestCase):
    def test_niveis(self):
        self.assertEqual(log.level_of("[DEBUG] Phrase after cleaning: oi"), logging.DEBUG)
        self.assertEqual(log.level_of("[IMAGEM] Falhou: x"), logging.ERROR)
        self.assertEqual(log.level_of("[MEMÓRIA] Embeddings indisponíveis"), logging.WARNING)
        self.assertEqual(log.level_of("⚠️ waitress não instalado"), logging.WARNING)
        self.assertEqual(log.level_of("[LLM] Primeiras palavras em 0.2s."), logging.INFO)


class TeeTest(unittest.TestCase):
    def test_janela_esconde_debug_mas_log_guarda(self):
        records = []

        class H(logging.Handler):
            def emit(self, record):
                records.append((record.levelno, record.getMessage()))

        handler = H()
        log.logger.addHandler(handler)
        log.logger.setLevel(logging.DEBUG)
        try:
            screen = io.StringIO()
            tee = log._Tee(screen, logging.INFO)
            print("[DEBUG] detalhe", file=tee)
            print("[LLM] resposta", end="", file=tee)
            tee.write(" pronta\n")
        finally:
            log.logger.removeHandler(handler)
        self.assertEqual(screen.getvalue(), "[LLM] resposta pronta\n")
        self.assertEqual(records, [(logging.DEBUG, "[DEBUG] detalhe"), (logging.INFO, "[LLM] resposta pronta")])


class TimeTest(unittest.TestCase):
    def test_grava_csv(self):
        folder = tempfile.mkdtemp()
        log.record_time("pedido", 1.234, "que horas são", log_dir=folder)
        log.record_time("imagem", 20, "lobo", log_dir=folder)
        with open(os.path.join(folder, "tempos.csv"), encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertEqual(lines[0], "data;etapa;segundos;detalhe")
        self.assertTrue(lines[1].endswith(";pedido;1.23;que horas são"))
        self.assertEqual(len(lines), 3)

    def test_sem_setup_nao_suja_os_logs(self):
        with unittest.mock.patch.object(log, "open", create=True) as opened:
            log.record_time("pedido", 1)
        opened.assert_not_called()


if __name__ == "__main__":
    unittest.main()
