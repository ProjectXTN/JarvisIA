import re
from brain.audio import say
from modules.stable_diffusion_controller import StableDiffusionGenerator

# NO CORPO DA FUNÇÃO - CERTO
def dispatch_image_command(query):
    try:
        from comandos.comandos_imagem import image_command

        query = query.lower().strip()

        criar_patterns = [
            r"\b(crie|criar|desenhe|desenhar|gere|gerar|cria|desenha|gera)\b.*(imagem|foto)",
            r"(imagem|foto).*\b(crie|criar|desenhe|desenhar|gere|gerar|cria|desenha|gera)\b",
        ]

        for pattern in criar_patterns:
            if re.search(pattern, query):
                say("Entendido, estou criando a imagem!")
                cleaned_prompt = re.sub(r"\b(crie|criar|desenhe|desenhar|gere|gerar|cria|desenha|gera)\b\s*(uma|um)?\s*(imagem|foto)\s*(de|da|do)?\s*", "", query).strip()

                if not cleaned_prompt:
                    say("Você precisa me dizer o que deseja que eu desenhe!")
                    return True

                generator = StableDiffusionGenerator()
                final_path = generator.generate_image(cleaned_prompt)

                if final_path:
                    say("Imagem criada com sucesso!")
                else:
                    say("Tive um problema e não consegui criar a imagem.")
                return True

        say("Ok, vou analisar a imagem!")
        return image_command(query)

    except Exception as e:
        say(f"Ocorreu um erro no comando de imagem: {e}")
        return True
