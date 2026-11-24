"""Registro do Jarvis (Fase 6, item 45).

O código usa print() com etiquetas ([LLM], [AUDIO], [MEMÓRIA]...). Em vez de
trocar centenas de prints, a saída passa por aqui:
  - tudo vai para logs/jarvis.log, com data, hora e nível, em arquivos que
    giram ao passar de 5 MB (guarda 5);
  - o nível de cada linha sai do conteúdo: [DEBUG] → DEBUG; erro/falhou →
    ERROR; aviso/indisponível → WARNING; o resto → INFO;
  - JARVIS_CONSOLE_LEVEL=INFO esconde as linhas [DEBUG] na janela (padrão:
    mostra tudo, como antes); o arquivo sempre guarda tudo;
  - etapa("nome") mede quanto cada parte levou e grava em logs/tempos.csv,
    para ver onde o Jarvis perde tempo.
"""

import csv
import logging
import os
import re
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from logging.handlers import RotatingFileHandler

from core.settings import BASE_DIR

LOG_DIR = os.path.join(BASE_DIR, "logs")
logger = logging.getLogger("jarvis")

_ERROR = re.compile(r"(\[ERRO|\berro\b|\berror\b|falhou|traceback|exception|🔥|❌)", re.I)
_WARNING = re.compile(r"(⚠️|\baviso\b|indispon[ií]ve|n[ãa]o consegui|timed out|warning)", re.I)
_LEVELS = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR}


def level_of(line):
    if "[DEBUG]" in line:
        return logging.DEBUG
    if _ERROR.search(line):
        return logging.ERROR
    if _WARNING.search(line):
        return logging.WARNING
    return logging.INFO


class _Tee:
    """Substitui sys.stdout/sys.stderr: mostra na janela e manda cada linha ao log."""

    def __init__(self, stream, console_level, default_level=None):
        self.stream = stream
        self.console_level = console_level
        self.default_level = default_level
        self._buffer = ""
        self._lock = threading.Lock()

    def write(self, text):
        with self._lock:
            self._buffer += text
            *lines, self._buffer = self._buffer.split("\n")
        for line in lines:
            self._emit(line)
        return len(text)

    def _emit(self, line):
        level = self.default_level or level_of(line)
        if line.strip():
            logger.log(level, line.rstrip())
        if level >= self.console_level or not line.strip():
            try:
                self.stream.write(line + "\n")
                self.stream.flush()
            except Exception:
                pass

    def flush(self):
        with self._lock:
            rest, self._buffer = self._buffer, ""
        if rest:
            self._emit(rest)
        try:
            self.stream.flush()
        except Exception:
            pass

    def __getattr__(self, name):  # isatty, encoding, fileno...
        return getattr(self.stream, name)


def setup(console_level=None, log_dir=LOG_DIR):
    """Liga o registro. Chame uma vez, no começo do jarvis.py ou do server.py."""
    if getattr(setup, "done", False):
        return
    setup.done = True
    os.makedirs(log_dir, exist_ok=True)
    handler = RotatingFileHandler(os.path.join(log_dir, "jarvis.log"), maxBytes=5_000_000,
                                  backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    name = (console_level or os.getenv("JARVIS_CONSOLE_LEVEL", "DEBUG")).upper()
    console = _LEVELS.get(name, logging.DEBUG)
    sys.stdout = _Tee(sys.stdout, console)
    # stderr (avisos de bibliotecas, tracebacks) aparece sempre
    sys.stderr = _Tee(sys.stderr, logging.DEBUG, default_level=logging.WARNING)
    logger.info("===== Jarvis iniciado =====")


# ----------------------------------------------------------------- tempos
_csv_lock = threading.Lock()


def record_time(stage, seconds, detail="", log_dir=LOG_DIR):
    if not getattr(setup, "done", False) and log_dir == LOG_DIR:
        return  # testes e scripts soltos não sujam logs/tempos.csv
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, "tempos.csv")
    with _csv_lock:
        new = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            if new:
                writer.writerow(["data", "etapa", "segundos", "detalhe"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), stage,
                             f"{seconds:.2f}", detail[:120]])


@contextmanager
def etapa(stage, detail="", show=True):
    """Mede um bloco: with etapa("pedido", texto): ..."""
    started = time.monotonic()
    try:
        yield
    finally:
        elapsed = time.monotonic() - started
        try:
            record_time(stage, elapsed, detail)
        except OSError:
            pass
        if show:
            print(f"[TEMPO] {stage}: {elapsed:.1f}s")
