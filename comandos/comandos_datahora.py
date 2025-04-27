from utils_datetime import respond_date, respond_time
from brain.audio import say

def date_command(query):
    say(respond_date())
    return True

def time_command(query):
    say(respond_time())
    return True

# === COMMANDS DICTIONARY ===
datetime_commands = {
    "que dia é hoje": date_command,
    "qual é a data de hoje": date_command,
    "que horas são": time_command,
    "me diga as horas": time_command,
    "horas": time_command
}
