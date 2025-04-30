import re
from brain.audio import say

# Expressions indicating command chaining
MULTIPLE_PATTERNS = [
    r"\b(e\s+então|e\s+depois|então|depois|e)\b"
]

def multiple_command(query):
    query = query.lower()

    if not any(re.search(p, query) for p in MULTIPLE_PATTERNS):
        return False  # No multiple command detected

    from jarvis_commands import process_command

    parts = re.split(r"\b(?:e\s+então|e\s+depois|então|depois|e)\b", query)

    for part in parts:
        part = part.strip()
        if part:
            success = process_command(part)
            if not success:
                say(f"Não consegui entender essa parte: \"{part}\".")
    return True

multiple_commands = {
    "comando_multiplo": multiple_command
}
