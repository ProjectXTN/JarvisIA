import os
import re
from brain.audio import say
from brain.traduction_file_srt.traduction import translate_srt_llm

def execute_subtitle_translation(query, speak=True):
    match = re.search(
        r"traduz(?:a|ir)?\s*(?:o\s*)?arquivo\s+(?P<file>[^\s]+)(?:\s+para\s+(?P<lang>[\w\-éêáãíóç]+))?",
        query,
        re.IGNORECASE
    )
    if not match:
        if speak:
            say("Fale, por exemplo: 'traduzir arquivo legenda para português'")
        return False

    input_name = match.group("file")
    target_lang = match.group("lang")

    # Documents path
    documents_dir = os.path.join(os.path.expanduser('~'), 'Documents')
    input_path = os.path.join(documents_dir, f"{input_name}.srt")
    output_path = os.path.join(documents_dir, f"{input_name}-{target_lang}.srt")

    if not target_lang:
        if speak:
            say("Para qual idioma você quer traduzir?")
        return False

    if not os.path.isfile(input_path):
        if speak:
            say(f"Arquivo não encontrado: {input_path}.")
        return False

    try:
        say(f"Iniciando tradução do arquivo {input_name} para {target_lang}.")
        translate_srt_llm(input_path, output_path, target_lang)
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
