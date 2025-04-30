from brain.memory import llama_query
from brain.memory import DEFAULT_MODEL

def translate_to_english(text):
    try:
        prompt = (
            f"Traduza a seguinte frase de português para inglês. "
            f"Preserve com exatidão qualquer informação sobre quantidade (como 'um', 'uma', 'apenas um', 'somente um'). "
            f"A tradução deve manter explicitamente que é apenas um objeto ou uma pessoa se isso for mencionado. "
            f"Não adicione frases como 'I want you to', 'Please', 'Can you', nem qualquer instrução. "
            f"Apenas traduza o conteúdo diretamente, pronto para ser usado por uma inteligência artificial, sem explicações extras: \"{text}\""
        )

        translated_text = llama_query(prompt, model=DEFAULT_MODEL, direct_mode=True)
        
        translated_text = translated_text.strip().strip('"')
        
        print(f"[DEBUG] Tradução via LLaMA ({DEFAULT_MODEL}): {translated_text}")
        return translated_text
    except Exception as e:
        print(f"[ERRO] Falha ao traduzir com LLaMA: {e}")
        print("[Aviso] Continuando usando o texto original.")
        return text
