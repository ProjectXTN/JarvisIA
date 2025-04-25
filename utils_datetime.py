# utils_datetime.py
from datetime import datetime

def responder_data():
    hoje = datetime.now().strftime("%d/%m/%Y")
    return f"Hoje é {hoje}."

def responder_hora():
    hora = datetime.now().strftime("%H:%M")
    return f"Agora são {hora}."
