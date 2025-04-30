# utils_datetime.py
from datetime import datetime

def respond_date():
    today = datetime.now().strftime("%d/%m/%Y")
    return f"Hoje é {today}."

def respond_time():
    time_now = datetime.now().strftime("%H:%M")
    return f"Agora são {time_now}."
