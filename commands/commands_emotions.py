import re
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.audio import say
from brain.learning.insert_emotion import register_emotion
from brain.learning.consult_emotions import query_emotions
from brain.learning.normalize_emotions import normalize_emotion
from brain.learning.interpret_date import interpret_date_range



def register_emotional_memory(content):
    try:
        match = re.search(
            r"(lembre que|lembra que|registre que|registro que) (.+?) (me deixou|me fez sentir|me deixa|me deixa com|eu gosto) (.+?)(?: em (.+))?$",
            content,
            re.IGNORECASE,
        )
        if match:
            event = match.group(2).strip()
            raw_emotion = match.group(4).strip().lower()
            emotion = normalize_emotion(raw_emotion)

            date = (
                match.group(5)
                if match.group(5)
                else datetime.now().strftime("%Y-%m-%d")
            )
            tags = None

            success = register_emotion(event, emotion, date, tags)

            if success:
                say(f"Lembrança registrada com emoção '{emotion}'.")
            else:
                say("Não consegui registrar essa lembrança.")
            return True
        else:
            print("[DEBUG] Regex não bateu.")
            say("Não entendi bem o que você quer que eu lembre com emoção.")
            return True
    except Exception as e:
        print(f"[ERROR] Failed to register emotional memory: {e}")
        say("Ocorreu um erro ao tentar registrar sua lembrança.")
        return True

def query_emotional_memory(content):
    try:
        print(f"[DEBUG] Content received for emotional query: {content}")
        match = re.search(
            r"(?:o que\s+|que\s+|)?me\s+(fez feliz|deixou feliz|deixou triste|estressou|marcou|irritou)(.*)?",
            content,
            re.IGNORECASE,
        )
        if match:
            raw_emotion = match.group(1).strip().lower()
            complement = match.group(2).strip().lower() if match.group(2) else ""
            emotion = normalize_emotion(raw_emotion)
            start_date, end_date = interpret_date_range(complement)

            print(f"[DEBUG] Detected emotion: {emotion}")
            print(f"[DEBUG] Date range: {start_date} -> {end_date}")

            results = query_emotions(emotion, start_date, end_date)
            print(f"[DEBUG] Results found: {results}")

            if results:
                sentences = [f"- {r[0]} (em {r[2]})" for r in results]
                response = "\n".join(sentences)
                say(f"Esses eventos te causaram '{emotion}':\n{response}")
            else:
                say(f"Não encontrei lembranças relacionadas a '{emotion}' nesse período.")
            return True
        else:
            print("[DEBUG] No emotion recognized in the sentence.")
            say("Não consegui entender qual emoção ou período você quer que eu consulte.")
            return True
    except Exception as e:
        print(f"[ERROR] Failed to query emotional memory: {e}")
        say("Ocorreu um erro ao tentar lembrar disso.")
        return True

emotional_commands = {
    "lembre que": register_emotional_memory,
    "lembra que": register_emotional_memory,
    "registre que": register_emotional_memory,
    "me fez feliz": query_emotional_memory,
    "me deixou triste": query_emotional_memory,
    "me estressou": query_emotional_memory,
    "me marcou": query_emotional_memory,
    "me irritou": query_emotional_memory,
    "me deixou feliz": query_emotional_memory,
}