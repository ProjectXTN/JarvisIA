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

MAX_QUESTION = 2000
LANGS = {"pt", "en"}
MIN_TOKEN = 16


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
    lang = data.get("lang", "pt")
    if lang not in LANGS:
        raise BadRequest("Idioma inválido (use 'pt' ou 'en').")
    return question.strip(), lang


def allowed_origins(value):
    return [o.strip() for o in (value or "").split(",") if o.strip()]


def create_app(token, answer, origins=()):
    """Monta o app Flask. answer(pergunta, lang) devolve o texto da resposta."""
    from flask import Flask, jsonify, request

    from core import config

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    if origins:
        from flask_cors import CORS

        CORS(app, origins=list(origins))
    busy = threading.Lock()

    @app.get("/")
    def home():
        from flask import redirect

        return redirect("/painel")

    @app.get("/ping")
    def ping():
        return jsonify({"status": "online"})

    # ---- Painel "o que o Jarvis sabe" (Fase 7, item 59): página + API com o mesmo token
    def authorized():
        return token_ok(request.headers.get("Authorization"), token)

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


def main():
    token = os.getenv("SECRET_TOKEN_JARVIS", "")
    if len(token) < MIN_TOKEN:
        print("❌ Defina SECRET_TOKEN_JARVIS no .env (mínimo 16 caracteres). Sugestão:")
        print(f"   SECRET_TOKEN_JARVIS={secrets.token_urlsafe(32)}")
        sys.exit(1)
    host = os.getenv("JARVIS_API_HOST", "127.0.0.1")
    port = int(os.getenv("JARVIS_API_PORT", "11600"))

    def answer(question, lang):
        # Importa o Jarvis (Whisper, voz) só no primeiro /ask: o painel não precisa
        # disso e não ocupa a placa de vídeo à toa junto com o Jarvis aberto
        from jarvis_commands import process_command_api

        return process_command_api(question, lang=lang)

    app = create_app(token, answer,
                     allowed_origins(os.getenv("JARVIS_API_ORIGINS")))
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
