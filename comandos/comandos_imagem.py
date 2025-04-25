import os
import re
from brain.audio import say, listen
from brain.memoria import generate_response, DEFAULT_MODEL
from jarvis_vision import descrever_imagem

def comando_imagem(query):
    try:
        query = query.lower()

        padroes = [
            r"(descrev[ae]?|analisa[rs]?|veja|olha|visualiza[rs]?).*(imagem|foto)",
            r"(imagem|foto).*(descrev[ae]?|analisa[rs]?|veja|olha|visualiza[rs]?)",
            r"o que (tem|há|existe).*(imagem|foto)",
            r"o que aparece.*(imagem|foto)",
            r"me diga.*(imagem|foto)",
            r"o que você vê.*(imagem|foto)"
        ]

        if not any(re.search(p, query) for p in padroes):
            return False

        match = re.search(r"(imagem|foto)(?:\s+(?:de|em|do|da|na|no))?\s+([\w-]+)", query)
        if not match:
            say("Informe o nome da imagem. Exemplo: 'descreva a imagem skyline' ou 'analise a foto corrida'.")
            return True

        nome_base = match.group(2)
        formatos = ["jpg", "jpeg", "png", "webp"]
        pasta = os.path.expanduser("~/Pictures")

        for ext in formatos:
            caminho = os.path.join(pasta, f"{nome_base}.{ext}")
            if os.path.exists(caminho):
                say(f"Você quer que eu analise visualmente a imagem \"{nome_base}\" ?")
                try:
                    resposta = listen()
                    if not resposta:
                        say("Não entendi sua resposta. Vou deixar essa imagem para depois.")
                        return True

                    resposta = resposta.lower()
                    gatilhos_analise = [
                        "sim", "pode", "claro", "analise", "analisa", "análise", "olhe", "olha",
                        "descreva", "descrever", "faça a análise", "explique a imagem", "explique",
                        "me diga o que tem", "quero que veja", "quero que analise", "traduza visualmente", "quero que você analise",
                    ]

                    if any(g in resposta for g in gatilhos_analise):
                        descricao = descrever_imagem(caminho, texto_usuario=query)

                        if not descricao or not descricao.strip():
                            say(f"Tentei analisar a imagem {os.path.basename(caminho)}, mas não consegui obter uma descrição.")
                            return True

                        if re.search(r"\b(the|and|with|in|of|a|is|are|car|background)\b", descricao.lower()):
                            traducao = generate_response(f"Traduza para português: {descricao}", DEFAULT_MODEL)
                            descricao = traducao if traducao else descricao

                        say(f"{os.path.basename(caminho)}: {descricao}")
                    else:
                        resposta_textual = generate_response(f"Fale sobre a imagem {nome_base}", DEFAULT_MODEL)
                        say(resposta_textual)

                    return True
                except Exception as e:
                    say(f"Ocorreu um erro durante a interação com a imagem: {e}")
                    return True

        say(f"Não encontrei a imagem ou foto \"{nome_base}\" na sua pasta Imagens.")
        return True

    except Exception as e:
        say(f"Ocorreu um erro geral na análise da imagem: {e}")
        return True

comandos_imagem = {
    "imagem": comando_imagem,
    "foto": comando_imagem,
}
