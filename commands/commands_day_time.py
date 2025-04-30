from brain.utils_datetime import respond_date, respond_time
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

datetime_commands = {
    "que dia é hoje": date_command,
    "qual é a data de hoje": date_command,
    "que horas são": time_command,
    "me diga as horas": time_command,
    "horas": time_command
}
