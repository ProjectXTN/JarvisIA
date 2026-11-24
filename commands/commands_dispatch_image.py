import re
from brain.audio import say
import requests


def dispatch_image_command(query):
    try:
        from commands.commands_image import image_command

        query = query.lower().strip()

        criar_patterns = [
            r"\b(crie|criar|desenhe|desenhar|gere|gerar|cria|desenha|gera)\b.*(imagem|foto)",
            r"(imagem|foto).*\b(crie|criar|desenhe|desenhar|gere|gerar|cria|desenha|gera)\b",
        ]

        for pattern in criar_patterns:
            if re.search(pattern, query):
                cleaned_prompt = re.sub(r"\b(crie|criar|desenhe|desenhar|gere|gerar|cria|desenha|gera)\b\s*(uma|um)?\s*(imagem|foto)\s*(de|da|do)?\s*", "", query).strip()

                if not cleaned_prompt:
                    say("Você precisa me dizer o que deseja que eu desenhe!")
                    return True

                from brain.tools import criar_imagem

                criar_imagem(cleaned_prompt)
                return True

        say("Ok, vou analisar a imagem!")
        return image_command(query)

    except Exception as e:
        say(f"Ocorreu um erro no comando de imagem: {e}")
        return True
