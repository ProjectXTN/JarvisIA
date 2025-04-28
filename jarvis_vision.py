import subprocess
import re

VISION_MODEL_LOW = "llava:13b"
VISION_MODEL_HIGH = "llama3.2-vision:90b"

PRECISION_TRIGGERS = [
    r"\b(detalh(e|es|ado|ada|ados|adas)?)\b",
    r"\bprecisão\b",
    r"\bcom\s+riqueza\b",
    r"\bem alta definição\b",
    r"\bcom\s+detalhes\b"
]

def is_detailed_prompt(user_text):
    return any(re.search(p, user_text.lower()) for p in PRECISION_TRIGGERS)

def describe_image(image_path, user_text=""):
    use_detailed_model = is_detailed_prompt(user_text)
    chosen_model = VISION_MODEL_HIGH if use_detailed_model else VISION_MODEL_LOW

    model_prompt = (
        "Describe the image with rich detail, in Portuguese."
        if use_detailed_model else
        "Describe the image content clearly, in Portuguese."
    )

    prompt_with_image = f"<image>{image_path}</image>\n{model_prompt}"
    
    print(f"🔍 [VISION] Analisando imagem usando modelo: {chosen_model}")

    try:
        result = subprocess.run(
            ["ollama", "run", chosen_model],
            input=prompt_with_image,
            capture_output=True,
            encoding="utf-8",
            text=True,
            timeout=600 if use_detailed_model else 90
        )

        if result.returncode != 0:
            return f"Error describing image (code {result.returncode}): {result.stderr.strip()}"

        output = result.stdout.strip()
        return output if output else "I couldn't describe the image."

    except subprocess.TimeoutExpired as e:
        partial_output = e.stdout or ""
        return (
            f"The description took too long and was interrupted.\n"
            f"Partial output obtained so far:\n{partial_output.strip()}"
        )

    except Exception as e:
        return f"Critical error using LLaMA: {e}"
