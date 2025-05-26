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
    code_patterns = [
        # Generic words
        r"\bcódigo\b", r"\bcode\b", r"\bscript\b", r"\bclasse\b", r"\bclass\b",
        r"\bfunção\b", r"\bfunction\b", r"\bmétodo\b", r"\bmethod\b", r"\bprocédure\b", r"\bprocédure\b",
        r"\bexample\b", r"\bexemplo\b", r"\bsnippet\b", r"\btutoriel\b", r"\btutorial\b", r"\bimplémentation\b",
        r"\bimplementação\b", r"\bimplémentation\b", r"\bextrait\b", r"\bfragmento\b", r"\bfragment\b",
        # Requests like "show me", "generate", "example"
        r"me mostre.*(código|code|script|função|classe|exemplo|example|snippet)",
        r"gera( um| uma| o)?(.*)?(código|code|script|classe|class|function|função|example|exemplo)",
        r"faça( um| uma| o)?(.*)?(código|code|script|classe|class|function|função|example|exemplo)",
        r"escreva( um| uma| o)?(.*)?(código|code|script|classe|class|function|função|example|exemplo)",
        r"show( me| us)?(.*)?(code|snippet|example|class|function|script)",
        r"how (to|do i|do you).*(code|script|program|função|classe|exemplo|example|snippet)",
        # Language specification - PT/EN/FR
        r"\bem\s+([a-z#\+\d]+)\b",      # ex: em python, em c++, em c#
        r"\bin\s+([a-z#\+\d]+)\b",      # ex: in python, in c++
        r"\ben\s+([a-z#\+\d]+)\b",      # ex: en python (FR)
        r"\bpar\s+exemple\s+en\s+([a-z#\+\d]+)\b",  # ex: par exemple en python (FR)
        r"utilisant\s+([a-z#\+\d]+)\b", # ex: utilisant python (FR)
        # Popular formats (PT/EN/FR)
        r"\b(expressão regular|regex|regexp)\b",
        r"\bhtml\b", r"\bcss\b", r"\bjavascript\b", r"\btypescript\b", r"\bjsx\b", r"\btsx\b",
        r"\bpython\b", r"\bjava\b", r"\bc\+\+\b", r"\bc#\b", r"\bc\b", r"\bphp\b", r"\bruby\b", r"\bgo\b", r"\brust\b",
        r"\bkotlin\b", r"\bscala\b", r"\bswift\b", r"\bperl\b", r"\blua\b", r"\bsql\b", r"\bash\b", r"\bpowershell\b",
        r"\bmatlab\b", r"\br\b", r"\bdart\b", r"\bflutter\b", r"\bvue\b", r"\bangular\b", r"\breact\b", r"\bnode\b",
    ]
    query_lower = query.lower()
    return any(re.search(pattern, query_lower) for pattern in code_patterns)
