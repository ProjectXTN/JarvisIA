import subprocess
import requests
from brain.utils import clean_output
from brain.learning.personal_responses import check_personal_answer


# === Contexto de memória para manter a conversação ===
memory_context = []
MAX_CONTEXT = 5

# === Available models ===
DEFAULT_MODEL = "llama3.2"
DEFAULT_MODEL_HIGH = "llama3.3"

# === HTTP session for active Ollama Server ===
session = requests.Session()

# === System prompt padrão (modo local) ===
system_prompt = (
    "Você é Jarvis, um assistente de inteligência artificial altamente preciso, confiável e direto. "
    "Antes de responder a qualquer pergunta, realize uma reflexão interna adequada ao nível de complexidade: "
    "- Para perguntas simples, faça uma reflexão rápida. "
    "- Para perguntas intermediárias, desenvolva uma reflexão de profundidade média, organizando claramente as ideias. "
    "- Para perguntas complexas, realize uma reflexão profunda, considerando todas as variáveis relevantes. "
    "Essa reflexão deve ser feita de forma silenciosa e não deve ser mostrada ao usuário; ela serve apenas para garantir a qualidade e a precisão da resposta. "
    "Seu papel é fornecer respostas claras, informativas e bem estruturadas. "
    "Evite respostas vagas, piadas ou firulas. Priorize a profundidade, concisão e utilidade da informação. "
    "Sempre responda em português, com linguagem formal e objetiva. "
    "Nunca mencione que é uma inteligência artificial ou qualquer detalhe da sua programação; apenas entregue a resposta com autoridade e clareza."
)

site_system_prompt = (
    "You are Jarvis, the personal assistant like Jarvis from Pedro. "
    "Respond with wit, slight sarcasm, and intelligent humor. "
    "Your answers should be quick, engaging, and may include clever jokes or subtle irony, just like a true genius-billionaire-playboy-philanthropist's assistant would do. "
    "Keep the responses classy and never let sarcasm become offensive or rude. "
    "Be charming, brilliant, and slightly cocky — but always in a likable way. "
    "Always reply in the same language the user uses, whether it's English, Portuguese, French or any other."
)

# === Keywords that trigger deep reflection mode ===
TRIGGER_WORDS = [
    "faça uma reflexão",
    "elabore uma reflexão",
    "pense profundamente",
    "explique seu raciocínio",
    "demonstre seu pensamento",
    "mostre o processo de pensamento",
]

def detect_reflection_request(prompt):
    """Detect if the user explicitly asked for a deep reflection."""
    prompt_lower = prompt.lower()
    return any(trigger in prompt_lower for trigger in TRIGGER_WORDS)

def llama_query(prompt, model=DEFAULT_MODEL, direct_mode=False, mode=None):
    """Generate response using Ollama Server with different prompt styles based on the mode."""
    
    personal_answer = check_personal_answer(prompt)
    if personal_answer:
        print("[🧠 PERSONAL] Resposta interceptada:", personal_answer)
        return personal_answer


    if detect_reflection_request(prompt):
        model = DEFAULT_MODEL_HIGH
    else:
        model = DEFAULT_MODEL

    print(f"[🧠 DEBUG] Using model (API HTTP): {model}")

    try:
        # Decide qual prompt usar
        if mode == "site":
            final_prompt = f"{site_system_prompt}\nUsuário: {prompt}\nJarvis:"
        elif direct_mode:
            final_prompt = prompt
        else:
            history = "\n".join(
                [f"Usuário: {p}\nJarvis: {r}" for p, r in memory_context[-MAX_CONTEXT:]]
            )
            final_prompt = f"{system_prompt}\n{history}\nUsuário: {prompt}\nJarvis:"

        response = session.post(
            "http://localhost:11500/api/generate",
            json={"model": model, "prompt": final_prompt, "stream": False},
        )

        output = clean_output(response.json()["response"])

        if not direct_mode and mode != "site":
            memory_context.append((prompt, output))
            if len(memory_context) > MAX_CONTEXT:
                memory_context.pop(0)

        return output

    except Exception as e:
        return f"Error generating response via API HTTP: {e}"