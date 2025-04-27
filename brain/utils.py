import os
import re
import difflib
from datetime import datetime

def contains_old_date(response: str, tolerance=1) -> bool:
    """Returns True if very old dates are found in the response."""
    years = re.findall(r"\b(19\d{2}|20\d{2})\b", response)
    if not years:
        return False

    current_year = datetime.now().year
    for year in years:
        if int(year) < (current_year - tolerance):  # allow 2023 if we are in 2024
            return True
    return False

def is_outdated_response(response: str, query: str) -> bool:
    keywords = ["hoje", "atual", "agora", "neste momento", "previsão", "cotação", "valor"]
    ignore_if_historical_query = ["história", "presidentes", "biografia", "quando", "passado", "fundação", "inauguração"]

    query_lower = query.lower()

    # If it's a historical question, do not consider outdated
    if any(p in query_lower for p in ignore_if_historical_query):
        return False

    # If the question talks about something current, check for old dates
    if any(p in query_lower for p in keywords):
        years = re.findall(r"\b(19\d{2}|20\d{2})\b", response)
        for year in years:
            if int(year) < datetime.now().year - 1:
                return True

    return False

def log_interaction(user_input, response):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y-%m-%d')}.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Você: {user_input}\n")
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Jarvis: {response}\n\n")

def clean_output(text):
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    lines = text.splitlines()
    lines = [line for line in lines if line.strip() and not line.strip().startswith(">")]
    return " ".join(lines)

def sounds_like_jarvis(text):
    activation_words = ["jarvis"]
    text = text.lower()
    words = text.split()

    for word in words:
        for activator in activation_words:
            similarity = difflib.SequenceMatcher(None, word, activator).ratio()
            if similarity >= 0.2:
                return True
    return False
