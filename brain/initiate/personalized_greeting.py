from datetime import datetime
from brain.audio import say


def personalized_greeting():
    current_hour = datetime.now().hour

    if 5 <= current_hour < 12:
        greeting = (
            "Bom dia Pedro. Jarvis online e pronto apra entrar no codigo da Matrix!"
        )
    elif 12 <= current_hour < 18:
        greeting = (
            "Boa tarde Pedro.  Jarvis online e pronto apra entrar no codigo da Matrix!"
        )
    elif 18 <= current_hour < 23:
        greeting = (
            "Boa noite Pedro. Jarvis online e pronto apra entrar no codigo da Matrix!"
        )
    else:
        greeting = (
            "É madrugada Pedro. Jarvis online e pronto apra entrar no codigo da Matrix!"
        )

    say(greeting)
