import re
from brain.audio import say

# Expressões que indicam encadeamento de comandos
PADROES_MULTIPLOS = [
    r"\b(e\s+então|e\s+depois|então|depois|e)\b"
]

def comando_multiplos(query):
    query = query.lower()

    if not any(re.search(p, query) for p in PADROES_MULTIPLOS):
        return False  # Não contém comando múltiplo

    from jarvis_commands import process_command

    partes = re.split(r"\b(?:e\s+então|e\s+depois|então|depois|e)\b", query)

    for parte in partes:
        parte = parte.strip()
        if parte:
            sucesso = process_command(parte)
            if not sucesso:
                say(f"Não consegui entender essa parte: \"{parte}\".")
    return True

comandos_multiplos = {
    "comando_multiplo": comando_multiplos
}
