from datetime import datetime
from brain.audio import say

def personalized_greeting():
    current_hour = datetime.now().hour

    if 5 <= current_hour < 12:
        greeting = "Bom dia Pedro. Sistema operacional online."
    elif 12 <= current_hour < 18:
        greeting = "Boa tarde Pedro. Jarvis pronto para auxiliar."
    elif 18 <= current_hour < 23:
        greeting = "Boa noite Pedro. Continuamos operacionais."
    else:
        greeting = "É madrugada Pedro. Sistemas em modo de vigilância."

    say(greeting)
