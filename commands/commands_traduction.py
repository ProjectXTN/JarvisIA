import os
import re
from brain.audio import say
from brain.traduction_file_srt.traduction import translate_subtitle_llm

def execute_subtitle_translation(query, speak=True):
    match = re.search(
        r"traduz(?:a|ir)?\s*(?:o\s*)?arquivo\s+(?P<file>[^\s]+)(?:\s+para\s+(?P<lang>[\w\-éêáãíóç]+))?",
        query,
        re.IGNORECASE
    )
    if not match:
        if speak:
            say("Exemplo: 'traduzir arquivo legenda para português'")
        return False

    input_name = match.group("file")
    target_lang = match.group("lang")
    
    documents_dir = os.path.join(os.path.expanduser('~'), 'Documents')

    possible_extensions = [".srt", ".ass"]
    input_path = None
    for ext in possible_extensions:
        test_path = os.path.join(documents_dir, f"{input_name}{ext}")
        if os.path.isfile(test_path):
            input_path = test_path
            break

    if not target_lang:
        if speak:
            say("Para qual idioma você quer traduzir?")
        return False

    if not input_path:
        if speak:
            say(f"Arquivo '{input_name}.srt' ou '{input_name}.ass' não encontrado em {documents_dir}.")
        return False

    base, ext = os.path.splitext(input_path)
    output_path = f"{base}-{target_lang}{ext}"

    try:
        say(f"Iniciando tradução do arquivo {os.path.basename(input_path)} para {target_lang}.")
        translate_subtitle_llm(input_path, output_path, target_lang)
        say(f"Tradução concluída! Legenda salva em {output_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to translate file: {e}")
        say(f"Falha ao traduzir o arquivo: {e}")
        return False
    
# Regex to detect all possible forms (remains in pt for Jarvis trigger)
TRANSLATION_REGEX = r"traduz(?:a|ir)?\s*(?:o\s*)?arquivo\s+[^\s]+(?:\s+para\s+[\w\-éêáãíóç]+)?"

translation_commands = [
    (TRANSLATION_REGEX, execute_subtitle_translation)
]