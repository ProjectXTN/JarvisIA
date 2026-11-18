"""Avatar holográfico do Jarvis.

Abre uma janela com um rosto 3D que acompanha o estado do Jarvis (ouvindo,
processando, falando) e mexe a boca no volume real da voz.

Funciona assim: um servidor HTTP local entrega a página (static/index.html) e
envia eventos para ela por /events. Nada aqui pode derrubar o Jarvis: se o
avatar não estiver aberto, as funções simplesmente não fazem nada.
"""

import atexit
import functools
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from core.settings import AVATAR_AUDIO_DELAY_MS, AVATAR_PORT

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
FRAME_MS = 40  # intervalo entre medidas de volume enviadas à página

_lock = threading.Lock()
_clients = set()  # uma fila por janela aberta
_server = None
_url = None
_last_mode = "idle"
_last_alive = 0.0  # último sinal de vida enviado pela página


def _safe(func):
    """O avatar é enfeite: qualquer erro vira aviso no console e a vida segue."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[AVATAR] {func.__name__} falhou: {e}")
            return None

    return wrapper


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(os.path.join(STATIC_DIR, "index.html"), "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        elif path == "/events":
            self._events()
        elif path == "/alive":
            _mark_alive()
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404)

    def _events(self):
        events = queue.Queue(maxsize=100)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with _lock:
            _clients.add(events)
        _mark_alive()
        try:
            self._write({"type": "state", "mode": _last_mode})
            while True:
                try:
                    self._write(events.get(timeout=10))
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")  # detecta janela fechada
                    self.wfile.flush()
        except OSError:
            pass
        finally:
            with _lock:
                _clients.discard(events)

    def _write(self, message):
        self.wfile.write(f"data: {json.dumps(message)}\n\n".encode("utf-8"))
        self.wfile.flush()


def _broadcast(message):
    with _lock:
        targets = list(_clients)
    for events in targets:
        try:
            events.put_nowait(message)
        except queue.Full:
            pass


def _mark_alive():
    global _last_alive
    _last_alive = time.time()


def is_open():
    """True se há uma janela do avatar conectada e dando sinal de vida.

    A página chama /alive a cada 1,5 s; sem isso, uma janela fechada pelo
    usuário continuaria contando como aberta por vários segundos.
    """
    with _lock:
        connected = bool(_clients)
    return connected and time.time() - _last_alive < 4.0


@_safe
def start():
    """Sobe o servidor local (uma vez) e devolve o endereço da página."""
    global _server, _url
    if _server is not None:
        return _url
    for port in range(AVATAR_PORT, AVATAR_PORT + 10):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
        except OSError:
            continue
        server.daemon_threads = True
        threading.Thread(target=server.serve_forever, daemon=True).start()
        _server, _url = server, f"http://127.0.0.1:{port}/"
        atexit.register(_goodbye)
        return _url
    raise RuntimeError(f"nenhuma porta livre a partir de {AVATAR_PORT}")


def _browser_for_app_window():
    """Edge ou Chrome, para abrir a página como janela própria, sem abas."""
    candidates = [shutil.which("msedge"), shutil.which("chrome"), shutil.which("google-chrome")]
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LocalAppData")):
        if base:
            candidates.append(os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"))
            candidates.append(os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"))
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


@_safe
def show(wait=4.0):
    """Mostra o avatar. Devolve True quando a janela está conectada."""
    url = start()
    if not url:
        return False
    if is_open():
        _broadcast({"type": "show"})
        return True

    browser = _browser_for_app_window()
    if browser:
        subprocess.Popen(
            [browser, f"--app={url}", "--window-size=520,820"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        webbrowser.open(url, new=1)

    deadline = time.time() + wait
    while time.time() < deadline:
        if is_open():
            return True
        time.sleep(0.1)
    return is_open()


@_safe
def hide():
    """Fecha a janela do avatar (ou a escurece, se o navegador não deixar fechar)."""
    global _last_alive
    _broadcast({"type": "hide"})
    # Se a janela fechar de fato, os sinais de vida param e o próximo show()
    # abre outra. Se só escureceu, ela volta a dar sinal e é reaproveitada.
    _last_alive = 0.0
    return True


def _goodbye():
    with _lock:
        connected = bool(_clients)
    if connected:
        _broadcast({"type": "hide"})
        time.sleep(0.4)  # tempo para a mensagem sair antes de o processo morrer


@_safe
def set_state(mode):
    """mode: 'idle', 'listening', 'thinking' ou 'speaking'."""
    global _last_mode
    _last_mode = mode
    if is_open():
        _broadcast({"type": "state", "mode": mode})


def _volume_envelope(audio_path):
    """Volume da fala a cada FRAME_MS, de 0 a 1, ou None se não der para medir."""
    import numpy as np

    if audio_path.lower().endswith(".wav"):
        # WAV do Kokoro: lido direto, sem precisar do ffmpeg
        from brain.player import read_wav

        data, wav_rate = read_wav(audio_path)
        return _envelope_from_samples(data[:, 0].astype(np.float32), wav_rate)

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None

    rate = 8000
    raw = subprocess.run(
        [ffmpeg, "-v", "quiet", "-i", audio_path, "-f", "s16le", "-ac", "1", "-ar", str(rate), "-"],
        capture_output=True,
        timeout=8,
    ).stdout
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    return _envelope_from_samples(samples, rate)


def _envelope_from_samples(samples, rate):
    """Volume (0 a 1) a cada FRAME_MS a partir das amostras de áudio."""
    import numpy as np

    step = int(rate) * FRAME_MS // 1000
    count = len(samples) // step
    if count < 2:
        return None
    rms = np.sqrt((samples[: count * step].reshape(count, step) ** 2).mean(axis=1))
    peak = float(np.percentile(rms, 92)) or 1.0
    level = np.clip(rms / peak, 0, 1)
    level = np.clip((level - 0.08) / 0.92, 0, 1) ** 0.75  # corta o chiado, realça fala baixa
    return [round(float(v), 2) for v in level]


@_safe
def speak_start(audio_path, text="", delay_ms=None):
    """Avise logo antes de tocar o áudio; a boca segue o volume do arquivo.

    delay_ms: quanto o som demora para sair depois do aviso (depende do player).
    """
    global _last_mode
    _last_mode = "speaking"
    if not is_open():
        return
    try:
        envelope = _volume_envelope(audio_path)
    except Exception as e:
        print(f"[AVATAR] Sem medida de volume, usando movimento genérico: {e}")
        envelope = None
    _broadcast(
        {
            "type": "speak",
            "envelope": envelope,
            "frame_ms": FRAME_MS,
            "delay_ms": AVATAR_AUDIO_DELAY_MS if delay_ms is None else delay_ms,
            "text": text,
        }
    )


@_safe
def speak_stop():
    global _last_mode
    _last_mode = "idle"
    if is_open():
        _broadcast({"type": "stop", "mode": "idle"})
