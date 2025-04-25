import subprocess
import re

VISION_MODEL_LOW = "llava:13b"
VISION_MODEL_HIGH = "llama3.2-vision:90b"

GATILHOS_DE_PRECISAO = [
    r"\bdetalh(ad[oa]?|e|es)\b",
    r"\bprecis[ao]\b",
    r"\bcom\s+riqueza\b",
    r"\bem alta definição\b",
    r"\bcom\s+detalhes\b"
]

def prompt_detalhado(texto_usuario):
    return any(re.search(p, texto_usuario.lower()) for p in GATILHOS_DE_PRECISAO)

def descrever_imagem(caminho_imagem, texto_usuario=""):
    usar_modelo_detalhado = prompt_detalhado(texto_usuario)
    modelo_escolhido = VISION_MODEL_HIGH if usar_modelo_detalhado else VISION_MODEL_LOW

    prompt_modelo = (
        "Descreva a imagem com riqueza de detalhes, em português."
        if usar_modelo_detalhado else
        "Descreva o conteúdo da imagem de forma clara, em português."
    )

    prompt_com_imagem = f"<image>{caminho_imagem}</image>\n{prompt_modelo}"

    try:
        resultado = subprocess.run(
            ["ollama", "run", modelo_escolhido],
            input=prompt_com_imagem,
            capture_output=True,
            encoding="utf-8",
            text=True,
            timeout=600 if usar_modelo_detalhado else 90
        )

        if resultado.returncode != 0:
            return f"Erro ao descrever imagem (código {resultado.returncode}): {resultado.stderr.strip()}"

        saida = resultado.stdout.strip()
        return saida if saida else "Não consegui descrever a imagem."

    except subprocess.TimeoutExpired as e:
        saida_parcial = e.stdout or ""
        return (
            f"A descrição demorou demais e foi interrompida.\n"
            f"Parcial obtida até o momento:\n{saida_parcial.strip()}"
        )

    except Exception as e:
        return f"Erro crítico ao usar LLaMA: {e}"
