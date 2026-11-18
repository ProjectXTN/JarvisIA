"""Teste manual: carrega o modelo principal do Jarvis no Ollama e faz uma pergunta."""
import subprocess

from core.settings import DEFAULT_MODEL

subprocess.run(["ollama", "run", DEFAULT_MODEL, "Responda só: ok"])
