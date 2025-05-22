from brain.memory.memory import llama_query
from brain.memory.memory import DEFAULT_MODEL

def translate_to_english(text):
    try:
        prompt = (
            f"Traduza a seguinte frase do português para o inglês. "
            f"Preserve com exatidão qualquer informação de quantidade, como 'um', 'uma', 'apenas um', 'somente um', etc. "
            f"A tradução deve deixar absolutamente claro que se trata de apenas uma única instância de cada objeto ou pessoa mencionada. "
            f"Use palavras como 'a single', 'only one' ou 'just one' quando necessário para garantir isso. "
            f"Não adicione instruções, nem frases como 'Please', 'I want you to', etc. "
            f"Somente traduza o conteúdo diretamente, de forma objetiva e pronta para ser interpretada por uma IA de geração de imagens: \"{text}\""
        )
        translated_text = llama_query(prompt, model=DEFAULT_MODEL, direct_mode=True)
        
        translated_text = translated_text.strip().strip('"')
        
        print(f"[DEBUG] Tradução via LLaMA ({DEFAULT_MODEL}): {translated_text}")
        return translated_text
    except Exception as e:
        print(f"[ERRO] Falha ao traduzir com LLaMA: {e}")
        print("[Aviso] Continuando usando o texto original.")
        return text
