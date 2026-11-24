"""Janela de texto: escrever para o Jarvis em vez de falar.

"Jarvis, abre o chat" abre uma janela própria (Chrome em modo app) em
http://127.0.0.1:8766. O que você escreve passa pelo mesmo caminho da voz
(process_command); a janela mostra a conversa inteira, inclusive o que foi
falado por voz. Com "Responder só por escrito" marcado, o Jarvis responde na
janela sem falar.

Segurança: só escuta em 127.0.0.1 e cada abertura do Jarvis gera uma chave
nova, que vai no endereço da janela. Pedidos sem a chave (de outro site aberto
no navegador, por exemplo) são recusados.
"""
import json
import os
import secrets
import subprocess
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from core.settings import BASE_DIR, CHAT_PORT

KEY = secrets.token_urlsafe(24)
MAX_TEXT = 4000
_messages = []  # {"n", "quem", "texto", "hora"}
_lock = threading.Lock()
_server = {"url": None}
_queue_lock = threading.Lock()


# ------------------------------------------------------------ conversa
def publish(who, text):
    """Acrescenta uma linha à conversa mostrada na janela (voz ou texto)."""
    text = str(text or "").strip()
    if not text:
        return
    with _lock:
        _messages.append({"n": len(_messages) + 1, "quem": who, "texto": text[:MAX_TEXT],
                          "hora": time.strftime("%H:%M")})
        del _messages[:-500]


def messages_since(n):
    with _lock:
        return [m for m in _messages if m["n"] > n]


def handle_text(text, text_only=False):
    """Atende um pedido escrito como se fosse falado (um de cada vez)."""
    from brain import audio
    from jarvis_commands import process_command

    with _queue_lock:
        audio.silenced = False  # escrever também "desfaz" um pare anterior
        with audio.text_only(text_only):
            try:
                result = process_command(text)
            except Exception as error:
                print(f"[CHAT] Erro ao atender: {error}")
                publish("jarvis", "Tive um problema com esse pedido.")
                return
        if result is False:
            publish("jarvis", "Desligando. Até a próxima.")
            os._exit(0)


# --------------------------------------------------------------- servidor
class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _key_ok(self, query=None):
        given = self.headers.get("X-Jarvis-Key") or (query or {}).get("k", [""])[0]
        return secrets.compare_digest(given or "", KEY)

    def _send(self, code, body, kind="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path == "/":
            if not self._key_ok(query):
                return self._send(403, b"Abra pelo Jarvis: diga 'abre o chat'.", "text/plain; charset=utf-8")
            with open(os.path.join(BASE_DIR, "interface", "chat.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if url.path == "/monitor":
            if not self._key_ok(query):
                return self._send(403, b"Abra pelo Jarvis: diga 'abre o monitor'.", "text/plain; charset=utf-8")
            with open(os.path.join(BASE_DIR, "interface", "monitor.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if url.path == "/monitor/dados":
            if not self._key_ok():
                return self._send(403, {"erro": "chave"})
            from brain.monitor import snapshot

            return self._send(200, snapshot())
        if url.path == "/mensagens":
            if not self._key_ok():
                return self._send(403, {"erro": "chave"})
            since = int((query.get("desde") or ["0"])[0] or 0)
            return self._send(200, {"mensagens": messages_since(since)})
        self._send(404, {"erro": "não encontrado"})

    def do_POST(self):
        if urlparse(self.path).path != "/enviar" or not self._key_ok():
            return self._send(403, {"erro": "chave"})
        try:
            size = min(int(self.headers.get("Content-Length", 0)), 64 * 1024)
            data = json.loads(self.rfile.read(size) or b"{}")
            text = str(data.get("texto", "")).strip()[:MAX_TEXT]
        except (ValueError, TypeError):
            return self._send(400, {"erro": "pedido inválido"})
        if not text:
            return self._send(400, {"erro": "texto vazio"})
        threading.Thread(target=handle_text, args=(text, bool(data.get("so_texto"))), daemon=True).start()
        self._send(200, {"ok": True})


def start():
    if _server["url"]:
        return _server["url"]
    for port in range(CHAT_PORT, CHAT_PORT + 10):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
        except OSError:
            continue
        threading.Thread(target=server.serve_forever, daemon=True).start()
        _server["url"] = f"http://127.0.0.1:{port}/?k={KEY}"
        return _server["url"]
    raise RuntimeError("Nenhuma porta livre para a janela de texto.")


def open_window(path="/", size="480,720"):
    url = start().replace("/?k=", f"{path}?k=" if path != "/" else "/?k=")
    from brain.avatar import _browser_for_app_window

    browser = _browser_for_app_window()
    if browser:
        subprocess.Popen([browser, f"--app={url}", f"--window-size={size}"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        webbrowser.open(url, new=1)
    return url
