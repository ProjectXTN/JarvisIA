"""API HTTP do Jarvis (perguntas em texto, para o app de chat e outros clientes).

Segurança:
  - token obrigatório (SECRET_TOKEN_JARVIS no .env, mínimo 16 caracteres);
    sem token o servidor nem abre;
  - comparação do token em tempo constante (hmac.compare_digest);
  - escuta só em 127.0.0.1, a não ser que JARVIS_API_HOST diga outro endereço;
  - CORS desligado, a não ser para as origens em JARVIS_API_ORIGINS
    (separadas por vírgula);
  - pedidos atendidos um de cada vez (o modelo é um só) e com tamanho limitado;
  - erros internos vão para o log, não para quem chamou.
Serve com waitress (pip install waitress); sem ele, usa o servidor do Flask.
"""

import hmac
import os
import secrets
import sys
import threading

from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    from core import log

    log.setup()

MAX_QUESTION = 8000          # o site manda prompts longos (gráfico de conceitos)
LANGS = {"pt", "en", "fr"}
MIN_TOKEN = 16
# Site do Pedro (pedromeireles.dev) e o Vite em desenvolvimento. JARVIS_API_ORIGINS troca a lista.
DEFAULT_ORIGINS = "https://pedromeireles.dev,https://www.pedromeireles.dev,http://localhost:5173"
# Pedidos por minuto por visitante (o token do site é público, vai no JavaScript)
RATE_PER_MINUTE = int(os.getenv("JARVIS_API_RATE", "20"))


class BadRequest(ValueError):
    pass


def token_ok(header, token):
    """Confere "Authorization: Bearer <token>" em tempo constante."""
    if not token or not header or not header.startswith("Bearer "):
        return False
    return hmac.compare_digest(header[len("Bearer "):].encode(), token.encode())


def parse_question(data):
    """(pergunta, idioma) de um JSON de pedido, ou BadRequest."""
    if not isinstance(data, dict):
        raise BadRequest("Envie um JSON com o campo 'question'.")
    question = data.get("question")
    if not isinstance(question, str) or not question.strip():
        raise BadRequest("O campo 'question' precisa ser um texto.")
    if len(question) > MAX_QUESTION:
        raise BadRequest(f"Pergunta longa demais (máximo {MAX_QUESTION} caracteres).")
    lang = str(data.get("lang") or "pt").lower()[:2]  # o site manda "pt-BR", "en-US", "fr"
    if lang not in LANGS:
        lang = "pt"
    return question.strip(), lang


class RateLimiter:
    """No máximo `per_minute` pedidos por visitante em 60 s."""

    def __init__(self, per_minute):
        self.per_minute = per_minute
        self.hits = {}
        self.lock = threading.Lock()

    def allow(self, who, now=None):
        import time

        now = now or time.monotonic()
        with self.lock:
            recent = [t for t in self.hits.get(who, []) if now - t < 60]
            if len(recent) >= self.per_minute:
                self.hits[who] = recent
                return False
            recent.append(now)
            self.hits[who] = recent
            if len(self.hits) > 5000:  # não cresce sem fim
                self.hits = {k: v for k, v in self.hits.items() if v and now - v[-1] < 60}
            return True


def allowed_origins(value):
    return [o.strip() for o in (value or "").split(",") if o.strip()]


# Só isto pode ser acessado pela internet (túnel do Cloudflare); o resto é só deste PC
PUBLIC_PATHS = {"/ask", "/ping"}
_LOCAL_HOSTS = {"127.0.0.1", "localhost", "[::1]"}
_PROXY_HEADERS = ("CF-Connecting-IP", "CF-Ray", "X-Forwarded-For", "X-Real-IP", "Forwarded")


def is_external(headers, host):
    """True se o pedido veio de fora (túnel/proxy), mesmo chegando em 127.0.0.1."""
    if any(headers.get(h) for h in _PROXY_HEADERS):
        return True
    return (host or "").split(":")[0].lower() not in _LOCAL_HOSTS and not (host or "").startswith("[::1]")


def create_app(token, answer, origins=(), panel_token=None):
    """Monta o app Flask. answer(pergunta, lang) devolve o texto da resposta.

    token: o do site (público, vai no JavaScript): só serve para /ask.
    panel_token: outro token, só para o painel, que além disso só abre neste PC.
    """
    from flask import Flask, jsonify, request

    from core import config

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    if origins:
        from flask_cors import CORS

        CORS(app, origins=list(origins))
    busy = threading.Lock()
    limiter = RateLimiter(RATE_PER_MINUTE)

    def visitor():
        # Atrás do túnel do Cloudflare o IP real vem neste cabeçalho
        return request.headers.get("CF-Connecting-IP") or request.remote_addr or "?"

    @app.before_request
    def only_chat_from_outside():
        # Pela internet só existe o chat; painel e o resto nem aparecem
        if request.path not in PUBLIC_PATHS and is_external(request.headers, request.host):
            return jsonify({"error": "Not found"}), 404
        return None

    @app.get("/")
    def home():
        from flask import redirect

        return redirect("/painel")

    @app.get("/ping")
    def ping():
        return jsonify({"status": "online"})

    # ---- Painel "o que o Jarvis sabe" (Fase 7, item 59): só neste PC e com token próprio
    def authorized():
        if is_external(request.headers, request.host) or not panel_token:
            return False
        return token_ok(request.headers.get("Authorization"), panel_token)

    @app.get("/painel")
    def panel_page():
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "interface", "painel.html"), encoding="utf-8") as f:
            return f.read(), 200, {"Content-Type": "text/html; charset=utf-8",
                                   "Cache-Control": "no-store",
                                   "Content-Security-Policy": "default-src 'self' 'unsafe-inline'"}

    @app.get("/api/painel")
    def panel_data():
        if not authorized():
            return jsonify({"error": "Unauthorized"}), 401
        from brain.persona import painel

        return jsonify(painel.overview())

    @app.post("/api/painel/<kind>/<row_id>")
    def panel_change(kind, row_id):
        if not authorized():
            return jsonify({"error": "Unauthorized"}), 401
        from brain.persona import painel

        data = request.get_json(silent=True) or {}
        try:
            if data.get("acao") == "apagar":
                count = (painel.delete_memory(row_id) if kind == "memorias"
                         else painel.delete_row(kind, row_id))
            elif kind == "memorias":
                painel.edit_memory(row_id, data.get("valor"), data.get("assunto"))
                count = 1
            else:
                count = painel.edit_row(kind, row_id, data.get("campo"), data.get("valor"))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        from brain.persona.core import invalidate

        invalidate()
        return jsonify({"ok": bool(count)})

    @app.post("/ask")
    def ask_jarvis():
        if not token_ok(request.headers.get("Authorization"), token):
            return jsonify({"error": "Unauthorized"}), 401
        if not limiter.allow(visitor()):
            return jsonify({"error": "Muitas perguntas seguidas; espere um minuto."}), 429
        try:
            question, lang = parse_question(request.get_json(silent=True))
        except BadRequest as error:
            return jsonify({"error": str(error)}), 400
        if not busy.acquire(timeout=90):
            return jsonify({"error": "Jarvis ocupado, tente de novo."}), 429
        try:
            with config.api_request():
                return jsonify({"answer": answer(question, lang)})
        except Exception as error:
            app.logger.exception("Erro ao responder pela API: %s", error)
            return jsonify({"error": "Erro interno."}), 500
        finally:
            busy.release()

    return app


def ensure_ollama():
    """O site precisa do Ollama mesmo com o Jarvis de voz fechado: abre se não estiver no ar.

    Sem importar core.initializer, que carregaria o Whisper e a voz à toa.
    """
    import subprocess
    import time

    import requests

    from core.settings import OLLAMA_HOST

    try:
        requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        return True
    except requests.RequestException:
        pass
    print(f"⚙️ Ollama fora do ar em {OLLAMA_HOST}; abrindo...")
    env = dict(os.environ, OLLAMA_HOST=OLLAMA_HOST.split("//", 1)[-1])
    try:
        subprocess.Popen(["ollama", "serve"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except OSError as error:
        print(f"⚠️ Não consegui abrir o Ollama: {error}")
        return False
    for _ in range(20):
        time.sleep(1)
        try:
            requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
            print("✅ Ollama no ar.")
            return True
        except requests.RequestException:
            continue
    print("⚠️ O Ollama não respondeu; o site vai dar erro até ele abrir.")
    return False

def main():
    token = os.getenv("SECRET_TOKEN_JARVIS", "")
    if len(token) < MIN_TOKEN:
        print("❌ Defina SECRET_TOKEN_JARVIS no .env (mínimo 16 caracteres). Sugestão:")
        print(f"   SECRET_TOKEN_JARVIS={secrets.token_urlsafe(32)}")
        sys.exit(1)
    host = os.getenv("JARVIS_API_HOST", "127.0.0.1")

    ensure_ollama()
    port = int(os.getenv("JARVIS_API_PORT", "11600"))

    def answer(question, lang):
        # Importa o Jarvis (Whisper, voz) só no primeiro /ask: o painel não precisa
        # disso e não ocupa a placa de vídeo à toa junto com o Jarvis aberto
        from jarvis_commands import process_command_api

        return process_command_api(question, lang=lang)

    panel_token = os.getenv("JARVIS_PANEL_TOKEN", "")
    if len(panel_token) < MIN_TOKEN or hmac.compare_digest(panel_token, token):
        panel_token = secrets.token_urlsafe(18)
        print(f"🔑 Token do painel (só vale nesta abertura; fixe com JARVIS_PANEL_TOKEN no .env): {panel_token}")
    app = create_app(token, answer,
                     allowed_origins(os.getenv("JARVIS_API_ORIGINS", DEFAULT_ORIGINS)), panel_token)
    if host not in ("127.0.0.1", "localhost"):
        print(f"⚠️ API aberta para a rede em {host}; use só em rede confiável.")
    try:
        from waitress import serve
    except ImportError:
        print("⚠️ waitress não instalado (pip install waitress); usando o servidor do Flask.")
        app.run(host=host, port=port)
    else:
        print(f"🚀 API do Jarvis em http://{host}:{port} (waitress) — painel: http://{host}:{port}/painel")
        serve(app, host=host, port=port, threads=4)


if __name__ == "__main__":
    main()
