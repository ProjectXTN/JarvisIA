import os
import re
import difflib
from datetime import datetime
import unicodedata

COUNTRY_CODES = {
    "brasil": "BR",
    "frança": "FR",
    "portugal": "PT",
    "espanha": "ES",
    "estados unidos": "US",
    "canadá": "CA",
    "alemanha": "DE",
    "japão": "JP",
    "china": "CN",
    "itália": "IT",
}

def normalize_country(country_name):
    country_name = country_name.strip().lower()
    return COUNTRY_CODES.get(country_name, country_name)

def normalize_text(text):
    text = text.lower()
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()

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
    """Clean the model's output for better TTS experience."""
    # Remove bold and italic markdown
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    
    # Remove markdown headers (###, ##, #)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    
    # Remove blockquotes
    lines = text.splitlines()
    lines = [line for line in lines if line.strip() and not line.strip().startswith(">")]
    
    # Join everything back into a single string
    return " ".join(lines)

def sounds_like_jarvis(text):
    activation_words = ["jarvis"]
    text = normalize_text(text)

    words = text.split()

    best_match = 0.0
    best_word = None

    for word in words:
        for activator in activation_words:
            similarity = difflib.SequenceMatcher(None, word, activator).ratio()
            if similarity > best_match:
                best_match = similarity
                best_word = word

    if best_match >= 0.6:
        return True, best_word
    else:
        return False, None

def is_code_request(query):
    query_lower = query.lower().strip()

    false_positives = [
        "mapa de conhecimento",
        "knowledge map",
        "knowledge graph",
    ]

    if any(p in query_lower for p in false_positives):
        return False 

    code_patterns = [
        # PT
        r"\bcódigo\b", r"\bscript\b", r"\bclasse\b", r"\bfunção\b", r"\bmétodo\b", r"\bimplementação\b", r"\bexemplo\b",
        # EN
        r"\bcode\b", r"\bscript\b", r"\bclass\b", r"\bfunction\b", r"\bmethod\b", r"\bimplementation\b", r"\bexample\b",
        # FR
        r"\bcode\b", r"\bscript\b", r"\bclasse\b", r"\bfonction\b", r"\bméthode\b", r"\bimplémentation\b", r"\bexemple\b",

        # PT
        r"me mostre.*(código|script|função|classe|exemplo)",
        r"gera\s+(um|uma|o)?\s*(código|code|script|classe|function|função|exemplo)",
        r"escreva\s+(um|uma|o)?\s*(código|code|script|classe|function|função|exemplo)",
        # EN
        r"show( me| us)?.*(code|script|example|class|function|snippet)",
        r"generate\s+(a|the)?\s*(code|script|function|example|snippet)",
        r"write\s+(a|the)?\s*(code|script|function|example)",
        r"how (to|do i|do you).*(code|script|program|function|class|example)",
        # FR
        r"montre( moi| nous)?\s*(le|la)?\s*(code|script|exemple|classe|fonction)",
        r"génère( un| une| le| la)?\s*(code|script|exemple|classe|fonction)",
        r"écris( un| une| le| la)?\s*(code|script|fonction|exemple|classe)",
        r"comment\s+(faire|écrire|coder).*(code|script|fonction|classe|exemple)",

        # PT
        r"\bem\s+(python|javascript|typescript|c\+\+|c#|java|php|go|rust)\b",
        # EN
        r"\bin\s+(python|javascript|typescript|c\+\+|c#|java|php|go|rust)\b",
        # FR
        r"\ben\s+(python|javascript|typescript|c\+\+|c#|java|php|go|rust)\b",
        r"\bpar\s+exemple\s+en\s+(python|javascript|typescript|c\+\+|c#|java|php|go|rust)\b",
        r"utilisant\s+(python|javascript|typescript|c\+\+|c#|java|php|go|rust)\b",

        r"\bregex\b", r"\bexpressão regular\b", r"\bexpression régulière\b",
        r"\bhtml\b", r"\bcss\b", r"\bjavascript\b", r"\btypescript\b", r"\bjsx\b", r"\btsx\b",
    ]


    return any(re.search(pattern, query_lower) for pattern in code_patterns)
