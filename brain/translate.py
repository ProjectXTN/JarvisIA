from brain.memoria import llama_query
from brain.memoria import DEFAULT_MODEL

def translate_to_english(text):
    try:
        prompt = (
            f"Traduza a seguinte frase de português para inglês. "
            f"Apenas me dê o texto traduzido de forma direta, como um comando, pronto para ser usado por uma inteligência artificial. "
            f"Não adicione frases como 'I want you to', 'Please', 'Can you', nem qualquer instrução. "
            f"Traduza apenas o conteúdo, sem explicações ou formatação extra: \"{text}\""
        )

        translated_text = llama_query(prompt, model=DEFAULT_MODEL)
        
        translated_text = translated_text.strip().strip('"')
        
        print(f"[DEBUG] Tradução via LLaMA ({DEFAULT_MODEL}): {translated_text}")
        return translated_text
    except Exception as e:
        print(f"[ERRO] Falha ao traduzir com LLaMA: {e}")
        print("[Aviso] Continuando usando o texto original.")
        return text
