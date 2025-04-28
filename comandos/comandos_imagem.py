import os
import re
from brain.audio import say, listen
from brain.memoria import generate_response, DEFAULT_MODEL, DEFAULT_MODEL_HIGH
from comandos.commands_dispatch_image import dispatch_image_command
from jarvis_vision import describe_image


def image_command(query):
    try:
        query = query.lower()

        match = re.search(
            r"(imagem|foto)(?:\s+(?:de|em|do|da|na|no))?\s+([\w-]+)", query
        )
        if not match:
            say(
                "Informe o nome da imagem. Exemplo: 'descreva a imagem skyline' ou 'analise a foto corrida'."
            )
            return True

        base_name = match.group(2)
        formats = ["jpg", "jpeg", "png", "webp"]
        folder = os.path.expanduser("~/Pictures")

        for ext in formats:
            path = os.path.join(folder, f"{base_name}.{ext}")
            if os.path.exists(path):
                say(f'Você quer que eu analise visualmente a imagem "{base_name}" ?')
                try:
                    response = listen()
                    if not response:
                        say(
                            "Não entendi sua resposta. Vou deixar essa imagem para depois."
                        )
                        return True

                    response = response.lower()
                    analysis_triggers = [
                        "sim",
                        "pode",
                        "claro",
                        "analise",
                        "analisa",
                        "análise",
                        "olhe",
                        "olha",
                        "descreva",
                        "descrever",
                        "faça a análise",
                        "explique a imagem",
                        "explique",
                        "me diga o que tem",
                        "quero que veja",
                        "quero que analise",
                        "traduza visualmente",
                        "quero que você analise",
                    ]

                    if any(trigger in response for trigger in analysis_triggers):
                        description = describe_image(path, user_text=query)

                        if not description or not description.strip():
                            say(
                                f"Tentei analisar a imagem {os.path.basename(path)}, mas não consegui obter uma descrição."
                            )
                            return True

#                        if re.search(
#                            r"\b(o|a|e|com|em|de|um|uma|é|são|fundo)\b",
#                            description.lower(),
#                        ):
#                            translation = generate_response(
#                                f"Traduza para português: {description}",
#                                DEFAULT_MODEL_HIGH,
#                            )
#                            description = translation if translation else description

                        say(f"{os.path.basename(path)}: {description}")
                    else:
                        textual_response = generate_response(
                            f"Fale sobre a imagem {base_name}", DEFAULT_MODEL_HIGH
                        )
                        say(textual_response)

                    return True
                except Exception as e:
                    say(f"Ocorreu um erro durante a interação com a imagem: {e}")
                    return True

        say(f'Não encontrei a imagem ou foto "{base_name}" na sua pasta Imagens.')
        return True

    except Exception as e:
        say(f"Ocorreu um erro geral na análise da imagem: {e}")
        return True


image_commands = {
    "imagem": dispatch_image_command,
    "foto": dispatch_image_command,
}
