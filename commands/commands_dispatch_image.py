import re
from brain.audio import say
from modules.stable_diffusion_controller import StableDiffusionGenerator
from core.initializer import start_stable_diffusion
import requests


def is_stable_diffusion_running():
    try:
        return requests.get("http://127.0.0.1:7860/sdapi/v1/options", timeout=3).status_code == 200
    except requests.exceptions.RequestException:
        return False

# NO CORPO DA FUNÇÃO - CERTO
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
                say("Entendido, estou criando a imagem!")
                cleaned_prompt = re.sub(r"\b(crie|criar|desenhe|desenhar|gere|gerar|cria|desenha|gera)\b\s*(uma|um)?\s*(imagem|foto)\s*(de|da|do)?\s*", "", query).strip()

                if not cleaned_prompt:
                    say("Você precisa me dizer o que deseja que eu desenhe!")
                    return True

                # O Stable Diffusion não abre mais junto com o Jarvis
                if not is_stable_diffusion_running():
                    say("Abrindo o gerador de imagens. Isso leva cerca de um minuto.")
                    start_stable_diffusion()

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
