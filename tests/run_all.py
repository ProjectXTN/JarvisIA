"""Roda os testes automáticos do Jarvis (não precisa de microfone, GPU nem Ollama).

Uso: venv\\Scripts\\python.exe tests\\run_all.py
"""
import importlib
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SUITES = [
    "tests.test_regressao", "tests.test_tool_router", "tests.test_ferramentas",
    "tests.test_speech_stream", "tests.test_player", "tests.test_microphone",
    "tests.test_media_window", "tests.test_browser_choice", "tests.test_tts_engine",
    "tests.test_fase2", "tests.test_playback", "tests.test_news",
    "tests.test_semantic_memory", "tests.test_server", "tests.test_image_gen",
    "tests.test_log", "tests.test_persona", "tests.test_autonomia", "tests.test_iniciativa", "tests.test_chat_window", "tests.test_whisper_loader",
]

if __name__ == "__main__":
    os.chdir(ROOT)
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for name in SUITES:
        try:
            suite.addTests(loader.loadTestsFromModule(importlib.import_module(name)))
        except Exception as error:  # biblioteca faltando neste PC, por exemplo
            print(f"⚠️ {name} não carregou: {error}")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
