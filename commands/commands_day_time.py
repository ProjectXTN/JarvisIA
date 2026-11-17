from brain.utils.utils_datetime import respond_date, respond_time
from brain.audio import say
import core.config  # ✅ Corrigido

def date_command(query):
    response = respond_date()
    if not core.config.IS_API_REQUEST:
        say(response)
    return response

def time_command(query):
    response = respond_time()
    if not core.config.IS_API_REQUEST:
        say(response)
    return response

# Lista de (regex, função). Antes a chave "horas" respondia a hora para
# qualquer frase que tivesse essa palavra.
datetime_commands = [
    (r"\bque dia (é|e) hoje\b", date_command),
    (r"\bqual (é |e )?a data de hoje\b", date_command),
    # "que horas são", mas não "que horas são em Tóquio" (vai para o LLM)
    (r"\bque horas? (são|sao|é|e)\b(?!\s+(agora\s+)?(em|no|na|nos|nas)\b)", time_command),
    (r"\bque horas? tem(os)?\b", time_command),
    (r"\b(diga|fala|fale|informe)( as)? horas\b", time_command),
]
