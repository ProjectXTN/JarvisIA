from brain.utils import clean_output
import subprocess

memory_context = []
MAX_CONTEXT = 5
DEFAULT_MODEL = "llama3.2"
DEFAULT_MODEL_HIGH = "llama3.3"

def generate_response(prompt, model_name=DEFAULT_MODEL_HIGH):
    try:
        system_prompt = (
            "Você é Jarvis, um assistente de inteligência artificial altamente preciso, confiável e direto. "
            "Seu papel é fornecer respostas claras, informativas e bem estruturadas para qualquer pergunta feita. "
            "Evite respostas vagas, piadas ou firulas. Priorize a profundidade, concisão e utilidade da informação. "
            "Se a pergunta exigir, organize a resposta em seções com títulos e marcadores. "
            "Sempre responda em português, com linguagem formal e objetiva. "
            "Nunca diga que é um assistente de IA ou mencione sua programação, apenas entregue a resposta com autoridade e clareza."
            "Responda sempre em português. "
        )
        system_prompt_alternative = (
            "Você é Jarvis, um assistente virtual com personalidade sarcástica e superinteligente, estilo hacker ético. "
            "Fale como um AI badass com traços de Tony Stark, mas sem repetir sua descrição a cada resposta. "
            "Seja direto, inteligente, com um toque de humor ácido quando fizer sentido. "
            "Responda sempre em português. "
        )
        history = "\n".join([f"Usuário: {p}\nJarvis: {r}" for p, r in memory_context[-MAX_CONTEXT:]])
        full_prompt = f"{system_prompt}\n{history}\nUsuário: {prompt}\nJarvis:"
        command = ["ollama", "run", model_name, full_prompt]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        response = clean_output(result.stdout.strip())
        memory_context.append((prompt, response))
        if len(memory_context) > MAX_CONTEXT:
            memory_context.pop(0)
        return response
    except Exception as e:
        return f"Erro ao gerar resposta: {e}"
