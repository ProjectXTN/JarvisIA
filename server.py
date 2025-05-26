import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from jarvis_commands import process_command_api
from core import config

app = Flask(__name__)
CORS(app)

load_dotenv()
SECRET_TOKEN = os.getenv("SECRET_TOKEN_JARVIS")

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "online"})


@app.route("/ask", methods=["POST"])
def ask_jarvis():
    
    config.IS_API_REQUEST = True 

    auth = request.headers.get("Authorization")
    if auth != f"Bearer {SECRET_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    question = data.get("question")
    lang = data.get("lang", "pt")
    print(f"[DEBUG] [FLASK] Language received from frontend: {lang}")

    if question:
        try:
            response = process_command_api(question, lang=lang)
            config.IS_API_REQUEST = False
            return jsonify({"answer": response})
        except Exception as e:
            config.IS_API_REQUEST = False
            return jsonify({"error": str(e)}), 500
    else:
        config.IS_API_REQUEST = False
        return jsonify({"error": "No question provided"}), 400

    
if __name__ == "__main__":
    print("🚀 Jarvis Flask server is running on port 11600")
    app.run(host="0.0.0.0", port=11600)
